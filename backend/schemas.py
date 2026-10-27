
from datetime import date, datetime
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    model_validator,
    field_validator,
)


# AUTHENTICATION SCHEMAS

class UserRegister(BaseModel):
    username: str = Field(
        min_length=3,
        max_length=50,
        pattern=r"^[A-Za-z0-9_.-]+$",
    )
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    role: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# EMPLOYEE SCHEMAS

class EmployeeCreate(BaseModel):
    employee_code: str = Field(min_length=1, max_length=30)
    full_name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    department: str = Field(min_length=1, max_length=100)
    designation: str = Field(min_length=1, max_length=100)
    salary: float = Field(ge=0)
    status: str = Field(
        default="Active",
        pattern=r"^(Active|Inactive)$",
    )


class EmployeeUpdate(EmployeeCreate):
    pass


class EmployeeResponse(EmployeeCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)


# ATTENDANCE SCHEMAS

class AttendanceCheckIn(BaseModel):
    employee_id: int = Field(gt=0)


class AttendanceStatusUpdate(BaseModel):
    employee_id: int = Field(gt=0)
    attendance_date: date
    status: Literal["PRESENT", "ABSENT", "HALF_DAY"]


class AttendanceResponse(BaseModel):
    id: int
    employee_id: int
    attendance_date: date
    check_in: datetime | None = None
    check_out: datetime | None = None
    status: str
    working_hours: float | None = None

    model_config = ConfigDict(from_attributes=True)


# LEAVE MANAGEMENT SCHEMAS

class LeaveCreate(BaseModel):
    # EMPLOYEE accounts must omit employee_id.
    # HR/ADMIN may supply an employee_id.
    employee_id: int | None = Field(default=None, gt=0)
    leave_type: Literal["SICK", "CASUAL", "PAID"]
    start_date: date
    end_date: date
    reason: str = Field(min_length=3, max_length=1000)

    @model_validator(mode="after")
    def validate_leave_dates(self):
        if self.end_date < self.start_date:
            raise ValueError(
                "End date must be on or after start date."
            )

        if self.start_date < date.today():
            raise ValueError(
                "Leave cannot start in the past."
            )

        if not self.reason.strip():
            raise ValueError("Reason cannot be empty.")

        return self


class LeaveReview(BaseModel):
    status: Literal["APPROVED", "REJECTED"]


class LeaveResponse(BaseModel):
    id: int
    employee_id: int
    leave_type: str
    start_date: date
    end_date: date
    reason: str
    status: str
    created_at: datetime
    reviewed_by: int | None = None

    model_config = ConfigDict(from_attributes=True)

from datetime import date
from pydantic import BaseModel, Field, ConfigDict, field_validator


class PayrollCreate(BaseModel):
    employee_id: int = Field(gt=0)
    basic_salary: float = Field(ge=0)
    deductions: float = Field(default=0, ge=0)
    bonus: float = Field(default=0, ge=0)
    month: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")

    @field_validator("basic_salary", "deductions", "bonus")
    @classmethod
    def validate_money(cls, value):
        if not float(value) < float("inf"):
            raise ValueError("Amount must be finite.")
        return round(value, 2)


class PayrollResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    employee_id: int
    employee_name: str | None = None
    basic_salary: float
    deductions: float
    bonus: float
    net_salary: float
    month: str
    created_at: datetime
# PAYROLL SCHEMAS

class PayrollCreate(BaseModel):
    employee_id: int = Field(gt=0)
    basic_salary: float = Field(ge=0)
    deductions: float = Field(default=0, ge=0)
    bonus: float = Field(default=0, ge=0)
    month: str = Field(
        pattern=r"^\d{4}-(0[1-9]|1[0-2])$"
    )

    @field_validator("basic_salary", "deductions", "bonus")
    @classmethod
    def validate_money(cls, value):
        import math

        if not math.isfinite(value):
            raise ValueError("Amount must be finite.")

        return round(value, 2)


class PayrollResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    employee_id: int
    employee_name: str | None = None
    basic_salary: float
    deductions: float
    bonus: float
    net_salary: float
    month: str
    created_at: datetime

# NOTIFICATION SCHEMAS

class NotificationCreate(BaseModel):
    user_id: int = Field(gt=0)
    title: str = Field(min_length=1, max_length=150)
    message: str = Field(min_length=1, max_length=1000)
    notification_type: str = Field(
        default="GENERAL",
        min_length=1,
        max_length=50,
    )


class NotificationResponse(BaseModel):
    id: int
    user_id: int
    title: str
    message: str
    notification_type: str
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# LEAVE POLICY AND BALANCE SCHEMAS

class LeavePolicyCreate(BaseModel):
    leave_type: Literal["SICK", "CASUAL", "PAID"]
    total_days_allowed: int = Field(ge=0, le=365)


class LeavePolicyResponse(BaseModel):
    id: int
    leave_type: str
    total_days_allowed: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LeaveBalanceResponse(BaseModel):
    id: int
    employee_id: int
    leave_type: str
    remaining_days: int
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
class AdminUserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    role: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserRoleUpdate(BaseModel):
    role: Literal["ADMIN", "HR", "EMPLOYEE"]


class UserStatusUpdate(BaseModel):
    is_active: bool
