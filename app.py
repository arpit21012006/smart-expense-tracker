from flask import Flask, render_template, request, redirect, Response
import sqlite3
from datetime import datetime
import csv
import io
import os


# =========================================================
# FLASK APPLICATION
# =========================================================

app = Flask(__name__)


# =========================================================
# DATABASE CONFIGURATION
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "expenses.db")

DEFAULT_BUDGET = 10000


# =========================================================
# DATABASE INITIALIZATION
# IMPORTANT:
# This runs when Gunicorn imports app.py on Render.
# =========================================================

def init_db():

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # -----------------------------------------------------
    # EXPENSES TABLE
    # -----------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            expense_date TEXT
        )
    """)

    # -----------------------------------------------------
    # SETTINGS TABLE
    # -----------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY,
            budget REAL NOT NULL
        )
    """)

    # -----------------------------------------------------
    # ADD DEFAULT BUDGET IF NOT PRESENT
    # -----------------------------------------------------

    cursor.execute("""
        SELECT budget
        FROM settings
        WHERE id = 1
    """)

    budget = cursor.fetchone()

    if budget is None:

        cursor.execute("""
            INSERT INTO settings (id, budget)
            VALUES (1, ?)
        """, (DEFAULT_BUDGET,))

    # -----------------------------------------------------
    # FIX OLD DATABASES
    # If an older expenses table does not have
    # expense_date, add the column.
    # -----------------------------------------------------

    cursor.execute("PRAGMA table_info(expenses)")

    columns = [
        column[1]
        for column in cursor.fetchall()
    ]

    if "expense_date" not in columns:

        cursor.execute("""
            ALTER TABLE expenses
            ADD COLUMN expense_date TEXT
        """)

        today = datetime.now().strftime("%Y-%m-%d")

        cursor.execute("""
            UPDATE expenses
            SET expense_date = ?
            WHERE expense_date IS NULL
        """, (today,))

    conn.commit()
    conn.close()


# =========================================================
# INITIALIZE DATABASE
# IMPORTANT FOR RENDER + GUNICORN
# =========================================================

init_db()


# =========================================================
# GET CURRENT BUDGET
# =========================================================

def get_budget():

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT budget
        FROM settings
        WHERE id = 1
    """)

    result = cursor.fetchone()

    conn.close()

    if result:
        return result[0]

    return DEFAULT_BUDGET


# =========================================================
# HOME PAGE
# =========================================================

@app.route("/")
def home():

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # -----------------------------------------------------
    # SEARCH
    # -----------------------------------------------------

    search = request.args.get(
        "search",
        ""
    ).strip()

    # -----------------------------------------------------
    # CATEGORY FILTER
    # -----------------------------------------------------

    category_filter = request.args.get(
        "category",
        ""
    ).strip()

    # -----------------------------------------------------
    # GET EXPENSES
    # -----------------------------------------------------

    query = """
        SELECT
            id,
            name,
            amount,
            category,
            expense_date
        FROM expenses
        WHERE 1=1
    """

    params = []

    if search:

        query += """
            AND name LIKE ?
        """

        params.append(
            "%" + search + "%"
        )

    if category_filter:

        query += """
            AND category = ?
        """

        params.append(
            category_filter
        )

    query += """
        ORDER BY id DESC
    """

    cursor.execute(
        query,
        params
    )

    expenses = cursor.fetchall()

    # -----------------------------------------------------
    # TOTAL EXPENSE
    # -----------------------------------------------------

    cursor.execute("""
        SELECT SUM(amount)
        FROM expenses
    """)

    total = cursor.fetchone()[0] or 0

    # -----------------------------------------------------
    # CURRENT MONTH EXPENSE
    # -----------------------------------------------------

    current_month = datetime.now().strftime(
        "%Y-%m"
    )

    cursor.execute("""
        SELECT SUM(amount)
        FROM expenses
        WHERE substr(expense_date, 1, 7) = ?
    """, (
        current_month,
    ))

    monthly_total = cursor.fetchone()[0] or 0

    # -----------------------------------------------------
    # USER BUDGET
    # -----------------------------------------------------

    cursor.execute("""
        SELECT budget
        FROM settings
        WHERE id = 1
    """)

    budget_result = cursor.fetchone()

    if budget_result:
        budget = budget_result[0]
    else:
        budget = DEFAULT_BUDGET

    # -----------------------------------------------------
    # REMAINING BUDGET
    # -----------------------------------------------------

    remaining = budget - total

    # -----------------------------------------------------
    # BUDGET STATUS
    # -----------------------------------------------------

    if remaining < 0:

        budget_status = (
            "⚠️ Budget Exceeded!"
        )

    elif remaining <= budget * 0.20:

        budget_status = (
            "⚠️ Warning: Budget is almost over!"
        )

    else:

        budget_status = (
            "✅ Budget is under control."
        )

    # -----------------------------------------------------
    # CATEGORY TOTALS
    # -----------------------------------------------------

    cursor.execute("""
        SELECT
            category,
            SUM(amount)
        FROM expenses
        GROUP BY category
        ORDER BY SUM(amount) DESC
    """)

    category_totals = cursor.fetchall()

    # -----------------------------------------------------
    # MONTHLY TOTALS
    # -----------------------------------------------------

    cursor.execute("""
        SELECT
            substr(expense_date, 1, 7),
            SUM(amount)
        FROM expenses
        GROUP BY substr(expense_date, 1, 7)
        ORDER BY substr(expense_date, 1, 7)
    """)

    monthly_totals = cursor.fetchall()

    # =====================================================
    # SMART SPENDING INSIGHT
    # =====================================================

    smart_insight = (
        "Add more expenses to generate "
        "smart insights."
    )

    if total > 0 and category_totals:

        highest_category = category_totals[0]

        highest_category_name = (
            highest_category[0]
        )

        highest_category_amount = (
            highest_category[1]
        )

        category_percentage = (
            highest_category_amount / total
        ) * 100

        if remaining < 0:

            smart_insight = (
                "⚠️ Your total spending has "
                "exceeded the budget. Consider "
                "reducing non-essential expenses."
            )

        elif total >= budget * 0.80:

            smart_insight = (
                "⚠️ You have used more than 80% "
                "of your budget. Monitor your "
                "upcoming expenses carefully."
            )

        elif category_percentage >= 40:

            smart_insight = (
                f"💡 Your highest spending category "
                f"is {highest_category_name} "
                f"({category_percentage:.1f}% of total "
                f"spending). Consider reviewing "
                f"expenses in this category."
            )

        else:

            smart_insight = (
                "✅ Your spending is currently "
                "distributed across multiple "
                "categories."
            )

    # =====================================================
    # SPENDING PREDICTION
    # =====================================================

    prediction_data = monthly_totals

    predicted_expense = 0

    if prediction_data:

        monthly_values = [
            row[1]
            for row in prediction_data
        ]

        predicted_expense = (
            sum(monthly_values)
            / len(monthly_values)
        )

    if predicted_expense == 0:

        prediction_message = (
            "Add expenses to generate "
            "a spending prediction."
        )

    elif predicted_expense > budget:

        prediction_message = (
            "⚠️ Based on previous spending, "
            "your estimated next-month expense "
            "may exceed your current budget."
        )

    else:

        prediction_message = (
            "📈 Based on your previous spending "
            "pattern, your estimated next-month "
            "expense is "
            f"₹{predicted_expense:.2f}."
        )

    # =====================================================
    # UNUSUAL SPENDING DETECTION
    # =====================================================

    cursor.execute("""
        SELECT
            id,
            name,
            amount,
            category,
            expense_date
        FROM expenses
        ORDER BY amount DESC
    """)

    all_expenses = cursor.fetchall()

    unusual_expenses = []

    if all_expenses:

        expense_amounts = [
            expense[2]
            for expense in all_expenses
        ]

        average_expense = (
            sum(expense_amounts)
            / len(expense_amounts)
        )

        for expense in all_expenses:

            if (
                expense[2] >= 1000
                and
                expense[2] > average_expense * 2
            ):

                unusual_expenses.append({

                    "id": expense[0],

                    "name": expense[1],

                    "amount": expense[2],

                    "category": expense[3],

                    "date": expense[4]
                })

    unusual_expenses = unusual_expenses[:5]

    if unusual_expenses:

        unusual_message = (
            "⚠️ Some expenses are significantly "
            "higher than your average spending."
        )

    else:

        unusual_message = (
            "✅ No unusual high spending detected."
        )

    conn.close()

    # =====================================================
    # SEND DATA TO HTML
    # =====================================================

    return render_template(
        "index.html",

        expenses=expenses,

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


# =========================================================
# SET USER BUDGET
# =========================================================

@app.route(
    "/set-budget",
    methods=["POST"]
)
def set_budget():

    budget_text = request.form.get(
        "budget",
        ""
    ).strip()

    try:

        budget = float(
            budget_text
        )

    except ValueError:

        return render_template(
            "error.html",
            error_message=(
                "Please enter a valid budget."
            )
        ), 400

    if budget <= 0:

        return render_template(
            "error.html",
            error_message=(
                "Budget must be greater than 0."
            )
        ), 400

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO settings
        (id, budget)
        VALUES (1, ?)
    """, (
        budget,
    ))

    conn.commit()
    conn.close()

    return redirect("/")


# =========================================================
# ADD EXPENSE
# =========================================================

@app.route(
    "/add",
    methods=["POST"]
)
def add_expense():

    name = request.form.get(
        "name",
        ""
    ).strip()

    amount_text = request.form.get(
        "amount",
        ""
    ).strip()

    category = request.form.get(
        "category",
        ""
    ).strip()

    # -----------------------------------------------------
    # VALIDATE NAME
    # -----------------------------------------------------

    if not name:

        return render_template(
            "error.html",
            error_message=(
                "Expense name is required."
            )
        ), 400

    # -----------------------------------------------------
    # VALIDATE CATEGORY
    # -----------------------------------------------------

    if not category:

        return render_template(
            "error.html",
            error_message=(
                "Please select a category."
            )
        ), 400

    # -----------------------------------------------------
    # VALIDATE AMOUNT
    # -----------------------------------------------------

    try:

        amount = float(
            amount_text
        )

    except ValueError:

        return render_template(
            "error.html",
            error_message=(
                "Please enter a valid amount."
            )
        ), 400

    if amount <= 0:

        return render_template(
            "error.html",
            error_message=(
                "Amount must be greater than 0."
            )
        ), 400

    # -----------------------------------------------------
    # DATE
    # -----------------------------------------------------

    expense_date = datetime.now().strftime(
        "%Y-%m-%d"
    )

    # -----------------------------------------------------
    # SAVE EXPENSE
    # -----------------------------------------------------

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO expenses
        (
            name,
            amount,
            category,
            expense_date
        )
        VALUES (?, ?, ?, ?)
    """, (
        name,
        amount,
        category,
        expense_date
    ))

    conn.commit()
    conn.close()

    return redirect("/")


# =========================================================
# EDIT EXPENSE PAGE
# =========================================================

@app.route(
    "/edit/<int:id>"
)
def edit_expense(id):

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            name,
            amount,
            category,
            expense_date
        FROM expenses
        WHERE id = ?
    """, (
        id,
    ))

    expense = cursor.fetchone()

    conn.close()

    if not expense:

        return render_template(
            "error.html",
            error_message=(
                "Expense not found."
            )
        ), 404

    return render_template(
        "edit.html",
        expense=expense
    )


# =========================================================
# UPDATE EXPENSE
# =========================================================

@app.route(
    "/update/<int:id>",
    methods=["POST"]
)
def update_expense(id):

    name = request.form.get(
        "name",
        ""
    ).strip()

    amount_text = request.form.get(
        "amount",
        ""
    ).strip()

    category = request.form.get(
        "category",
        ""
    ).strip()

    expense_date = request.form.get(
        "expense_date",
        ""
    ).strip()

    # -----------------------------------------------------
    # VALIDATE NAME
    # -----------------------------------------------------

    if not name:

        return render_template(
            "error.html",
            error_message=(
                "Expense name is required."
            )
        ), 400

    # -----------------------------------------------------
    # VALIDATE CATEGORY
    # -----------------------------------------------------

    if not category:

        return render_template(
            "error.html",
            error_message=(
                "Please select a category."
            )
        ), 400

    # -----------------------------------------------------
    # VALIDATE AMOUNT
    # -----------------------------------------------------

    try:

        amount = float(
            amount_text
        )

    except ValueError:

        return render_template(
            "error.html",
            error_message=(
                "Please enter a valid amount."
            )
        ), 400

    if amount <= 0:

        return render_template(
            "error.html",
            error_message=(
                "Amount must be greater than 0."
            )
        ), 400

    # -----------------------------------------------------
    # DEFAULT DATE
    # -----------------------------------------------------

    if not expense_date:

        expense_date = datetime.now().strftime(
            "%Y-%m-%d"
        )

    # -----------------------------------------------------
    # UPDATE DATABASE
    # -----------------------------------------------------

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE expenses
        SET
            name = ?,
            amount = ?,
            category = ?,
            expense_date = ?
        WHERE id = ?
    """, (
        name,
        amount,
        category,
        expense_date,
        id
    ))

    conn.commit()

    updated = cursor.rowcount

    conn.close()

    if updated == 0:

        return render_template(
            "error.html",
            error_message=(
                "Expense not found."
            )
        ), 404

    return redirect("/")


# =========================================================
# EXPORT EXPENSES TO CSV
# =========================================================

@app.route("/export")
def export_expenses():

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            name,
            amount,
            category,
            expense_date
        FROM expenses
        ORDER BY id DESC
    """)

    expenses = cursor.fetchall()

    conn.close()

    # -----------------------------------------------------
    # CREATE CSV
    # -----------------------------------------------------

    output = io.StringIO()

    writer = csv.writer(
        output
    )

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

    # -----------------------------------------------------
    # SEND CSV FILE
    # -----------------------------------------------------

    response = Response(
        output.getvalue(),
        mimetype="text/csv"
    )

    response.headers[
        "Content-Disposition"
    ] = (
        "attachment; "
        "filename=expense_report.csv"
    )

    return response


# =========================================================
# DELETE EXPENSE
# =========================================================

@app.route(
    "/delete/<int:id>"
)
def delete_expense(id):

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM expenses
        WHERE id = ?
    """, (
        id,
    ))

    conn.commit()
    conn.close()

    return redirect("/")


# =========================================================
# RUN APPLICATION LOCALLY
# =========================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(
            os.environ.get(
                "PORT",
                5000
            )
        ),
        debug=True
        )
