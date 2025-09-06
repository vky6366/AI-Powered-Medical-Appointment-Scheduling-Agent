from __future__ import annotations
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict

import pandas as pd
from fastapi import APIRouter, Body, Query
from fastapi.responses import JSONResponse

from api.config import BOOKINGS_XLSX, SCHEDULES_XLSX, DOCTORS_CSV
from api.services.calendar import CalendarService
from api.services.patients import PatientsService
from api.utils import set_booking_done 

router = APIRouter(tags=["scheduling"])

cal = CalendarService()
patients = PatientsService()

@router.get("/appointments/available")
def appointments_available(
    doctor: str = Query(..., description="Doctor name (matches schedules.xlsx sheet)"),
    date: str   = Query(..., description="YYYY-MM-DD"),
    duration_min: int = Query(30, description="Desired appointment length (min)"),
):
    """
    Excel-first availability (schedules.xlsx) with CSV fallback (doctors.csv).
    """
    return cal.available(doctor=doctor, date_str=date, duration_min=duration_min)


@router.post("/appointments/book")
def book(payload: Dict[str, Any] = Body(...)):
    data = dict(payload)
    data.setdefault("booking_id", str(uuid.uuid4()))
    data.setdefault("ts", datetime.now().isoformat(timespec="seconds"))

    # write bookings.xlsx (unchanged) …
    try:
        if BOOKINGS_XLSX.exists():
            prev = pd.read_excel(BOOKINGS_XLSX)
            out = pd.concat([prev, pd.DataFrame([data])], ignore_index=True)
        else:
            out = pd.DataFrame([data])
        out.to_excel(BOOKINGS_XLSX, index=False)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"book_error: {e}"})

    # upsert patient (best effort)
    try:
        patients.upsert_from_booking(data)
    except Exception:
        pass

    # mark this conversation as booked
    tid = (data.get("thread_id") or "").strip()
    if tid:
        set_booking_done(tid)

    return {"status": "ok", "booking_id": data["booking_id"], "payload": data}


@router.get("/appointments/next_available")
def next_available(
    doctor: str = Query(..., description="Doctor name"),
    start_date: str = Query(..., description="YYYY-MM-DD"),
    duration_min: int = Query(30),
    horizon_days: int = Query(14),
):
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "start_date must be YYYY-MM-DD"})

    for d in range(horizon_days):
        day = (start + timedelta(days=d)).isoformat()
        resp = cal.available(doctor=doctor, date_str=day, duration_min=duration_min)
        slots = resp.get("slots", [])
        if slots:
            return {"date": day, "slots": slots}
    return {"date": None, "slots": []}
