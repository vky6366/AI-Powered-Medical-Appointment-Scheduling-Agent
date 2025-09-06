from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, date as _date
from typing import List, Dict, Tuple, Optional, Iterable, Set
from pandas import ExcelFile
from typing import Tuple
from api.config import SCHEDULES_XLSX, DOCTORS_CSV, BOOKINGS_XLSX

import pandas as pd

from api.config import (
    BOOKINGS_XLSX,
    SCHEDULES_XLSX,
    DOCTORS_CSV,
)

def _hm_diff_min(hm1: str, hm2: str) -> int:
    a = datetime.strptime(hm1, "%H:%M")
    b = datetime.strptime(hm2, "%H:%M")
    return int((b - a).total_seconds() // 60)

def _weekday_key(dt: _date) -> str:
    wd = dt.weekday()  # Mon=0..Sun=6
    if wd == 6: return "hours_sunday"
    if wd == 5: return "hours_saturday"
    return "hours_weekday"

def _parse_ranges(ranges_str: str) -> List[Tuple[str, str]]:
    if not isinstance(ranges_str, str) or not ranges_str.strip():
        return []
    parts = [p.strip() for p in ranges_str.split(";") if p.strip()]
    out = []
    for p in parts:
        if "-" in p:
            a, b = p.split("-", 1)
            out.append((a.strip(), b.strip()))
    return out

def _mk_slots(step_min: int, ranges: Iterable[Tuple[str, str]]) -> List[Tuple[str, str]]:
    out: List[Tuple[str, str]] = []
    for s, e in ranges:
        h1, m1 = map(int, s.split(":")); h2, m2 = map(int, e.split(":"))
        cur = h1 * 60 + m1
        end = h2 * 60 + m2
        while cur + step_min <= end:
            sh, sm = divmod(cur, 60)
            eh, em = divmod(cur + step_min, 60)
            out.append((f"{sh:02d}:{sm:02d}", f"{eh:02d}:{em:02d}"))
            cur += step_min
    return out

def _dedupe(seq: Iterable[Tuple[str, str]]) -> List[Tuple[str, str]]:
    seen: Set[Tuple[str, str]] = set()
    out: List[Tuple[str, str]] = []
    for s in seq:
        if s not in seen:
            seen.add(s)
            out.append(s)
    return out

@dataclass
class CalendarService:
    """Excel-first scheduling engine with CSV fallback (per assignment)."""

    def read_bookings(self) -> pd.DataFrame:
        if BOOKINGS_XLSX.exists():
            try:
                return pd.read_excel(BOOKINGS_XLSX)
            except Exception:
                pass
        return pd.DataFrame(columns=["doctor", "date", "start", "end"])

    # ---------- Excel source of truth ----------
    def available_from_excel(self, doctor: str, date_str: str, duration_min: int) -> List[Dict]:
        if not SCHEDULES_XLSX.exists():
            return []
        try:
            df = pd.read_excel(SCHEDULES_XLSX, sheet_name=doctor)  # sheet name == doctor
        except Exception:
            return []

        df["date"] = df["date"].astype(str)
        day = df[df["date"] == date_str].copy()
        if day.empty:
            return []

        day["start"] = day["start"].astype(str).str.slice(0, 5)
        day["end"] = day["end"].astype(str).str.slice(0, 5)

        booked = self.read_bookings()
        booked = booked[(booked["doctor"].str.strip().str.lower() == doctor.strip().lower())
                        & (booked["date"].astype(str) == date_str)]
        booked_set = set((str(r["start"])[:5], str(r["end"])[:5]) for _, r in booked.iterrows())
        base = [(s, e) for s, e in day[["start", "end"]].itertuples(index=False, name=None)
                if (s, e) not in booked_set]

        if not base:
            return []

        step = _hm_diff_min(base[0][0], base[0][1]) or 30
        if duration_min <= step:
            return [{"doctor": doctor, "date": date_str, "start": s, "end": e} for (s, e) in base]

        # stitch
        k = (duration_min + step - 1) // step
        stitched: List[Tuple[str, str]] = []
        for i in range(len(base)):
            block = base[i:i+k]
            if len(block) < k:
                break
            if all(block[j][1] == block[j+1][0] for j in range(k-1)):
                stitched.append((block[0][0], block[-1][1]))
        stitched = _dedupe(stitched)
        return [{"doctor": doctor, "date": date_str, "start": s, "end": e} for (s, e) in stitched]

    # ---------- CSV fallback ----------
    def available_from_csv(self, doctor: str, date_str: str, duration_min: int) -> List[Dict]:
        if not DOCTORS_CSV.exists():
            return []
        try:
            df = pd.read_csv(DOCTORS_CSV)
        except Exception:
            return []
        hit = df[df["doctor"].str.strip().str.lower() == doctor.strip().lower()]
        if hit.empty:
            return []
        row = hit.iloc[0].to_dict()

        try:
            step = int(row.get("slot_mins", 30))
        except Exception:
            step = 30

        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d").date()
        except Exception:
            return []

        ranges = _parse_ranges(row.get(_weekday_key(dt), ""))
        if not ranges:
            return []
        base = _mk_slots(step, ranges)

        booked = self.read_bookings()
        booked = booked[(booked["doctor"].str.strip().str.lower() == doctor.strip().lower())
                        & (booked["date"].astype(str) == date_str)]
        booked_set = set((str(r["start"])[:5], str(r["end"])[:5]) for _, r in booked.iterrows())
        open_slots = [s for s in base if s not in booked_set]

        if duration_min <= step:
            final = open_slots
        else:
            k = (duration_min + step - 1) // step
            stitched: List[Tuple[str, str]] = []
            for i in range(len(open_slots)):
                blk = open_slots[i:i+k]
                if len(blk) < k:
                    break
                if all(blk[j][1] == blk[j+1][0] for j in range(k-1)):
                    stitched.append((blk[0][0], blk[-1][1]))
            final = _dedupe(stitched)

        return [{"doctor": doctor, "date": date_str, "start": s, "end": e} for (s, e) in final]

    # ---------- Public API ----------
    def available(self, doctor: str, date_str: str, duration_min: int) -> Dict[str, List[Dict]]:
        doctor_normalized = (doctor or "").strip().lower()
        if doctor_normalized in ("any", "any doctor", "no", "none"):
            slots = self.available_any(date_str, duration_min)
            return {"slots": slots}

        try:
            slots = self.available_from_excel(doctor, date_str, duration_min)
        except Exception:
            slots = []
        if not slots:
            try:
                slots = self.available_from_csv(doctor, date_str, duration_min)
            except Exception:
                slots = []
        return {"slots": slots}
    
    def list_excel_doctors(self) -> list[str]:
        """Return all sheet names available in schedules.xlsx (doctor names)."""
        if not SCHEDULES_XLSX.exists():
            return []
        try:
            with ExcelFile(SCHEDULES_XLSX) as xf:
                return [s for s in xf.sheet_names]
        except Exception:
            return []

    def available_any(self, date_str: str, duration_min: int) -> list[dict]:
        """
        Aggregate available slots across ALL doctors (all sheets in schedules.xlsx).
        If Excel has nothing, fall back to doctors.csv rows (if present).
        """
        results: list[dict] = []

        # 1) Try Excel sheets
        for doctor in self.list_excel_doctors():
            slots = self.available_from_excel(doctor, date_str, duration_min)
            if slots:
                results.extend(slots)

        # 2) If still empty, try CSV fallback for each doctor row
        if not results and DOCTORS_CSV.exists():
            try:
                df = pd.read_csv(DOCTORS_CSV)
                for _, row in df.iterrows():
                    doctor = str(row.get("doctor") or "").strip()
                    if not doctor:
                        continue
                    slots = self.available_from_csv(doctor, date_str, duration_min)
                    if slots:
                        results.extend(slots)
            except Exception:
                pass

        return results

