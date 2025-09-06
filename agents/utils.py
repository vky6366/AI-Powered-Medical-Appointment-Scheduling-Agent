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

SYMPTOM_WORDS = {"fever","allergy","allergies","tooth","pain","cough","cold","headache","sore throat","vomiting","nausea"}

CITY_WORDS = {
    "pune","mumbai","delhi","new delhi","bangalore","bengaluru","chennai","kolkata","hyderabad","gurgaon","noida"
}

YES_WORDS = {"yes","y","yeah","yep","visited","i have","i've"}
NO_WORDS  = {"no","n","new","first time","nope"}

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

def infer_inline_updates(user_text: str, context_step: str | None = None) -> dict:
    """
    Map a single short reply (or phrase) to likely PatientIntake fields.
    Uses context_step to avoid cross-field collisions (e.g., date vs dob).
    """
    d: dict = {}
    t = (user_text or "").strip()
    low = t.lower()

    # ---- YES/NO for returning patient ----
    # Capture aggressively if we're currently asking, or if the reply is a single yes/no-ish token.
    tok = low.strip(" .!?,;")
    if (context_step == "ask_returning" and tok in YES_WORDS | NO_WORDS) or (tok in YES_WORDS | NO_WORDS):
        d["_yes_no"] = tok in YES_WORDS
        return d

    # ---- Email ----
    m = EMAIL_RE.search(t)
    if m:
        d["email"] = m.group(0)
        return d

    # ---- Phone (>=10 digits) ----
    digits = re.sub(r"[^\d+]", "", t)
    if len(re.sub(r"\D", "", digits)) >= 10:
        d["phone"] = digits
        return d

    # ---- Date / DOB ----
    # Only accept appointment_date when we specifically asked for it
    if context_step == "ask_date" and re.fullmatch(r"\d{4}-\d{2}-\d{2}", t):
        d["appointment_date"] = t
        return d

    # Otherwise, accept DOB if present (and not in ask_date)
    if context_step != "ask_date":
        m = DOB_RE.search(t)
        if m:
            d["dob"] = m.group(0)
            return d

    # ---- Name ----
    m = NAME_RE.search(t)
    if m:
        d["name"] = m.group(1).strip()
        return d

    # ---- Doctor ----
    if low in {"any", "any doctor", "no", "none", "na"}:
        d["doctor"] = "any doctor"
        return d


    m = DR_RE.search(t)
    if m:
        doc = m.group(0)
        if not doc.lower().startswith("dr."):
            doc = doc.replace("Dr", "Dr.")
        d["doctor"] = doc.strip()
        return d

    # ---- City / Location ----
    if low in CITY_WORDS:
        d["location"] = t
        return d

    # ---- Symptoms / Problem ----
    if any(w in low for w in SYMPTOM_WORDS):
        # Keep problem short; description captured by LLM when we ask
        # If user typed a short word like "fever" -> treat as problem, not description
        if len(low.split()) <= 3:
            d["problem"] = low
        else:
            # longer phrase → likely description; let LLM fill problem later
            d["problem_description"] = t
        return d

    # ---- Light-weight insurance parsing if user volunteered proactively ----
    if "insurance" in low or low in {"no", "none", "no insurance", "self pay", "self-pay"}:
        # Negative case → self-pay
        if low in {"no", "none", "no insurance", "self pay", "self-pay"}:
            d["insurance_carrier"] = "self-pay"
            return d

        # Positive case → try to parse inline details
        parts = user_text.strip().split()   # use original text, not lowercased
        if len(parts) >= 2:
            d["insurance_carrier"] = parts[1]
        if len(parts) >= 3:
            d["insurance_member_id"] = parts[2]
        if len(parts) >= 4:
            d["insurance_group"] = parts[3]
        return d


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
