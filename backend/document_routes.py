
import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models import Employee, EmployeeDocument

router = APIRouter(
    prefix="/documents",
    tags=["Employee Documents"],
)

UPLOAD_DIR = Path(__file__).resolve().parent / "uploads" / "employee_documents"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

MAX_FILE_SIZE = 5 * 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".png", ".jpg", ".jpeg"}


def user_role(user):
    return str(getattr(user.role, "value", user.role)).upper()


def can_access_employee(user, employee_id: int) -> bool:
    role = user_role(user)

    if role in {"ADMIN", "HR"}:
        return True

    # Employees may access documents belonging to their own employee record.
    return getattr(user, "employee_id", None) == employee_id


@router.post("/upload/{employee_id}")
async def upload_document(
    employee_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not can_access_employee(current_user, employee_id):
        raise HTTPException(status_code=403, detail="Access denied")

    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    original_name = Path(file.filename or "").name
    extension = Path(original_name).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="File type not allowed")

    stored_name = f"{uuid.uuid4().hex}{extension}"
    destination = UPLOAD_DIR / stored_name
    size = 0

    try:
        with destination.open("wb") as output:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break

                size += len(chunk)
                if size > MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=413,
                        detail="File exceeds the 5 MB limit",
                    )

                output.write(chunk)

        document = EmployeeDocument(
            employee_id=employee_id,
            filename=original_name,
            stored_filename=stored_name,
            content_type=file.content_type or "application/octet-stream",
            uploaded_by=current_user.id,
        )
        db.add(document)
        db.commit()
        db.refresh(document)

        return {
            "message": "Document uploaded successfully",
            "id": document.id,
            "employee_id": document.employee_id,
            "filename": document.filename,
            "uploaded_at": document.uploaded_at,
        }

    except Exception:
        if destination.exists():
            destination.unlink()
        db.rollback()
        raise
    finally:
        await file.close()


@router.get("/{employee_id}")
def list_employee_documents(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not can_access_employee(current_user, employee_id):
        raise HTTPException(status_code=403, detail="Access denied")

    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    documents = (
        db.query(EmployeeDocument)
        .filter(EmployeeDocument.employee_id == employee_id)
        .order_by(EmployeeDocument.uploaded_at.desc())
        .all()
    )

    return [
        {
            "id": doc.id,
            "employee_id": doc.employee_id,
            "filename": doc.filename,
            "content_type": doc.content_type,
            "uploaded_by": doc.uploaded_by,
            "uploaded_at": doc.uploaded_at,
        }
        for doc in documents
    ]


@router.get("/download/{document_id}")
def download_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    document = (
        db.query(EmployeeDocument)
        .filter(EmployeeDocument.id == document_id)
        .first()
    )

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if not can_access_employee(current_user, document.employee_id):
        raise HTTPException(status_code=403, detail="Access denied")

    path = UPLOAD_DIR / document.stored_filename
    if not path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=str(path),
        media_type=document.content_type,
        filename=document.filename,
    )
