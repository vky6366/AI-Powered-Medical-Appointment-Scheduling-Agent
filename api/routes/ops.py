# api/routes/ops.py
from __future__ import annotations

from fastapi import APIRouter, Body
from fastapi.responses import JSONResponse
from typing import Any, Dict, List, Optional
from pathlib import Path
from datetime import datetime, timedelta
import json

# Mailers
from ..services.notify import send_confirmation_email, send_email

# Optional reminders service (robust import)
try:
    from ..services import reminders as _reminders_mod  # api/services/reminders.py
except Exception:
    _reminders_mod = None

OUTBOX_DIR = Path("storage/outbox")
REMINDERS_DIR = Path("storage/reminders")
OUTBOX_DIR.mkdir(parents=True, exist_ok=True)
REMINDERS_DIR.mkdir(parents=True, exist_ok=True)

router = APIRouter()


@router.post("/notify/send_after_confirm")
def send_after_confirm(payload: Dict[str, Any] = Body(...)):
    """
    Send the actual confirmation email after booking.
    Body should include at least:
      - email (recipient)
      - booking details used by the templates (name, doctor, appointment_date, appointment_start, appointment_end, booking_id)
      - confirmation_pdf_path (optional; will attach if present)
    """
    data = dict(payload)
    to = data.get("email") or data.get("to") or ""

    # Attach confirmation PDF if present
    atts: List[Path] = []
    pdf = data.get("confirmation_pdf_path")
    if pdf:
        p = Path(pdf)
        if p.exists():
            atts.append(p)

    try:
        ok, info = send_confirmation_email(to=to, data=data, attachments=atts)
        return {"ok": ok, **({} if info is None else info)}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"notify_error: {e}"})


@router.post("/emails/send")
def send_test_email(payload: Dict[str, Any] = Body(...)):
    """
    Lightweight email tester.
    {
      "to": "you@example.com",
      "subject": "Test",
      "text": "Hello",
      "html": "<b>Hello</b>",
      "attachments": ["storage/confirmations/abc.pdf"]
    }
    """
    to = payload.get("to")
    subject = payload.get("subject", "Test Email")
    text = payload.get("text", "")
    html = payload.get("html")
    attachments = [Path(p) for p in payload.get("attachments", []) if p]
    ok, eml = send_email(to=to, subject=subject, text_body=text, html_body=html, attachments=attachments)
    return {"ok": ok, "eml_path": eml}


@router.post("/reminders/schedule")
def schedule_reminder(payload: Dict[str, Any] = Body(...)):
    """
    Tolerant reminder scheduler.

    Accepts any of:
      1) {"to": "...", "when_iso": "YYYY-MM-DDTHH:MM:SS", "text": "..."}
      2) {"to": "...", "minutes_from_now": 30, "text": "..."}
      3) Booking-like payload with appointment_date & appointment_start
         (we derive reminder time = start - 30 minutes)
      4) Fallback: now + 30 minutes

    If api/services/reminders.py exposes schedule_reminder(...), we call it.
    Otherwise we create a JSON ticket in storage/reminders/.
    """
    to = payload.get("to") or payload.get("email")
    text = payload.get("text") or "Appointment reminder"

    # 1) Direct ISO timestamp
    when_iso = payload.get("when_iso")

    # 2) minutes_from_now
    if not when_iso:
        mfn = payload.get("minutes_from_now")
        try:
            if mfn is not None:
                when_iso = (datetime.now() + timedelta(minutes=int(mfn))).isoformat(timespec="seconds")
        except Exception:
            when_iso = None

    # 3) Derive from appointment_date + appointment_start (T-30m)
    if not when_iso:
        adate = payload.get("appointment_date")
        astart = payload.get("appointment_start")
        dt = None
        if adate and astart:
            try:
                dt = datetime.strptime(f"{adate} {astart}", "%Y-%m-%d %H:%M") - timedelta(minutes=30)
            except Exception:
                dt = None
        if dt is None:
            dt = datetime.now() + timedelta(minutes=30)  # 4) fallback
        when_iso = dt.isoformat(timespec="seconds")

    # Try the real reminders service first
    try:
        if _reminders_mod and hasattr(_reminders_mod, "schedule_reminder"):
            _reminders_mod.schedule_reminder(to=to, when_iso=when_iso, text=text, payload=payload)
            return {"ok": True, "scheduled_for": when_iso, "via": "service"}
    except Exception:
        pass

    # Fallback: write a ticket for a worker/cron to pick up
    ticket = {
        "to": to,
        "text": text,
        "when_iso": when_iso,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "payload": payload,
    }
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    ticket_path = REMINDERS_DIR / f"reminder_{ts}.json"
    with open(ticket_path, "w", encoding="utf-8") as f:
        json.dump(ticket, f, ensure_ascii=False, indent=2)

    return {"ok": True, "scheduled_for": when_iso, "ticket": str(ticket_path), "via": "file"}
