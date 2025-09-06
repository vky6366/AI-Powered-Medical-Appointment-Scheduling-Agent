# api/services/notify.py
from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, Iterable, Optional, List, Tuple
import os
import smtplib
import mimetypes
from email.message import EmailMessage
from datetime import datetime

# --- App config (read from environment) ---
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM     = os.getenv("SMTP_FROM", SMTP_USERNAME or "no-reply@example.com")
SMTP_USE_TLS  = os.getenv("SMTP_USE_TLS", "true").lower() in ("1", "true", "yes")
OUTBOX_DIR    = Path(os.getenv("OUTBOX_DIR", "storage/outbox"))  # for .eml fallback

OUTBOX_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------
# Utility: safe path finder for the Intake form the assignment provided
# ---------------------------------------------------------------------
def locate_intake_form() -> Optional[Path]:
    """
    Tries a few conventional locations/filenames for the intake form PDF.
    Returns a Path if found, else None.
    """
    candidates = [
        Path("assets/forms/intake_form.pdf"),
        Path("assets/forms/Intake Form.pdf"),
        Path("assets/forms/New Patient Intake Form.pdf"),
        Path("storage/forms/intake_form.pdf"),
        Path("storage/forms/New Patient Intake Form.pdf"),
        Path("New Patient Intake Form.pdf"),  # project root
    ]
    for p in candidates:
        if p.exists() and p.is_file():
            return p
    return None


# -----------------------
# Core SMTP send function
# -----------------------
def send_email(
    to: str | Iterable[str],
    subject: str,
    text_body: str,
    html_body: Optional[str] = None,
    attachments: Optional[Iterable[Path]] = None,
    cc: Optional[Iterable[str]] = None,
    bcc: Optional[Iterable[str]] = None,
    reply_to: Optional[str] = None,
) -> Tuple[bool, Optional[str] | Dict[str, str]]:
    """
    Sends an email. If SMTP creds are missing or SMTP fails, writes an .eml in storage/outbox
    and returns (False, {"eml_path": path, "error": "..."}). On success returns (True, None).
    Also tries TLS:587 first, then SSL:465 as fallback.
    """
    # --- normalize recipients ---
    if isinstance(to, str):
        to_list = [to]
    else:
        to_list = list(to)
    cc_list = list(cc) if cc else []
    bcc_list = list(bcc) if bcc else []

    # --- password normalization: people often paste Gmail app passwords with spaces ---
    pwd = (SMTP_PASSWORD or "").replace(" ", "")

    # --- build message ---
    msg = EmailMessage()
    msg["From"] = SMTP_FROM or SMTP_USERNAME or "no-reply@example.com"
    msg["To"] = ", ".join(to_list)
    if cc_list:
        msg["Cc"] = ", ".join(cc_list)
    msg["Subject"] = subject
    if reply_to:
        msg["Reply-To"] = reply_to

    if html_body:
        msg.set_content(text_body or "")
        msg.add_alternative(html_body, subtype="html")
    else:
        msg.set_content(text_body or "")

    for path in (attachments or []):
        try:
            p = Path(path)
            if not p.exists():
                continue
            ctype, _ = mimetypes.guess_type(p.name)
            maintype, subtype = (ctype or "application/octet-stream").split("/", 1)
            with open(p, "rb") as f:
                msg.add_attachment(f.read(), maintype=maintype, subtype=subtype, filename=p.name)
        except Exception:
            continue

    # If creds missing → write .eml and return
    if not (SMTP_USERNAME and pwd):
        eml_path = OUTBOX_DIR / f"email_{datetime.now().strftime('%Y%m%d_%H%M%S')}.eml"
        with open(eml_path, "wb") as f:
            f.write(bytes(msg))
        return (False, {"eml_path": str(eml_path), "error": "SMTP_USERNAME or SMTP_PASSWORD missing"})

    # --- attempt 1: TLS on 587 ---
    try:
        import smtplib
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT or 587, timeout=25) as server:
            server.ehlo()
            if SMTP_USE_TLS:
                server.starttls()
                server.ehlo()
            server.login(SMTP_USERNAME, pwd)
            server.send_message(msg, to_addrs=to_list + cc_list + bcc_list)
        return (True, None)
    except Exception as e_tls:
        # --- attempt 2: SSL on 465 ---
        try:
            import smtplib
            with smtplib.SMTP_SSL(SMTP_HOST, 465, timeout=25) as server:
                server.login(SMTP_USERNAME, pwd)
                server.send_message(msg, to_addrs=to_list + cc_list + bcc_list)
            return (True, None)
        except Exception as e_ssl:
            # write .eml and return errors
            eml_path = OUTBOX_DIR / f"email_{datetime.now().strftime('%Y%m%d_%H%M%S')}.eml"
            with open(eml_path, "wb") as f:
                f.write(bytes(msg))
            return (False, {
                "eml_path": str(eml_path),
                "error": f"TLS failed: {e_tls.__class__.__name__}: {e_tls}; SSL failed: {e_ssl.__class__.__name__}: {e_ssl}"
            })

# ---------------------------------------------------
# High-level confirmation email tailored for booking
# ---------------------------------------------------
def _build_confirmation_bodies(data: Dict[str, Any]) -> tuple[str, str]:
    name = data.get("name") or "Patient"
    doctor = data.get("doctor") or "Doctor"
    date = data.get("appointment_date") or ""
    s = data.get("appointment_start") or ""
    e = data.get("appointment_end") or ""
    booking_id = data.get("booking_id") or ""
    duration = data.get("appointment_duration_min") or ""
    problem = data.get("problem") or ""
    phone = data.get("phone") or ""
    email = data.get("email") or ""

    when = f"{date}"
    if s and e:
        when = f"{date}, {s}–{e}"

    text = (
        f"Hi {name},\n\n"
        f"Your appointment is confirmed with {doctor} on {when}.\n"
        f"Booking ID: {booking_id}\n"
        f"Duration: {duration} minutes\n"
        f"Reason: {problem}\n\n"
        "Please find attached your Appointment Confirmation and the Intake Form.\n"
        "Kindly complete the intake form and bring it to your visit (or submit online if available).\n\n"
        "If you need to reschedule, reply to this email.\n\n"
        "— Clinic Team\n"
    )

    html = f"""
    <html>
      <body style="font-family:Arial,Helvetica,sans-serif;line-height:1.5">
        <h2>Appointment Confirmed</h2>
        <p>Hi {name},</p>
        <p>Your appointment is confirmed with <b>{doctor}</b> on <b>{when}</b>.</p>
        <table cellpadding="6" cellspacing="0" border="0" style="border-collapse:collapse;background:#f7f7f7">
          <tr><td><b>Booking ID</b></td><td>{booking_id}</td></tr>
          <tr><td><b>Duration</b></td><td>{duration} minutes</td></tr>
          <tr><td><b>Reason</b></td><td>{problem}</td></tr>
          <tr><td><b>Patient Email</b></td><td>{email}</td></tr>
          <tr><td><b>Patient Phone</b></td><td>{phone}</td></tr>
        </table>
        <p>Please find attached your <b>Appointment Confirmation</b> and the <b>Intake Form</b>.
           Kindly complete the intake form and bring it to your visit (or submit online if available).</p>
        <p>Need to reschedule? Just reply to this email.</p>
        <p>— Clinic Team</p>
      </body>
    </html>
    """
    return text, html


def send_confirmation_email(
    to: str,
    data: Dict[str, Any],
    attachments: Optional[Iterable[Path]] = None,
    cc: Optional[Iterable[str]] = None,
    bcc: Optional[Iterable[str]] = None,
) -> Tuple[bool, Optional[str]]:
    """
    Builds and sends the confirmation email with attachments (confirmation PDF + intake form).
    Returns (success, eml_path_if_fallback).
    """
    if not to:
        # no email; write to outbox only
        to = SMTP_FROM  # at least addressable, but it will fallback to .eml without creds

    text, html = _build_confirmation_bodies(data)

    # Ensure intake form is attached if present
    att: List[Path] = []
    for a in (attachments or []):
        if a:
            att.append(Path(a))
    intake = locate_intake_form()
    if intake:
        att.append(intake)

    subject = f"Appointment Confirmation • {data.get('appointment_date', '')} {data.get('appointment_start', '')}-{data.get('appointment_end', '')}"
    return send_email(to=to, subject=subject, text_body=text, html_body=html, attachments=att, cc=cc, bcc=bcc)


# -----------------------------------------------------------------
# Existing logger kept for backward-compat (no-ops ok in your app)
# -----------------------------------------------------------------
def send_confirmation_log(**kwargs) -> None:
    """
    Kept for compatibility with earlier calls. You can still call this to log,
    but real sending should use send_confirmation_email above.
    """
    try:
        OUTBOX_DIR.mkdir(parents=True, exist_ok=True)
        p = OUTBOX_DIR / f"log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(p, "a", encoding="utf-8") as f:
            f.write(f"[CONFIRMATION LOG] {datetime.now().isoformat(timespec='seconds')}\n")
            for k, v in kwargs.items():
                f.write(f"{k}: {v}\n")
            f.write("\n")
    except Exception:
        pass
