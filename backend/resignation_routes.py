from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import Employee, Resignation, User
from permissions import require_authenticated, require_hr_or_admin
from schemas import (
    ResignationCreate,
    ResignationResponse,
    ResignationStatusUpdate,
)

router = APIRouter(
    prefix="/resignations",
    tags=["Resignation & Exit Management"],
)


@router.post(
    "/",
    response_model=ResignationResponse,
    status_code=status.HTTP_201_CREATED,
)
def submit_resignation(
    data: ResignationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated),
):
    if current_user.role != "EMPLOYEE":
        raise HTTPException(
            status_code=403,
            detail="Only employees can submit resignations",
        )

    employee = db.query(Employee).filter(
        Employee.email == current_user.email
    ).first()

    if not employee:
        raise HTTPException(
            status_code=404,
            detail="Employee profile not found for this account",
        )

    resignation = Resignation(
        employee_id=employee.id,
        reason=data.reason,
        notice_period=data.notice_period,
        status="PENDING",
    )

    db.add(resignation)
    db.commit()
    db.refresh(resignation)

    return resignation


@router.get(
    "/my",
    response_model=list[ResignationResponse],
)
def get_my_resignations(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated),
):
    if current_user.role != "EMPLOYEE":
        raise HTTPException(
            status_code=403,
            detail="Only employees can view their own requests here",
        )

    employee = db.query(Employee).filter(
        Employee.email == current_user.email
    ).first()

    if not employee:
        raise HTTPException(
            status_code=404,
            detail="Employee profile not found for this account",
        )

    return (
        db.query(Resignation)
        .filter(Resignation.employee_id == employee.id)
        .order_by(Resignation.created_at.desc())
        .all()
    )


@router.get(
    "/",
    response_model=list[ResignationResponse],
)
def list_resignations(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_or_admin),
):
    return (
        db.query(Resignation)
        .order_by(Resignation.created_at.desc())
        .all()
    )


@router.patch(
    "/{resignation_id}/status",
    response_model=ResignationResponse,
)
def update_resignation_status(
    resignation_id: int,
    data: ResignationStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_or_admin),
):
    resignation = db.query(Resignation).filter(
        Resignation.id == resignation_id
    ).first()

    if not resignation:
        raise HTTPException(
            status_code=404,
            detail="Resignation request not found",
        )

    if resignation.status != "PENDING":
        raise HTTPException(
            status_code=400,
            detail="Only pending requests can be approved or rejected",
        )

    resignation.status = data.status

    db.commit()
    db.refresh(resignation)

    return resignation