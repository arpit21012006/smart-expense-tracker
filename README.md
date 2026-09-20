💰 Smart Expense Tracker

A web-based Smart Expense Tracker built using Python, Flask, SQLite, HTML, CSS and JavaScript.

The application helps users record, manage and analyze their daily expenses while providing budget tracking and smart spending insights.

🌐 Live Demo

🚀 Live Application:
https://smart-expense-tracker-1s4s.onrender.com

📌 Project Overview

Managing daily expenses manually can make it difficult to understand where money is being spent.

The Smart Expense Tracker provides a simple dashboard where users can:

Add daily expenses

Categorize expenses

Edit and delete expenses

Search and filter expenses

Set a personal budget

Track total spending

Monitor remaining budget

View spending insights

Detect unusually high expenses

Estimate future spending

Export expense data as CSV

The project is developed as a B.Tech CSE project with the goal of combining web development, database management and intelligent expense analysis.

✨ Features

🧾 Expense Management

Add new expenses

Edit existing expenses

Delete expenses

Store expense name, amount, category and date

View all recorded expenses

🔎 Search & Filtering

Search expenses by name

Filter expenses by category

Sort expenses by latest entries

💵 Budget Management

Set monthly/personal budget

Calculate total spending

Calculate remaining budget

Display budget warnings

Detect when the budget is exceeded

🧠 Smart Spending Insights

The application analyzes spending data and provides useful insights such as:

Highest spending category

Percentage of spending by category

Budget usage warnings

Spending pattern analysis

Unusual/high-value expense detection

Estimated future spending

📊 Expense Analytics

The system maintains:

Category-wise spending

Monthly spending

Total expenses

Current-month expenses

Remaining budget

📥 Export

Users can export their expense records as a CSV file for further analysis or record keeping.

🛠️ Technology Stack

Frontend

HTML5

CSS3

JavaScript

Backend

Python

Flask

Database

SQLite

Deployment

Render

Gunicorn

Version Control

Git

GitHub

📂 Project Structure

smart-expense-tracker/
│
├── app.py
├── requirements.txt
├── expenses.db
│
├── templates/
│   ├── index.html
│   ├── edit.html
│   └── error.html
│
└── README.md

⚙️ Installation & Setup

1. Clone the repository

git clone https://github.com/arpit21012006/smart-expense-tracker.git

2. Navigate to the project directory

cd smart-expense-tracker

3. Create a virtual environment

python -m venv venv

4. Activate the virtual environment

Windows

venv\Scripts\activate

Linux / macOS

source venv/bin/activate

5. Install dependencies

pip install -r requirements.txt

6. Run the application

python app.py

The application will be available at:

http://127.0.0.1:5000

🚀 Deployment

The application is deployed using Render.

Build Command

pip install -r requirements.txt

Start Command

gunicorn app:app

🗄️ Database

The project currently uses SQLite.

The database contains tables for:

Expenses

Stores:

Expense ID

Expense name

Amount

Category

Expense date

Settings

Stores:

Budget configuration

The database is automatically initialized when the Flask application starts.

🧠 Smart Analysis

The application provides rule-based spending analysis.

For example, if a particular category represents a large percentage of total spending, the application can recommend reviewing spending in that category.

It can also identify unusually large expenses compared with the user's average expense amount.

Future versions will expand these capabilities using more advanced analytics and AI techniques.

🎯 Project Objectives

The main objectives of this project are:

To develop a simple expense management system.

To provide users with an easy way to track daily spending.

To implement budget monitoring.

To analyze spending patterns.

To provide intelligent spending insights.

To demonstrate practical implementation of Flask and SQLite.

To deploy a real-world web application on the cloud.

🔮 Future Scope

The project can be further enhanced with:

👤 User registration and login

🔐 Secure authentication

🗄️ PostgreSQL database

📊 Interactive charts and graphs

🤖 Advanced AI-based financial insights

📄 PDF expense reports

📧 Email budget alerts

📱 Mobile-friendly/PWA support

☁️ Cloud database storage

📈 Advanced spending prediction

🌙 Dark mode

🔔 Smart notifications

🧪 Testing

The application has been tested for:

Expense creation

Expense editing

Expense deletion

Budget calculation

Search and filtering

Database initialization

CSV export

Flask application startup

Gunicorn deployment

Render cloud deployment

👨‍💻 Author

Arpit Sharma

B.Tech Computer Science & Engineering

📜 License

This project is developed for educational and academic purposes.

⭐ Acknowledgement

This project was developed as part of a B.Tech CSE project to demonstrate practical knowledge of:

Python

Flask

SQLite

Web Development

Database Management

Data Analysis

Cloud Deployment
