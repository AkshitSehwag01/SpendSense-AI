import atexit
import math
import os
import sqlite3
import threading
from contextlib import contextmanager
from datetime import date, datetime, timezone
from pathlib import Path

from utils.constants import EXPENSE_CATEGORIES, INCOME_CATEGORIES


# SQLite file used when no DATABASE_URL is configured (local mode)
DB_PATH = Path(__file__).parent / "spendsense.db"

MAX_AMOUNT = 100_000_000.0
MAX_DESCRIPTION_LENGTH = 200

# Reserved account that owns data created before user accounts existed.
# It cannot sign in. It is also the account used when login is switched
# off (local mode).
LOCAL_USER_ID = 1
LOCAL_USER_EMAIL = "local@spendsense.local"

# Canonical spellings. Lookup is case-insensitive, so "emi / loans"
# and "EMI / LOANS" are both saved as "EMI / Loans".
KNOWN_CATEGORIES = list(
    dict.fromkeys(EXPENSE_CATEGORIES + INCOME_CATEGORIES)
)

_CANONICAL_CATEGORY = {
    name.casefold(): name for name in KNOWN_CATEGORIES
}


# =========================================================
# Choosing the database
#
# No DATABASE_URL  -> SQLite file on this computer (local mode)
# DATABASE_URL set -> PostgreSQL (hosted mode, e.g. Neon)
#
# All SQL in this file is written with "?" placeholders. For Postgres
# they are converted to "%s" in one place (_Connection.execute).
# =========================================================

def _database_url():
    """The Postgres address from the environment or Streamlit secrets."""

    url = os.environ.get("DATABASE_URL", "").strip()

    if url:
        return url

    try:
        import streamlit as st

        return str(st.secrets.get("DATABASE_URL", "") or "").strip()
    except Exception:
        return ""


def database_backend():
    """'postgres' or 'sqlite' (useful for checks and debugging)."""
    return "postgres" if _database_url() else "sqlite"


def _load_psycopg():
    try:
        import psycopg
        from psycopg.rows import dict_row
    except ImportError:
        raise RuntimeError(
            "DATABASE_URL is set, but the 'psycopg' package is not "
            'installed. Run: pip install "psycopg[binary,pool]"'
        )

    return psycopg, dict_row


class _Connection:
    """Small wrapper so the same SQL works on SQLite and Postgres."""

    def __init__(self, raw, postgres):
        self._raw = raw
        self.postgres = postgres

    def execute(self, sql, params=()):
        if self.postgres:
            sql = sql.replace("?", "%s")

        return self._raw.execute(sql, params)

    @property
    def in_transaction(self):
        return bool(getattr(self._raw, "in_transaction", False))


_pool = None
_pool_url = None
_pool_lock = threading.Lock()
_exit_hook_registered = False


def close_pool():
    """Close the shared connections (called automatically at exit)."""

    global _pool, _pool_url

    with _pool_lock:
        if _pool is not None:
            try:
                _pool.close()
            except Exception:
                pass

        _pool = None
        _pool_url = None


def _get_pool(url):
    """
    One shared set of open connections, created on first use.

    Opening a new secure connection takes several network round trips,
    so reusing connections makes every page noticeably faster.
    Returns None if the optional 'psycopg_pool' package is missing
    (the app then still works, just more slowly).
    """

    global _pool, _pool_url, _exit_hook_registered

    with _pool_lock:
        if _pool is not None and _pool_url == url:
            return _pool

        try:
            from psycopg_pool import ConnectionPool
        except ImportError:
            return None

        _, dict_row = _load_psycopg()

        if _pool is not None:
            try:
                _pool.close()
            except Exception:
                pass

        _pool = ConnectionPool(
            url,
            min_size=1,
            max_size=6,
            kwargs={
                "row_factory": dict_row,
                # keeps this safe behind Neon's pooler
                "prepare_threshold": None,
                "connect_timeout": 20,
                # No automatic BEGIN / COMMIT around every statement.
                # Each statement is already atomic on its own; steps that
                # must succeed together use get_connection(atomic=True).
                "autocommit": True,
            },
            # test a connection before lending it out, so one that the
            # database closed while idle is replaced instead of failing
            check=ConnectionPool.check_connection,
            max_idle=120,
            max_lifetime=900,
            timeout=20,
            open=False,
        )
        _pool.open()
        _pool_url = url

        if not _exit_hook_registered:
            atexit.register(close_pool)
            _exit_hook_registered = True

        return _pool


@contextmanager
def get_connection(atomic=False):
    """
    Open a database connection that commits on success,
    rolls back on error, and is always released.

    atomic=True makes several statements succeed or fail together.
    """

    url = _database_url()

    if url:
        if not url.startswith(("postgresql://", "postgres://")):
            raise RuntimeError(
                "DATABASE_URL must start with postgresql://"
            )

        pool = _get_pool(url)

        if pool is not None:
            # Pooled connection path
            with pool.connection() as raw:
                if atomic:
                    with raw.transaction():
                        yield _Connection(raw, postgres=True)
                else:
                    yield _Connection(raw, postgres=True)
            return  # Cleanly exit pooled path

        # Non-pooled PostgreSQL fallback path
        psycopg, dict_row = _load_psycopg()
        raw = psycopg.connect(
            url,
            row_factory=dict_row,
            prepare_threshold=None,
            connect_timeout=20,
        )
        try:
            connection = _Connection(raw, postgres=True)
            yield connection
            raw.commit()
        except Exception:
            raw.rollback()
            raise
        finally:
            raw.close()
        return  # Cleanly exit non-pooled Postgres path

    # SQLite (Local Mode) path — reached when no DATABASE_URL is set
    raw = sqlite3.connect(DB_PATH, timeout=10)
    raw.row_factory = sqlite3.Row
    connection = _Connection(raw, postgres=False)

    try:
        yield connection
        raw.commit()
    except Exception:
        raw.rollback()
        raise
    finally:
        raw.close()


def _insert_returning_id(connection, sql, params):
    """Run an INSERT and return the new row's ID on either database."""

    if connection.postgres:
        row = connection.execute(sql + " RETURNING id", params).fetchone()
        return int(row["id"])

    return connection.execute(sql, params).lastrowid


def _is_integrity_error(error):
    """True for 'duplicate / constraint' errors from SQLite or Postgres."""

    if isinstance(error, sqlite3.IntegrityError):
        return True

    return any(
        cls.__module__.startswith("psycopg")
        and cls.__name__ == "IntegrityError"
        for cls in type(error).__mro__
    )


# =========================================================
# Setup and migration
# =========================================================

def initialize_database():
    """Create tables and indexes, and upgrade older databases."""

    with get_connection(atomic=True) as connection:
        if connection.postgres:
            _create_schema_postgres(connection)
        else:
            _create_schema_sqlite(connection)


def _create_schema_postgres(connection):
    connection.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
            email TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            display_name TEXT DEFAULT '',
            failed_attempts INTEGER NOT NULL DEFAULT 0,
            locked_until TEXT,
            terms_accepted_at TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    # Databases created before the terms were added get the new column.
    connection.execute(
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS terms_accepted_at TEXT"
    )

    # Emails are unique regardless of capital letters.
    connection.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email_lower
        ON users (LOWER(email))
    """)

    # Reserved local account. On a new database it becomes ID 1.
    local = connection.execute(
        "SELECT id FROM users WHERE email = ?",
        (LOCAL_USER_EMAIL,),
    ).fetchone()

    if local is None:
        connection.execute(
            """
            INSERT INTO users (email, password_hash, display_name)
            VALUES (?, '!', 'Local user')
            ON CONFLICT DO NOTHING
            """,
            (LOCAL_USER_EMAIL,),
        )

        local = connection.execute(
            "SELECT id FROM users WHERE email = ?",
            (LOCAL_USER_EMAIL,),
        ).fetchone()

    if local is None or int(local["id"]) != LOCAL_USER_ID:
        raise RuntimeError(
            "The reserved local account must have ID 1. "
            "This database was not created by SpendSense AI."
        )

    connection.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
            user_id BIGINT NOT NULL DEFAULT 1,
            transaction_type TEXT NOT NULL
                CHECK (transaction_type IN ('Income', 'Expense')),
            amount DOUBLE PRECISION NOT NULL CHECK (amount > 0),
            category TEXT NOT NULL,
            description TEXT DEFAULT '',
            transaction_date TEXT NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS budgets (
            id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
            user_id BIGINT NOT NULL DEFAULT 1,
            month TEXT NOT NULL,
            category TEXT NOT NULL,
            amount DOUBLE PRECISION NOT NULL CHECK (amount >= 0),
            UNIQUE (user_id, month, category)
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
            user_id BIGINT NOT NULL,
            token_hash TEXT NOT NULL UNIQUE,
            expires_at TEXT NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    connection.execute("""
        CREATE INDEX IF NOT EXISTS idx_sessions_user
        ON sessions (user_id)
    """)

    connection.execute("""
        CREATE INDEX IF NOT EXISTS idx_transactions_user_date
        ON transactions (user_id, transaction_date)
    """)

    connection.execute("""
        CREATE INDEX IF NOT EXISTS idx_transactions_user_type
        ON transactions (user_id, transaction_type)
    """)


def _column_names(connection, table):
    rows = connection.execute(f"PRAGMA table_info({table})").fetchall()
    return {row["name"] for row in rows}


def _create_schema_sqlite(connection):
    connection.execute("PRAGMA journal_mode = WAL")

    connection.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE COLLATE NOCASE,
            password_hash TEXT NOT NULL,
            display_name TEXT DEFAULT '',
            failed_attempts INTEGER NOT NULL DEFAULT 0,
            locked_until TEXT,
            terms_accepted_at TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Reserved local account ("!" is never a valid password hash).
    connection.execute(
        """
        INSERT OR IGNORE INTO users (id, email, password_hash, display_name)
        VALUES (?, ?, '!', 'Local user')
        """,
        (LOCAL_USER_ID, LOCAL_USER_EMAIL),
    )

    if "terms_accepted_at" not in _column_names(connection, "users"):
        connection.execute(
            "ALTER TABLE users ADD COLUMN terms_accepted_at TEXT"
        )

    connection.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL DEFAULT 1,
            transaction_type TEXT NOT NULL
                CHECK (
                    transaction_type IN ('Income', 'Expense')
                ),
            amount REAL NOT NULL CHECK (amount > 0),
            category TEXT NOT NULL,
            description TEXT DEFAULT '',
            transaction_date TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL DEFAULT 1,
            month TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL CHECK (amount >= 0),
            UNIQUE(user_id, month, category)
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token_hash TEXT NOT NULL UNIQUE,
            expires_at TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    connection.execute("""
        CREATE INDEX IF NOT EXISTS idx_sessions_user
        ON sessions (user_id)
    """)

    _migrate_sqlite_to_multi_user(connection)

    connection.execute("DROP INDEX IF EXISTS idx_transactions_date")
    connection.execute("DROP INDEX IF EXISTS idx_transactions_type")

    connection.execute("""
        CREATE INDEX IF NOT EXISTS idx_transactions_user_date
        ON transactions (user_id, transaction_date)
    """)

    connection.execute("""
        CREATE INDEX IF NOT EXISTS idx_transactions_user_type
        ON transactions (user_id, transaction_type)
    """)

    _repair_category_spelling(connection)


def _migrate_sqlite_to_multi_user(connection):
    """
    Upgrade SQLite databases created before user accounts existed.
    Existing rows are kept and assigned to the local account.
    Runs inside one transaction, so a failure changes nothing.
    """

    if not connection.in_transaction:
        connection.execute("BEGIN")

    if "user_id" not in _column_names(connection, "transactions"):
        connection.execute(
            f"""
            ALTER TABLE transactions
            ADD COLUMN user_id INTEGER NOT NULL DEFAULT {LOCAL_USER_ID}
            """
        )

    if "user_id" not in _column_names(connection, "budgets"):
        # The unique rule changes from (month, category) to
        # (user_id, month, category), which needs a table rebuild.
        connection.execute("ALTER TABLE budgets RENAME TO budgets_old")

        connection.execute("""
            CREATE TABLE budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL DEFAULT 1,
                month TEXT NOT NULL,
                category TEXT NOT NULL,
                amount REAL NOT NULL CHECK (amount >= 0),
                UNIQUE(user_id, month, category)
            )
        """)

        connection.execute(
            """
            INSERT INTO budgets (user_id, month, category, amount)
            SELECT ?, month, category, amount FROM budgets_old
            """,
            (LOCAL_USER_ID,),
        )

        connection.execute("DROP TABLE budgets_old")


def _repair_category_spelling(connection):
    """
    Fix rows saved by older versions that title-cased every category
    (for example "Emi / Loans" instead of "EMI / Loans").
    Only needed for old SQLite files. Cheap and safe to repeat.
    """

    for canonical in KNOWN_CATEGORIES:
        for table in ("transactions", "budgets"):
            connection.execute(
                f"""
                UPDATE OR IGNORE {table}
                SET category = ?
                WHERE LOWER(category) = ?
                  AND category <> ?
                """,
                (canonical, canonical.casefold(), canonical),
            )


# =========================================================
# User helpers
# =========================================================

def _resolve_user_id(user_id):
    """
    Use the given user, or the signed-in user when none is given.
    Fails closed: with no signed-in user, nothing is read or written.
    """

    if user_id is None:
        # Imported here to avoid a circular import (auth uses this file).
        from auth import current_user_id

        user_id = current_user_id()

    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        raise ValueError("Invalid user.")

    if user_id <= 0:
        raise ValueError("Invalid user.")

    return user_id


def create_user(email, password_hash, display_name="", terms_accepted_at=None):
    """Create an account. Returns the new user's ID."""

    with get_connection() as connection:
        try:
            return _insert_returning_id(
                connection,
                """
                INSERT INTO users (
                    email, password_hash, display_name, terms_accepted_at
                )
                VALUES (?, ?, ?, ?)
                """,
                (email, password_hash, display_name, terms_accepted_at),
            )
        except Exception as error:
            if _is_integrity_error(error):
                raise ValueError(
                    "An account with this email already exists."
                )
            raise


def get_user_by_email(email):
    """Return the user as a dict, or None."""

    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM users WHERE LOWER(email) = LOWER(?)",
            (email,),
        ).fetchone()

    return dict(row) if row else None


def get_user(user_id):
    """Return the user as a dict, or None."""

    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM users WHERE id = ?",
            (int(user_id),),
        ).fetchone()

    return dict(row) if row else None


def set_login_state(user_id, failed_attempts, locked_until):
    """Store the failed-login counter and lock time for a user."""

    with get_connection() as connection:
        connection.execute(
            """
            UPDATE users
            SET failed_attempts = ?, locked_until = ?
            WHERE id = ?
            """,
            (int(failed_attempts), locked_until, int(user_id)),
        )


def claim_local_data(user_id):
    """
    Move everything saved before accounts existed (the local account's
    transactions and budgets) to a real account.
    Returns (transactions moved, budgets moved).
    """

    user_id = _resolve_user_id(user_id)

    if user_id == LOCAL_USER_ID:
        return 0, 0

    with get_connection(atomic=True) as connection:
        moved_transactions = connection.execute(
            "UPDATE transactions SET user_id = ? WHERE user_id = ?",
            (user_id, LOCAL_USER_ID),
        ).rowcount

        if connection.postgres:
            moved_budgets = connection.execute(
                """
                UPDATE budgets
                SET user_id = ?
                WHERE user_id = ?
                  AND NOT EXISTS (
                      SELECT 1 FROM budgets AS other
                      WHERE other.user_id = ?
                        AND other.month = budgets.month
                        AND other.category = budgets.category
                  )
                """,
                (user_id, LOCAL_USER_ID, user_id),
            ).rowcount
        else:
            moved_budgets = connection.execute(
                """
                UPDATE OR IGNORE budgets
                SET user_id = ?
                WHERE user_id = ?
                """,
                (user_id, LOCAL_USER_ID),
            ).rowcount

    return moved_transactions, moved_budgets


def create_session(user_id, token_hash, expires_at):
    """Store a 'stay signed in' session (only the token's hash is kept)."""

    user_id = _resolve_user_id(user_id)

    with get_connection() as connection:
        # Tidy up sessions that have already expired.
        connection.execute(
            "DELETE FROM sessions WHERE expires_at < ?",
            (datetime.now(timezone.utc).isoformat(),),
        )

        connection.execute(
            """
            INSERT INTO sessions (user_id, token_hash, expires_at)
            VALUES (?, ?, ?)
            """,
            (user_id, token_hash, expires_at),
        )


def get_session(token_hash):
    """Return {'user_id', 'expires_at'} for a session, or None."""

    with get_connection() as connection:
        row = connection.execute(
            "SELECT user_id, expires_at FROM sessions WHERE token_hash = ?",
            (token_hash,),
        ).fetchone()

    return dict(row) if row else None


def delete_session(token_hash):
    """End one session (used when logging out)."""

    with get_connection() as connection:
        connection.execute(
            "DELETE FROM sessions WHERE token_hash = ?",
            (token_hash,),
        )


def delete_user_sessions(user_id):
    """End every session of a user (used after a password change)."""

    with get_connection() as connection:
        connection.execute(
            "DELETE FROM sessions WHERE user_id = ?",
            (int(user_id),),
        )


def delete_user_account(user_id):
    """
    Permanently delete an account with all its transactions and budgets.
    Returns (transactions deleted, budgets deleted).
    """

    user_id = _resolve_user_id(user_id)

    if user_id == LOCAL_USER_ID:
        raise ValueError("The local account cannot be deleted.")

    with get_connection(atomic=True) as connection:
        deleted_transactions = connection.execute(
            "DELETE FROM transactions WHERE user_id = ?",
            (user_id,),
        ).rowcount

        deleted_budgets = connection.execute(
            "DELETE FROM budgets WHERE user_id = ?",
            (user_id,),
        ).rowcount

        connection.execute(
            "DELETE FROM sessions WHERE user_id = ?", (user_id,)
        )

        connection.execute("DELETE FROM users WHERE id = ?", (user_id,))

    return deleted_transactions, deleted_budgets


# =========================================================
# Validation helpers
# =========================================================

def normalize_category(category):
    """Validate and standardize a category name."""

    if not isinstance(category, str):
        raise ValueError("Category must be text.")

    category = " ".join(category.split())

    if not category:
        raise ValueError("Category cannot be empty.")

    if len(category) > 50:
        raise ValueError("Category must be 50 characters or fewer.")

    known = _CANONICAL_CATEGORY.get(category.casefold())

    if known:
        return known

    return category.title()


def validate_amount(amount, allow_zero=False):
    """Validate and round monetary amounts to 2 decimals."""

    try:
        amount = float(amount)
    except (TypeError, ValueError):
        raise ValueError("Amount must be a valid number.")

    if not math.isfinite(amount):
        raise ValueError("Amount must be a finite number.")

    amount = round(amount, 2)

    if amount < 0:
        raise ValueError("Amount cannot be negative.")

    if amount == 0 and not allow_zero:
        raise ValueError("Amount must be greater than zero.")

    if amount > MAX_AMOUNT:
        raise ValueError(
            f"Amount cannot exceed {MAX_AMOUNT:,.0f}."
        )

    return amount


def validate_transaction_type(transaction_type):
    """Validate transaction type."""

    if transaction_type not in ("Income", "Expense"):
        raise ValueError(
            "Transaction type must be Income or Expense."
        )

    return transaction_type


def validate_transaction_id(transaction_id):
    """Validate a transaction ID (accepts numpy integers too)."""

    try:
        transaction_id = int(transaction_id)
    except (TypeError, ValueError):
        raise ValueError("Transaction ID must be a whole number.")

    if transaction_id <= 0:
        raise ValueError("Transaction ID must be positive.")

    return transaction_id


def validate_transaction_date(transaction_date):
    """Validate and standardize transaction dates."""

    # Accept date / datetime objects as well as text.
    if isinstance(transaction_date, datetime):
        return transaction_date.strftime("%Y-%m-%d %H:%M:%S")

    if isinstance(transaction_date, date):
        return transaction_date.strftime("%Y-%m-%d")

    if not isinstance(transaction_date, str):
        raise ValueError("Transaction date must be text or a date.")

    transaction_date = transaction_date.strip()

    if not transaction_date:
        raise ValueError("Transaction date cannot be empty.")

    for date_format in (
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
    ):
        try:
            parsed = datetime.strptime(transaction_date, date_format)
        except ValueError:
            continue

        if date_format == "%Y-%m-%d":
            return parsed.strftime("%Y-%m-%d")

        return parsed.strftime("%Y-%m-%d %H:%M:%S")

    raise ValueError("Invalid date. Use YYYY-MM-DD format.")


def validate_month(month):
    """Validate a budget month in YYYY-MM format."""

    if not isinstance(month, str):
        raise ValueError("Month must be text.")

    month = month.strip()

    try:
        datetime.strptime(month, "%Y-%m")
    except ValueError:
        raise ValueError("Invalid month. Use YYYY-MM format.")

    return month


def normalize_description(description):
    """Convert a missing description into an empty string."""

    if description is None:
        return ""

    if not isinstance(description, str):
        raise ValueError("Description must be text.")

    description = " ".join(description.split())

    if len(description) > MAX_DESCRIPTION_LENGTH:
        raise ValueError(
            f"Description must be {MAX_DESCRIPTION_LENGTH} "
            "characters or fewer."
        )

    return description


# =========================================================
# Transaction operations
# (every query is limited to one user's own rows)
# =========================================================

def add_transaction(
    transaction_type,
    amount,
    category,
    description,
    transaction_date,
    user_id=None,
):
    """Save a new income or expense transaction."""

    user_id = _resolve_user_id(user_id)
    transaction_type = validate_transaction_type(transaction_type)
    amount = validate_amount(amount)
    category = normalize_category(category)
    description = normalize_description(description)
    transaction_date = validate_transaction_date(transaction_date)

    with get_connection() as connection:
        return _insert_returning_id(
            connection,
            """
            INSERT INTO transactions (
                user_id,
                transaction_type,
                amount,
                category,
                description,
                transaction_date
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                transaction_type,
                amount,
                category,
                description,
                transaction_date,
            ),
        )


def get_transactions(user_id=None):
    """Retrieve the user's transactions, newest first."""

    user_id = _resolve_user_id(user_id)

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                id,
                transaction_type,
                amount,
                category,
                description,
                transaction_date,
                CAST(created_at AS TEXT) AS created_at
            FROM transactions
            WHERE user_id = ?
            ORDER BY transaction_date DESC, id DESC
            """,
            (user_id,),
        ).fetchall()

    return [dict(row) for row in rows]


def delete_transaction(transaction_id, user_id=None):
    """Delete one of the user's transactions. Returns rows deleted."""

    user_id = _resolve_user_id(user_id)
    transaction_id = validate_transaction_id(transaction_id)

    with get_connection() as connection:
        cursor = connection.execute(
            "DELETE FROM transactions WHERE id = ? AND user_id = ?",
            (transaction_id, user_id),
        )

        return cursor.rowcount


def update_transaction(
    transaction_id,
    transaction_type,
    amount,
    category,
    description,
    transaction_date,
    user_id=None,
):
    """Update one of the user's transactions. Returns rows updated."""

    user_id = _resolve_user_id(user_id)
    transaction_id = validate_transaction_id(transaction_id)
    transaction_type = validate_transaction_type(transaction_type)
    amount = validate_amount(amount)
    category = normalize_category(category)
    description = normalize_description(description)
    transaction_date = validate_transaction_date(transaction_date)

    with get_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE transactions
            SET transaction_type = ?,
                amount = ?,
                category = ?,
                description = ?,
                transaction_date = ?
            WHERE id = ? AND user_id = ?
            """,
            (
                transaction_type,
                amount,
                category,
                description,
                transaction_date,
                transaction_id,
                user_id,
            ),
        )

        return cursor.rowcount


# =========================================================
# Budget operations
# =========================================================

def save_budget(month, category, amount, user_id=None):
    """Create or update a monthly category budget."""

    user_id = _resolve_user_id(user_id)
    month = validate_month(month)
    category = normalize_category(category)
    amount = validate_amount(amount, allow_zero=True)

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO budgets (user_id, month, category, amount)
            VALUES (?, ?, ?, ?)
            ON CONFLICT (user_id, month, category)
            DO UPDATE SET amount = excluded.amount
            """,
            (user_id, month, category, amount),
        )


def get_budgets(month, user_id=None):
    """Retrieve the user's category budgets for a given month."""

    user_id = _resolve_user_id(user_id)
    month = validate_month(month)

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT category, amount
            FROM budgets
            WHERE user_id = ? AND month = ?
            ORDER BY category
            """,
            (user_id, month),
        ).fetchall()

    return {row["category"]: row["amount"] for row in rows}


def delete_budget(month, category, user_id=None):
    """Delete one of the user's category budgets. Returns rows deleted."""

    user_id = _resolve_user_id(user_id)
    month = validate_month(month)
    category = normalize_category(category)

    with get_connection() as connection:
        cursor = connection.execute(
            """
            DELETE FROM budgets
            WHERE user_id = ? AND month = ? AND category = ?
            """,
            (user_id, month, category),
        )

        return cursor.rowcount
    
def get_all_budgets(user_id=None):
    """Retrieve all of the user's budgets across every month."""

    user_id = _resolve_user_id(user_id)

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT month, category, amount
            FROM budgets
            WHERE user_id = ?
            ORDER BY month DESC, category
            """,
            (user_id,),
        ).fetchall()

    return [dict(row) for row in rows]

def save_budgets_batch(month, budget_dict, user_id=None):
    """Create or update multiple category budgets in a single database transaction."""

    user_id = _resolve_user_id(user_id)
    month = validate_month(month)

    validated_items = []
    for category, amount in budget_dict.items():
        cat = normalize_category(category)
        amt = validate_amount(amount, allow_zero=True)
        validated_items.append((user_id, month, cat, amt))

    if not validated_items:
        return

    with get_connection(atomic=True) as connection:
        for item in validated_items:
            connection.execute(
                """
                INSERT INTO budgets (user_id, month, category, amount)
                VALUES (?, ?, ?, ?)
                ON CONFLICT (user_id, month, category)
                DO UPDATE SET amount = excluded.amount
                """,
                item,
            )