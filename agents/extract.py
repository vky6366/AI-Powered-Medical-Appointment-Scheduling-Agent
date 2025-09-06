import re
from typing import Any, Dict, Optional
from .schema import IntakeState, PatientIntake
from .config import LLM_MODEL
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)
DOB_RE = re.compile(r"\b(19|20)\d{2}-\d{2}-\d{2}\b")
NAME_RE = re.compile(r"\bmy name is\s+([A-Za-z][A-Za-z .'-]{1,60})", re.I)
DR_RE = re.compile(r"\bDr\.?\s+[A-Z][a-zA-Z.-]{1,40}\b")

def safe_json_loads(text: str) -> Dict[str, Any]:
    text = text.strip()
    try:
        import json
        return json.loads(text)
    except Exception:
        pass
    if "```" in text:
        for part in text.split("```"):
            try:
                return json.loads(part.strip())
            except Exception:
                continue
    start = text.find("{"); end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            import json
            return json.loads(text[start:end+1])
        except Exception:
            return {}
    return {}

def infer_inline_updates(user_text: str, context_step: Optional[str]) -> dict:
    """
    Context-aware mapper. The same reply like 'no' maps differently depending on the question.
    """
    d = {}
    t = (user_text or "").strip()
    low = t.lower()

    # ---------- Context-specific first ----------
    if context_step == "ask_doctor":
        if low in {"any", "any doctor", "no", "none", "na"}:
            d["doctor"] = "any doctor"; return d
        m = DR_RE.search(t)
        if m:
            doc = m.group(0)
            if not doc.lower().startswith("dr."):
                doc = doc.replace("Dr", "Dr.")
            d["doctor"] = doc.strip(); return d

    if context_step == "ask_returning":
        if low in {"yes", "y", "yeah", "yep", "visited", "i have"}:
            d["_yes_no"] = True; return d
        if low in {"no", "n", "new", "first time"}:
            d["_yes_no"] = False; return d

    if context_step == "ask_date":
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", t):
            d["appointment_date"] = t; return d

    if context_step == "ask_email":
        m = EMAIL_RE.search(t)
        if m: d["email"] = m.group(0); return d

    if context_step == "ask_phone":
        digits = re.sub(r"[^\d+]", "", t)
        if len(re.sub(r"\D", "", digits)) >= 10:
            d["phone"] = digits; return d

    if context_step == "ask_insurance_carrier":
        # Negative → self-pay
        if low in {"no", "none", "no insurance", "self pay", "self-pay"}:
            d["insurance_carrier"] = "self-pay"
            d["insurance_member_id"] = ""
            d["insurance_group"] = ""
            return d
        # Positive → allow "yes <carrier> <member> <group>"
        parts = t.split()
        if parts and parts[0].lower() == "yes":
            parts = parts[1:]
        if len(parts) >= 1: d["insurance_carrier"] = parts[0]
        if len(parts) >= 2: d["insurance_member_id"] = parts[1]
        if len(parts) >= 3: d["insurance_group"] = parts[2]
        if any(k in d for k in ("insurance_carrier", "insurance_member_id", "insurance_group")):
            return d

    if context_step == "ask_insurance_member_id":
        if low in {"no", "none"}:
            d["insurance_member_id"] = ""; return d
        d["insurance_member_id"] = t; return d

    if context_step == "ask_insurance_group":
        if low in {"no", "none"}:
            d["insurance_group"] = ""; return d
        d["insurance_group"] = t; return d

    if context_step == "ask_problem":
        # short, clean label
        symptom_map = {
            "coughing": "cough",
            "cough": "cough",
            "fever": "fever",
            "allergy": "allergies",
            "allergies": "allergies",
            "tooth": "tooth pain",
            "toothache": "tooth pain",
            "headache": "headache",
            "cold": "cold",
            "pain": "pain",
        }
        label = None
        for k, v in symptom_map.items():
            if k in low:
                label = v; break
        d["problem"] = label or (t[:50] if len(t) > 50 else t)
        return d

    if context_step == "ask_problem_details":
        d["problem_description"] = t.strip().rstrip(".") + "."
        return d

    # ---------- Context-agnostic fallbacks ----------
    m = EMAIL_RE.search(t)
    if m: d["email"] = m.group(0); return d

    digits = re.sub(r"[^\d+]", "", t)
    if len(re.sub(r"\D", "", digits)) >= 10:
        d["phone"] = digits; return d

    m = DOB_RE.search(t)
    if m: d["dob"] = m.group(0); return d

    m = NAME_RE.search(t)
    if m: d["name"] = m.group(1).strip(); return d

    if low in {"any", "any doctor", "no", "none", "na"}:
        d["doctor"] = "any doctor"; return d

    m = DR_RE.search(t)
    if m:
        doc = m.group(0)
        if not doc.lower().startswith("dr."):
            doc = doc.replace("Dr", "Dr.")
        d["doctor"] = doc.strip(); return d

    # symptom heuristic (only set clean label here)
    if any(w in low for w in ["fever","allergy","allergies","toothache","tooth","pain","cough","coughing","cold","headache"]):
        symptom_map = {
            "coughing": "cough",
            "cough": "cough",
            "fever": "fever",
            "allergy": "allergies",
            "allergies": "allergies",
            "toothache": "tooth pain",
            "tooth": "tooth pain",
            "headache": "headache",
            "cold": "cold",
            "pain": "pain",
        }
        for k, v in symptom_map.items():
            if k in low:
                d["problem"] = v; break
        # Don't set description here to avoid capturing greetings as description
        return d

    # one generic insurance pass (no duplicates)
    # after merging data into `patient`
        if (patient.insurance_carrier or "").strip().lower() in {"self-pay", "self pay", "no", "none"}:
            patient.insurance_carrier = "self-pay"
            patient.insurance_member_id = ""
            patient.insurance_group = ""

            return d
        parts = t.split()
        if parts and parts[0].lower() == "yes":
            parts = parts[1:]
        if len(parts) >= 1: d["insurance_carrier"] = parts[0]
        if len(parts) >= 2: d["insurance_member_id"] = parts[1]
        if len(parts) >= 3: d["insurance_group"] = parts[2]
        if any(k in d for k in ("insurance_carrier", "insurance_member_id", "insurance_group")):
            return d

    # date outside ask_date → treat as DOB
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", t):
        d["dob"] = t; return d

    return d

extract_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", """Return ONLY JSON with keys:
name, dob, doctor, location, problem, problem_description, email, phone,
insurance_carrier, insurance_member_id, insurance_group.
Use "" for missing. DOB must be YYYY-MM-DD. No extra keys, no prose."""),
        ("human", "User input:\n{input_text}"),
    ]
)
_llm = ChatOpenAI(model=LLM_MODEL, temperature=0)
extract_chain = extract_prompt | _llm | StrOutputParser()

def node_extract(state: IntakeState) -> IntakeState:
    user_text = state.get("input_text", "") or ""
    context_step = state.get("next_step")
    patient: PatientIntake = state.get("patient") or PatientIntake()

    # 1) inline with context
    inline = infer_inline_updates(user_text, context_step)
    for k, v in inline.items():
        if v is not None:
            setattr(patient, k, v)

    # 2) LLM extraction (for rich inputs)
    raw = extract_chain.invoke({"input_text": user_text})
    data = safe_json_loads(raw)

    # Guard: only accept description when we asked for it
    if "problem_description" in data and context_step != "ask_problem_details":
        data.pop("problem_description", None)
    # Guard: if we asked for date, don't let LLM set DOB
    if context_step == "ask_date" and "dob" in data:
        data.pop("dob", None)

    # merge but don't overwrite existing non-empty values
    for k, v in data.items():
        if isinstance(v, str) and not v.strip():
            continue
        if getattr(patient, k, None) in (None, "", False):
            setattr(patient, k, v)

    state["patient"] = PatientIntake(**patient.model_dump())
    state["_inline"] = inline
    return state

