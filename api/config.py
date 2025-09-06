from pathlib import Path

APP_TITLE = "RagaAI Scheduling Agent API"

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

# Files used across services
BOOKINGS_XLSX = DATA_DIR / "bookings.xlsx"     # simulated “Calendly” calendar (file operations)
SCHEDULES_XLSX = DATA_DIR / "schedules.xlsx"   # source of truth for availability (per brief)
PATIENTS_CSV = DATA_DIR / "patients.csv"       # simulated EMR
DOCTORS_CSV = DATA_DIR / "doctors.csv"         # doctor metadata (optional for fallback)
MAIL_LOG_CSV = DATA_DIR / "mail_log.csv"       # simulated mail log
REMINDERS_XLSX = DATA_DIR / "reminders.xlsx"   # reminder schedule
ADMIN_EXPORT_XLSX = DATA_DIR / "admin_report.xlsx"
