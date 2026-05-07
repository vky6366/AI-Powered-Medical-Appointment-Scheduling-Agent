from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

APP_TITLE = "RagaAI Scheduling Agent API"

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

DATABASE_URL = os.getenv("DATABASE_URL")

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_FROM = os.getenv("SMTP_FROM")

SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() in (
    "1", "true", "yes"
)