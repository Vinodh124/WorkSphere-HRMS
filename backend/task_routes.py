
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import Employee, Task, User
from permissions import require_authenticated, require_hr_or_admin
from schemas import TaskCreate, TaskResponse, TaskStatusUpdate

router = APIRouter(
    prefix="/tasks",
    tags=["Task Assignment & Tracking"],
)


def get_employee_for_user(db: Session, user: User):
    employee = db.query(Employee).filter(
        Employee.email == user.email
    ).first()

    if not employee:
        raise HTTPException(
            status_code=404,
            detail="Employee profile not found for this account",
        )

    return employee


@router.post(
    "/",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_task(
    data: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_or_admin),
):
    employee = db.query(Employee).filter(
        Employee.id == data.assigned_to
    ).first()

    if not employee:
        raise HTTPException(
            status_code=404,
            detail="Assigned employee not found",
        )

    task = Task(
        title=data.title,
        description=data.description,
        assigned_to=data.assigned_to,
        assigned_by=current_user.id,
        due_date=data.due_date,
        status="PENDING",
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    return task


@router.get(
    "/my",
    response_model=list[TaskResponse],
)
def get_my_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated),
):
    if current_user.role != "EMPLOYEE":
        raise HTTPException(
            status_code=403,
            detail="Only employees can use this endpoint",
        )

    employee = get_employee_for_user(db, current_user)

    return (
        db.query(Task)
        .filter(Task.assigned_to == employee.id)
        .order_by(Task.created_at.desc())
        .all()
    )


@router.get(
    "/",
    response_model=list[TaskResponse],
)
def list_all_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_or_admin),
):
    return (
        db.query(Task)
        .order_by(Task.created_at.desc())
        .all()
    )


@router.patch(
    "/{task_id}/status",
    response_model=TaskResponse,
)
def update_task_status(
    task_id: int,
    data: TaskStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated),
):
    task = db.query(Task).filter(Task.id == task_id).first()

    if not task:
        raise HTTPException(
            status_code=404,
            detail="Task not found",
        )

    if current_user.role == "EMPLOYEE":
        employee = get_employee_for_user(db, current_user)

        if task.assigned_to != employee.id:
            raise HTTPException(
                status_code=403,
                detail="You can only update tasks assigned to you",
            )
    elif current_user.role not in ("HR", "ADMIN"):
        raise HTTPException(
            status_code=403,
            detail="You are not allowed to update task status",
        )

    task.status = data.status

    db.commit()
    db.refresh(task)

    return task
