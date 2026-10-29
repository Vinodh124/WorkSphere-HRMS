# WorkSphere HRMS
## Phase 4 — Employee Onboarding Module

### 1. Project Overview

**Project Name:** WorkSphere HRMS  
**Phase:** Phase 4 — Employee Onboarding  
**Module:** Employee Onboarding Management  
**Backend:** Python, FastAPI  
**Database:** SQLite  
**API Documentation and Testing:** Swagger UI  
**Authentication:** JWT-based authentication  
**ORM:** SQLAlchemy

### 2. Objective

The objective of Phase 4 is to develop an Employee Onboarding module for the WorkSphere Human Resource Management System (HRMS).

The module enables HR/Admin users to assign onboarding tasks to employees. Employees can view their onboarding checklists and update the status of their assigned tasks. HR/Admin users can monitor employee onboarding progress through a progress-tracking API.

### 3. Features Implemented

The following features have been implemented:

1. **Create onboarding tasks:** HR/Admin users can create onboarding tasks for active employees.
2. **View personal checklist:** Employees can retrieve their own onboarding tasks.
3. **View employee checklist:** HR/Admin users can retrieve an employee's onboarding checklist.
4. **Update task status:** Authorized users can update task status from `PENDING` to `COMPLETED`.
5. **Track onboarding progress:** The system calculates total tasks, completed tasks, pending tasks, and completion percentage.
6. **Authentication:** Protected endpoints require a valid authentication token.
7. **Role-based access control:** Access to onboarding operations depends on the authenticated user's role.
8. **Database persistence:** Onboarding tasks are stored in an SQLite database.

### 4. Technology Stack

| Technology | Purpose |
|---|---|
| Python | Backend programming language |
| FastAPI | REST API development |
| SQLite | Database storage |
| SQLAlchemy | Database ORM |
| Pydantic | Request validation and response schemas |
| JWT | Authentication |
| Swagger UI | API documentation and testing |
| Uvicorn | ASGI server |

### 5. Database Design

The onboarding module uses an `onboarding` database table.

| Column | Data Type | Description |
|---|---|---|
| `id` | Integer | Primary key for the onboarding task |
| `employee_id` | Integer | References the employee record |
| `task_name` | String | Name of the onboarding task |
| `status` | String | Task status: `PENDING` or `COMPLETED` |
| `due_date` | Date | Deadline for completing the task |

The `employee_id` field establishes a relationship between the onboarding task and the employee record.

### 6. API Endpoints

#### 6.1 Create Onboarding Task

**Method:** POST  
**Endpoint:** `/onboarding/`  
**Access:** HR/Admin

Purpose: Creates an onboarding task for an active employee.

Example request:

```json
{
  "employee_id": 5,
  "task_name": "Complete HR Orientation",
  "due_date": "2026-11-05"
}
```

Test result: **201 Created**

The API created task ID 2 for Employee ID 5 with an initial status of `PENDING`.

#### 6.2 View Personal Onboarding Checklist

**Method:** GET  
**Endpoint:** `/onboarding/my-checklist`  
**Access:** Employee

Purpose: Retrieves onboarding tasks belonging to the authenticated employee.

The endpoint uses the logged-in user's identity to identify the corresponding employee record.

#### 6.3 View an Employee's Checklist

**Method:** GET  
**Endpoint:** `/onboarding/employee/{employee_id}`

Purpose: Retrieves onboarding tasks for a specified employee. HR/Admin users can access employee checklists, while employees are restricted to their own checklist.

#### 6.4 Update Onboarding Task Status

**Method:** PATCH  
**Endpoint:** `/onboarding/{task_id}/status`

Purpose: Updates the status of an onboarding task.

Example request:

```json
{
  "status": "COMPLETED"
}
```

Test result: **200 OK**

Task ID 2 was successfully updated to `COMPLETED`.

#### 6.5 View Onboarding Progress

**Method:** GET  
**Endpoint:** `/onboarding/employee/{employee_id}/progress`

Purpose: Calculates the onboarding progress of an employee.

The response includes:
- Employee ID
- Total number of tasks
- Number of completed tasks
- Number of pending tasks
- Progress percentage

### 7. Progress Calculation

The onboarding completion percentage is calculated using the following formula:

Completion Percentage = (Completed Tasks / Total Tasks) × 100

For example, if an employee has one completed task out of one total task:

Completion Percentage = (1 / 1) × 100 = 100%

If no tasks exist, the implementation should handle the zero-task case without attempting division by zero.

### 8. Testing and Results

The APIs were tested using FastAPI Swagger UI at:

`http://127.0.0.1:8000/docs`

| Test | Operation | Result |
|---|---|---|
| 1 | Create onboarding task | HTTP 201 Created |
| 2 | Retrieve employee progress for Employee ID 1 | HTTP 200 OK |
| 3 | Create task for Employee ID 5 | HTTP 201 Created |
| 4 | Update Task ID 2 to `COMPLETED` | HTTP 200 OK |
| 5 | Retrieve progress for Employee ID 5 | HTTP 200 OK |
| 6 | Verify final progress | 100% completed |

### 9. Final Verified Test Output

The following response was returned by the progress endpoint for Employee ID 5 after completing the onboarding task:

```json
{
  "employee_id": 5,
  "total_tasks": 1,
  "completed_tasks": 1,
  "pending_tasks": 0,
  "progress_percentage": 100
}
```

This confirms that the tested employee has completed all assigned onboarding tasks.

### 10. Authentication and Authorization

The onboarding module integrates with the existing authentication system.

- Users must provide a valid access token to access protected endpoints.
- HR/Admin users can create onboarding tasks.
- Employees can view their own checklists and update their own task status.
- Employees cannot create onboarding tasks or access another employee's restricted information.
- Invalid or expired tokens are rejected.
- Unauthorized operations return appropriate HTTP error responses.

### 11. How to Run the Backend

Open PowerShell in the project directory and execute:

```powershell
cd backend
python -m uvicorn main:app --reload
```

If the virtual environment is not activated, activate it from the project root:

```powershell
.\backend\.venv\Scripts\Activate.ps1
cd backend
python -m uvicorn main:app --reload
```

Open Swagger UI in a browser:

`http://127.0.0.1:8000/docs`

### 12. Screenshots for Submission

Include the following screenshots in the project submission:

1. Swagger UI showing the onboarding endpoints.
2. Successful onboarding task creation response (`201 Created`).
3. Successful onboarding task status update (`200 OK`).
4. Final onboarding progress response showing `100%`.
5. Project folder structure containing the backend and documentation.

Save the screenshots in a folder named `Phase4_Screenshots`.

### 13. Conclusion

Phase 4 of the WorkSphere HRMS project implements employee onboarding task management and progress tracking using FastAPI and SQLite.

The implemented APIs support task creation, checklist retrieval, task status updates, and progress calculation. Testing confirmed that the task creation and status update operations succeeded and that Employee ID 5 reached 100% onboarding completion.

This phase demonstrates REST API development, database relationships, request validation, authentication, role-based authorization, and API testing.
