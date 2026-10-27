# WorkSphere HRMS

A Human Resource Management System (HRMS) built with React and FastAPI to help manage employees and HR operations.

## Features

- User authentication with JWT
- Role-based access for Admin and HR
- Employee management
- Attendance check-in, check-out, and reports
- Leave applications and approvals
- Leave balance and team leave calendar
- Payroll management
- Shift management
- Employee document management
- Performance reviews and ratings
- Notifications and dashboard summaries

## Technology Stack

### Frontend
- React
- JavaScript
- CSS
- Vite

### Backend
- Python
- FastAPI
- SQLAlchemy
- SQLite
- JWT authentication

## Project Structure

```text
WorkSphere-HRMS-Phase2/
├── backend/
│   ├── main.py
│   ├── auth.py
│   ├── models.py
│   ├── database.py
│   └── ...
├── frontend-app/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── ...
└── .gitignore
```

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/Vinodh124/WorkSphere-HRMS.git
cd WorkSphere-HRMS
```

### 2. Start the backend

Open a terminal:

```bash
cd backend
python -m venv .venv
```

Activate the virtual environment on Windows:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start FastAPI:

```bash
python -m uvicorn main:app --reload
```

Backend API documentation:

http://127.0.0.1:8000/docs

### 3. Start the frontend

Open a second terminal from the project root:

```bash
cd frontend-app
npm install
npm run dev
```

Open the local URL printed by Vite in your terminal, commonly:

http://localhost:5173/

## Security Notes

- Do not commit `.env` files, passwords, JWT secrets, databases containing personal information, or private employee documents.
- Configure environment variables locally before running the application.
- Use test data when demonstrating the project.

## Project Status

WorkSphere HRMS is a development project. Verify all features and configuration before deploying it to production.

## Author

Vinodh124
