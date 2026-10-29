
import csv
import io

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from database import get_db
from models import Employee, User
from permissions import require_hr_or_admin

router = APIRouter(
    prefix="/integrations",
    tags=["Third-Party Integrations"],
)


@router.get("/employees/csv")
def export_employees_csv(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_or_admin),
):
    employees = db.query(Employee).order_by(Employee.id.asc()).all()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Employee ID",
        "Name",
        "Email",
        "Phone",
        "Department",
        "Course",
    ])

    for employee in employees:
        writer.writerow([
            employee.id,
            getattr(employee, "name", ""),
            employee.email,
            getattr(employee, "phone", ""),
            getattr(employee, "department", ""),
            getattr(employee, "course", ""),
        ])

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": 'attachment; filename="employees_report.csv"'
        },
    )
