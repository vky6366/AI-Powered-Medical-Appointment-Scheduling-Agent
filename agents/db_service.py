from __future__ import annotations

from datetime import date, time
from typing import Optional, List

from sqlalchemy.orm import Session

from .db import SessionLocal
from .models import (
    User,
    PatientProfile,
    Doctor,
    DoctorAvailability,
    Appointment,
)


# =========================================================
# DATABASE SESSION
# =========================================================

def get_db():
    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


# =========================================================
# USER SERVICES
# =========================================================

# def create_user(
#     db: Session,
#     name: str,
#     email: str,
#     phone: str,
#     password_hash: str,
# ) -> User:

#     user = User(
#         name=name,
#         email=email,
#         phone=phone,
#         password_hash=password_hash,
#     )

#     db.add(user)
#     db.commit()
#     db.refresh(user)

#     return user


# def get_user_by_email(
#     db: Session,
#     email: str,
# ) -> Optional[User]:

#     return (
#         db.query(User)
#         .filter(User.email == email)
#         .first()
#     )


# def get_user_by_id(
#     db: Session,
#     user_id: int,
# ) -> Optional[User]:

#     return (
#         db.query(User)
#         .filter(User.id == user_id)
#         .first()
#     )


# =========================================================
# PATIENT PROFILE SERVICES
# =========================================================

def create_patient_profile(
    db: Session,
    user_id: int,
    dob: Optional[date] = None,
    insurance_carrier: Optional[str] = None,
    insurance_member_id: Optional[str] = None,
    insurance_group: Optional[str] = None,
) -> PatientProfile:

    profile = PatientProfile(
        user_id=user_id,
        dob=dob,
        insurance_carrier=insurance_carrier,
        insurance_member_id=insurance_member_id,
        insurance_group=insurance_group,
    )

    db.add(profile)
    db.commit()
    db.refresh(profile)

    return profile


def get_patient_profile(
    db: Session,
    user_id: int,
) -> Optional[PatientProfile]:

    return (
        db.query(PatientProfile)
        .filter(PatientProfile.user_id == user_id)
        .first()
    )


# =========================================================
# DOCTOR SERVICES
# =========================================================

def create_doctor(
    db: Session,
    doctor_name: str,
    specialty: str,
    location: str,
    slot_mins: int = 30,
    hours_weekday: Optional[str] = None,
    hours_saturday: Optional[str] = None,
    hours_sunday: Optional[str] = None,
) -> Doctor:

    doctor = Doctor(
        doctor_name=doctor_name,
        specialty=specialty,
        location=location,
        slot_mins=slot_mins,
        hours_weekday=hours_weekday,
        hours_saturday=hours_saturday,
        hours_sunday=hours_sunday,
    )

    db.add(doctor)
    db.commit()
    db.refresh(doctor)

    return doctor


def get_doctor_by_name(
    db: Session,
    doctor_name: str,
) -> Optional[Doctor]:

    return (
        db.query(Doctor)
        .filter(Doctor.doctor_name == doctor_name)
        .first()
    )


def get_all_doctors(
    db: Session,
) -> List[Doctor]:

    return db.query(Doctor).all()


# =========================================================
# DOCTOR AVAILABILITY SERVICES
# =========================================================

def create_availability_slot(
    db: Session,
    doctor_id: int,
    available_date: date,
    start_time: time,
    end_time: time,
) -> DoctorAvailability:

    slot = DoctorAvailability(
        doctor_id=doctor_id,
        available_date=available_date,
        start_time=start_time,
        end_time=end_time,
    )

    db.add(slot)
    db.commit()
    db.refresh(slot)

    return slot


def get_available_slots(
    db: Session,
    doctor_id: int,
    available_date: date,
) -> List[DoctorAvailability]:

    return (
        db.query(DoctorAvailability)
        .filter(
            DoctorAvailability.doctor_id == doctor_id,
            DoctorAvailability.available_date == available_date,
            DoctorAvailability.is_booked == False,
        )
        .order_by(DoctorAvailability.start_time)
        .all()
    )


def mark_slot_booked(
    db: Session,
    slot_id: int,
) -> Optional[DoctorAvailability]:

    slot = (
        db.query(DoctorAvailability)
        .filter(DoctorAvailability.id == slot_id)
        .first()
    )

    if not slot:
        return None

    slot.is_booked = True

    db.commit()
    db.refresh(slot)

    return slot


# =========================================================
# APPOINTMENT SERVICES
# =========================================================

def create_appointment(
    db: Session,
    user_id: int,
    doctor_id: int,
    appointment_date: date,
    appointment_start: time,
    appointment_end: time,
    appointment_duration_min: int,
    returning_patient: bool,
    problem: Optional[str] = None,
    problem_description: Optional[str] = None,
    status: str = "pending",
    thread_id: Optional[str] = None,
):
    import uuid as _uuid

    # thread_id column is UUID type — safely cast the string.
    # Falls back to None if the value is not a valid UUID
    # (e.g. the fallback "user-42" format used in dev).
    parsed_thread_id = None
    if thread_id:
        try:
            parsed_thread_id = _uuid.UUID(str(thread_id))
        except (ValueError, AttributeError):
            parsed_thread_id = None

    appointment = Appointment(
        user_id=user_id,
        doctor_id=doctor_id,
        appointment_date=appointment_date,
        appointment_start=appointment_start,
        appointment_end=appointment_end,
        appointment_duration_min=appointment_duration_min,
        returning_patient=returning_patient,
        problem=problem,
        problem_description=problem_description,
        status=status,
        thread_id=parsed_thread_id,
    )

    db.add(appointment)
    db.commit()
    db.refresh(appointment)

    return appointment


def get_user_appointments(
    db: Session,
    user_id: int,
) -> List[Appointment]:

    return (
        db.query(Appointment)
        .filter(Appointment.user_id == user_id)
        .order_by(Appointment.created_at.desc())
        .all()
    )


def get_doctor_appointments(
    db: Session,
    doctor_id: int,
) -> List[Appointment]:

    return (
        db.query(Appointment)
        .filter(Appointment.doctor_id == doctor_id)
        .order_by(Appointment.appointment_date)
        .all()
    )


def get_appointment_by_id(
    db: Session,
    appointment_id: int,
) -> Optional[Appointment]:

    return (
        db.query(Appointment)
        .filter(Appointment.id == appointment_id)
        .first()
    )


def update_appointment_status(
    db: Session,
    appointment_id: int,
    status: str,
) -> Optional[Appointment]:

    appointment = (
        db.query(Appointment)
        .filter(Appointment.id == appointment_id)
        .first()
    )

    if not appointment:
        return None

    appointment.status = status

    db.commit()
    db.refresh(appointment)

    return appointment

def get_user_by_google_id(
    db: Session,
    google_id: str,
):
    return (
        db.query(User)
        .filter(User.google_id == google_id)
        .first()
    )

def create_google_user(
    db: Session,
    google_id: str,
    name: str,
    email: str,
    profile_picture: str | None = None,
):
    user = User(
        google_id=google_id,
        name=name,
        email=email,
        profile_picture=profile_picture,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user

def get_user_by_id(
    db: Session,
    user_id: int,
):
    return (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )