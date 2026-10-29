
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Session

from auth import get_current_user, require_roles
from database import Base, get_db
from models import User

router = APIRouter(
    prefix="/feedback",
    tags=["Employee Feedback"],
)


class EmployeeFeedback(Base):
    __tablename__ = "employee_feedback"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    subject = Column(String(150), nullable=False)
    message = Column(String(2000), nullable=False)
    status = Column(String(20), nullable=False, default="PENDING")
    response = Column(String(2000), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


class FeedbackCreate(BaseModel):
    subject: str = Field(min_length=3, max_length=150)
    message: str = Field(min_length=5, max_length=2000)


class FeedbackResponse(BaseModel):
    response: str = Field(min_length=1, max_length=2000)


class FeedbackStatusUpdate(BaseModel):
    status: str = Field(pattern="^(PENDING|REVIEWED|RESOLVED)$")


@router.post("/")
def submit_feedback(
    data: FeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("EMPLOYEE", "HR", "ADMIN")
    ),
):
    feedback = EmployeeFeedback(
        user_id=current_user.id,
        subject=data.subject.strip(),
        message=data.message.strip(),
        status="PENDING",
    )

    if not feedback.subject or not feedback.message:
        raise HTTPException(
            status_code=422,
            detail="Subject and message cannot be blank",
        )

    db.add(feedback)
    db.commit()
    db.refresh(feedback)

    return {
        "message": "Feedback submitted successfully",
        "id": feedback.id,
        "status": feedback.status,
        "created_at": feedback.created_at,
    }


@router.get("/mine")
def get_my_feedback(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items = (
        db.query(EmployeeFeedback)
        .filter(EmployeeFeedback.user_id == current_user.id)
        .order_by(EmployeeFeedback.created_at.desc())
        .all()
    )

    return [
        {
            "id": item.id,
            "subject": item.subject,
            "message": item.message,
            "status": item.status,
            "response": item.response,
            "created_at": item.created_at,
        }
        for item in items
    ]


@router.get("/")
def get_all_feedback(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("ADMIN", "HR")
    ),
):
    items = (
        db.query(EmployeeFeedback)
        .order_by(EmployeeFeedback.created_at.desc())
        .all()
    )

    return [
        {
            "id": item.id,
            "user_id": item.user_id,
            "subject": item.subject,
            "message": item.message,
            "status": item.status,
            "response": item.response,
            "created_at": item.created_at,
        }
        for item in items
    ]


@router.patch("/{feedback_id}/status")
def update_feedback_status(
    feedback_id: int,
    data: FeedbackStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("ADMIN", "HR")
    ),
):
    item = (
        db.query(EmployeeFeedback)
        .filter(EmployeeFeedback.id == feedback_id)
        .first()
    )

    if item is None:
        raise HTTPException(
            status_code=404,
            detail="Feedback not found",
        )

    item.status = data.status
    db.commit()
    db.refresh(item)

    return {
        "message": "Feedback status updated",
        "id": item.id,
        "status": item.status,
    }


@router.patch("/{feedback_id}/response")
def respond_to_feedback(
    feedback_id: int,
    data: FeedbackResponse,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("ADMIN", "HR")
    ),
):
    item = (
        db.query(EmployeeFeedback)
        .filter(EmployeeFeedback.id == feedback_id)
        .first()
    )

    if item is None:
        raise HTTPException(
            status_code=404,
            detail="Feedback not found",
        )

    response_text = data.response.strip()

    if not response_text:
        raise HTTPException(
            status_code=422,
            detail="Response cannot be blank",
        )

    item.response = response_text
    item.status = "REVIEWED"

    db.commit()
    db.refresh(item)

    return {
        "message": "Response saved successfully",
        "id": item.id,
        "status": item.status,
        "response": item.response,
    }
