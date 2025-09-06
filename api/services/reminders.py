from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta
import pandas as pd
from api.config import REMINDERS_XLSX

@dataclass
class ReminderService:
    def schedule_three(self, email: str, appointment_iso: str) -> int:
        base = datetime.fromisoformat(appointment_iso)
        times = [base - timedelta(hours=h) for h in (48, 24, 2)]
        msgs = [
            "Reminder 1: Regular reminder ✅",
            "Reminder 2: Have you filled the forms? ✅ / Is visit confirmed? ✅ / If not, why cancellation?",
            "Reminder 3: Have you filled the forms? ✅ / Is visit confirmed? ✅ / If not, why cancellation?",
        ]
        rows = []
        for t, m in zip(times, msgs):
            rows.append({
                "send_at": t.isoformat(timespec="seconds"),
                "to": email,
                "message": m,
                "appointment_iso": appointment_iso,
            })
        if REMINDERS_XLSX.exists():
            prev = pd.read_excel(REMINDERS_XLSX)
            out = pd.concat([prev, pd.DataFrame(rows)], ignore_index=True)
        else:
            out = pd.DataFrame(rows)
        out.to_excel(REMINDERS_XLSX, index=False)
        return len(rows)
