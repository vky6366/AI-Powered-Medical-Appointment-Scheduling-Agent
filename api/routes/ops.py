from __future__ import annotations
from typing import Any, Dict
from datetime import datetime

import pandas as pd
from fastapi import APIRouter, Body
from fastapi.responses import JSONResponse

from api.config import ADMIN_EXPORT_XLSX, BOOKINGS_XLSX
from api.services.notify import NotificationService
from api.services.reminders import ReminderService

router = APIRouter(tags=["ops"])

notify = NotificationService()
reminders = ReminderService()

@router.post("/export/admin_report")
def export_admin():
    """
    Copy bookings.xlsx into admin_report.xlsx for admin review (simulated export).
    """
    if not BOOKINGS_XLSX.exists():
        return JSONResponse(status_code=404, content={"error": "no bookings yet"})
    try:
        df = pd.read_excel(BOOKINGS_XLSX)
        df.to_excel(ADMIN_EXPORT_XLSX, index=False)
        return {"status": "ok", "file": str(ADMIN_EXPORT_XLSX)}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"export_error: {e}"})


@router.post("/notify/send_after_confirm")
def send_after_confirm(payload: Dict[str, Any] = Body(...)):
    """
    Simulate email with attached PDF intake form after booking.
    payload: {email, name, booking_id, problem, problem_description}
    """
    email_to = (payload.get("email") or "").strip()
    if not email_to:
        return JSONResponse(status_code=400, content={"error": "email is required"})

    try:
        # extend NotificationService to accept extra meta
        notify.send_after_confirm(
            email=email_to,
            name=payload.get("name",""),
            booking_id=payload.get("booking_id",""),
            meta={
                "problem": payload.get("problem",""),
                "problem_description": payload.get("problem_description","")
            }
        )
        return {"status": "sent", "to": email_to}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"notify_error: {e}"})


@router.post("/reminders/schedule")
def schedule_reminders(payload: Dict[str, Any] = Body(...)):
    """
    Create three reminders (T-48h, T-24h, T-2h).
    payload: {email, appointment_iso}
    """
    email_to = (payload.get("email") or "").strip()
    appt_iso = (payload.get("appointment_iso") or "").strip()
    if not email_to or not appt_iso:
        return JSONResponse(status_code=400, content={"error": "email and appointment_iso are required"})
    try:
        count = reminders.schedule_three(email=email_to, appointment_iso=appt_iso)
        return {"status": "scheduled", "count": count}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"reminders_error: {e}"})
