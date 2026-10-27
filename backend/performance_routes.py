
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import get_db
from auth import get_current_user, require_roles
from models import Employee, PerformanceReview

router = APIRouter(
    prefix="/performance",
    tags=["Performance Management"],
)


class PerformanceReviewCreate(BaseModel):
    employee_id: int = Field(gt=0)
    rating: int = Field(ge=1, le=5)
    feedback: str = Field(min_length=1, max_length=2000)
    review_period: str = Field(min_length=1, max_length=30)


@router.post("/")
def create_performance_review(
    review_data: PerformanceReviewCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("ADMIN", "HR")),
):
    employee = (
        db.query(Employee)
        .filter(Employee.id == review_data.employee_id)
        .first()
    )

    if not employee:
        raise HTTPException(
            status_code=404,
            detail="Employee not found",
        )

    review = PerformanceReview(
        employee_id=review_data.employee_id,
        reviewer_id=current_user.id,
        rating=review_data.rating,
        feedback=review_data.feedback,
        review_period=review_data.review_period,
    )

    db.add(review)
    db.commit()
    db.refresh(review)

    return {
        "message": "Performance review created successfully",
        "id": review.id,
        "employee_id": review.employee_id,
        "reviewer_id": review.reviewer_id,
        "rating": review.rating,
        "feedback": review.feedback,
        "review_period": review.review_period,
        "created_at": review.created_at,
    }


@router.get("/")
def get_all_performance_reviews(
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("ADMIN", "HR")),
):
    reviews = (
        db.query(PerformanceReview)
        .order_by(PerformanceReview.created_at.desc())
        .all()
    )

    return [
        {
            "id": review.id,
            "employee_id": review.employee_id,
            "reviewer_id": review.reviewer_id,
            "rating": review.rating,
            "feedback": review.feedback,
            "review_period": review.review_period,
            "created_at": review.created_at,
        }
        for review in reviews
    ]


@router.get("/employee/{employee_id}")
def get_employee_performance_reviews(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("ADMIN", "HR")),
):
    employee = (
        db.query(Employee)
        .filter(Employee.id == employee_id)
        .first()
    )

    if not employee:
        raise HTTPException(
            status_code=404,
            detail="Employee not found",
        )

    reviews = (
        db.query(PerformanceReview)
        .filter(PerformanceReview.employee_id == employee_id)
        .order_by(PerformanceReview.created_at.desc())
        .all()
    )

    return [
        {
            "id": review.id,
            "employee_id": review.employee_id,
            "reviewer_id": review.reviewer_id,
            "rating": review.rating,
            "feedback": review.feedback,
            "review_period": review.review_period,
            "created_at": review.created_at,
        }
        for review in reviews
    ]
