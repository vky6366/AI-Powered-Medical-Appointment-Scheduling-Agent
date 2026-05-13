from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from .models import (
    Doctor,
    DoctorAvailability,
    Appointment,
)

from .db_service import (
    get_doctor_by_name,
    get_available_slots,
    mark_slot_booked,
    create_appointment,
)


# =========================================================
# APPOINTMENT DURATION POLICY
# =========================================================

def assign_duration(
    returning_patient: Optional[bool]
) -> int:
    """
    Business rule:
    Returning patients -> 30 mins
    New patients -> 60 mins
    """

    return 30 if returning_patient else 60


# =========================================================
# FIND BEST SLOT
# =========================================================

def find_best_slot(
    db: Session,
    doctor_name: str,
    appointment_date: date,
):
    """
    Returns the earliest available slot
    for the requested doctor and date.
    """

    doctor = get_doctor_by_name(
        db,
        doctor_name
    )

    if not doctor:
        return None

    slots = get_available_slots(
        db,
        doctor.id,
        appointment_date
    )

    if not slots:
        return None

    return slots[0]


# =========================================================
# AUTO BOOK APPOINTMENT
# =========================================================

def auto_book_appointment(
    db: Session,
    user_id: int,
    doctor_name: str,
    appointment_date: date,
    returning_patient: bool,
    problem: Optional[str] = None,
    problem_description: Optional[str] = None,
):
    """
    Main scheduling engine.

    Flow:
    1. Find doctor
    2. Find available slot
    3. Mark slot booked
    4. Create appointment
    """

    # ---------------------------------------------
    # Find doctor
    # ---------------------------------------------

    doctor = get_doctor_by_name(
        db,
        doctor_name
    )

    if not doctor:
        raise ValueError(
            f"Doctor '{doctor_name}' not found."
        )

    # ---------------------------------------------
    # Find available slots
    # ---------------------------------------------

    slots = get_available_slots(
        db,
        doctor.id,
        appointment_date
    )

    if not slots:
        raise ValueError(
            "No available slots found."
        )

    # ---------------------------------------------
    # Pick earliest slot
    # ---------------------------------------------

    slot = slots[0]

    # ---------------------------------------------
    # Calculate duration
    # ---------------------------------------------

    duration = assign_duration(
        returning_patient
    )

    # ---------------------------------------------
    # Mark slot booked
    # ---------------------------------------------

    mark_slot_booked(
        db,
        slot.id
    )

    # ---------------------------------------------
    # Create appointment
    # ---------------------------------------------

    appointment = create_appointment(
        db=db,
        user_id=user_id,
        doctor_id=doctor.id,
        appointment_date=slot.available_date,
        appointment_start=slot.start_time,
        appointment_end=slot.end_time,
        appointment_duration_min=duration,
        returning_patient=returning_patient,
        problem=problem,
        problem_description=problem_description,
        status="confirmed",
    )

    return appointment


# =========================================================
# FIND NEXT AVAILABLE DATE
# =========================================================

def find_next_available_date(
    db: Session,
    doctor_name: str,
    start_date: date,
    max_days: int = 30,
):
    """
    Search future dates for availability.
    """

    doctor = get_doctor_by_name(
        db,
        doctor_name
    )

    if not doctor:
        return None

    for i in range(max_days):

        check_date = start_date + timedelta(days=i)

        slots = get_available_slots(
            db,
            doctor.id,
            check_date
        )

        if slots:
            return {
                "date": check_date,
                "slots": slots,
            }

    return None


# =========================================================
# CHECK SLOT CONFLICT
# =========================================================

def is_slot_available(
    db: Session,
    doctor_id: int,
    appointment_date: date,
    start_time,
    end_time,
) -> bool:
    """
    Check whether a slot is already booked.
    """

    conflict = (
        db.query(Appointment)
        .filter(
            Appointment.doctor_id == doctor_id,
            Appointment.appointment_date == appointment_date,
            Appointment.appointment_start == start_time,
            Appointment.appointment_end == end_time,
        )
        .first()
    )

    return conflict is None


# =========================================================
# CANCEL APPOINTMENT
# =========================================================

def cancel_appointment(
    db: Session,
    appointment: Appointment,
):
    """
    Cancel appointment and free slot.
    """

    appointment.status = "cancelled"

    # free matching slot
    slot = (
        db.query(DoctorAvailability)
        .filter(
            DoctorAvailability.doctor_id
            == appointment.doctor_id,

            DoctorAvailability.available_date
            == appointment.appointment_date,

            DoctorAvailability.start_time
            == appointment.appointment_start,

            DoctorAvailability.end_time
            == appointment.appointment_end,
        )
        .first()
    )

    if slot:
        slot.is_booked = False

    db.commit()

    return appointment