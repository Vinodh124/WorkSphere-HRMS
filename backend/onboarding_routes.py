
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import Employee, Onboarding, User
from permissions import require_authenticated, require_hr_or_admin
from schemas import (
    OnboardingCreate,
    OnboardingResponse,
    OnboardingStatusUpdate,
)

router = APIRouter(
    prefix="/onboarding",
    tags=["Employee Onboarding"],
)


@router.post(
    "/",
    response_model=OnboardingResponse,
    status_code=status.HTTP_201_CREATED,
)
def assign_onboarding_task(
    data: OnboardingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_or_admin),
):
    employee = db.query(Employee).filter(
        Employee.id == data.employee_id
    ).first()

    if not employee:
        raise HTTPException(
            status_code=404,
            detail="Employee not found",
        )

    if employee.status != "Active":
        raise HTTPException(
            status_code=400,
            detail="Cannot assign onboarding to an inactive employee",
        )

    task = Onboarding(
        employee_id=data.employee_id,
        task_name=data.task_name,
        due_date=data.due_date,
        status="PENDING",
    )

    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get(
    "/my-checklist",
    response_model=list[OnboardingResponse],
)
def get_my_checklist(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated),
):
    if current_user.role not in ("EMPLOYEE", "HR", "ADMIN"):
        raise HTTPException(status_code=403, detail="Access denied")

    if current_user.role == "EMPLOYEE":
        employee = db.query(Employee).filter(
            Employee.email == current_user.email
        ).first()

        if not employee:
            raise HTTPException(
                status_code=404,
                detail="Employee profile not found for this account",
            )

        employee_id = employee.id
    else:
        raise HTTPException(
            status_code=400,
            detail="HR/Admin should use the employee checklist endpoint",
        )

    return (
        db.query(Onboarding)
        .filter(Onboarding.employee_id == employee_id)
        .order_by(Onboarding.due_date.asc())
        .all()
    )


@router.get(
    "/employee/{employee_id}",
    response_model=list[OnboardingResponse],
)
def get_employee_checklist(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated),
):
    if current_user.role == "EMPLOYEE":
        employee = db.query(Employee).filter(
            Employee.email == current_user.email
        ).first()

        if not employee or employee.id != employee_id:
            raise HTTPException(
                status_code=403,
                detail="You can only view your own checklist",
            )
    elif current_user.role not in ("HR", "ADMIN"):
        raise HTTPException(status_code=403, detail="Access denied")

    employee = db.query(Employee).filter(
        Employee.id == employee_id
    ).first()

    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    return (
        db.query(Onboarding)
        .filter(Onboarding.employee_id == employee_id)
        .order_by(Onboarding.due_date.asc())
        .all()
    )


@router.patch(
    "/{task_id}/status",
    response_model=OnboardingResponse,
)
def update_onboarding_status(
    task_id: int,
    data: OnboardingStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated),
):
    task = db.query(Onboarding).filter(
        Onboarding.id == task_id
    ).first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if current_user.role == "EMPLOYEE":
        employee = db.query(Employee).filter(
            Employee.email == current_user.email
        ).first()

        if not employee or employee.id != task.employee_id:
            raise HTTPException(
                status_code=403,
                detail="You can only update your own onboarding tasks",
            )
    elif current_user.role not in ("HR", "ADMIN"):
        raise HTTPException(status_code=403, detail="Access denied")

    task.status = data.status
    db.commit()
    db.refresh(task)
    return task


@router.get(
    "/employee/{employee_id}/progress",
)
def get_onboarding_progress(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated),
):
    if current_user.role == "EMPLOYEE":
        employee = db.query(Employee).filter(
            Employee.email == current_user.email
        ).first()

        if not employee or employee.id != employee_id:
            raise HTTPException(
                status_code=403,
                detail="You can only view your own progress",
            )
    elif current_user.role not in ("HR", "ADMIN"):
        raise HTTPException(status_code=403, detail="Access denied")

    if not db.query(Employee).filter(
        Employee.id == employee_id
    ).first():
        raise HTTPException(status_code=404, detail="Employee not found")

    tasks = db.query(Onboarding).filter(
        Onboarding.employee_id == employee_id
    ).all()

    total = len(tasks)
    completed = sum(1 for task in tasks if task.status == "COMPLETED")

    return {
        "employee_id": employee_id,
        "total_tasks": total,
        "completed_tasks": completed,
        "pending_tasks": total - completed,
        "progress_percentage": round(
            completed / total * 100, 2
        ) if total else 0,
    }
