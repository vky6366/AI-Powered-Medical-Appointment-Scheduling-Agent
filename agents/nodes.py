# agents/nodes.py
from __future__ import annotations
from .schema import IntakeState, PatientIntake
from .utils import assign_duration, fetch_patient_record

def node_ensure_problem(state: IntakeState) -> IntakeState:
    """
    Ensure we have a short problem label (e.g., 'fever') and then a brief description.
    """
    p: PatientIntake = state["patient"]

    # Ask for the main issue first
    if not p.problem:
        state["message"] = (
            "I’m sorry you’re dealing with this — I’ll help you quickly.\n"
            "In a few words, what’s the main issue (e.g., ‘allergies’, ‘tooth pain’, ‘fever’)?"
        )
        state["next_step"] = "ask_problem"
        return state

    # Then ask for a little more detail
    if not p.problem_description:
        state["message"] = (
            "Thanks. Could you describe it a bit more?\n"
            "How long, how severe (mild/moderate/severe), anything that makes it better/worse?"
        )
        state["next_step"] = "ask_problem_details"
        return state

    return state

YES_WORDS = {"yes","y","yeah","yep","visited","i have","i've"}
NO_WORDS  = {"no","n","new","first time","nope"}

# agents/nodes.py  (only the node_ask_returning function)
def node_ask_returning(state: IntakeState) -> IntakeState:
    p: PatientIntake = state["patient"]
    inline = dict(state.get("_inline", {}))

    if p.returning_patient is None:
        if "_yes_no" in inline:
            p.returning_patient = bool(inline.pop("_yes_no"))
            # assign duration now
            from .utils import assign_duration
            p.appointment_duration_min = assign_duration(p.returning_patient)
            state["patient"] = p
            state["_inline"] = inline
        else:
            state["message"] = "Have you visited us before? (yes/no)"
            state["next_step"] = "ask_returning"
            return state

    # If returning, but we still lack minimal contact, we’ll fill later in finalize
    return state


def node_ensure_doctor(state: IntakeState) -> IntakeState:
    p: PatientIntake = state["patient"]

    if not p.doctor:
        state["message"] = "Do you have a preferred doctor? If yes, share the name; else say 'any'."
        state["next_step"] = "ask_doctor"
        return state

    # Always normalize and SAVE
    doc = (p.doctor or "").strip().lower()
    if doc in {"any", "any doctor", "no", "none", "na"}:
        p.doctor = "any doctor"
        state["patient"] = p

    return state



def node_ensure_date(state: IntakeState) -> IntakeState:
    """
    Ask for preferred appointment date. Flag next_step='ask_date' so the inline
    parser maps YYYY-MM-DD to appointment_date (not DOB).
    """
    p: PatientIntake = state["patient"]

    if not p.appointment_date:
        who = "returning" if p.returning_patient else "new"
        mins = p.appointment_duration_min or assign_duration(p.returning_patient)
        p.appointment_duration_min = mins
        state["patient"] = p
        state["message"] = f"Okay. Your appointment will be {mins} minutes.\nWhich date works for you? (YYYY-MM-DD)"
        state["next_step"] = "ask_date"
        return state

    return state


def node_ensure_contact(state: IntakeState) -> IntakeState:
    """
    Collect contact only for new patients; for returning, only if missing.
    """
    p: PatientIntake = state["patient"]
    if p.returning_patient:
        if not p.email:
            state["message"] = "To send your confirmation, what’s your email?"
            state["next_step"] = "ask_email"
            return state
        if not p.phone:
            state["message"] = "And your phone number for SMS reminders?"
            state["next_step"] = "ask_phone"
            return state
        return state

    # New patient
    if not p.email:
        state["message"] = "Share your email so I can send the confirmation & intake form."
        state["next_step"] = "ask_email"
        return state

    if not p.phone:
        state["message"] = "And your phone number for SMS reminders?"
        state["next_step"] = "ask_phone"
        return state

    return state


def node_ensure_insurance(state: IntakeState) -> IntakeState:
    """
    Ask insurance ONLY after the appointment is booked (better UX).
    - We detect booking via state["booking_done"] (set by /appointments/book).
    - If self-pay, we skip member/group.
    """
    p: PatientIntake = state["patient"]

    # Not booked yet? Do nothing; keep the previous message from finalize.
    if not state.get("booking_done"):
        return state

    # For returning patients we can skip by default (or still collect; keeping skip for simplicity)
    if p.returning_patient:
        return state

    carrier = (p.insurance_carrier or "").strip().lower()

    # Ask carrier (first time)
    if not carrier:
        state["message"] = "Before your visit, do you have insurance? If yes, please share your insurance carrier name."
        state["next_step"] = "ask_insurance_carrier"
        return state

    # Self-pay short-circuit
    if carrier in {"self-pay", "self pay", "no", "none"}:
        p.insurance_carrier = "self-pay"
        p.insurance_member_id = ""
        p.insurance_group = ""
        state["patient"] = p
        # No new message; we're done
        return state

    # Need member/group
    if not (p.insurance_member_id or "").strip():
        state["message"] = "Please share your insurance member ID."
        state["next_step"] = "ask_insurance_member_id"
        return state

    if not (p.insurance_group or "").strip():
        state["message"] = "And the insurance group number?"
        state["next_step"] = "ask_insurance_group"
        return state

    # All set; no additional message
    return state


def node_finalize(state: IntakeState) -> IntakeState:
    p: PatientIntake = state["patient"]

    # doctor guard
    if not p.doctor:
        state["message"] = "Do you have a preferred doctor? If yes, share the name; else say 'any'."
        state["next_step"] = "ask_doctor"
        return state
    else:
        if p.doctor.strip().lower() in {"any", "any doctor", "no", "none", "na"}:
            p.doctor = "any doctor"
            state["patient"] = p

    # problem guards
    if not p.problem:
        state["message"] = (
            "I’m sorry you’re dealing with this — I’ll help you quickly.\n"
            "In a few words, what’s the main issue (e.g., ‘allergies’, ‘tooth pain’, ‘fever’)?"
        )
        state["next_step"] = "ask_problem"
        return state
    if not p.problem_description:
        state["message"] = (
            "Thanks. Could you describe it a bit more?\n"
            "How long, how severe (mild/moderate/severe), anything that makes it better/worse?"
        )
        state["next_step"] = "ask_problem_details"
        return state

    # returning vs new (contact & insurance for new only)
    if p.returning_patient is None:
        state["message"] = "Have you visited us before? (yes/no)"
        state["next_step"] = "ask_returning"
        return state

    if p.returning_patient:
        if not p.email:
            state["message"] = "To send your confirmation, what’s your email?"
            state["next_step"] = "ask_email"
            return state
        if not p.phone:
            state["message"] = "And your phone number for SMS reminders?"
            state["next_step"] = "ask_phone"
            return state
    else:
        # NEW patient: insurance guards must **skip** when self-pay
        carrier = (p.insurance_carrier or "").strip().lower()
        if not carrier:
            state["message"] = "Do you have insurance? If yes, please share your insurance carrier name."
            state["next_step"] = "ask_insurance_carrier"
            return state
        if carrier not in {"self-pay", "self pay", "no", "none"}:
            if not (p.insurance_member_id or "").strip():
                state["message"] = "Please share your insurance member ID."
                state["next_step"] = "ask_insurance_member_id"
                return state
            if not (p.insurance_group or "").strip():
                state["message"] = "And the insurance group number?"
                state["next_step"] = "ask_insurance_group"
                return state

        # contact (also required)
        if not p.email:
            state["message"] = "Share your email so I can send the confirmation & intake form."
            state["next_step"] = "ask_email"
            return state
        if not p.phone:
            state["message"] = "And your phone number for SMS reminders?"
            state["next_step"] = "ask_phone"
            return state

    # date guard
    if not p.appointment_date:
        mins = p.appointment_duration_min or assign_duration(p.returning_patient)
        p.appointment_duration_min = mins
        state["patient"] = p
        state["message"] = f"Okay. Your appointment will be {mins} minutes.\nWhich date works for you? (YYYY-MM-DD)"
        state["next_step"] = "ask_date"
        return state

    # ready → UI fetch slots
    state["message"] = (
        f"Great. I’ll fetch available slots for {p.doctor or 'any doctor'} "
        f"on {p.appointment_date}. Please pick one in the UI and I’ll confirm."
    )
    state["next_step"] = "done"
    return state
