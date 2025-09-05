from __future__ import annotations
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from .config import LLM_MODEL
from .schema import IntakeState, PatientIntake
from .utils import infer_inline_updates, safe_json_loads

prompt = ChatPromptTemplate.from_messages([
    ("system", """Return ONLY compact JSON with keys:
name, dob, doctor, location, problem, problem_description, email, phone,
insurance_carrier, insurance_member_id, insurance_group.
Use "" for missing fields. No commentary."""),
    ("human", "User input:\n{input_text}")
])

llm = ChatOpenAI(model=LLM_MODEL, temperature=0)
chain = prompt | llm | StrOutputParser()

def node_extract(state: IntakeState) -> IntakeState:
    text = state.get("input_text","")
    patient: PatientIntake = state.get("patient") or PatientIntake()

    # Inline hints (don’t overwrite existing)
    inline = infer_inline_updates(text)
    for k,v in inline.items():
        if k.startswith("_"): continue
        if v and getattr(patient,k,None) in (None,"",False): setattr(patient,k,v)

    # LLM extraction
    raw = chain.invoke({"input_text": text})
    data = safe_json_loads(raw)
    for k,v in data.items():
        if isinstance(v,str) and v.strip()=="": continue
        if getattr(patient,k,None) in (None,"",False): setattr(patient,k,v)

    # Revalidate (age from dob)
    patient = PatientIntake(**patient.model_dump())
    state["patient"] = patient
    if inline: state["_inline"] = inline
    return state
