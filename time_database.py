"""
Measures how fast your computer can talk to the Postgres database.

Run it from the project folder (with DATABASE_URL set):

    python time_database.py

It does not print or save your database address.
"""

import os
import statistics
import sys
import time

try:
    import psycopg
except ImportError:
    print('psycopg is not installed. Run: pip install "psycopg[binary]"')
    sys.exit(1)


url = os.environ.get("DATABASE_URL", "").strip()

if not url:
    print("DATABASE_URL is not set in this terminal. Set it first.")
    sys.exit(1)


def ms(seconds):
    return f"{seconds * 1000:.0f} ms"


def connect():
    return psycopg.connect(url, connect_timeout=15, prepare_threshold=None)


print("Measuring from this computer to your database...")
print()

try:
    # Warm-up: the first call may wake the database from sleep.
    started = time.perf_counter()
    warm = connect()
    warm.execute("SELECT 1").fetchone()
    warm.close()
    print(f"Wake-up call (first connection): {ms(time.perf_counter() - started)}")

    # Opening a brand-new connection each time (what the app does today).
    connect_times = []
    for _ in range(3):
        started = time.perf_counter()
        connection = connect()
        connect_times.append(time.perf_counter() - started)
        connection.close()

    # Asking questions on one connection that stays open.
    connection = connect()
    connection.execute("SELECT 1").fetchone()

    query_times = []
    for _ in range(5):
        started = time.perf_counter()
        connection.execute("SELECT 1").fetchone()
        query_times.append(time.perf_counter() - started)

    connection.close()

except Exception as error:
    print(f"Could not measure: {type(error).__name__}")
    sys.exit(1)

connect_median = statistics.median(connect_times)
query_median = statistics.median(query_times)

print(f"Open a new connection (3 tries): "
      + ", ".join(ms(t) for t in connect_times))
print(f"One question on an open connection (5 tries): "
      + ", ".join(ms(t) for t in query_times))
print()
print(f"Typical new connection:  {ms(connect_median)}")
print(f"Typical question:        {ms(query_median)}")
print()

if query_median < 0.1:
    print("Distance to the database is small. Good.")
elif query_median < 0.4:
    print("The database is far from this computer (probably a different "
          "continent). Normal when testing from India against Ohio.")
else:
    print("The database is very slow to answer from here. Check your "
          "internet connection and try again.")

if connect_median > query_median * 3:
    print("Opening connections is the expensive part, so reusing one "
          "connection would make the app noticeably faster.")