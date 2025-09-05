from __future__ import annotations
from .schema import IntakeState, PatientIntake
from .utils import assign_duration, fetch_patient_record

def node_ensure_problem(state: IntakeState) -> IntakeState:
    p: PatientIntake = state["patient"]
    if not p.problem:
        state["message"] = "What brings you in today? (e.g., 'allergies', 'tooth pain')"
        state["next_step"] = "ask_more"; return state
    if not p.problem_description:
        state["message"] = "Got it. Could you add a few details about the issue?"
        state["next_step"] = "ask_more"; return state
    return state

def node_ask_returning(state: IntakeState) -> IntakeState:
    p: PatientIntake = state["patient"]
    inline = state.get("_inline", {})
    if p.returning_patient is None:
        if "_yes_no" in inline:
            p.returning_patient = bool(inline["_yes_no"])
            p.appointment_duration_min = assign_duration(p.returning_patient)
            state["patient"] = p
        else:
            state["message"] = "Have you visited us before? (yes/no)"
            state["next_step"] = "ask_more"; return state

    # If returning, try to fetch record (needs email OR name+dob)
    if p.returning_patient:
        if not (p.email or (p.name and p.dob)):
            state["message"] = "To find your record, please share your registered email OR your full name and DOB (YYYY-MM-DD)."
            state["next_step"] = "ask_more"; return state
        rec = fetch_patient_record(p.email, p.name, p.dob)
        if rec:
            # Prefill basics if missing
            p.name  = p.name  or rec.get("name")
            p.dob   = p.dob   or str(rec.get("dob") or "")
            p.email = p.email or rec.get("email")
            p.phone = p.phone or rec.get("phone")
            state["patient"] = PatientIntake(**p.model_dump())
    return state

def node_ensure_doctor(state: IntakeState) -> IntakeState:
    p: PatientIntake = state["patient"]
    if not p.doctor:
        state["message"] = "Do you have a preferred doctor? If yes, share the name; else say 'any'."
        state["next_step"] = "ask_more"; return state
    return state

def node_ensure_date(state: IntakeState) -> IntakeState:
    p: PatientIntake = state["patient"]
    if not p.appointment_date:
        who = "returning" if p.returning_patient else "new"
        mins = p.appointment_duration_min or assign_duration(p.returning_patient)
        p.appointment_duration_min = mins
        state["patient"] = p
        state["message"] = f"Perfect. I've marked you as {who}; your appointment will be {mins} minutes.\nWhich date works for you? (YYYY-MM-DD)"
        state["next_step"] = "ask_more"; return state
    return state

def node_ensure_contact(state: IntakeState) -> IntakeState:
    p: PatientIntake = state["patient"]
    if not p.email:
        state["message"] = "Share your email so I can send the confirmation & intake form."
        state["next_step"] = "ask_more"; return state
    if not p.phone:
        state["message"] = "And your phone number for SMS reminders?"
        state["next_step"] = "ask_more"; return state
    return state

def node_ensure_insurance(state: IntakeState) -> IntakeState:
    p: PatientIntake = state["patient"]
    if not p.insurance_carrier:
        state["message"] = "Do you have insurance? If yes, please share your insurance carrier name."
        state["next_step"] = "ask_more"; return state
    if not p.insurance_member_id:
        state["message"] = "Please share your insurance member ID."
        state["next_step"] = "ask_more"; return state
    if not p.insurance_group:
        state["message"] = "And the insurance group number?"
        state["next_step"] = "ask_more"; return state
    return state

def node_finalize(state: IntakeState) -> IntakeState:
    p: PatientIntake = state["patient"]

    # Safety guards so we never finalize with missing essentials
    if not p.doctor:
        state["message"] = "Do you have a preferred doctor? If yes, share the name; else say 'any'."
        state["next_step"] = "ask_more"
        return state

    if not p.appointment_date:
        who = "returning" if p.returning_patient else "new"
        mins = p.appointment_duration_min or assign_duration(p.returning_patient)
        p.appointment_duration_min = mins
        state["patient"] = p
        state["message"] = (
            f"Perfect. I've marked you as {who}; your appointment will be {mins} minutes.\n"
            f"Which date works for you? (YYYY-MM-DD)"
        )
        state["next_step"] = "ask_more"
        return state

    state["message"] = (
        f"Great. I’ll fetch available slots for {p.doctor or 'any doctor'} "
        f"on {p.appointment_date}. Please pick one in the UI and I’ll confirm."
    )
    state["next_step"] = "done"
    return state

