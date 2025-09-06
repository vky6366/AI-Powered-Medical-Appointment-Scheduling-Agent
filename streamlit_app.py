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

def _dedupe_slots(slots: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    out = []
    for s in slots:
        key = (s.get("doctor","").strip().lower(),
               s.get("date",""),
               str(s.get("start",""))[:5],
               str(s.get("end",""))[:5])
        if key not in seen:
            seen.add(key)
            out.append({
                "doctor": s.get("doctor",""),
                "date": s.get("date",""),
                "start": str(s.get("start",""))[:5],
                "end": str(s.get("end",""))[:5],
            })
    return out


def show_slot_picker(p: Dict[str, Any]):
    st.subheader("🗓️ Schedule")

    doc_raw = (p.get("doctor") or "").strip()
    # Normalize "any doctor" → "any" for the API
    doc = "any" if doc_raw.lower() in {"any", "any doctor", "no", "none", "na"} else doc_raw
    date_str = (p.get("appointment_date") or "").strip()
    duration = int(p.get("appointment_duration_min", 60))

    if not doc or not date_str:
        st.info("Pick a doctor and date in chat to see available slots.")
        return

    # Reset override cache if context changed
    cache_key = f"{doc}|{date_str}|{duration}"
    if st.session_state.get("__override_ctx__") != cache_key:
        st.session_state.pop("__override_slots__", None)
        st.session_state["__override_ctx__"] = cache_key

    # Fetch slots
    slots: List[Dict[str, Any]] = []
    try:
        with st.spinner("Fetching available slots…"):
            rr = call_api(
                "/appointments/available",
                params={"doctor": doc, "date": date_str, "duration_min": duration},
            )
            slots = rr.json().get("slots", [])
    except Exception as e:
        st.error(f"Could not fetch slots: {e}")
        return

    # Use overrides if we have them
    override = st.session_state.get("__override_slots__")
    if override:
        slots = override

    slots = _dedupe_slots(slots)

    if not slots:
        st.warning("No slots available for this doctor/date.")
        colA, colB = st.columns(2)

        # Try any doctor
        with colA:
            if doc != "any" and st.button("🔍 Try any doctor"):
                try:
                    rr2 = call_api(
                        "/appointments/available",
                        params={"doctor": "any", "date": date_str, "duration_min": duration},
                    )
                    slots_any = _dedupe_slots(rr2.json().get("slots", []))
                    if slots_any:
                        st.success("Found slots with other doctors:")
                        st.session_state["__override_slots__"] = slots_any
                        st.rerun()
                    else:
                        st.info("No other doctors available on that date.")
                except Exception as e:
                    st.error(f"Search failed: {e}")

        # Next available search
        with colB:
            if st.button("⏭️ Next available (14 days)"):
                try:
                    rr3 = call_api(
                        "/appointments/next_available",
                        params={
                            "doctor": doc,
                            "start_date": date_str,
                            "duration_min": duration,
                            "horizon_days": 14,
                        },
                    )
                    next_data = rr3.json()
                    ndate = next_data.get("date")
                    nslots = _dedupe_slots(next_data.get("slots", []))
                    if ndate and nslots:
                        st.success(f"Next available: {ndate}")
                        st.session_state["__override_slots__"] = nslots
                        st.session_state["__override_ctx__"] = f"{doc}|{ndate}|{duration}"
                        st.session_state["last_patient"]["appointment_date"] = ndate
                        st.rerun()
                    else:
                        st.info("No availability in the next 14 days.")
                except Exception as e:
                    st.error(f"Search failed: {e}")

        # No slots and no override: stop rendering
        if not st.session_state.get("__override_slots__"):
            return
        # If we did set overrides above, refresh locals
        slots = st.session_state["__override_slots__"]

    # Pretty labels
    pretty = [
        f"{s['start']}–{s['end']} ({s.get('doctor','').strip() or doc_raw or 'doctor'})"
        for s in slots
    ]
    radio_key = f"slot_choice::{st.session_state.get('__override_ctx__','')}"
    choice = st.radio("Available time slots:", pretty, index=0, key=radio_key)

    # Review block
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
            "doctor": doc_raw if doc == "any" else doc,
            "date": date_str,
            "duration_min": duration,
            "returning": p.get("returning_patient", False),
            "problem": p.get("problem", ""),
            "problem_description": p.get("problem_description", ""),
        })

    # Require contact before booking (brief requires email+SMS)
    missing = []
    if not (p.get("email") or "").strip(): missing.append("email")
    if not (p.get("phone") or "").strip(): missing.append("phone")

    col1, col2 = st.columns(2)
    with col1:
        disabled = len(missing) > 0
        if disabled:
            st.info(f"Missing {', '.join(missing)} — please provide in chat.")
        if st.button("✅ Confirm appointment", disabled=disabled):
            # Parse selection to start/end
            time_part = choice.split("(", 1)[0].strip()
            start, end = [x.strip() for x in time_part.split("–", 1)]

            # If 'any', respect the doctor from the selected slot
            selected_idx = pretty.index(choice)
            slot = slots[selected_idx]
            chosen_doc = slot.get("doctor") or doc_raw or "any doctor"

            payload = {
                "name": p.get("name", ""),
                "dob": p.get("dob", ""),
                "doctor": chosen_doc,
                "date": date_str,
                "start": start,
                "end": end,
                "duration": duration,
                "returning": p.get("returning_patient", False),
                "insurance_carrier": p.get("insurance_carrier", ""),
                "member_id": p.get("insurance_member_id", "") or p.get("member_id", ""),
                "group": p.get("insurance_group", "") or p.get("group", ""),
                "email": p.get("email", ""),
                "phone": p.get("phone", ""),
                "problem": p.get("problem", ""),
                "problem_description": p.get("problem_description", ""),
                "location": p.get("location", ""),
                "thread_id": st.session_state["thread_id"],  # important for post-booking flow
            }

            try:
                br = call_api("/appointments/book", method="POST", json=payload).json()
                st.session_state["last_booking"] = br
                st.success(f"Appointment confirmed ✅  \nBooking ID: `{br.get('booking_id','')}`")

                # --- Auto send email + schedule reminders ---
                email = (payload.get("email") or "").strip()
                if email:
                    # Send confirmation + intake form
                    try:
                        call_api(
                            "/notify/send_after_confirm",
                            method="POST",
                            json={
                                "email": email,
                                "name": payload.get("name",""),
                                "booking_id": br.get("booking_id",""),
                                "problem": payload.get("problem",""),
                                "problem_description": payload.get("problem_description",""),
                            },
                        )
                        msg = f"I’ve emailed your confirmation and the intake form to **{email}**."
                        st.session_state["message_history"].append({"role": "assistant", "content": msg})
                        with st.chat_message("assistant"):
                            st.markdown(msg)
                    except Exception as e:
                        st.warning(f"Couldn’t send email: {e}")

                    # Schedule reminders (48h/24h/2h)
                    try:
                        appt_iso = iso_from_date_time(date_str, start)
                        call_api("/reminders/schedule", method="POST",
                                 json={"email": email, "appointment_iso": appt_iso})
                    except Exception as e:
                        st.warning(f"Couldn’t schedule reminders: {e}")

                # --- Trigger post-booking prompt (insurance) ---
                try:
                    follow = call_api(
                        "/stream",
                        params={"q": "", "thread_id": st.session_state["thread_id"]},
                        method="GET",
                    ).json()
                    st.session_state["last_patient"] = follow.get("data", st.session_state["last_patient"])
                    post_msg = follow.get("message")
                    if post_msg:
                        st.session_state["message_history"].append({"role": "assistant", "content": post_msg})
                        with st.chat_message("assistant"):
                            st.markdown(post_msg)
                except Exception:
                    pass

            except Exception as e:
                st.error(f"Booking failed: {e}")

    with col2:
        if st.button("📤 Resend intake form + 📆 Reminders"):
            br = st.session_state.get("last_booking", {})
            bk_payload = br.get("payload", {}) if isinstance(br, dict) else {}
            email = (bk_payload.get("email") or p.get("email") or "").strip()
            if not email:
                st.error("Email missing — please provide email in chat first.")
                return
            # Resend + reschedule (manual)
            try:
                call_api("/notify/send_after_confirm", method="POST",
                         json={
                             "email": email,
                             "name": p.get("name",""),
                             "booking_id": br.get("booking_id",""),
                             "problem": p.get("problem",""),
                             "problem_description": p.get("problem_description",""),
                         })
                st.success("Form sent (simulated) ✓")
            except Exception as e:
                st.error(f"Send form failed: {e}")
            try:
                # reuse the currently selected radio time for ISO
                time_part = choice.split("(", 1)[0].strip()
                start_again = time_part.split("–", 1)[0].strip()
                appt_iso = iso_from_date_time(date_str, start_again)
                call_api("/reminders/schedule", method="POST",
                         json={"email": email, "appointment_iso": appt_iso})
                st.success("Reminders scheduled (48h/24h/2h) ✓")
            except Exception as e:
                st.error(f"Schedule reminders failed: {e}")

# Render picker if doctor + date are known
if patient.get("doctor") and patient.get("appointment_date"):
    show_slot_picker(patient)

