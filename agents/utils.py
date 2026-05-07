from __future__ import annotations

import json
import re
from typing import Any, Dict, Optional

# -----------------------------
# REGEX
# -----------------------------

DOB_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")

# -----------------------------
# JSON PARSER
# -----------------------------

def safe_json_loads(text: str) -> Dict[str, Any]:
    """
    Safely parse JSON returned by the LLM.
    """

    text = text.strip()

    try:
        return json.loads(text)

    except Exception:
        pass

    # Handle markdown-wrapped JSON
    if "```" in text:

        for part in text.split("```"):

            try:
                return json.loads(part.strip())

            except Exception:
                pass

    # Attempt partial extraction
    start = text.find("{")
    end = text.rfind("}")

    if start != -1 and end != -1 and end > start:

        try:
            return json.loads(text[start:end + 1])

        except Exception:
            pass

    return {}

# -----------------------------
# LIGHTWEIGHT INLINE EXTRACTION
# -----------------------------

def infer_inline_updates(
    user_text: str,
    context_step: Optional[str] = None
) -> dict:
    """
    Minimal deterministic extraction.

    Only handles:
    - appointment_date
    - dob

    Everything else is delegated to:
    - LLM extraction
    - frontend forms
    - authenticated profile data
    """

    d: dict = {}

    t = (user_text or "").strip()

    # -----------------------------
    # Appointment Date
    # -----------------------------

    if (
        context_step == "ask_date"
        and re.fullmatch(r"\d{4}-\d{2}-\d{2}", t)
    ):

        d["appointment_date"] = t
        return d

    # -----------------------------
    # DOB
    # -----------------------------

    if context_step != "ask_date":

        m = DOB_RE.search(t)

        if m:
            d["dob"] = m.group(0)
            return d

    return d

# -----------------------------
# BUSINESS LOGIC
# -----------------------------

def assign_duration(
    returning: Optional[bool]
) -> int:
    """
    Appointment duration policy.
    """

    return 30 if returning else 60