from flask import Flask, render_template, request, redirect, Response
import os
import io
import csv
import sqlite3
from datetime import datetime

import psycopg2


app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SQLITE_DATABASE = os.path.join(BASE_DIR, "expenses.db")
DATABASE_URL = os.environ.get("DATABASE_URL")
DEFAULT_BUDGET = 10000.0

# True on Render when DATABASE_URL is present.
USE_POSTGRES = bool(DATABASE_URL)


def get_conn():
    """Return a PostgreSQL connection on Render, otherwise local SQLite."""
    if USE_POSTGRES:
        return psycopg2.connect(DATABASE_URL)

    conn = sqlite3.connect(SQLITE_DATABASE)
    return conn


def placeholder():
    """Database parameter placeholder."""
    return "%s" if USE_POSTGRES else "?"


def init_db():
    """Create the required tables if they do not already exist."""
    conn = get_conn()
    cursor = conn.cursor()

    if USE_POSTGRES:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id BIGSERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                amount DOUBLE PRECISION NOT NULL,
                category TEXT NOT NULL,
                expense_date DATE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY,
                budget DOUBLE PRECISION NOT NULL
            )
        """)

        cursor.execute(
            """
            INSERT INTO settings (id, budget)
            VALUES (%s, %s)
            ON CONFLICT (id) DO NOTHING
            """,
            (1, DEFAULT_BUDGET)
        )

    else:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                expense_date TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY,
                budget REAL NOT NULL
            )
        """)

        cursor.execute(
            "SELECT budget FROM settings WHERE id = ?",
            (1,)
        )

        if cursor.fetchone() is None:
            cursor.execute(
                """
                INSERT INTO settings (id, budget)
                VALUES (?, ?)
                """,
                (1, DEFAULT_BUDGET)
            )

        # Upgrade older local SQLite databases that do not have expense_date.
        cursor.execute("PRAGMA table_info(expenses)")
        columns = [column[1] for column in cursor.fetchall()]

        if "expense_date" not in columns:
            cursor.execute("""
                ALTER TABLE expenses
                ADD COLUMN expense_date TEXT
            """)

            today = datetime.now().strftime("%Y-%m-%d")
            cursor.execute(
                """
                UPDATE expenses
                SET expense_date = ?
                WHERE expense_date IS NULL
                """,
                (today,)
            )

    conn.commit()
    cursor.close()
    conn.close()


# Initialize the database when Flask/Gunicorn imports this module.
init_db()


@app.route("/")
def home():
    conn = get_conn()
    cursor = conn.cursor()
    p = placeholder()

    search = request.args.get("search", "").strip()
    category_filter = request.args.get("category", "").strip()

    query = """
        SELECT id, name, amount, category, expense_date
        FROM expenses
        WHERE 1=1
    """
    params = []

    if search:
        query += f" AND name LIKE {p}"
        params.append("%" + search + "%")

    if category_filter:
        query += f" AND category = {p}"
        params.append(category_filter)

    query += " ORDER BY id DESC"

    cursor.execute(query, params)
    expenses = cursor.fetchall()

    cursor.execute("SELECT SUM(amount) FROM expenses")
    total_result = cursor.fetchone()[0]
    total = float(total_result or 0)

    current_month = datetime.now().strftime("%Y-%m")

    if USE_POSTGRES:
        cursor.execute(
            """
            SELECT SUM(amount)
            FROM expenses
            WHERE TO_CHAR(expense_date, 'YYYY-MM') = %s
            """,
            (current_month,)
        )
    else:
        cursor.execute(
            """
            SELECT SUM(amount)
            FROM expenses
            WHERE substr(expense_date, 1, 7) = ?
            """,
            (current_month,)
        )

    monthly_result = cursor.fetchone()[0]
    monthly_total = float(monthly_result or 0)

    cursor.execute("SELECT budget FROM settings WHERE id = " + p, (1,))
    budget_result = cursor.fetchone()
    budget = float(budget_result[0]) if budget_result else DEFAULT_BUDGET

    remaining = budget - total

    if remaining < 0:
        budget_status = "⚠️ Budget Exceeded!"
    elif remaining <= budget * 0.20:
        budget_status = "⚠️ Warning: Budget is almost over!"
    else:
        budget_status = "✅ Budget is under control."

    cursor.execute("""
        SELECT category, SUM(amount)
        FROM expenses
        GROUP BY category
        ORDER BY SUM(amount) DESC
    """)
    category_rows = cursor.fetchall()
    category_totals = [
        (row[0], float(row[1] or 0))
        for row in category_rows
    ]

    if USE_POSTGRES:
        cursor.execute("""
            SELECT TO_CHAR(expense_date, 'YYYY-MM') AS month,
                   SUM(amount)
            FROM expenses
            GROUP BY TO_CHAR(expense_date, 'YYYY-MM')
            ORDER BY month
        """)
    else:
        cursor.execute("""
            SELECT substr(expense_date, 1, 7), SUM(amount)
            FROM expenses
            GROUP BY substr(expense_date, 1, 7)
            ORDER BY substr(expense_date, 1, 7)
        """)

    monthly_rows = cursor.fetchall()
    monthly_totals = [
        (row[0], float(row[1] or 0))
        for row in monthly_rows
    ]

    # -------------------------
    # Smart spending insight
    # -------------------------
    smart_insight = "Add more expenses to generate smart insights."

    if total > 0 and category_totals:
        highest_category_name = category_totals[0][0]
        highest_category_amount = category_totals[0][1]
        category_percentage = (
            highest_category_amount / total
        ) * 100

        if remaining < 0:
            smart_insight = (
                "⚠️ Your total spending has exceeded the budget. "
                "Consider reducing non-essential expenses."
            )
        elif total >= budget * 0.80:
            smart_insight = (
                "⚠️ You have used more than 80% of your budget. "
                "Monitor your upcoming expenses carefully."
            )
        elif category_percentage >= 40:
            smart_insight = (
                f"💡 Your highest spending category is "
                f"{highest_category_name} ({category_percentage:.1f}% of "
                "total spending). Consider reviewing expenses in this category."
            )
        else:
            smart_insight = (
                "✅ Your spending is currently distributed across "
                "multiple categories."
            )

    # -------------------------
    # Spending prediction
    # -------------------------
    predicted_expense = 0.0

    if monthly_totals:
        monthly_values = [row[1] for row in monthly_totals]
        predicted_expense = (
            sum(monthly_values) / len(monthly_values)
        )

    if predicted_expense == 0:
        prediction_message = (
            "Add expenses to generate a spending prediction."
        )
    elif predicted_expense > budget:
        prediction_message = (
            "⚠️ Based on previous spending, your estimated next-month "
            "expense may exceed your current budget."
        )
    else:
        prediction_message = (
            f"📈 Based on your previous spending pattern, your estimated "
            f"next-month expense is ₹{predicted_expense:.2f}."
        )

    # -------------------------
    # Unusual expenses
    # -------------------------
    cursor.execute("""
        SELECT id, name, amount, category, expense_date
        FROM expenses
        ORDER BY amount DESC
    """)
    all_expenses = cursor.fetchall()

    unusual_expenses = []

    if all_expenses:
        expense_amounts = [
            float(expense[2])
            for expense in all_expenses
        ]

        average_expense = (
            sum(expense_amounts) / len(expense_amounts)
        )

        for expense in all_expenses:
            amount = float(expense[2])

            if amount >= 1000 and amount > average_expense * 2:
                unusual_expenses.append({
                    "id": expense[0],
                    "name": expense[1],
                    "amount": amount,
                    "category": expense[3],
                    "date": str(expense[4]) if expense[4] else ""
                })

    unusual_expenses = unusual_expenses[:5]

    if unusual_expenses:
        unusual_message = (
            "⚠️ Some expenses are significantly higher than "
            "your average spending."
        )
    else:
        unusual_message = "✅ No unusual high spending detected."

    # Convert expense amounts safely for the Jinja template.
    expenses_for_template = []
    for expense in expenses:
        expenses_for_template.append((
            expense[0],
            expense[1],
            float(expense[2]),
            expense[3],
            str(expense[4]) if expense[4] else ""
        ))

    cursor.close()
    conn.close()

    return render_template(
        "index.html",
        expenses=expenses_for_template,
        total=total,
        monthly_total=monthly_total,
        remaining=remaining,
        budget=budget,
        budget_status=budget_status,
        category_totals=category_totals,
        monthly_totals=monthly_totals,
        search=search,
        category_filter=category_filter,
        smart_insight=smart_insight,
        predicted_expense=predicted_expense,
        prediction_message=prediction_message,
        unusual_expenses=unusual_expenses,
        unusual_message=unusual_message
    )


@app.route("/set-budget", methods=["POST"])
def set_budget():
    budget_text = request.form.get("budget", "").strip()

    try:
        budget = float(budget_text)
    except ValueError:
        return render_template(
            "error.html",
            error_message="Please enter a valid budget."
        ), 400

    if budget <= 0:
        return render_template(
            "error.html",
            error_message="Budget must be greater than 0."
        ), 400

    conn = get_conn()
    cursor = conn.cursor()

    if USE_POSTGRES:
        cursor.execute(
            """
            INSERT INTO settings (id, budget)
            VALUES (%s, %s)
            ON CONFLICT (id)
            DO UPDATE SET budget = EXCLUDED.budget
            """,
            (1, budget)
        )
    else:
        cursor.execute(
            """
            INSERT OR REPLACE INTO settings (id, budget)
            VALUES (?, ?)
            """,
            (1, budget)
        )

    conn.commit()
    cursor.close()
    conn.close()

    return redirect("/")


@app.route("/add", methods=["POST"])
def add_expense():
    name = request.form.get("name", "").strip()
    amount_text = request.form.get("amount", "").strip()
    category = request.form.get("category", "").strip()

    if not name:
        return render_template(
            "error.html",
            error_message="Expense name is required."
        ), 400

    if not category:
        return render_template(
            "error.html",
            error_message="Please select a category."
        ), 400

    try:
        amount = float(amount_text)
    except ValueError:
        return render_template(
            "error.html",
            error_message="Please enter a valid amount."
        ), 400

    if amount <= 0:
        return render_template(
            "error.html",
            error_message="Amount must be greater than 0."
        ), 400

    expense_date = datetime.now().strftime("%Y-%m-%d")

    conn = get_conn()
    cursor = conn.cursor()

    if USE_POSTGRES:
        cursor.execute(
            """
            INSERT INTO expenses
                (name, amount, category, expense_date)
            VALUES (%s, %s, %s, %s)
            """,
            (name, amount, category, expense_date)
        )
    else:
        cursor.execute(
            """
            INSERT INTO expenses
                (name, amount, category, expense_date)
            VALUES (?, ?, ?, ?)
            """,
            (name, amount, category, expense_date)
        )

    conn.commit()
    cursor.close()
    conn.close()

    return redirect("/")


@app.route("/edit/<int:id>")
def edit_expense(id):
    conn = get_conn()
    cursor = conn.cursor()
    p = placeholder()

    cursor.execute(
        f"""
        SELECT id, name, amount, category, expense_date
        FROM expenses
        WHERE id = {p}
        """,
        (id,)
    )

    expense = cursor.fetchone()

    cursor.close()
    conn.close()

    if not expense:
        return render_template(
            "error.html",
            error_message="Expense not found."
        ), 404

    return render_template("edit.html", expense=expense)


@app.route("/update/<int:id>", methods=["POST"])
def update_expense(id):
    name = request.form.get("name", "").strip()
    amount_text = request.form.get("amount", "").strip()
    category = request.form.get("category", "").strip()
    expense_date = request.form.get("expense_date", "").strip()

    if not name:
        return render_template(
            "error.html",
            error_message="Expense name is required."
        ), 400

    if not category:
        return render_template(
            "error.html",
            error_message="Please select a category."
        ), 400

    try:
        amount = float(amount_text)
    except ValueError:
        return render_template(
            "error.html",
            error_message="Please enter a valid amount."
        ), 400

    if amount <= 0:
        return render_template(
            "error.html",
            error_message="Amount must be greater than 0."
        ), 400

    if not expense_date:
        expense_date = datetime.now().strftime("%Y-%m-%d")

    conn = get_conn()
    cursor = conn.cursor()
    p = placeholder()

    cursor.execute(
        f"""
        UPDATE expenses
        SET name = {p},
            amount = {p},
            category = {p},
            expense_date = {p}
        WHERE id = {p}
        """,
        (name, amount, category, expense_date, id)
    )

    conn.commit()
    updated = cursor.rowcount

    cursor.close()
    conn.close()

    if updated == 0:
        return render_template(
            "error.html",
            error_message="Expense not found."
        ), 404

    return redirect("/")


@app.route("/export")
def export_expenses():
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT name, amount, category, expense_date
        FROM expenses
        ORDER BY id DESC
    """)

    expenses = cursor.fetchall()

    cursor.close()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Expense Name",
        "Amount",
        "Category",
        "Date"
    ])

    for expense in expenses:
        writer.writerow([
            expense[0],
            expense[1],
            expense[2],
            expense[3]
        ])

    response = Response(
        output.getvalue(),
        mimetype="text/csv"
    )

    response.headers["Content-Disposition"] = (
        "attachment; filename=expense_report.csv"
    )

    return response


@app.route("/delete/<int:id>")
def delete_expense(id):
    conn = get_conn()
    cursor = conn.cursor()
    p = placeholder()

    cursor.execute(
        f"DELETE FROM expenses WHERE id = {p}",
        (id,)
    )

    conn.commit()
    cursor.close()
    conn.close()

    return redirect("/")


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=True
    )
