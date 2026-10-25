"""
Quick health check for the SpendSense AI database.

Run it from the project folder:

    python check_database.py

It works on whichever database is configured (SQLite on your computer,
or Postgres when DATABASE_URL is set). It creates two temporary test
accounts, tries the main operations, and removes everything it made.
"""

import sys
import time
import uuid
from datetime import date

import database as db


failures = []


def check(name, ok, detail=""):
    mark = "PASS" if ok else "FAIL"
    print(f"  {mark}  {name}" + (f"  ({detail})" if detail else ""))

    if not ok:
        failures.append(name)


def main():
    print(f"Database in use: {db.database_backend()}")
    print()

    db.initialize_database()
    check("Tables created / upgraded", True)

    tag = uuid.uuid4().hex[:8]
    month = date.today().strftime("%Y-%m")
    user_ids = []

    try:
        user_a = db.create_user(f"check-a-{tag}@example.com", "x", "Check A")
        user_b = db.create_user(f"check-b-{tag}@example.com", "x", "Check B")
        user_ids = [user_a, user_b]
        check("Two test accounts created", user_a != user_b)

        try:
            db.create_user(f"CHECK-A-{tag}@example.com", "x")
            check("Duplicate email (different case) refused", False)
        except ValueError:
            check("Duplicate email (different case) refused", True)

        transaction_id = db.add_transaction(
            "Expense", 123.45, "Food", "check", date.today().isoformat(),
            user_id=user_a,
        )
        check("Transaction saved", transaction_id > 0)

        db.save_budget(month, "Food", 5000, user_id=user_a)
        db.save_budget(month, "Food", 6000, user_id=user_a)
        budgets = db.get_budgets(month, user_id=user_a)
        check(
            "Budget saved and updated (no duplicate)",
            budgets == {"Food": 6000.0},
            str(budgets),
        )

        started = time.perf_counter()
        rows = db.get_transactions(user_id=user_a)
        elapsed_ms = (time.perf_counter() - started) * 1000

        check("Transaction read back", len(rows) == 1)
        check(
            "Amount comes back as a normal number",
            rows and isinstance(rows[0]["amount"], float)
            and rows[0]["amount"] == 123.45,
            repr(rows[0]["amount"]) if rows else "",
        )
        check(
            "One read takes under 1 second",
            elapsed_ms < 1000,
            f"{elapsed_ms:.0f} ms",
        )

        check(
            "Other account sees none of it",
            db.get_transactions(user_id=user_b) == []
            and db.get_budgets(month, user_id=user_b) == {},
        )
        check(
            "Other account cannot delete it",
            db.delete_transaction(transaction_id, user_id=user_b) == 0,
        )
        check(
            "Owner can delete it",
            db.delete_transaction(transaction_id, user_id=user_a) == 1,
        )

        found = db.get_user_by_email(f"CHECK-A-{tag}@example.com")
        check("Email lookup ignores capital letters", found is not None)

    finally:
        with db.get_connection() as connection:
            for user_id in user_ids:
                connection.execute(
                    "DELETE FROM transactions WHERE user_id = ?", (user_id,)
                )
                connection.execute(
                    "DELETE FROM budgets WHERE user_id = ?", (user_id,)
                )
                connection.execute(
                    "DELETE FROM users WHERE id = ?", (user_id,)
                )

        print()
        print("Test accounts and data removed.")

    db.close_pool()

    print()

    if failures:
        print(f"{len(failures)} check(s) FAILED: " + ", ".join(failures))
        sys.exit(1)

    print("All checks passed.")


if __name__ == "__main__":
    main()