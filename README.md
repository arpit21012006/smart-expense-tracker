💰 Smart Expense Tracker

A web-based Smart Expense Tracker built with Python, Flask, PostgreSQL, HTML, CSS, and JavaScript.

The application helps users record, manage, search, analyze, and monitor their daily expenses. It also provides budget tracking, spending insights, monthly analytics, spending prediction, unusual-spending detection, CSV export, and a modern responsive dashboard.

🌐 Live Demo

Live Website:
https://smart-expense-tracker-1s4s.onrender.com

📌 Project Overview

Managing daily expenses manually can make it difficult to understand spending patterns and stay within a budget.

The Smart Expense Tracker solves this problem by providing a centralized web application where users can:

Add new expenses

Edit existing expenses

Delete expenses

Search and filter transactions

Set and update a monthly/overall budget

View total and monthly spending

Analyze category-wise spending

View spending charts

Receive smart spending insights

Get a simple next-month spending prediction

Detect unusually high expenses

Export expense records as CSV

Switch between light and dark mode

🎯 Objectives

The main objectives of the project are:

To develop a simple and user-friendly expense management application.

To store and manage expense records in a relational database.

To provide budget monitoring and spending analysis.

To visualize spending patterns using charts.

To provide basic smart insights from recorded expense data.

To deploy the application online for real-world accessibility.

✨ Features

1. Add Expense

Users can add an expense with:

Expense name

Amount

Category

The application automatically records the current date.

2. Edit Expense

Existing expense records can be edited through the edit page.

3. Delete Expense

Users can delete unwanted expense records with a confirmation step.

4. Search & Filter

Expenses can be searched by name and filtered by category.

5. Budget Management

Users can set a budget and monitor:

Total spending

Remaining budget

Budget status

The dashboard displays warnings when spending approaches or exceeds the budget.

6. Smart Spending Insight

The application analyzes category distribution and budget usage to generate a simple spending insight.

7. Spending Prediction

The application calculates an average of recorded monthly spending and uses it as a basic estimated next-month expense.

8. Unusual Spending Detection

The system identifies expenses that are significantly higher than the average spending, helping users notice potentially unusual transactions.

9. Monthly Analytics

Monthly expense totals are visualized using a line chart and a bar chart.

10. Category Analytics

Category-wise expense distribution is shown using a doughnut chart and progress bars.

11. CSV Export

All recorded expenses can be downloaded as:

expense_report.csv

12. Responsive Professional UI

The dashboard is designed for desktop and mobile screens and includes:

Sidebar navigation

Dashboard summary cards

Responsive tables

Responsive charts

Light/Dark mode

Modern fintech-style layout

🛠️ Tech Stack

Frontend

HTML5

CSS3

JavaScript

Chart.js

Backend

Python

Flask

Database

PostgreSQL for the deployed Render application

SQLite database retained locally as a backup/development database

Deployment

Render

Version Control

GitHub

GitHub Desktop

🏗️ System Architecture

                    ┌──────────────────────┐
                    │      User / Browser  │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ HTML + CSS + JS      │
                    │ Chart.js Dashboard   │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Flask Web Application │
                    │       app.py         │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ PostgreSQL Database  │
                    │      on Render       │
                    └──────────────────────┘

📂 Project Structure

smart-expense-tracker/
│
├── app.py
├── requirements.txt
├── README.md
├── expenses.db
│
└── templates/
    ├── index.html
    ├── edit.html
    └── error.html

File Description

File / Folder

Purpose

app.py

Flask backend, routes, database logic, analytics and smart features

requirements.txt

Python dependencies

README.md

Project documentation

expenses.db

Local SQLite backup/development database

templates/index.html

Main dashboard UI

templates/edit.html

Expense editing page

templates/error.html

Error display page

🗃️ Database Design

expenses table

Column

Description

id

Unique expense ID

name

Expense name

amount

Expense amount

category

Expense category

expense_date

Date of the expense

settings table

Column

Description

id

Settings record ID

budget

Current budget value

🔌 Main Flask Routes

Route

Method

Purpose

/

GET

Dashboard, search, filter, analytics

/add

POST

Add expense

/edit/<id>

GET

Open expense edit page

/update/<id>

POST

Update expense

/delete/<id>

GET

Delete expense

/set-budget

POST

Update budget

/export

GET

Export expenses as CSV

🧠 Smart Features

The project includes simple rule/statistics-based smart features.

Smart Insight Logic

The application considers:

Budget usage

Total spending

Highest spending category

Category percentage of total spending

Based on these values, it displays a user-friendly spending message.

Spending Prediction Logic

The current implementation uses:

Predicted Expense
=
Average of recorded monthly expense totals

This is a basic statistical estimation, not a machine-learning model.

Unusual Spending Logic

The application checks whether an expense is both:

At least ₹1000

More than twice the average expense

Such transactions are shown in the unusual/high-spending section.

💻 Local Setup

1. Clone the repository

git clone https://github.com/arpit21012006/smart-expense-tracker.git
cd smart-expense-tracker

2. Create a virtual environment

Windows:

python -m venv venv

Activate it:

venv\Scripts\activate

3. Install dependencies

pip install -r requirements.txt

4. Run the application

python app.py

The local application will normally be available at:

http://127.0.0.1:5000

☁️ Render Deployment

The deployed application runs on Render.

Build Command

pip install -r requirements.txt

Start Command

gunicorn app:app

Environment Variable

The deployed Flask application uses:

DATABASE_URL

This variable contains the PostgreSQL connection string configured in Render.

The database connection string should never be committed to GitHub.

🔄 SQLite to PostgreSQL Migration

During development, the application used SQLite.

For deployment, the database was migrated to PostgreSQL on Render.

Migration flow:

Local SQLite
     ↓
expenses.db
     ↓
Migration Script
     ↓
Render PostgreSQL
     ↓
DATABASE_URL
     ↓
Flask Application

The one-time migration script was used during migration and should not be kept in the production repository once migration is complete.

🔐 Security Notes

Keep DATABASE_URL private.

Never commit database passwords or connection strings to GitHub.

Rotate database credentials if they are accidentally exposed.

Use environment variables for production database credentials.

🧪 Testing Checklist

Before final submission, verify:

Add expense works

Edit expense works

Delete expense works

Search works

Category filter works

Budget update works

Remaining budget is calculated correctly

Monthly analytics work

Category chart works

Smart insight appears

Spending prediction appears

Unusual spending detection works

CSV export works

Light/Dark mode works

Mobile layout works

PostgreSQL data persists after refresh

Render deployment is live

🚀 Future Scope

Possible future improvements include:

User authentication and registration

Multiple user accounts

PostgreSQL-backed user-specific expense data

Recurring expenses

Expense reminders

Monthly and yearly reports

PDF report generation

More advanced machine-learning-based predictions

Automatic category suggestions

Spending goals

Email notifications

Progressive Web App (PWA) support

More detailed financial dashboards

📊 Learning Outcomes

This project demonstrates practical knowledge of:

Python programming

Flask web development

CRUD operations

SQL and relational databases

PostgreSQL

HTML/CSS/JavaScript

Chart.js data visualization

Form handling and validation

Environment variables

Git and GitHub

GitHub Desktop

Render deployment

Basic data analysis and rule-based smart features

🎓 Academic Use

This project is suitable as a B.Tech Computer Science and Engineering academic project demonstrating full-stack web development, database integration, deployment, and basic data-driven features.

👨‍💻 Author

Arpit Sharma

B.Tech Computer Science and Engineering specialization in DATA SCIENCE and HONS. of Cyber Security

📜 License

This project is intended for educational and academic use.

You may modify and extend the project for learning, demonstration, and academic submission.

🙏 Acknowledgement

This project was developed as an educational full-stack web application using open-source technologies including Python, Flask, PostgreSQL, HTML, CSS, JavaScript, Chart.js, GitHub, and Render.

⭐ Project Summary

Smart Expense Tracker is a Flask-based expense management web application that combines CRUD functionality, budget management, analytics, data visualization, rule-based smart insights, spending prediction, unusual-spending detection, CSV export, PostgreSQL integration, and online deployment into one complete academic project.
