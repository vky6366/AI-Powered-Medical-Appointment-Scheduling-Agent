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

# api/config.py  (or your top-level config.py)
import os

SMTP_HOST = os.environ.get("SMTP_HOST") or "smtp.gmail.com"
SMTP_PORT = int(os.environ.get("SMTP_PORT") or "587")
SMTP_USERNAME = os.environ.get("SMTP_USERNAME") or "bosslazy33@gmail.com"
SMTP_PASSWORD = (os.environ.get("SMTP_PASSWORD") or "pmywmgawqhhewjcn").replace(" ", "")  # strip spaces just in case
SMTP_FROM     = os.environ.get("SMTP_FROM") or f"Clinic <{SMTP_USERNAME}>"
SMTP_USE_TLS  = (os.environ.get("SMTP_USE_TLS") or "true").lower() in ("1", "true", "yes")

print("[SMTP CONFIG]", "HOST:", SMTP_HOST, "PORT:", SMTP_PORT, "USER:", SMTP_USERNAME, "FROM:", SMTP_FROM, "TLS:", SMTP_USE_TLS)

