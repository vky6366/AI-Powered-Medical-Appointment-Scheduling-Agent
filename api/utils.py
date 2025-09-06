from __future__ import annotations
import socket
from typing import Any, Dict
from agents import PatientIntake

def patient_to_dict(p: PatientIntake | Dict[str, Any] | None) -> Dict[str, Any]:
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
    try:
        import socket as _s
        s = _s.socket(_s.AF_INET, _s.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

# one global dict that all routers import
SESSION_STORE: Dict[str, Dict[str, Any]] = {}

def ensure_session(thread_id: str) -> Dict[str, Any]:
    """
    Get or create a session dict for a given thread_id.
    """
    return SESSION_STORE.setdefault(thread_id, {
        "patient": None,          # optionally a PatientIntake
        "next_step": None,
        "booking_done": False,
    })

def set_booking_done(thread_id: str) -> None:
    """
    Mark the thread as having completed a booking. Insurance node runs after this.
    """
    s = ensure_session(thread_id)
    s["booking_done"] = True