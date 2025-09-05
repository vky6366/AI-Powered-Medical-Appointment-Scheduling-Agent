from __future__ import annotations

import os
import uuid
from datetime import datetime
from typing import Dict, Any, List

import requests
import streamlit as st

# -----------------------------
# Config
# -----------------------------
FASTAPI_URL = os.getenv("FASTAPI_URL", "http://localhost:5000")

st.set_page_config(page_title="RagaAI – Patient Intake Assistant", page_icon="💬", layout="centered")
st.title("🦷 RagaAI – Patient Intake Assistant")

# -----------------------------
# Session state
# -----------------------------
if "thread_id" not in st.session_state:
    st.session_state["thread_id"] = str(uuid.uuid4())

if "message_history" not in st.session_state:
    st.session_state["message_history"] = []

if "last_patient" not in st.session_state:
    st.session_state["last_patient"] = {}

if "last_booking" not in st.session_state:
    st.session_state["last_booking"] = {}

# -----------------------------
# Helpers
# -----------------------------
def call_api(path: str, params: Dict[str, Any] | None = None, method: str = "GET", json: Dict[str, Any] | None = None):
    url = f"{FASTAPI_URL}{path}"
    if method.upper() == "GET":
        r = requests.get(url, params=params, timeout=20)
    else:
        r = requests.post(url, params=params, json=json, timeout=30)
    r.raise_for_status()
    return r

def iso_from_date_time(date_str: str, time_str: str) -> str:
    """Build naive ISO datetime 'YYYY-MM-DDTHH:MM:SS'."""
    try:
        dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    except Exception:
        # try HH:MM:SS
        dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
    return dt.isoformat(timespec="seconds")

# -----------------------------
# Left header: server health
# -----------------------------
with st.sidebar:
    st.subheader("Server")
    try:
        h = call_api("/health").json()
        st.success("API ✓")
        st.caption(h)
    except Exception as e:
        st.error(f"API not reachable: {e}")
    st.divider()
    st.caption(f"Thread: {st.session_state['thread_id']}")

# -----------------------------
# Chat history
# -----------------------------
for m in st.session_state["message_history"]:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# -----------------------------
# Input box
# -----------------------------
user_input = st.chat_input("Describe your problem, or say 'hi' to begin…")

if user_input:
    st.session_state["message_history"].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    try:
        r = call_api(
            "/stream",
            params={"q": user_input, "thread_id": st.session_state["thread_id"]},
            method="GET",
        )
        data = r.json()
        ai_msg = data.get("message", "Okay.")
        patient = data.get("data", {})
        st.session_state["last_patient"] = patient
    except Exception as e:
        ai_msg = f"⚠️ Backend error: {e}"
        patient = st.session_state.get("last_patient", {})

    st.session_state["message_history"].append({"role": "assistant", "content": ai_msg})
    with st.chat_message("assistant"):
        st.markdown(ai_msg)

# -----------------------------
# Slot picker (when ready)
# -----------------------------
patient = st.session_state.get("last_patient", {}) or {}

def show_slot_picker(p: Dict[str, Any]):
    st.subheader("🗓️ Schedule")
    doc = p.get("doctor") or ""
    date_str = p.get("appointment_date") or ""

    if not doc or not date_str:
        st.info("Pick a doctor and date in chat to see available slots.")
        return

    # Fetch slots
    slots: List[Dict[str, Any]] = []
    err = None
    try:
        rr = call_api("/appointments/available", params={"doctor": doc, "date": date_str})
        slots = rr.json().get("slots", [])
    except Exception as e:
        err = str(e)

    if err:
        st.error(f"Could not fetch slots: {err}")
        return

    if not slots:
        st.warning("No slots available for this doctor/date.")
        return

    pretty = [f"{s['start']}–{s['end']}" for s in slots]
    choice = st.radio("Available time slots:", pretty, index=0, key="slot_choice")

    with st.expander("Booking details (review)"):
        st.json({
            "name": p.get("name", ""),
            "dob": p.get("dob", ""),
            "email": p.get("email", ""),
            "phone": p.get("phone", ""),
            "location": p.get("location", ""),
            "insurance": {
                "carrier": p.get("insurance_carrier", ""),
                "member_id": p.get("insurance_member_id", ""),
                "group": p.get("insurance_group", ""),
            },
            "doctor": doc,
            "date": date_str,
            "duration_min": p.get("appointment_duration_min", 60),
            "returning": p.get("returning_patient", False),
            "problem": p.get("problem", ""),
            "problem_description": p.get("problem_description", ""),
        })

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Confirm appointment"):
            start, end = choice.split("–")
            payload = {
                "name": p.get("name", ""),
                "dob": p.get("dob", ""),
                "doctor": doc,
                "date": date_str,
                "start": start.strip(),
                "end": end.strip(),
                "duration": p.get("appointment_duration_min", 60),
                "returning": p.get("returning_patient", False),
                "insurance_carrier": p.get("insurance_carrier", ""),
                "member_id": p.get("insurance_member_id", ""),
                "group": p.get("insurance_group", ""),
                "email": p.get("email", ""),
                "phone": p.get("phone", ""),
                "problem": p.get("problem", ""),
                "problem_description": p.get("problem_description", ""),
                "location": p.get("location", ""),
            }
            try:
                br = call_api("/appointments/book", method="POST", json=payload).json()
                st.session_state["last_booking"] = br
                st.success(f"Appointment confirmed ✅  \nBooking ID: `{br.get('booking_id','')}`")
            except Exception as e:
                st.error(f"Booking failed: {e}")

    with col2:
        if st.button("📤 Send intake form + 📆 Schedule reminders"):
            br = st.session_state.get("last_booking", {})
            bk_payload = br.get("payload", {}) if isinstance(br, dict) else {}
            email = (bk_payload.get("email") or p.get("email") or "").strip()
            if not email:
                st.error("Email missing — please provide email in chat first.")
                return

            # 1) Send intake form (simulated)
            try:
                call_api("/notify/send_after_confirm", method="POST",
                         json={"email": email, "name": p.get("name",""), "booking_id": br.get("booking_id","")})
                st.success("Form sent (simulated) ✓")
            except Exception as e:
                st.error(f"Send form failed: {e}")

            # 2) Schedule 3 reminders
            try:
                appt_iso = iso_from_date_time(date_str, choice.split("–")[0].strip())
                call_api("/reminders/schedule", method="POST",
                         json={"email": email, "appointment_iso": appt_iso})
                st.success("Reminders scheduled (48h/24h/2h) ✓")
            except Exception as e:
                st.error(f"Schedule reminders failed: {e}")

# Render picker if doctor + date are known
if patient.get("doctor") and patient.get("appointment_date"):
    show_slot_picker(patient)

st.divider()
st.caption("Tip: say “any doctor on YYYY-MM-DD” to quickly jump to scheduling.")
