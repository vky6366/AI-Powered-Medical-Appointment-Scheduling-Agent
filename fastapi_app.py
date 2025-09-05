from __future__ import annotations

import os
import socket
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict

import pandas as pd
from fastapi import Body, FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# IMPORTANT: your file is at project root, not "agents/intake_agent"
from agents import intake_graph, PatientIntake


APP_TITLE = "RagaAI Scheduling Agent API"
app = FastAPI(title=APP_TITLE)

# CORS (safe default: allow localhost/streamlit)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten later if you want
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data dir
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

# Simple in-memory session store for conversation threads
SESSION_STORE: Dict[str, Dict[str, Any]] = {}


def patient_to_dict(p: PatientIntake | Dict[str, Any] | None) -> Dict[str, Any]:
    """Robustly convert PatientIntake (pydantic v2) to plain dict."""
    if p is None:
        return {}
    if isinstance(p, dict):
        return p
    to_dict = getattr(p, "model_dump", None)
    if callable(to_dict):
        return to_dict()
    to_dict = getattr(p, "dict", None)
    if callable(to_dict):
        return to_dict()
    return dict(p)


def dict_to_patient(d: Dict[str, Any] | None) -> PatientIntake:
    return PatientIntake(**(d or {}))


def get_ip_address() -> str:
    """Best-effort local network IP for pretty logging."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
    except Exception:
        ip = "127.0.0.1"
    return ip


@app.get("/health")
async def health():
    return {"ok": True, "app": APP_TITLE}


@app.get("/stream")
async def stream(
    q: str = Query(..., description="User input"),
    thread_id: str = Query("default", description="Conversation thread id"),
):
    """
    Runs one turn through the intake agent graph and returns:
    - message: assistant text to show
    - data: current patient state (so UI can render slot picker later)
    """
    # Get or init session
    session = SESSION_STORE.setdefault(thread_id, {"patient": PatientIntake()})
    patient: PatientIntake = session["patient"]

    # Build state for the graph
    state = {
        "input_text": q,
        "patient": patient,
    }

    try:
        result = intake_graph.invoke(state)
        # DEBUG: print full patient state each turn
        try:
            dbg = session.get("patient")
            print("\n=== DEBUG: PatientIntake state ===")
            print((dbg.model_dump() if hasattr(dbg, "model_dump") else dict(dbg)))
            print("==================================\n")
        except Exception as _:
            pass

    except Exception as e:
        import traceback, sys
        traceback.print_exc()  # <-- prints full stack in your server console
        return JSONResponse(
            status_code=500,
            content={"error": f"agent_error: {e.__class__.__name__}: {e}"},
        )


    # Persist updated patient if returned
    new_patient = result.get("patient", None)
    if new_patient is not None:
        try:
            session["patient"] = (
                new_patient if isinstance(new_patient, PatientIntake) else dict_to_patient(new_patient)
            )
        except Exception:
            pass

    message = result.get("message") or result.get("reply") or "Okay."

    return {
        "message": message,
        "data": patient_to_dict(session.get("patient")),
        "next_step": result.get("next_step"),
    }


# ---------------------------
# Scheduling / Calendar APIs
# ---------------------------

@app.get("/appointments/available")
def available(
    doctor: str = Query(..., description="Doctor name equals sheet name in schedules.xlsx"),
    date: str = Query(..., description="YYYY-MM-DD"),
):
    """
    Read synthetic schedule Excel: data/schedules.xlsx -> sheet per doctor with start/end slots.
    Returns list of {date,start,end}
    """
    xlf = DATA_DIR / "schedules.xlsx"
    if not xlf.exists():
        return {"slots": []}

    try:
        xls = pd.ExcelFile(xlf)
        if doctor not in xls.sheet_names:
            return JSONResponse(status_code=404, content={"error": "doctor not found"})
        df = pd.read_excel(xls, sheet_name=doctor)
        df = df[df["date"] == date]
        for col in ("date", "start", "end"):
            if col in df.columns:
                df[col] = df[col].astype(str)
        return {"slots": df.to_dict(orient="records")}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"schedules_read_error: {e}"})


@app.post("/appointments/book")
def book(payload: Dict[str, Any] = Body(...)):
    """
    payload should include:
    name,dob,doctor,date,start,end,duration,returning,insurance_carrier,member_id,group,email,phone,problem,problem_description,location
    """
    df_path = DATA_DIR / "bookings.xlsx"
    payload = dict(payload)
    payload.setdefault("booking_id", str(uuid.uuid4()))
    payload.setdefault("ts", datetime.now().isoformat(timespec="seconds"))

    try:
        row = pd.DataFrame([payload])
        if df_path.exists():
            prev = pd.read_excel(df_path)
            out = pd.concat([prev, row], ignore_index=True)
        else:
            out = row
        out.to_excel(df_path, index=False)
        return {"status": "confirmed", "booking_id": payload["booking_id"], "payload": payload}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"booking_write_error: {e}"})


@app.post("/export/admin_report")
def export_admin():
    """Simple copy of bookings.xlsx as admin_report.xlsx"""
    src = DATA_DIR / "bookings.xlsx"
    dst = DATA_DIR / "admin_report.xlsx"
    if not src.exists():
        return JSONResponse(status_code=404, content={"error": "no bookings yet"})
    try:
        df = pd.read_excel(src)
        df.to_excel(dst, index=False)
        return {"status": "ok", "file": str(dst)}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"export_error: {e}"})


@app.post("/notify/send_after_confirm")
def send_after_confirm(payload: Dict[str, Any] = Body(...)):
    """
    Simulate sending email with attached intake PDF after booking.
    payload: {email, name, booking_id}
    Logs to data/mail_log.csv with attachment 'New Patient Intake Form.pdf'
    """
    email_to = payload.get("email", "")
    if not email_to:
        return JSONResponse(status_code=400, content={"error": "email is required"})

    log = DATA_DIR / "mail_log.csv"
    try:
        row = pd.DataFrame(
            [{
                "ts": datetime.now().isoformat(timespec="seconds"),
                "to": email_to,
                "subject": "Your appointment confirmation + intake form",
                "attachment": "New Patient Intake Form.pdf",
                "booking_id": payload.get("booking_id", ""),
            }]
        )
        if log.exists():
            prev = pd.read_csv(log)
            pd.concat([prev, row], ignore_index=True).to_csv(log, index=False)
        else:
            row.to_csv(log, index=False)
        return {"status": "sent", "to": email_to}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"notify_error: {e}"})


@app.post("/reminders/schedule")
def schedule_reminders(payload: Dict[str, Any] = Body(...)):
    """
    Create three reminders (T-48h, T-24h, T-2h) with the required actions.
    payload: {email, appointment_iso}
    """
    email_to = payload.get("email", "")
    appt_iso = payload.get("appointment_iso", "")
    if not email_to or not appt_iso:
        return JSONResponse(status_code=400, content={"error": "email and appointment_iso are required"})

    try:
        base = datetime.fromisoformat(appt_iso)
    except Exception:
        return JSONResponse(status_code=400, content={"error": "appointment_iso must be ISO format"})

    times = [base - timedelta(hours=48), base - timedelta(hours=24), base - timedelta(hours=2)]
    msgs = [
        "Reminder 1: Regular reminder ✅",
        "Reminder 2: Have you filled the forms? ✅ / Is visit confirmed? ✅ / If not, why cancellation?",
        "Reminder 3: Have you filled the forms? ✅ / Is visit confirmed? ✅ / If not, why cancellation?",
    ]

    dfp = DATA_DIR / "reminders.xlsx"
    try:
        rows = []
        for t, m in zip(times, msgs):
            rows.append({
                "send_at": t.isoformat(timespec="seconds"),
                "to": email_to,
                "message": m,
                "appointment_iso": appt_iso,
            })
        if dfp.exists():
            prev = pd.read_excel(dfp)
            out = pd.concat([prev, pd.DataFrame(rows)], ignore_index=True)
        else:
            out = pd.DataFrame(rows)
        out.to_excel(dfp, index=False)
        return {"status": "scheduled", "count": len(rows)}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"reminders_error: {e}"})


if __name__ == "__main__":
    import uvicorn

    host_ip = "0.0.0.0"
    port = int(os.getenv("PORT", "5000"))

    print("\n" + "=" * 50)
    print(f"Server is running on:")
    print(f"Local URL:     http://localhost:{port}")
    print(f"Network URL:   http://{get_ip_address()}:{port}")
    print(f"API Docs URL:  http://{get_ip_address()}:{port}/docs")
    print("=" * 50 + "\n")

    uvicorn.run("fastapi_app:app", host=host_ip, port=port, reload=True)
