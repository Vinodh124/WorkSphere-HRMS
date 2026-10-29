from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import Announcement, User
from permissions import require_authenticated, require_hr_or_admin
from schemas import AnnouncementCreate, AnnouncementResponse

router = APIRouter(
    prefix="/announcements",
    tags=["Internal Announcements"],
)


@router.post(
    "/",
    response_model=AnnouncementResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_announcement(
    data: AnnouncementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_or_admin),
):
    announcement = Announcement(
        title=data.title,
        message=data.message,
        created_by=current_user.id,
    )

    db.add(announcement)
    db.commit()
    db.refresh(announcement)

    return announcement


@router.get(
    "/",
    response_model=list[AnnouncementResponse],
)
def list_announcements(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated),
):
    return (
        db.query(Announcement)
        .order_by(Announcement.created_at.desc())
        .all()
    )


@router.get(
    "/{announcement_id}",
    response_model=AnnouncementResponse,
)
def get_announcement(
    announcement_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated),
):
    announcement = db.query(Announcement).filter(
        Announcement.id == announcement_id
    ).first()

    if not announcement:
        raise HTTPException(
            status_code=404,
            detail="Announcement not found",
        )

    return announcement