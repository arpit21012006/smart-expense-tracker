import sqlite3
from datetime import datetime
from getpass import getpass

import psycopg2


SQLITE_DATABASE = "expenses.db"
DEFAULT_BUDGET = 10000.0


def parse_date(value):
    """Convert SQLite YYYY-MM-DD text into a PostgreSQL-friendly date."""
    if not value:
        return None

    try:
        return datetime.strptime(str(value), "%Y-%m-%d").date()
    except ValueError:
        return None


def main():
    print("=" * 60)
    print("Smart Expense Tracker")
    print("SQLite -> Render PostgreSQL Migration")
    print("=" * 60)
    print()
    print("IMPORTANT:")
    print("Use the NEW/ROTATED PostgreSQL credential.")
    print("Use the EXTERNAL Database URL because this script runs on your PC.")
    print("Do NOT commit this URL into GitHub.")
    print()

    database_url = getpass("Paste External Database URL: ").strip()

    if not database_url:
        print("No database URL entered. Exiting.")
        return

    sqlite_conn = None
    postgres_conn = None

    try:
        # ---------------------------------------------------------
        # 1. Read local SQLite database
        # ---------------------------------------------------------
        sqlite_conn = sqlite3.connect(SQLITE_DATABASE)
        sqlite_cursor = sqlite_conn.cursor()

        sqlite_cursor.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                expense_date TEXT
            )
        """)

        sqlite_cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY,
                budget REAL NOT NULL
            )
        """)

        sqlite_cursor.execute("""
            SELECT id, name, amount, category, expense_date
            FROM expenses
            ORDER BY id
        """)

        sqlite_expenses = sqlite_cursor.fetchall()

        sqlite_cursor.execute("""
            SELECT budget
            FROM settings
            WHERE id = 1
        """)

        budget_row = sqlite_cursor.fetchone()
        sqlite_budget = (
            float(budget_row[0])
            if budget_row
            else DEFAULT_BUDGET
        )

        print(f"Local SQLite expenses found: {len(sqlite_expenses)}")
        print(f"Local SQLite budget: ₹{sqlite_budget:.2f}")
        print()

        # ---------------------------------------------------------
        # 2. Connect to Render PostgreSQL
        # ---------------------------------------------------------
        print("Connecting to PostgreSQL...")
        postgres_conn = psycopg2.connect(
            database_url,
            connect_timeout=15
        )
        postgres_cursor = postgres_conn.cursor()

        # ---------------------------------------------------------
        # 3. Ensure schema exists
        # ---------------------------------------------------------
        postgres_cursor.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id BIGSERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                amount DOUBLE PRECISION NOT NULL,
                category TEXT NOT NULL,
                expense_date DATE
            )
        """)

        postgres_cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY,
                budget DOUBLE PRECISION NOT NULL
            )
        """)

        postgres_conn.commit()

        # ---------------------------------------------------------
        # 4. Read current PostgreSQL state
        # ---------------------------------------------------------
        postgres_cursor.execute("SELECT COUNT(*) FROM expenses")
        before_count = postgres_cursor.fetchone()[0]

        postgres_cursor.execute("""
            SELECT id, name, amount, category, expense_date
            FROM expenses
            ORDER BY id
        """)

        existing_by_id = {}

        for row in postgres_cursor.fetchall():
            existing_by_id[int(row[0])] = row

        print(f"PostgreSQL expenses before migration: {before_count}")
        print()

        # ---------------------------------------------------------
        # 5. Migrate expenses
        #
        # Preserve original SQLite IDs whenever possible.
        # If an ID already exists in PostgreSQL:
        #   - same record -> skip
        #   - different record -> insert with a new PostgreSQL ID
        # ---------------------------------------------------------
        inserted = 0
        skipped = 0
        conflicted = 0

        for expense in sqlite_expenses:
            sqlite_id, name, amount, category, expense_date = expense

            amount = float(amount)
            pg_date = parse_date(expense_date)

            existing = existing_by_id.get(int(sqlite_id))

            if existing:
                existing_same = (
                    str(existing[1]) == str(name)
                    and abs(float(existing[2]) - amount) < 0.000001
                    and str(existing[3]) == str(category)
                    and (
                        str(existing[4]) == str(pg_date)
                        or (
                            existing[4] is None
                            and pg_date is None
                        )
                    )
                )

                if existing_same:
                    skipped += 1
                    continue

                # ID collision with a different record.
                postgres_cursor.execute("""
                    INSERT INTO expenses
                        (name, amount, category, expense_date)
                    VALUES (%s, %s, %s, %s)
                """, (
                    name,
                    amount,
                    category,
                    pg_date
                ))

                inserted += 1
                conflicted += 1
                continue

            # No collision: preserve SQLite's original ID.
            postgres_cursor.execute("""
                INSERT INTO expenses
                    (id, name, amount, category, expense_date)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                int(sqlite_id),
                name,
                amount,
                category,
                pg_date
            ))

            inserted += 1

        # ---------------------------------------------------------
        # 6. Migrate the budget setting
        # ---------------------------------------------------------
        postgres_cursor.execute("""
            INSERT INTO settings (id, budget)
            VALUES (%s, %s)
            ON CONFLICT (id)
            DO UPDATE SET budget = EXCLUDED.budget
        """, (
            1,
            sqlite_budget
        ))

        # ---------------------------------------------------------
        # 7. Reset BIGSERIAL sequence after preserving IDs.
        # ---------------------------------------------------------
        postgres_cursor.execute("""
            SELECT setval(
                pg_get_serial_sequence('expenses', 'id'),
                COALESCE((SELECT MAX(id) FROM expenses), 1),
                true
            )
        """)

        postgres_conn.commit()

        # ---------------------------------------------------------
        # 8. Verify
        # ---------------------------------------------------------
        postgres_cursor.execute("SELECT COUNT(*) FROM expenses")
        after_count = postgres_cursor.fetchone()[0]

        postgres_cursor.execute("""
            SELECT budget
            FROM settings
            WHERE id = 1
        """)
        final_budget_row = postgres_cursor.fetchone()
        final_budget = (
            float(final_budget_row[0])
            if final_budget_row
            else DEFAULT_BUDGET
        )

        print("=" * 60)
        print("MIGRATION COMPLETED")
        print("=" * 60)
        print(f"Inserted: {inserted}")
        print(f"Skipped (already present): {skipped}")
        print(f"ID conflicts handled: {conflicted}")
        print(f"PostgreSQL expenses after migration: {after_count}")
        print(f"PostgreSQL budget: ₹{final_budget:.2f}")
        print()

        if after_count >= before_count:
            print("✅ PostgreSQL migration finished successfully.")
        else:
            print("⚠️ Please verify the PostgreSQL data manually.")

    except FileNotFoundError:
        print()
        print("❌ expenses.db was not found.")
        print("Run this script from your Smart Expense Tracker project folder.")

    except psycopg2.Error as exc:
        if postgres_conn:
            postgres_conn.rollback()
        print()
        print("❌ PostgreSQL error:")
        print(exc)

    except sqlite3.Error as exc:
        print()
        print("❌ SQLite error:")
        print(exc)

    except Exception as exc:
        if postgres_conn:
            postgres_conn.rollback()
        print()
        print("❌ Unexpected error:")
        print(exc)

    finally:
        if sqlite_conn:
            sqlite_conn.close()

        if postgres_conn:
            postgres_conn.close()


if __name__ == "__main__":
    main()
