# FINA - Personal Finance Tracker: Full Technical Documentation
Accessible via the link:https://personal-finance-tracker-6-y8oy.onrender.com

## 1. Project Overview

FINA is a professional-grade, full-stack personal finance management application. It allows users to gain control over their financial health by tracking income and expenses through a secure, cloud-hosted platform. The system uses a decoupled architecture, meaning the user interface (Frontend) and the data processing engine (Backend) operate independently but communicate through a secure API.

## 2. Technical Stack & Programming Languages

### Frontend (The User Interface)

*   **HTML5**: Used to build the semantic structure of the login, registration, and dashboard pages.
*   **JavaScript (ES6+)**: The "brain" of the frontend. It manages the application state, form submissions, and makes asynchronous requests to the backend using the Fetch API.
*   **Tailwind CSS**: A utility-first CSS framework. Note: This project does not use a traditional styles.css file. Instead, all styling is applied directly in the HTML via Tailwind classes and small internal <style> blocks for background management.

### Backend (The Logic Engine)

*   **Python 3.12/3.13**: Chosen for its robust standard library and excellent support for web frameworks.
*   **Flask**: A micro-web framework used to build the REST API. It routes incoming requests to the correct Python functions.
*   **Flask-SQLAlchemy**: An ORM (Object Relational Mapper) that translates Python code into SQL commands to interact with the database.
*   **Flask-JWT-Extended**: Handles security by issuing JSON Web Tokens (JWT) to users after they login.
*   **Flask-CORS**: Critical for deployment. It allows your Netlify frontend to securely access your Render backend.

## 3. Detailed Project Structure

### Backend Structure (`/finance_tracker_backend`)

*   `app.py`: The main entry point. It initializes the Flask app, configures security (CORS/JWT), and contains the API routes.
*   `models.py`: Defines the Database Schema. It contains the Python classes that represent the User and Transaction tables in the database.
*   `requirements.txt`: A configuration file listing all Python libraries needed (Flask, SQLAlchemy, etc.) for Render to build the environment.
*   `.env`: A hidden file containing sensitive configuration variables like database credentials and secret keys.

### Frontend Structure (Root Directory)

*   `index.html`: The primary entry point for users. It contains both the Login and Registration forms and the core JavaScript logic.
*   `dashboard.html`: The main workspace where users add transactions and view their total balance.
*   `top-view-desk-with-financial-instruments.jpg`: The high-resolution background image used for the login screen.
*   `tracklogo.png` : Branding assets for the application logo and browser tab icon.

## 4. Environment Variables (.env)

The `.env` file is used to store sensitive information that should never be shared publicly on GitHub. Below is the structure required for the project:

```bash
# Database Configuration
# This is the connection string provided by Render PostgreSQL
DATABASE_URL=postgresql://user:password@hostname:port/dbname

# Security Configuration
# Used to sign the JWT tokens - change this to a long random string
JWT_SECRET_KEY=your_super_secret_random_key_here

# Flask Configuration
FLASK_APP=app.py
FLASK_ENV=production
```

## 5. Detailed Project Structure

```text
Personal_finance_tracker/
├── finance_tracker_backend/        # Python Flask Backend (Deployed on Render)
│   ├── app.py                      # Core API: Routes, JWT setup, and Flask initialization
│   ├── models.py                   # Database Models: Defines User and Transaction tables
│   ├── requirements.txt            # Python dependencies (Flask, SQLAlchemy, etc.)
│   └── .env                        # Private environment variables (DATABASE_URL, SECRET_KEY)
├── frontend/                       # Static Frontend (Deployed on Netlify)
│   ├── index.html                  # Landing page: Login & Registration (with Tailwind)
│   ├── dashboard.html              # User Dashboard: Transaction history & Balance tracking
│   ├── tracklogo.png               # Brand Asset: Navbar and Form logo
│   ├── background.jpg              # UI Asset: General application background
│   └── top-view-desk-with-financial-instruments.jpg # UI Asset: Immersive Login background
└── README.md                       # Comprehensive Project Documentation (3+ pages)
```

## 6. Key Functions & Modules Deep-Dive

### Frontend JavaScript Functions

*   `handleLogin()`: Captures user credentials, sends them to the backend, and stores the returned JWT token in localStorage for session persistence.
*   `handleRegister()`: Validates user input (checking if passwords match) and sends a registration request to the server.
*   `checkLoginStatus()`: Runs automatically when the page loads. If a token is found in the browser, it redirects the user to the dashboard to avoid re-logging.

### Backend Modules

*   `psycopg2-binary`: The adapter that allows Python to speak to the PostgreSQL database.
*   `gunicorn`: The production-grade server that hosts your Python code on Render.

## 7. Step-by-Step App Working Process

### 1. The Authentication Phase

The user enters their details on the frontend. The JavaScript `fetch()` function sends a POST request to the backend. The backend hashes the password (for security) and checks it against the database. If correct, it returns a JWT token.

### 2. The Session Phase

The browser receives the JWT and saves it. For every future request (like fetching expenses), the frontend includes this token in the "Authorization Header." This is how the backend knows who is asking for data without asking for a password again.

### 3. The Data Processing Phase

When a user adds an expense:

1.  Frontend sends the data + JWT to `/api/transactions`.
2.  Backend verifies the JWT, identifies the User ID, and uses SQLAlchemy to save the record in PostgreSQL.
3.  The frontend then recalculates the balance using the formula:
    
    `Balance=∑Income−∑Expenses`

## 8. Deployment Summary

*   **Frontend Hosting**: Render(for fast delivery of HTML and images).
*   **Backend Hosting**: Render (running the Python/Flask environment).
*   **Database**: Render PostgreSQL (storing user and transaction data permanently).

Created by Felicite, Idris, Ngozi and Adam

