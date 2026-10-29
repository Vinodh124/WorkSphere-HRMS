
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Date,
    Float,
    ForeignKey,
)
from sqlalchemy.orm import relationship

from database import Base


def utc_now():
    return datetime.now(timezone.utc)


class UserRole(str, Enum):
    ADMIN = "ADMIN"
    HR = "HR"
    EMPLOYEE = "EMPLOYEE"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(8), nullable=False, default=UserRole.EMPLOYEE.value)
    is_active = Column(Integer, nullable=False, default=1)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    reviewed_leaves = relationship(
        "Leave",
        back_populates="reviewer",
        foreign_keys="Leave.reviewed_by",
    )


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    employee_code = Column(String(30), unique=True, nullable=False)
    full_name = Column(String(120), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    department = Column(String(100), nullable=False)
    designation = Column(String(100), nullable=False)
    salary = Column(Float, nullable=False)
    status = Column(String(20), nullable=False, default="Active")

    attendances = relationship(
        "Attendance",
        back_populates="employee",
        cascade="all, delete-orphan",
    )

    leaves = relationship(
        "Leave",
        back_populates="employee",
        cascade="all, delete-orphan",
    )


class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(
        Integer,
        ForeignKey("employees.id"),
        nullable=False,
    )
    attendance_date = Column(Date, nullable=False)
    check_in = Column(DateTime, nullable=True)
    check_out = Column(DateTime, nullable=True)
    status = Column(String(20), nullable=False, default="PRESENT")

    employee = relationship(
        "Employee",
        back_populates="attendances",
    )

    @property
    def working_hours(self):
        if self.check_in is None or self.check_out is None:
            return None

        duration = self.check_out - self.check_in
        return round(max(0, duration.total_seconds() / 3600), 2)


class Leave(Base):
    __tablename__ = "leaves"

    id = Column(Integer, primary_key=True, index=True)

    employee_id = Column(
        Integer,
        ForeignKey("employees.id"),
        nullable=False,
        index=True,
    )

    leave_type = Column(String(20), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    reason = Column(String(1000), nullable=False)
    status = Column(String(20), nullable=False, default="PENDING", index=True)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    reviewed_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
    )

    employee = relationship(
        "Employee",
        back_populates="leaves",
    )

    reviewer = relationship(
        "User",
        back_populates="reviewed_leaves",
        foreign_keys=[reviewed_by],
    )


class Payroll(Base):
    __tablename__ = "payroll"

    id = Column(Integer, primary_key=True, index=True)

    employee_id = Column(
        Integer,
        ForeignKey("employees.id"),
        nullable=False,
        index=True,
    )

    basic_salary = Column(Float, nullable=False)
    deductions = Column(Float, nullable=False, default=0)
    bonus = Column(Float, nullable=False, default=0)
    net_salary = Column(Float, nullable=False)

    month = Column(String(7), nullable=False, index=True)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    employee = relationship("Employee")
# NOTIFICATIONS MODEL

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    title = Column(String(150), nullable=False)
    message = Column(String(1000), nullable=False)
    notification_type = Column(
        String(50),
        nullable=False,
        default="GENERAL",
    )

    is_read = Column(
        Integer,
        nullable=False,
        default=0,
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    user = relationship("User")

from sqlalchemy import UniqueConstraint


class LeavePolicy(Base):
    __tablename__ = "leave_policies"

    id = Column(Integer, primary_key=True, index=True)
    leave_type = Column(String(20), unique=True, nullable=False)
    total_days_allowed = Column(Integer, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )


class LeaveBalance(Base):
    __tablename__ = "leave_balances"

    __table_args__ = (
        UniqueConstraint(
            "employee_id",
            "leave_type",
            name="uq_leave_balance_employee_type",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(
        Integer,
        ForeignKey("employees.id"),
        nullable=False,
        index=True,
    )
    leave_type = Column(String(20), nullable=False)
    remaining_days = Column(Integer, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )
    
class Shift(Base):
    __tablename__ = "shifts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(30), unique=True, nullable=False)
    start_time = Column(String(5), nullable=False)
    end_time = Column(String(5), nullable=False)


class EmployeeShift(Base):
    __tablename__ = "employee_shifts"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(
        Integer,
        ForeignKey("employees.id"),
        nullable=False,
        index=True,
    )
    shift_id = Column(
        Integer,
        ForeignKey("shifts.id"),
        nullable=False,
        index=True,
    )

    employee = relationship("Employee")
    shift = relationship("Shift")


class EmployeeDocument(Base):
    __tablename__ = "employee_documents"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(
        Integer,
        ForeignKey("employees.id"),
        nullable=False,
        index=True,
    )
    filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False, unique=True)
    content_type = Column(String(100), nullable=False)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    uploaded_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    employee = relationship("Employee")
    uploader = relationship("User")

class PerformanceReview(Base):
    __tablename__ = "performance_reviews"

    id = Column(Integer, primary_key=True, index=True)

    employee_id = Column(
        Integer,
        ForeignKey("employees.id"),
        nullable=False,
        index=True,
    )

    reviewer_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
    )

    rating = Column(Integer, nullable=False)
    feedback = Column(String(2000), nullable=False)
    review_period = Column(String(30), nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    employee = relationship("Employee")
    reviewer = relationship("User")

# ==========================================
# MODULE 21: EMPLOYEE ONBOARDING
# ==========================================

class Onboarding(Base):
    __tablename__ = "onboarding"

    id = Column(Integer, primary_key=True, index=True)

    employee_id = Column(
        Integer,
        ForeignKey("employees.id"),
        nullable=False,
        index=True,
    )

    task_name = Column(String(200), nullable=False)

    status = Column(
        String(20),
        nullable=False,
        default="PENDING",
    )

    due_date = Column(Date, nullable=False)

    employee = relationship("Employee")
class Resignation(Base):
    __tablename__ = "resignations"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(
        Integer,
        ForeignKey("employees.id"),
        nullable=False,
        index=True,
    )
    reason = Column(String(2000), nullable=False)
    notice_period = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False, default="PENDING")
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    employee = relationship("Employee")
class Announcement(Base):
    __tablename__ = "announcements"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    message = Column(String(5000), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    creator = relationship("User")
    
# TASK ASSIGNMENT AND TRACKING

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(String(2000), nullable=False, default="")
    assigned_to = Column(
        Integer,
        ForeignKey("employees.id"),
        nullable=False,
        index=True,
    )
    assigned_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
    )
    status = Column(String(20), nullable=False, default="PENDING")
    due_date = Column(Date, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    employee = relationship("Employee")
    assigner = relationship("User")
