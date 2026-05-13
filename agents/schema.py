from __future__ import annotations
from typing import Optional, TypedDict
from pydantic import BaseModel, EmailStr, model_validator
from datetime import date, datetime

class PatientIntake(BaseModel):
    # Basic
    # name: Optional[str] = None
    dob: Optional[str] = None
    age: Optional[int] = None
    doctor: Optional[str] = None
    location: Optional[str] = None  
    
    # Complaint
    problem: Optional[str] = None
    problem_description: Optional[str] = None

    # Contact
    # email: Optional[EmailStr] = None
    # phone: Optional[str] = None

    # Insurance
    insurance_carrier: Optional[str] = None
    insurance_member_id: Optional[str] = None
    insurance_group: Optional[str] = None

    # Scheduling
    returning_patient: Optional[bool] = None
    appointment_duration_min: Optional[int] = None
    appointment_date: Optional[str] = None
    appointment_start: Optional[str] = None
    appointment_end: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def derive_age_from_dob(cls, data):
        if not isinstance(data, dict): return data
        if data.get("age") is None and data.get("dob"):
            try:
                dob = datetime.strptime(data["dob"], "%Y-%m-%d").date()
                today = date.today()
                data["age"] = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            except Exception:
                pass
        return data

class IntakeState(TypedDict, total=False):
    # Core conversation fields
    input_text: str
    patient: PatientIntake
    message: str
    next_step: str
    _inline: dict

    # Auth / session
    user_id: int
    thread_id: str | None          # conversation key — may or may not be a valid UUID

    # Slot selection (Issue 9: graph WAITS here; booking is a separate request)
    available_slots: list          # list of {slot_id, start, end}
    selected_slot_id: int | None   # set by the /chat request when user picks a slot

    # Booking outcome
    booking_done: bool
    appointment_id: int | None


class PatientProfile(BaseModel):
    dob: Optional[str] = None
    age: Optional[int] = None

    insurance_carrier: Optional[str] = None
    insurance_member_id: Optional[str] = None
    insurance_group: Optional[str] = None

class AppointmentRequest(BaseModel):
    doctor: Optional[str] = None
    location: Optional[str] = None

    problem: Optional[str] = None
    problem_description: Optional[str] = None

    returning_patient: Optional[bool] = None

    appointment_duration_min: Optional[int] = None
    appointment_date: Optional[str] = None
    appointment_start: Optional[str] = None
    appointment_end: Optional[str] = None