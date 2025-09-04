from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime, date
from dotenv import load_dotenv
import json

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

# --------------------------
# Schema
# --------------------------
# Extend PatientIntake with a counter
class PatientIntake(BaseModel):
    name: Optional[str] = None
    dob: Optional[str] = None  
    age: Optional[int] = None  
    doctor: Optional[str] = None
    problem: Optional[str] = None
    problem_description: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    description_turns: int = 0  

    @field_validator("age", mode="before")
    def derive_age(cls, v, values):
        """Derive age from dob if dob is provided."""
        if v is not None:
            return v  
        dob = values.get("dob")
        if dob:
            try:
                dob_date = datetime.strptime(dob, "%Y-%m-%d").date()
                today = date.today()
                age = today.year - dob_date.year - (
                    (today.month, today.day) < (dob_date.month, dob_date.day)
                )
                return age
            except Exception:
                raise ValueError("dob must be in YYYY-MM-DD format")
        return None

# --------------------------
# Helpers
# --------------------------
def clean_data(data: dict) -> dict:
    """Convert empty strings or 'null' to None for safe Pydantic validation."""
    return {k: (v if v not in ["", "null", None] else None) for k, v in data.items()}

# --------------------------
# LLM setup
# --------------------------
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a medical scheduling assistant. Extract patient details from text."),
    ("human", "{input_text}"),
    ("system", """Return only valid JSON with keys:
    name, dob, doctor, problem, location, email, phone.
    If a field is missing, use null. 
    Do not include any explanations or code fences.""" )
])

# --------------------------
# Main function
# --------------------------
def extract_patient_info(user_text: str) -> PatientIntake:
    chain = prompt | llm
    response = chain.invoke({"input_text": user_text})

    raw_output = response.content.strip()

    # Remove code fences if the LLM added them
    if raw_output.startswith("```"):
        raw_output = raw_output.strip("`")
        if raw_output.lower().startswith("json"):
            raw_output = raw_output[4:].strip()

    try:
        data = json.loads(raw_output)
        data = clean_data(data)  # sanitize before Pydantic
        return PatientIntake(**data)
    except Exception as e:
        print("Error parsing:", e, "\nRaw output was:\n", raw_output)
        return PatientIntake()
