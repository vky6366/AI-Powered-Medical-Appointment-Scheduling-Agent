# agents/nodes.py

from __future__ import annotations
from datetime import datetime

from .schema import IntakeState, PatientIntake
from .scheduler import assign_duration
from .models import DoctorAvailability


# =========================================================
# AWAIT SLOT SELECTION
# =========================================================

def node_await_slot_selection(
    state: IntakeState,
) -> IntakeState:
    """
    Shown when the graph is waiting for the user to pick a slot
    (next_step == 'select_slot') but no selected_slot_id has arrived yet.

    Does NOT re-fetch from DB — just re-prompts with the same message.
    This prevents duplicate DB queries and protects against the extract
    node misinterpreting the user's slot reply as patient data.
    """

    # Keep available_slots in state so the frontend can re-render them
    # if needed (they were already sent in the previous response).
    state["message"] = (
        "Please select a slot from the list above "
        "by tapping the one you want."
    )

    state["next_step"] = "select_slot"

    return state

# =========================================================
# ENSURE PROBLEM
# =========================================================

def node_ensure_problem(
    state: IntakeState
) -> IntakeState:
    """
    Ensure:
    - problem
    - problem_description
    """

    p: PatientIntake = state["patient"]

    # -----------------------------------------
    # Main issue
    # -----------------------------------------

    if not p.problem:

        state["message"] = (
            "What seems to be the problem today?"
        )

        state["next_step"] = "ask_problem"

        return state

    # -----------------------------------------
    # Problem description
    # -----------------------------------------

    if not p.problem_description:

        state["message"] = (
            "Could you describe the symptoms in a bit more detail?"
        )

        state["next_step"] = "ask_problem_details"

        return state

    return state


# =========================================================
# ENSURE RETURNING PATIENT
# =========================================================

def node_ensure_returning(
    state: IntakeState
) -> IntakeState:
    """
    Determine whether patient is returning.
    """

    p: PatientIntake = state["patient"]

    if p.returning_patient is None:

        state["message"] = (
            "Have you visited us before? (yes/no)"
        )

        state["next_step"] = "ask_returning"

        return state

    # -----------------------------------------
    # Assign appointment duration
    # -----------------------------------------

    p.appointment_duration_min = assign_duration(
        p.returning_patient
    )

    state["patient"] = p

    return state


# =========================================================
# ENSURE DOCTOR
# =========================================================

def node_ensure_doctor(
    state: IntakeState
) -> IntakeState:
    """
    Ask preferred doctor if missing.
    """

    p: PatientIntake = state["patient"]

    if not p.doctor:

        state["message"] = (
            "Do you have a preferred doctor?"
        )

        state["next_step"] = "ask_doctor"

        return state

    return state


# =========================================================
# ENSURE DATE
# =========================================================

def node_ensure_date(
    state: IntakeState
) -> IntakeState:
    """
    Ensure appointment date exists.
    """

    p: PatientIntake = state["patient"]

    if not p.appointment_date:

        mins = (
            p.appointment_duration_min
            or assign_duration(
                p.returning_patient
            )
        )

        p.appointment_duration_min = mins

        state["patient"] = p

        state["message"] = (
            f"Your appointment duration will be "
            f"{mins} minutes.\n"
            f"Which date works for you? "
            f"(YYYY-MM-DD)"
        )

        state["next_step"] = "ask_date"

        return state

    return state


# =========================================================
# FETCH AVAILABLE SLOTS
# =========================================================

def node_fetch_slots(
    state: IntakeState,
) -> IntakeState:
    """
    Fetch available slots from DB.
    """

    from datetime import datetime

    from .doctor_router import (
        recommend_doctor,
    )

    from .db import SessionLocal

    from .db_service import (
        get_doctor_by_name,
        get_available_slots,
    )

    db = SessionLocal()

    p: PatientIntake = state["patient"]

    # -------------------------------------------------
    # Validate date
    # -------------------------------------------------

    if not p.appointment_date:

        state["message"] = (
            "Please provide an appointment date."
        )

        state["next_step"] = "ask_date"
        db.close()

        return state

    # -------------------------------------------------
    # Resolve doctor
    # -------------------------------------------------

    doctor = None

    # User selected any doctor
    if (
        not p.doctor
        or p.doctor.lower().strip()
        in {"any", "any doctor"}
    ):

        doctor = recommend_doctor(
            db=db,
            problem=p.problem,
            preferred_location=p.location,
        )

        if not doctor:

            state["message"] = (
                "Sorry, I couldn't find an "
                "available doctor for your issue."
            )

            state["next_step"] = "done"
            db.close()

            return state

        p.doctor = doctor.doctor_name

    else:

        doctor = get_doctor_by_name(
            db,
            p.doctor,
        )

        if not doctor:

            state["message"] = (
                f"Doctor '{p.doctor}' not found."
            )

            state["next_step"] = "ask_doctor"
            db.close()

            return state

    # -------------------------------------------------
    # Parse appointment date
    # -------------------------------------------------

    try:

        appointment_date = datetime.strptime(
            p.appointment_date,
            "%Y-%m-%d"
        ).date()

    except Exception:

        state["message"] = (
            "Invalid date format. "
            "Please use YYYY-MM-DD."
        )

        state["next_step"] = "ask_date"
        db.close()

        return state

    # -------------------------------------------------
    # Fetch available slots
    # -------------------------------------------------

    slots = get_available_slots(
        db=db,
        doctor_id=doctor.id,
        available_date=appointment_date,
    )

    if not slots:

        state["message"] = (
            f"No available slots found for "
            f"{doctor.doctor_name} on "
            f"{p.appointment_date}."
        )

        state["next_step"] = "done"
        db.close()

        return state

    # -------------------------------------------------
    # Store slots in graph state
    # -------------------------------------------------

    state["available_slots"] = [
        {
            "slot_id": slot.id,
            "start": str(slot.start_time),
            "end": str(slot.end_time),
        }
        for slot in slots
    ]

    state["patient"] = p

    # -------------------------------------------------
    # Build response message
    # -------------------------------------------------

    slot_lines = []

    for idx, slot in enumerate(
        slots,
        start=1,
    ):

        slot_lines.append(
            f"{idx}. "
            f"{slot.start_time} - "
            f"{slot.end_time}"
        )

    state["message"] = (
        f"Available slots for "
        f"{doctor.doctor_name} "
        f"on {p.appointment_date}:\n\n"
        + "\n".join(slot_lines)
        + "\n\nPlease choose a slot."
    )

    state["next_step"] = "select_slot"

    db.close()
    return state

# =========================================================
# BOOK APPOINTMENT
# =========================================================

def node_book_appointment(
    state: IntakeState,
) -> IntakeState:
    """
    Book selected appointment slot, then send a confirmation email
    to the patient.  Email is best-effort — a failing SMTP server
    does NOT roll back the booking.
    """
    from .db import SessionLocal
    from .db_service import (
        mark_slot_booked,
        create_appointment,
        get_doctor_by_name,
        get_user_by_id,
    )

    db = SessionLocal()

    p: PatientIntake = state["patient"]

    selected_slot_id = state.get(
        "selected_slot_id"
    )
    

    user_id = state.get("user_id")

    # TODO (production): wrap the slot check + mark_slot_booked inside a
    # DB transaction with SELECT FOR UPDATE to prevent the race condition
    # where two users book the same slot simultaneously.
    # e.g.  db.query(DoctorAvailability).filter(...).with_for_update().first()

    if not selected_slot_id:

        state["message"] = (
            "Please select a valid slot."
        )

        state["next_step"] = "select_slot"

        return state

    # -----------------------------------------------------
    # Find slot
    # -----------------------------------------------------

    slot = (
        db.query(DoctorAvailability)
        .filter(
            DoctorAvailability.id
            == selected_slot_id
        )
        .first()
    )

    if not slot:

        state["message"] = (
            "Selected slot not found."
        )

        state["next_step"] = "fetch_slots"

        return state

    # -----------------------------------------------------
    # Already booked
    # -----------------------------------------------------

    if slot.is_booked:

        state["message"] = (
            "Sorry, that slot was just booked. "
            "Please choose another slot."
        )

        state["next_step"] = "fetch_slots"

        return state

    # -----------------------------------------------------
    # Resolve doctor
    # -----------------------------------------------------

    doctor = get_doctor_by_name(
        db,
        p.doctor
    )

    if not doctor:

        state["message"] = (
            "Doctor not found."
        )

        state["next_step"] = "done"

        return state

    # -----------------------------------------------------
    # Mark slot booked
    # -----------------------------------------------------

    mark_slot_booked(
        db,
        slot.id
    )

    # -----------------------------------------------------
    # Create appointment
    # -----------------------------------------------------

    thread_id = state.get("thread_id")

    appointment = create_appointment(
        db=db,
        user_id=user_id,
        doctor_id=doctor.id,
        appointment_date=slot.available_date,
        appointment_start=slot.start_time,
        appointment_end=slot.end_time,
        appointment_duration_min=(
            p.appointment_duration_min
        ),
        returning_patient=(
            p.returning_patient
        ),
        problem=p.problem,
        problem_description=(
            p.problem_description
        ),
        status="confirmed",
        thread_id=thread_id,
    )

    # -----------------------------------------------------
    # Save appointment info into patient state
    # -----------------------------------------------------

    p.appointment_start = str(slot.start_time)
    p.appointment_end   = str(slot.end_time)

    state["appointment_id"] = appointment.id
    state["patient"]        = p

    # -----------------------------------------------------
    # Send confirmation email  (best-effort, non-blocking)
    # -----------------------------------------------------

    try:
        from api.services.notify import send_confirmation_email

        user = get_user_by_id(db, user_id)

        if user and user.email:
            send_confirmation_email(
                to=user.email,
                data={
                    "name":                   user.name or "Patient",
                    "email":                  user.email,
                    "doctor":                 doctor.doctor_name,
                    "appointment_date":       str(slot.available_date),
                    "appointment_start":      str(slot.start_time),
                    "appointment_end":        str(slot.end_time),
                    "appointment_duration_min": p.appointment_duration_min,
                    "problem":                p.problem or "",
                    "booking_id":             str(appointment.booking_uuid),
                },
            )

    except Exception:
        # Never let email failure break the booking confirmation
        import logging
        logging.getLogger("medical_api").exception(
            "node_book_appointment: email send failed for user_id=%s",
            user_id,
        )

    # -----------------------------------------------------
    # Confirmation message
    # -----------------------------------------------------

    state["message"] = (
        f"Your appointment has been confirmed! "
        f"A confirmation email has been sent to you.\n\n"
        f"Doctor: {doctor.doctor_name}\n"
        f"Date:   {slot.available_date}\n"
        f"Time:   {slot.start_time} – {slot.end_time}\n"
        f"Reason: {p.problem}"
    )

    state["next_step"] = "done"
    db.close()
    return state

