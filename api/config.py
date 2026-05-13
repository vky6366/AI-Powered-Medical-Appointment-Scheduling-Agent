# api/config.py
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Storage paths referenced by api/services/*
# ---------------------------------------------------------------------------

DATA_DIR    = Path("data")
STORAGE_DIR = Path("storage")

BOOKINGS_XLSX  = STORAGE_DIR / "bookings.xlsx"
SCHEDULES_XLSX = DATA_DIR    / "schedules.xlsx"
REMINDERS_XLSX = STORAGE_DIR / "reminders.xlsx"
DOCTORS_CSV    = DATA_DIR    / "doctors.csv"
PATIENTS_CSV   = DATA_DIR    / "patients.csv"

# Ensure directories exist at import time so services don't crash
DATA_DIR.mkdir(exist_ok=True)
STORAGE_DIR.mkdir(exist_ok=True)
(STORAGE_DIR / "confirmations").mkdir(exist_ok=True)
(STORAGE_DIR / "outbox").mkdir(exist_ok=True)
(STORAGE_DIR / "reminders").mkdir(exist_ok=True)
