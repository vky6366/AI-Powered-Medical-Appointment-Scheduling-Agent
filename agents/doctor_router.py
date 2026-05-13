# agents/doctor_router.py

from __future__ import annotations

from typing import Optional, List

from sqlalchemy.orm import Session

from .models import Doctor


# =========================================================
# SPECIALTY MAPPING
# =========================================================

SPECIALTY_MAP = {
    # General
    "fever": "General Practice",
    "cold": "General Practice",
    "cough": "General Practice",
    "headache": "General Practice",
    "body pain": "General Practice",
    "vomiting": "General Practice",
    "nausea": "General Practice",

    # Allergy
    "allergy": "Allergy & Immunology",
    "allergies": "Allergy & Immunology",
    "skin rash": "Allergy & Immunology",
    "rashes": "Allergy & Immunology",

    # Dental
    "tooth pain": "Dentistry",
    "toothache": "Dentistry",
    "gum pain": "Dentistry",

    # ENT
    "sore throat": "ENT",
    "ear pain": "ENT",

    # Eye
    "eye pain": "Ophthalmology",
    "blurred vision": "Ophthalmology",
}


# =========================================================
# DETECT SPECIALTY
# =========================================================

def detect_specialty(
    problem: Optional[str]
) -> Optional[str]:
    """
    Map symptom/problem -> medical specialty.
    """

    if not problem:
        return None

    low = problem.lower().strip()

    for keyword, specialty in SPECIALTY_MAP.items():

        if keyword in low:
            return specialty

    return "General Practice"


# =========================================================
# GET DOCTORS BY SPECIALTY
# =========================================================

def get_doctors_by_specialty(
    db: Session,
    specialty: str,
) -> List[Doctor]:
    """
    Fetch doctors for a given specialty.
    """

    return (
        db.query(Doctor)
        .filter(Doctor.specialty == specialty)
        .all()
    )


# =========================================================
# RECOMMEND DOCTOR
# =========================================================

def recommend_doctor(
    db: Session,
    problem: Optional[str],
    preferred_location: Optional[str] = None,
) -> Optional[Doctor]:
    """
    Recommend best matching doctor.

    Flow:
    1. Detect specialty
    2. Filter doctors
    3. Prefer matching location
    4. Return first match
    """

    specialty = detect_specialty(problem)

    if not specialty:
        return None

    query = (
        db.query(Doctor)
        .filter(Doctor.specialty == specialty)
    )

    # Optional location preference
    if preferred_location:

        query = query.filter(
            Doctor.location.ilike(
                f"%{preferred_location}%"
            )
        )

    doctors = query.all()

    if not doctors:
        return None

    # Simple strategy:
    # return first available doctor
    return doctors[0]


# =========================================================
# GET ALL SPECIALTIES
# =========================================================

def get_all_specialties() -> List[str]:
    """
    Return all supported specialties.
    """

    return sorted(
        set(SPECIALTY_MAP.values())
    )