# api/routes/scheduling.py
from fastapi import APIRouter, Body
from fastapi.responses import JSONResponse
from typing import Any, Dict, Optional, Tuple, List
from datetime import datetime
from pathlib import Path
import uuid
import pandas as pd

from ..state import SESSION_STORE

# Email + PDF
from ..services.notify import send_confirmation_email
from .utils.pdf import generate_booking_pdf

# Resilient import for patients upsert
try:
    from ..services.patients import patients_service as _PATIENTS_SVC  # instance export
except (ImportError, AttributeError):
    _PATIENTS_SVC = None
try:
    from ..services import patients as _patients_mod
except Exception:
    _patients_mod = None

router = APIRouter()

BOOKINGS_XLSX = Path("storage/bookings.xlsx")
BOOKINGS_CSV  = Path("storage/bookings.csv")   # fallback if openpyxl missing
CONFIRMATIONS_DIR = Path("storage/confirmations")


# ---------- helpers ----------

def _ensure_storage_dirs() -> None:
    BOOKINGS_XLSX.parent.mkdir(parents=True, exist_ok=True)
    CONFIRMATIONS_DIR.mkdir(parents=True, exist_ok=True)

def _normalize_hhmm(x: Optional[str]) -> Optional[str]:
    if x is None:
        return None
    s = str(x).strip()
    if not s:
        return None
    s = s.replace(".", ":").replace("-", ":")
    parts = s.split(":")
    try:
        h = int(parts[0])
        m = int(parts[1]) if len(parts) > 1 and parts[1] != "" else 0
        if not (0 <= h <= 23 and 0 <= m <= 59):
            return None
        return f"{h:02d}:{m:02d}"
    except Exception:
        return None

def _derive_times_from_payload(p: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    # Priority 1: explicit start/end
    start = _normalize_hhmm(p.get("start"))
    end   = _normalize_hhmm(p.get("end"))
    if start or end:
        return start, end
    # Priority 2: slot "10:00-11:00" or "10-11"
    slot = p.get("slot")
    if isinstance(slot, str) and "-" in slot:
        a, b = slot.split("-", 1)
        return _normalize_hhmm(a), _normalize_hhmm(b)
    return None, None

def _t2min(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)

def _min2t(x: int) -> str:
    return f"{x // 60:02d}:{x % 60:02d}"

def _interval_subtract(free: List[Tuple[int, int]], busy: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    if not busy:
        return free[:]
    busy_sorted = sorted(busy)
    res = []
    for fs, fe in free:
        cur_start, cur_end = fs, fe
        for bs, be in busy_sorted:
            if be <= cur_start or bs >= cur_end:
                continue
            if bs <= cur_start:
                cur_start = max(cur_start, be)
            else:
                if bs > cur_start:
                    res.append((cur_start, bs))
                cur_start = max(cur_start, be)
            if cur_start >= cur_end:
                break
        if cur_start < cur_end:
            res.append((cur_start, cur_end))
    return res

def _generate_slots(free_windows: List[Tuple[int, int]], duration: int, step: int) -> List[Tuple[str, str]]:
    out: List[Tuple[str, str]] = []
    for ws, we in free_windows:
        t = ws
        while t + duration <= we:
            out.append((_min2t(t), _min2t(t + duration)))
            t += step
    return out

def _upsert_patient_from_booking(data: Dict[str, Any]) -> None:
    """Call upsert regardless of how services/patients.py is structured."""
    try:
        if _PATIENTS_SVC and hasattr(_PATIENTS_SVC, "upsert_from_booking"):
            _PATIENTS_SVC.upsert_from_booking(data); return
    except Exception:
        pass
    try:
        if _patients_mod and hasattr(_patients_mod, "upsert_from_booking"):
            _patients_mod.upsert_from_booking(data); return
    except Exception:
        pass
    try:
        if _patients_mod and hasattr(_patients_mod, "PatientsService"):
            svc = _patients_mod.PatientsService()
            if hasattr(svc, "upsert_from_booking"):
                svc.upsert_from_booking(data); return
    except Exception:
        pass
    # Silent if unavailable


# ---------- routes ----------

@router.get("/appointments/available")
def available_slots(doctor: str, date: str, duration_min: int = 30, step_min: int = 30):
    """
    Returns available slots for a doctor on a given date.
    """
    # Validate date
    try:
        _ = datetime.strptime(date, "%Y-%m-%d").date()
    except Exception:
        return JSONResponse(status_code=422, content={"error": "date must be YYYY-MM-DD"})

    # Working hours default: 09:00–17:00
    working_hours = [("09:00", "17:00")]
    free_windows = [(_t2min(s), _t2min(e)) for s, e in working_hours]

    # Busy intervals from bookings.xlsx or csv
    busy: List[Tuple[int, int]] = []
    try:
        if BOOKINGS_XLSX.exists():
            df = pd.read_excel(BOOKINGS_XLSX, engine="openpyxl")
        elif BOOKINGS_CSV.exists():
            df = pd.read_csv(BOOKINGS_CSV)
        else:
            df = None

        if df is not None:
            cols = {c.lower(): c for c in df.columns}
            date_col = cols.get("appointment_date", "appointment_date")
            doc_col  = cols.get("doctor", "doctor")
            s_col    = cols.get("appointment_start", "appointment_start")
            e_col    = cols.get("appointment_end", "appointment_end")

            df = df[df[date_col] == date]
            if (doctor or "").strip().lower() not in ("any", "any doctor"):
                df = df[df[doc_col] == doctor]

            for _, row in df.iterrows():
                s, e = str(row.get(s_col, "")).strip(), str(row.get(e_col, "")).strip()
                if s and e and ":" in s and ":" in e:
                    busy.append((_t2min(s), _t2min(e)))
    except Exception:
        busy = []

    # Free = working hours minus busy, then generate grid slots
    free_after_busy = _interval_subtract(free_windows, busy)
    slots = _generate_slots(free_after_busy, duration=duration_min, step=step_min)

    return {
        "doctor": doctor,
        "date": date,
        "duration_min": duration_min,
        "step_min": step_min,
        "slots": [{"start": s, "end": e} for s, e in slots],
    }


@router.post("/appointments/book")
def book(payload: Dict[str, Any] = Body(...)):
    """
    Accepts: name, dob, doctor, date, start, end OR slot, duration, returning,
    insurance_carrier, member_id, group, email, phone,
    problem, problem_description, location, thread_id (optional)
    """
    _ensure_storage_dirs()  # ensure storage/ and confirmations/ exist

    data = dict(payload)
    data.setdefault("booking_id", str(uuid.uuid4()))
    data.setdefault("ts", datetime.now().isoformat(timespec="seconds"))

    # Normalize key fields
    data["appointment_date"] = (data.get("date") or "")
    start_norm, end_norm = _derive_times_from_payload(payload)
    data["appointment_start"] = start_norm
    data["appointment_end"]   = end_norm

    # 1) Append booking row to Excel (fallback to CSV if openpyxl missing)
    try:
        row_df = pd.DataFrame([data])
        used_format = "xlsx"

        if BOOKINGS_XLSX.exists():
            try:
                prev = pd.read_excel(BOOKINGS_XLSX, engine="openpyxl")
                # Align columns to avoid drift
                all_cols = list(dict.fromkeys(list(prev.columns) + list(row_df.columns)))
                prev = prev.reindex(columns=all_cols)
                row_df = row_df.reindex(columns=all_cols)
                out = pd.concat([prev, row_df], ignore_index=True)
                out.to_excel(BOOKINGS_XLSX, index=False, engine="openpyxl")
            except Exception:
                # Fallback to CSV to avoid blocking
                used_format = "csv"
                if BOOKINGS_CSV.exists():
                    prev = pd.read_csv(BOOKINGS_CSV)
                    all_cols = list(dict.fromkeys(list(prev.columns) + list(row_df.columns)))
                    prev = prev.reindex(columns=all_cols)
                    row_df = row_df.reindex(columns=all_cols)
                    out = pd.concat([prev, row_df], ignore_index=True)
                else:
                    out = row_df
                out.to_csv(BOOKINGS_CSV, index=False)
        else:
            try:
                row_df.to_excel(BOOKINGS_XLSX, index=False, engine="openpyxl")
            except Exception:
                used_format = "csv"
                row_df.to_csv(BOOKINGS_CSV, index=False)

        data["admin_export_format"] = used_format
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"book_error: {e}"})

    # 2) Upsert patient master (best-effort)
    try:
        _upsert_patient_from_booking(data)
    except Exception:
        pass

    # 3) Persist into conversation session (so agent + UI can read it)
    tid = (data.get("thread_id") or "").strip()
    if tid and tid in SESSION_STORE:
        sess = SESSION_STORE.get(tid, {})
        sess["booking_done"] = True  # ensure post-booking shows "Thank you"

        p = sess.get("patient")
        update_fields = {
            "doctor": data.get("doctor"),
            "appointment_date": data.get("appointment_date"),
            "appointment_start": data.get("appointment_start"),
            "appointment_end": data.get("appointment_end"),
        }
        update_fields = {k: v for k, v in update_fields.items() if v not in (None, "")}

        if p is not None:
            try:
                if hasattr(p, "model_copy"):  # Pydantic v2
                    p = p.model_copy(update=update_fields)
                else:
                    for k, v in update_fields.items():
                        setattr(p, k, v)
                sess["patient"] = p
            except Exception:
                pdict = dict(p); pdict.update(update_fields); sess["patient"] = pdict

        SESSION_STORE[tid] = sess

    # 4) Generate the PDF confirmation (best-effort)
    try:
        pdf_path = CONFIRMATIONS_DIR / f"{data['booking_id']}.pdf"
        generate_booking_pdf(pdf_path, data)
        data["confirmation_pdf_path"] = str(pdf_path)
    except Exception:
        data["confirmation_pdf_path"] = None

    # 5) Send the confirmation email and expose status in response
    email_status = {"ok": False}
    try:
        atts = []
        if data.get("confirmation_pdf_path"):
            atts.append(Path(data["confirmation_pdf_path"]))
        ok, info = send_confirmation_email(to=data.get("email",""), data=data, attachments=atts)
        # info is None on success or dict on failure (eml_path, error)
        email_status = {"ok": ok, **({} if info is None else info)}
    except Exception as e:
        email_status = {"ok": False, "error": str(e)}

    return {
        "status": "ok",
        "booking_id": data["booking_id"],
        "payload": data,
        "email": email_status,
    }
