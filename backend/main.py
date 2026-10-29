import calendar
from feedback_routes import router as feedback_router
import logging
from pydantic import BaseModel, EmailStr
from email_service import send_email
from integration_routes import router as integration_router
from task_routes import router as task_router
from resignation_routes import router as resignation_router
from announcement_routes import router as announcement_router
from onboarding_routes import router as onboarding_router
from contextlib import asynccontextmanager
from datetime import date, datetime
from document_routes import router as document_router
from auth import get_current_user, require_roles
from auth_routes import router as auth_router
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, or_
from sqlalchemy.orm import Session
from admin_routes import router as admin_router
from performance_routes import router as performance_router
from database import Base, engine, get_db
from models import (
    Attendance,
    Employee,
    Leave,
    Payroll,
    Notification,
    User,
    LeavePolicy,
    LeaveBalance,
    Shift,
    EmployeeShift,

)
from schemas import (
    AttendanceCheckIn,
    AttendanceResponse,
    AttendanceStatusUpdate,
    EmployeeCreate,
    EmployeeResponse,
    EmployeeUpdate,
    LeaveCreate,
    LeaveResponse,
    LeaveReview,
    PayrollCreate,
    PayrollResponse,
    NotificationCreate,
    NotificationResponse,
)


# ==================================================
# APPLICATION SETUP
# ==================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="WorkSphere HRMS API",
    description=(
        "Employee management, attendance tracking, "
        "authentication, leave management, payroll, "
        "notifications, and monthly reports."
    ),
    version="1.2.0",
    lifespan=lifespan,
)
app.include_router(document_router)
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(performance_router)
app.include_router(onboarding_router)
app.include_router(resignation_router)
app.include_router(announcement_router)
app.include_router(task_router)
app.include_router(integration_router)
app.include_router(feedback_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def normalized_role(user):
    return str(
        getattr(user.role, "value", user.role)
    ).upper()
def send_email_safely(
    to_email: str,
    subject: str,
    body: str,
) -> None:
    """Send an email without interrupting the HRMS workflow."""
    if not to_email:
        return

    try:
        send_email(to_email, subject, body)
    except Exception:
        logging.exception(
            "Failed to send HRMS email to %s",
            to_email,
        )


# ==================================================
# HEALTH CHECK
# ==================================================

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}


# ==================================================
# DASHBOARD STATISTICS
# ==================================================

@app.get("/dashboard/stats", tags=["Dashboard"])
def dashboard_stats(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    today = date.today()
    current_month = today.strftime("%Y-%m")

    total_employees = db.query(Employee).count()

    active_employees = (
        db.query(Employee)
        .filter(
            func.upper(func.trim(Employee.status)) == "ACTIVE"
        )
        .count()
    )

    present_today = (
        db.query(Attendance)
        .filter(
            Attendance.attendance_date == today,
            func.upper(func.trim(Attendance.status)) == "PRESENT",
        )
        .count()
    )

    absent_today = (
        db.query(Attendance)
        .filter(
            Attendance.attendance_date == today,
            func.upper(func.trim(Attendance.status)) == "ABSENT",
        )
        .count()
    )

    half_day_today = (
        db.query(Attendance)
        .filter(
            Attendance.attendance_date == today,
            func.upper(func.trim(Attendance.status)) == "HALF_DAY",
        )
        .count()
    )

    pending_leaves = (
        db.query(Leave)
        .filter(func.upper(func.trim(Leave.status)) == "PENDING")
        .count()
    )

    approved_leaves = (
        db.query(Leave)
        .filter(func.upper(func.trim(Leave.status)) == "APPROVED")
        .count()
    )

    rejected_leaves = (
        db.query(Leave)
        .filter(func.upper(func.trim(Leave.status)) == "REJECTED")
        .count()
    )

    payroll_total = (
        db.query(func.coalesce(func.sum(Payroll.net_salary), 0))
        .filter(Payroll.month == current_month)
        .scalar()
    )

    payroll_records_count = (
        db.query(Payroll)
        .filter(Payroll.month == current_month)
        .count()
    )

    return {
        "total_employees": total_employees,
        "active_employees": active_employees,
        "present_today": present_today,
        "absent_today": absent_today,
        "half_day_today": half_day_today,
        "attendance_date": today.isoformat(),
        "pending_leaves": pending_leaves,
        "approved_leaves": approved_leaves,
        "rejected_leaves": rejected_leaves,
        "payroll_total": float(payroll_total or 0),
        "payroll_records_count": payroll_records_count,
        "payroll_month": current_month,
    }


# ==================================================
# EMPLOYEE MANAGEMENT
# ==================================================

@app.post(
    "/employees/",
    response_model=EmployeeResponse,
    tags=["Employees"],
)
def create_employee(
    employee: EmployeeCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("ADMIN", "HR")),
):
    duplicate = (
        db.query(Employee)
        .filter(
            or_(
                Employee.employee_code == employee.employee_code,
                Employee.email == str(employee.email),
            )
        )
        .first()
    )

    if duplicate:
        raise HTTPException(
            status_code=400,
            detail="Employee code or email already exists.",
        )

    new_employee = Employee(
        **employee.model_dump(mode="json")
    )

    db.add(new_employee)
    db.commit()
    db.refresh(new_employee)
    send_email_safely(
    employee.email,
    "WorkSphere HRMS - Leave Request Submitted",
    (
        f"Hello {employee.full_name},\n\n"
        "Your leave request has been submitted successfully.\n\n"
        f"Leave type: {new_leave.leave_type}\n"
        f"Start date: {new_leave.start_date}\n"
        f"End date: {new_leave.end_date}\n"
        f"Status: {new_leave.status}\n\n"
        "Regards,\nWorkSphere HRMS"
    ),
)


    return new_employee


@app.get(
    "/employees/",
    response_model=list[EmployeeResponse],
    tags=["Employees"],
)
def get_employees(
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("ADMIN", "HR")),
):
    return (
        db.query(Employee)
        .order_by(Employee.id.desc())
        .all()
    )


@app.get(
    "/employees/me",
    response_model=EmployeeResponse,
    tags=["Employees"],
)
def get_my_employee_profile(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    employee = (
        db.query(Employee)
        .filter(Employee.email == current_user.email)
        .first()
    )

    if employee is None:
        raise HTTPException(
            status_code=404,
            detail="No employee record is linked to your account.",
        )

    return employee


@app.get(
    "/employees/{employee_id}",
    response_model=EmployeeResponse,
    tags=["Employees"],
)
def get_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("ADMIN", "HR")),
):
    employee = (
        db.query(Employee)
        .filter(Employee.id == employee_id)
        .first()
    )

    if employee is None:
        raise HTTPException(
            status_code=404,
            detail="Employee not found.",
        )

    return employee


@app.put(
    "/employees/{employee_id}",
    response_model=EmployeeResponse,
    tags=["Employees"],
)
def update_employee(
    employee_id: int,
    employee_data: EmployeeUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("ADMIN", "HR")),
):
    employee = (
        db.query(Employee)
        .filter(Employee.id == employee_id)
        .first()
    )

    if employee is None:
        raise HTTPException(
            status_code=404,
            detail="Employee not found.",
        )

    update_data = employee_data.model_dump(
        mode="json",
        exclude_unset=True,
    )

    new_code = update_data.get("employee_code")
    new_email = update_data.get("email")

    if new_code is not None or new_email is not None:
        conditions = []

        if new_code is not None:
            conditions.append(Employee.employee_code == new_code)

        if new_email is not None:
            conditions.append(Employee.email == new_email)

        duplicate = (
            db.query(Employee)
            .filter(
                Employee.id != employee_id,
                or_(*conditions),
            )
            .first()
        )

        if duplicate:
            raise HTTPException(
                status_code=400,
                detail="Employee code or email already exists.",
            )

    for field, value in update_data.items():
        setattr(employee, field, value)

    db.commit()
    db.refresh(employee)

    return employee


@app.delete(
    "/employees/{employee_id}",
    tags=["Employees"],
)
def delete_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("ADMIN", "HR")),
):
    employee = (
        db.query(Employee)
        .filter(Employee.id == employee_id)
        .first()
    )

    if employee is None:
        raise HTTPException(
            status_code=404,
            detail="Employee not found.",
        )

    # Remove dependent records to avoid orphaned employee data.
    db.query(Attendance).filter(
        Attendance.employee_id == employee_id
    ).delete(synchronize_session=False)

    db.query(Leave).filter(
        Leave.employee_id == employee_id
    ).delete(synchronize_session=False)

    db.query(Payroll).filter(
        Payroll.employee_id == employee_id
    ).delete(synchronize_session=False)

    db.query(LeaveBalance).filter(
        LeaveBalance.employee_id == employee_id
    ).delete(synchronize_session=False)

    db.delete(employee)
    db.commit()

    return {
        "message": "Employee and associated records deleted successfully."
    }


# ==================================================
# ATTENDANCE MANAGEMENT
# ==================================================


@app.post(
    "/attendance/check-in",
    response_model=AttendanceResponse,
    tags=["Attendance"],
)
def check_in(
    payload: AttendanceCheckIn,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles("ADMIN", "HR", "EMPLOYEE")
    ),
):
    from datetime import timedelta

    # Employees may only check in for themselves.
    if normalized_role(current_user) == "EMPLOYEE":
        own_employee = (
            db.query(Employee)
            .filter(Employee.email == current_user.email)
            .first()
        )

        if own_employee is None:
            raise HTTPException(
                status_code=404,
                detail="No employee record is linked to your account.",
            )

        if payload.employee_id != own_employee.id:
            raise HTTPException(
                status_code=403,
                detail="You can only check in for yourself.",
            )

    employee = (
        db.query(Employee)
        .filter(Employee.id == payload.employee_id)
        .first()
    )

    if employee is None:
        raise HTTPException(
            status_code=404,
            detail="Employee not found.",
        )

    if employee.status.strip().upper() != "ACTIVE":
        raise HTTPException(
            status_code=400,
            detail="Inactive employees cannot check in.",
        )

    now = datetime.now()
    today = now.date()
    attendance_date = today
    status = "PRESENT"

    # Find this employee's assigned shift.
    assignment = (
        db.query(EmployeeShift)
        .filter(EmployeeShift.employee_id == employee.id)
        .first()
    )

    shift = assignment.shift if assignment else None

    if shift:
        start_hour, start_minute = map(
            int, shift.start_time.split(":")
        )
        end_hour, end_minute = map(
            int, shift.end_time.split(":")
        )

        shift_start_time = datetime.strptime(
            shift.start_time, "%H:%M"
        ).time()

        shift_end_time = datetime.strptime(
            shift.end_time, "%H:%M"
        ).time()

        # Handle overnight shifts, such as 22:00–06:00.
        if shift_end_time <= shift_start_time:
            if now.time() < shift_end_time:
                # After midnight, still belongs to yesterday's shift.
                attendance_date = today - timedelta(days=1)
                shift_start = datetime.combine(
                    attendance_date,
                    shift_start_time,
                )
            else:
                shift_start = datetime.combine(
                    today,
                    shift_start_time,
                )
        else:
            shift_start = datetime.combine(
                today,
                shift_start_time,
            )

        # Allow a five-minute grace period.
        if now > shift_start + timedelta(minutes=5):
            status = "LATE"

    # Prevent duplicate attendance for the relevant shift date.
    existing_record = (
        db.query(Attendance)
        .filter(
            Attendance.employee_id == employee.id,
            Attendance.attendance_date == attendance_date,
        )
        .first()
    )

    if existing_record:
        raise HTTPException(
            status_code=400,
            detail="Attendance is already recorded for this employee on this attendance date.",
        )

    attendance = Attendance(
        employee_id=employee.id,
        attendance_date=attendance_date,
        check_in=now,
        status=status,
    )

    db.add(attendance)
    db.commit()
    db.refresh(attendance)

    
    return attendance


@app.post(
    "/attendance/check-out",
    response_model=AttendanceResponse,
    tags=["Attendance"],
)
def check_out(
    payload: AttendanceCheckIn,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles("ADMIN", "HR", "EMPLOYEE")
    ),
):
    from datetime import timedelta

    if normalized_role(current_user) == "EMPLOYEE":
        own_employee = (
            db.query(Employee)
            .filter(Employee.email == current_user.email)
            .first()
        )

        if own_employee is None:
            raise HTTPException(
                status_code=404,
                detail="No employee record is linked to your account.",
            )

        if payload.employee_id != own_employee.id:
            raise HTTPException(
                status_code=403,
                detail="You can only check out for yourself.",
            )

    employee = (
        db.query(Employee)
        .filter(Employee.id == payload.employee_id)
        .first()
    )

    if employee is None:
        raise HTTPException(
            status_code=404,
            detail="Employee not found.",
        )

    now = datetime.now()
    today = now.date()

    attendance = (
        db.query(Attendance)
        .filter(
            Attendance.employee_id == employee.id,
            Attendance.attendance_date.in_(
                [today, today - timedelta(days=1)]
            ),
            Attendance.check_in.isnot(None),
            Attendance.check_out.is_(None),
        )
        .order_by(Attendance.attendance_date.desc())
        .first()
    )

    if attendance is None:
        raise HTTPException(
            status_code=404,
            detail="No open check-in record found for today or yesterday.",
        )

    if now < attendance.check_in:
        raise HTTPException(
            status_code=400,
            detail="Check-out cannot be earlier than check-in.",
        )

    attendance.check_out = now

    assignment = (
        db.query(EmployeeShift)
        .filter(EmployeeShift.employee_id == employee.id)
        .first()
    )

    shift = assignment.shift if assignment else None

    if shift:
        shift_start_time = datetime.strptime(
            shift.start_time, "%H:%M"
        ).time()

        shift_end_time = datetime.strptime(
            shift.end_time, "%H:%M"
        ).time()

        shift_end_date = attendance.attendance_date

        # An overnight shift ends on the following day.
        if shift_end_time <= shift_start_time:
            shift_end_date += timedelta(days=1)

        shift_end = datetime.combine(
            shift_end_date,
            shift_end_time,
        )

        if now < shift_end:
            attendance.status = "EARLY_CHECKOUT"

    db.commit()
    db.refresh(attendance)

    return attendance



@app.get(
    "/attendance/",
    response_model=list[AttendanceResponse],
    tags=["Attendance"],
)
def get_attendance(
    attendance_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("ADMIN", "HR")),
):
    query = db.query(Attendance)

    if attendance_date is not None:
        query = query.filter(
            Attendance.attendance_date == attendance_date
        )

    return (
        query.order_by(
            Attendance.attendance_date.desc(),
            Attendance.id.desc(),
        ).all()
    )


@app.get(
    "/attendance/my-history",
    response_model=list[AttendanceResponse],
    tags=["Attendance"],
)
def get_my_attendance_history(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    employee = (
        db.query(Employee)
        .filter(Employee.email == current_user.email)
        .first()
    )

    if employee is None:
        raise HTTPException(
            status_code=404,
            detail="No employee record is linked to your account.",
        )

    return (
        db.query(Attendance)
        .filter(Attendance.employee_id == employee.id)
        .order_by(
            Attendance.attendance_date.desc(),
            Attendance.id.desc(),
        )
        .all()
    )


@app.post(
    "/attendance/mark-status",
    response_model=AttendanceResponse,
    tags=["Attendance"],
)
def mark_attendance_status(
    payload: AttendanceStatusUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("ADMIN", "HR")),
):
    employee = (
        db.query(Employee)
        .filter(Employee.id == payload.employee_id)
        .first()
    )

    if employee is None:
        raise HTTPException(
            status_code=404,
            detail="Employee not found.",
        )

    if payload.attendance_date > date.today():
        raise HTTPException(
            status_code=400,
            detail="Attendance cannot be marked for a future date.",
        )

    attendance = (
        db.query(Attendance)
        .filter(
            Attendance.employee_id == payload.employee_id,
            Attendance.attendance_date == payload.attendance_date,
        )
        .first()
    )

    if attendance is None:
        attendance = Attendance(
            employee_id=payload.employee_id,
            attendance_date=payload.attendance_date,
            status=payload.status,
            check_in=None,
            check_out=None,
        )
        db.add(attendance)
    else:
        attendance.status = payload.status

    if payload.status == "ABSENT":
        attendance.check_in = None
        attendance.check_out = None

    db.commit()
    db.refresh(attendance)

    return attendance


# ==================================================
# MONTHLY ATTENDANCE REPORT
# ==================================================

@app.get(
    "/attendance/monthly-report",
    tags=["Reports"],
)
def monthly_attendance_report(
    year: int = Query(..., ge=2000, le=2100),
    month: int = Query(..., ge=1, le=12),
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("ADMIN", "HR")),
):
    start_date = date(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    end_date = date(year, month, last_day)

    employees = (
        db.query(Employee)
        .order_by(Employee.full_name.asc())
        .all()
    )

    report = []

    for employee in employees:
        records = (
            db.query(Attendance)
            .filter(
                Attendance.employee_id == employee.id,
                Attendance.attendance_date >= start_date,
                Attendance.attendance_date <= end_date,
            )
            .order_by(Attendance.attendance_date.asc())
            .all()
        )

        report.append({
            "employee_id": employee.id,
            "employee_code": employee.employee_code,
            "employee_name": employee.full_name,
            "department": employee.department,
            "designation": employee.designation,
            "present_days": sum(
                1 for record in records
                if record.status == "PRESENT"
            ),
            "absent_days": sum(
                1 for record in records
                if record.status == "ABSENT"
            ),
            "half_days": sum(
                1 for record in records
                if record.status == "HALF_DAY"
            ),
            "days_recorded": len(records),
            "total_working_hours": round(
                sum(record.working_hours or 0 for record in records),
                2,
            ),
        })

    return {
        "year": year,
        "month": month,
        "month_name": calendar.month_name[month],
        "total_employees": len(employees),
        "report": report,
    }


# ==================================================
# LEAVE MANAGEMENT
# ==================================================

@app.post(
    "/leaves/",
    response_model=LeaveResponse,
    tags=["Leaves"],
)
def apply_for_leave(
    payload: LeaveCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    role = normalized_role(current_user)

    if payload.start_date > payload.end_date:
        raise HTTPException(
            status_code=400,
            detail="Leave start date cannot be after the end date.",
        )

    if role == "EMPLOYEE":
        if payload.employee_id is not None:
            raise HTTPException(
                status_code=403,
                detail="Employees can only apply for their own leave.",
            )

        employee = (
            db.query(Employee)
            .filter(Employee.email == current_user.email)
            .first()
        )

    elif role in ["HR", "ADMIN"]:
        if payload.employee_id is not None:
            employee = (
                db.query(Employee)
                .filter(Employee.id == payload.employee_id)
                .first()
            )
        else:
            employee = (
                db.query(Employee)
                .filter(Employee.email == current_user.email)
                .first()
            )
    else:
        raise HTTPException(
            status_code=403,
            detail="Access denied.",
        )

    if employee is None:
        raise HTTPException(
            status_code=404,
            detail="Employee record not found. Ensure the employee email matches the login email.",
        )

    if employee.status.strip().upper() != "ACTIVE":
        raise HTTPException(
            status_code=400,
            detail="Inactive employees cannot apply for leave.",
        )

    overlapping_leave = (
        db.query(Leave)
        .filter(
            Leave.employee_id == employee.id,
            Leave.status.in_(["PENDING", "APPROVED"]),
            Leave.start_date <= payload.end_date,
            Leave.end_date >= payload.start_date,
        )
        .first()
    )

    if overlapping_leave:
        raise HTTPException(
            status_code=409,
            detail="A pending or approved leave already overlaps these dates.",
        )

    new_leave = Leave(
        employee_id=employee.id,
        leave_type=payload.leave_type,
        start_date=payload.start_date,
        end_date=payload.end_date,
        reason=payload.reason.strip(),
        status="PENDING",
    )

    db.add(new_leave)

    hr_admin_users = (
        db.query(User)
        .filter(User.role.in_(["HR", "ADMIN"]))
        .all()
    )

    for recipient in hr_admin_users:
        db.add(
            Notification(
                user_id=recipient.id,
                title="New leave request",
                message=(
                    f"{employee.full_name} submitted a "
                    f"{new_leave.leave_type} leave request from "
                    f"{new_leave.start_date} to {new_leave.end_date}."
                ),
                notification_type="LEAVE",
                is_read=0,
            )
        )

    db.commit()
    db.refresh(new_leave)

    return new_leave

    db.commit()
    db.refresh(new_leave)

    # Send confirmation email to the employee
    send_email_safely(
        employee.email,
        "WorkSphere HRMS - Leave Request Submitted",
        (
            f"Hello {employee.full_name},\n\n"
            "Your leave request has been submitted successfully.\n\n"
            f"Leave type: {new_leave.leave_type}\n"
            f"Start date: {new_leave.start_date}\n"
            f"End date: {new_leave.end_date}\n"
            f"Status: {new_leave.status}\n\n"
            "You will receive another email when HR reviews your request.\n\n"
            "Regards,\nWorkSphere HRMS"
        ),
    )

    # Send notification emails to HR and Admin
    for recipient in hr_admin_users:
        send_email_safely(
            recipient.email,
            "WorkSphere HRMS - New Leave Request",
            (
                "A new leave request requires review.\n\n"
                f"Employee: {employee.full_name}\n"
                f"Employee email: {employee.email}\n"
                f"Leave type: {new_leave.leave_type}\n"
                f"Start date: {new_leave.start_date}\n"
                f"End date: {new_leave.end_date}\n"
                f"Reason: {new_leave.reason}\n"
                f"Status: {new_leave.status}\n\n"
                "Please log in to WorkSphere HRMS to review the request."
            ),
        )

    return new_leave



@app.get(
    "/leaves/",
    response_model=list[LeaveResponse],
    tags=["Leaves"],
)
def get_leaves(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    role = normalized_role(current_user)
    query = db.query(Leave)

    if role == "EMPLOYEE":
        employee = (
            db.query(Employee)
            .filter(Employee.email == current_user.email)
            .first()
        )

        if employee is None:
            raise HTTPException(
                status_code=404,
                detail="Employee record not found.",
            )

        query = query.filter(Leave.employee_id == employee.id)

    elif role not in ["HR", "ADMIN"]:
        raise HTTPException(
            status_code=403,
            detail="Access denied.",
        )

    return query.order_by(Leave.created_at.desc()).all()



@app.patch(
    "/leaves/{leave_id}/review",
    response_model=LeaveResponse,
    tags=["Leaves"],
)
def review_leave(
    leave_id: int,
    payload: LeaveReview,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("HR", "ADMIN")),
):
    try:
        # Find the leave request.
        leave = (
            db.query(Leave)
            .filter(Leave.id == leave_id)
            .first()
        )

        if leave is None:
            raise HTTPException(
                status_code=404,
                detail="Leave request not found.",
            )

        if str(leave.status).upper() != "PENDING":
            raise HTTPException(
                status_code=400,
                detail="Only pending leave requests can be reviewed.",
            )

        new_status = str(
            getattr(payload.status, "value", payload.status)
        ).upper()

        if new_status not in ("APPROVED", "REJECTED"):
            raise HTTPException(
                status_code=400,
                detail="Review status must be APPROVED or REJECTED.",
            )

        # Validate and deduct the balance only when approving.
        if new_status == "APPROVED":
            overlapping_leave = (
                db.query(Leave)
                .filter(
                    Leave.employee_id == leave.employee_id,
                    Leave.id != leave.id,
                    Leave.status == "APPROVED",
                    Leave.start_date <= leave.end_date,
                    Leave.end_date >= leave.start_date,
                )
                .first()
            )

            if overlapping_leave:
                raise HTTPException(
                    status_code=409,
                    detail="Another approved leave overlaps these dates.",
                )

            policy = (
                db.query(LeavePolicy)
                .filter(
                    LeavePolicy.leave_type == leave.leave_type
                )
                .first()
            )

            if policy is None:
                raise HTTPException(
                    status_code=409,
                    detail=(
                        f"No leave policy configured for "
                        f"{leave.leave_type}."
                    ),
                )

            balance = (
                db.query(LeaveBalance)
                .filter(
                    LeaveBalance.employee_id == leave.employee_id,
                    LeaveBalance.leave_type == leave.leave_type,
                )
                .with_for_update()
                .first()
            )

            if balance is None:
                previous_approved = (
                    db.query(Leave)
                    .filter(
                        Leave.employee_id == leave.employee_id,
                        Leave.leave_type == leave.leave_type,
                        Leave.status == "APPROVED",
                    )
                    .all()
                )

                days_already_used = sum(
                    (item.end_date - item.start_date).days + 1
                    for item in previous_approved
                )

                remaining_days = (
                    policy.total_days_allowed - days_already_used
                )

                if remaining_days < 0:
                    raise HTTPException(
                        status_code=409,
                        detail="Calculated leave balance is invalid.",
                    )

                balance = LeaveBalance(
                    employee_id=leave.employee_id,
                    leave_type=leave.leave_type,
                    remaining_days=remaining_days,
                )
                db.add(balance)
                db.flush()

            requested_days = (
                leave.end_date - leave.start_date
            ).days + 1

            if balance.remaining_days < requested_days:
                raise HTTPException(
                    status_code=409,
                    detail=(
                        f"Insufficient {leave.leave_type} leave balance. "
                        f"Remaining: {balance.remaining_days} days; "
                        f"requested: {requested_days} days."
                    ),
                )

            balance.remaining_days -= requested_days

        # Update the leave request.
        leave.status = new_status
        leave.reviewed_by = current_user.id

        # Notify the employee, if an account matches their email.
        employee = (
            db.query(Employee)
            .filter(Employee.id == leave.employee_id)
            .first()
        )

        if employee is not None:
            employee_user = (
                db.query(User)
                .filter(User.email == employee.email)
                .first()
            )

            if employee_user is not None:
                db.add(
                    Notification(
                        user_id=employee_user.id,
                        title=f"Leave request {new_status.lower()}",
                        message=(
                            f"Your {leave.leave_type} leave request from "
                            f"{leave.start_date} to {leave.end_date} "
                            f"has been {new_status.lower()}."
                        ),
                        notification_type="LEAVE",
                        is_read=0,
                    )
                )

        db.commit()
        db.refresh(leave)
        return leave

    except Exception:
        db.rollback()
        raise

# ==================================================
# PAYROLL MANAGEMENT
# ==================================================

@app.post(
    "/payroll/",
    response_model=PayrollResponse,
    status_code=201,
    tags=["Payroll"],
)
def create_payroll(
    payload: PayrollCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("HR", "ADMIN")),
):
    # Find employee
    employee = (
        db.query(Employee)
        .filter(Employee.id == payload.employee_id)
        .first()
    )

    if employee is None:
        raise HTTPException(
            status_code=404,
            detail="Employee not found.",
        )

    if employee.status.strip().upper() != "ACTIVE":
        raise HTTPException(
            status_code=400,
            detail="Cannot generate payroll for an inactive employee.",
        )

    # Prevent duplicate payroll for the same month
    existing = (
        db.query(Payroll)
        .filter(
            Payroll.employee_id == payload.employee_id,
            Payroll.month == payload.month,
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Payroll already exists for this employee and month.",
        )

    # Calculate net salary
    total_earnings = payload.basic_salary + payload.bonus

    if payload.deductions > total_earnings:
        raise HTTPException(
            status_code=400,
            detail="Deductions cannot exceed total earnings.",
        )

    net_salary = round(
        total_earnings - payload.deductions,
        2,
    )

    payroll = Payroll(
        employee_id=payload.employee_id,
        basic_salary=payload.basic_salary,
        deductions=payload.deductions,
        bonus=payload.bonus,
        net_salary=net_salary,
        month=payload.month,
    )

    db.add(payroll)

    # Notify the employee, if an account is linked
    employee_user = (
        db.query(User)
        .filter(User.email == employee.email)
        .first()
    )

    if employee_user:
        notification = Notification(
            user_id=employee_user.id,
            title="Payroll generated",
            message=(
                f"Your payroll for {payload.month} "
                "has been generated."
            ),
            notification_type="PAYROLL",
            is_read=0,
        )
        db.add(notification)

    db.commit()
    db.refresh(payroll)

    return payroll


@app.get(
    "/payroll/",
    response_model=list[PayrollResponse],
    tags=["Payroll"],
)
def list_payroll(
    month: str | None = Query(
        default=None,
        pattern=r"^\d{4}-(0[1-9]|1[0-2])$",
    ),
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("HR", "ADMIN")),
):
    query = (
        db.query(Payroll, Employee.full_name)
        .join(
            Employee,
            Payroll.employee_id == Employee.id,
        )
    )

    if month:
        query = query.filter(Payroll.month == month)

    records = query.order_by(
        Payroll.month.desc(),
        Payroll.id.desc(),
    ).all()

    results = []

    for payroll, employee_name in records:
        item = {
            column.name: getattr(payroll, column.name)
            for column in Payroll.__table__.columns
        }
        item["employee_name"] = employee_name
        results.append(item)

    return results


@app.get(
    "/payroll/my-history",
    response_model=list[PayrollResponse],
    tags=["Payroll"],
)
def get_my_payroll_history(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    employee = (
        db.query(Employee)
        .filter(Employee.email == current_user.email)
        .first()
    )

    if employee is None:
        raise HTTPException(
            status_code=404,
            detail="No employee record is linked to your account.",
        )

    records = (
        db.query(Payroll, Employee.full_name)
        .join(
            Employee,
            Payroll.employee_id == Employee.id,
        )
        .filter(Payroll.employee_id == employee.id)
        .order_by(
            Payroll.month.desc(),
            Payroll.id.desc(),
        )
        .all()
    )

    results = []

    for payroll, employee_name in records:
        item = {
            column.name: getattr(payroll, column.name)
            for column in Payroll.__table__.columns
        }
        item["employee_name"] = employee_name
        results.append(item)

    return results

# ==================================================
# NOTIFICATION MANAGEMENT
# ==================================================

@app.post(
    "/notifications/",
    response_model=NotificationResponse,
    status_code=201,
    tags=["Notifications"],
)
def create_notification(
    payload: NotificationCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("HR", "ADMIN")),
):
    user = (
        db.query(User)
        .filter(User.id == payload.user_id)
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found.",
        )

    notification = Notification(
        user_id=payload.user_id,
        title=payload.title,
        message=payload.message,
        notification_type=payload.notification_type,
        is_read=0,
    )

    db.add(notification)
    db.commit()
    db.refresh(notification)

    return notification


@app.get(
    "/notifications/",
    response_model=list[NotificationResponse],
    tags=["Notifications"],
)
def list_notifications(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    notifications = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .all()
    )

    return notifications


@app.patch(
    "/notifications/{notification_id}/read",
    response_model=NotificationResponse,
    tags=["Notifications"],
)
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    notification = (
        db.query(Notification)
        .filter(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
        .first()
    )

    if notification is None:
        raise HTTPException(
            status_code=404,
            detail="Notification not found.",
        )

    notification.is_read = 1

    db.commit()
    db.refresh(notification)

    return notification

# ==================================================
# SHIFT MANAGEMENT - PHASE 3
# ==================================================

from pydantic import BaseModel, Field
from datetime import time
from sqlalchemy.exc import IntegrityError


class ShiftCreate(BaseModel):
    name: str = Field(min_length=2, max_length=30)
    start_time: time
    end_time: time


class ShiftResponse(BaseModel):
    id: int
    name: str
    start_time: str
    end_time: str


class EmployeeShiftCreate(BaseModel):
    employee_id: int = Field(gt=0)
    shift_id: int = Field(gt=0)


@app.post("/shifts/", tags=["Shift Management"])
def create_shift(
    data: ShiftCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("ADMIN", "HR")),
):
    existing = db.query(Shift).filter(
        func.lower(Shift.name) == data.name.lower()
    ).first()

    if existing:
        raise HTTPException(
            status_code=409,
            detail="A shift with this name already exists",
        )

    shift = Shift(
        name=data.name.strip(),
        start_time=data.start_time.strftime("%H:%M"),
        end_time=data.end_time.strftime("%H:%M"),
    )

    db.add(shift)
    db.commit()
    db.refresh(shift)

    return {
        "id": shift.id,
        "name": shift.name,
        "start_time": shift.start_time,
        "end_time": shift.end_time,
    }


@app.get("/shifts/", tags=["Shift Management"])
def list_shifts(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return db.query(Shift).order_by(Shift.id).all()


@app.post("/employee-shifts/", tags=["Shift Management"])
def assign_employee_shift(
    data: EmployeeShiftCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("ADMIN", "HR")),
):
    employee = db.query(Employee).filter(
        Employee.id == data.employee_id
    ).first()

    if not employee:
        raise HTTPException(
            status_code=404,
            detail="Employee not found",
        )

    shift = db.query(Shift).filter(
        Shift.id == data.shift_id
    ).first()

    if not shift:
        raise HTTPException(
            status_code=404,
            detail="Shift not found",
        )

    assignment = db.query(EmployeeShift).filter(
        EmployeeShift.employee_id == data.employee_id
    ).first()

    if assignment:
        assignment.shift_id = data.shift_id
    else:
        assignment = EmployeeShift(
            employee_id=data.employee_id,
            shift_id=data.shift_id,
        )
        db.add(assignment)

    db.commit()
    db.refresh(assignment)

    return {
        "message": "Employee shift assigned successfully",
        "employee_id": assignment.employee_id,
        "shift_id": assignment.shift_id,
        "shift_name": shift.name,
    }


@app.get("/employee-shifts/", tags=["Shift Management"])
def list_employee_shifts(
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("ADMIN", "HR")),
):
    assignments = db.query(EmployeeShift).all()

    return [
        {
            "id": item.id,
            "employee_id": item.employee_id,
            "employee_name": item.employee.full_name,
            "shift_id": item.shift_id,
            "shift_name": item.shift.name,
            "start_time": item.shift.start_time,
            "end_time": item.shift.end_time,
        }
        for item in assignments
    ]


@app.get("/leaves/calendar", tags=["Leave Management"])
def get_leave_calendar(
    start_date: date = Query(..., description="Calendar start date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="Calendar end date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="start_date must be before or equal to end_date",
        )

    query = db.query(Leave).filter(
        Leave.start_date <= end_date,
        Leave.end_date >= start_date,
    )

    # Employees can see only their own leave requests.
    # Admin and HR can see the team calendar.
    role = getattr(current_user, "role", "")
    if role not in ["Admin", "HR", "ADMIN", "HR"]:
        query = query.filter(
            Leave.employee_id == current_user.id
        )

    leaves = query.order_by(Leave.start_date.asc()).all()

    return [
        {
            "id": leave.id,
            "employee_id": leave.employee_id,
            "leave_type": leave.leave_type,
            "start_date": leave.start_date,
            "end_date": leave.end_date,
            "status": leave.status,
            "reason": leave.reason,
        }
        for leave in leaves
    ]
class TestEmailRequest(BaseModel):
    to_email: EmailStr


@app.post("/test-email", tags=["Email"])
def test_email(payload: TestEmailRequest):
    try:
        send_email(
            payload.to_email,
            "WorkSphere HRMS Email Test",
            "Your WorkSphere HRMS email service is working.",
        )
        return {"message": "Email request accepted by Resend."}
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Email sending failed: {str(exc)}",
        )