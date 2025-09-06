# agents/llm.py
from __future__ import annotations
from dotenv import load_dotenv
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

load_dotenv()

LLM_MODEL = "gpt-4o-mini"

extract_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", """You are a precise information extraction assistant.
Return ONLY a compact JSON object with these keys:
name, dob, doctor, location, problem, problem_description, email, phone,
insurance_carrier, insurance_member_id, insurance_group.

Rules:
- Use empty string "" for any field not mentioned.
- DO NOT add extra keys.
- For "problem": a short title (e.g., "tooth pain").
- For "problem_description": keep the user's wording (short but faithful).
- DOB format must be YYYY-MM-DD if present, else "".
- Never include commentary or markdown, ONLY JSON."""),
        ("human", "User input:\n{input_text}"),
    ]
)

_llm = ChatOpenAI(model=LLM_MODEL, temperature=0)
extract_chain = extract_prompt | _llm | StrOutputParser()
