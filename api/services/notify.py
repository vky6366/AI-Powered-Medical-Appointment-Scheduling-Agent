from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
import pandas as pd
from api.config import MAIL_LOG_CSV

@dataclass
class NotificationService:
    def send_after_confirm(self, email: str, name: str = "", booking_id: str = "", meta: dict | None = None) -> None:
        meta = meta or {}
        row = pd.DataFrame([{
            "ts": datetime.now().isoformat(timespec="seconds"),
            "to": email,
            "subject": "Your appointment confirmation + intake form",
            "attachment": "New Patient Intake Form.pdf",
            "booking_id": booking_id,
            "problem": meta.get("problem",""),
            "problem_description": meta.get("problem_description",""),
        }])
        if MAIL_LOG_CSV.exists():
            prev = pd.read_csv(MAIL_LOG_CSV)
            pd.concat([prev, row], ignore_index=True).to_csv(MAIL_LOG_CSV, index=False)
        else:
            row.to_csv(MAIL_LOG_CSV, index=False)
