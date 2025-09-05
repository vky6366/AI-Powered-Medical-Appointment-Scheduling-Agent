from __future__ import annotations
import json, re
from typing import Any, Dict, Optional
import pandas as pd
from .config import DATA_DIR

# Regexes
PHONE_RE  = re.compile(r"(?:\+?\d[\s-]?){9,15}\d")
EMAIL_RE  = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)
DOB_RE    = re.compile(r"\b(19|20)\d{2}-\d{2}-\d{2}\b")
NAME_RE   = re.compile(r"\bmy name is\s+([A-Za-z][A-Za-z .'-]{1,60})", re.I)
DR_RE     = re.compile(r"\bDr\.?\s+[A-Z][a-zA-Z.-]{1,40}\b")
YESNO_RE  = re.compile(r"^\s*(yes|y|no|n)\s*$", re.I)
DATE_RE   = re.compile(r"^\s*(20\d{2}-\d{2}-\d{2})\s*$")

def safe_json_loads(text: str) -> Dict[str, Any]:
    text = text.strip()
    try: return json.loads(text)
    except Exception: pass
    if "```" in text:
        for part in text.split("```"):
            try: return json.loads(part.strip())
            except Exception: pass
    s, e = text.find("{"), text.rfind("}")
    if s != -1 and e != -1 and e > s:
        try: return json.loads(text[s:e+1])
        except Exception: pass
    return {}

def infer_inline_updates(user_text: str) -> dict:
    d: Dict[str, Any] = {}
    t = user_text.strip()

    m = YESNO_RE.match(t)
    if m: d["_yes_no"] = m.group(1).lower() in ("yes", "y")

    m = DATE_RE.match(t)
    if m: d["appointment_date"] = m.group(1)

    m = EMAIL_RE.search(t)
    if m: d["email"] = m.group(0); return d

    digits = re.sub(r"[^\d+]", "", t)
    if len(re.sub(r"\D", "", digits)) >= 10:
        d["phone"] = digits; return d

    m = DOB_RE.search(t)
    if m: d["dob"] = m.group(0); return d

    m = NAME_RE.search(t)
    if m: d["name"] = m.group(1).strip(); return d

    m = DR_RE.search(t)
    if m:
        doc = m.group(0)
        if not doc.lower().startswith("dr."): doc = doc.replace("Dr","Dr.")
        d["doctor"] = doc.strip(); return d

    # Insurance quick-captures
    low = t.lower()
    if "insurance" in low or "carrier" in low or "policy" in low or low.startswith("yes "):
        carrier = t[3:].strip(" :,-") if low.startswith("yes ") else t
        if carrier: d["insurance_carrier"] = carrier; return d
    if low.startswith("id") or low.startswith("member"):
        parts = t.split(); 
        if parts: d["insurance_member_id"] = parts[-1]; return d
    if "group" in low:
        parts = t.split(); 
        if parts: d["insurance_group"] = parts[-1]; return d

    return d

def fetch_patient_record(email: Optional[str], name: Optional[str], dob: Optional[str]) -> Dict[str, Any] | None:
    path = DATA_DIR / "patients.csv"
    if not path.exists(): return None
    try: df = pd.read_csv(path)
    except Exception: return None

    if email:
        hit = df[df["email"].str.lower() == str(email).lower()]
        if not hit.empty: return hit.iloc[0].to_dict()
    if name and dob:
        hit = df[(df["name"].str.lower()==(name or "").lower()) & (df["dob"].astype(str)==(dob or ""))]
        if not hit.empty: return hit.iloc[0].to_dict()
    return None

def is_returning_patient(email: Optional[str], name: Optional[str], dob: Optional[str]) -> Optional[bool]:
    return fetch_patient_record(email, name, dob) is not None

def assign_duration(returning: Optional[bool]) -> int:
    return 30 if returning else 60
