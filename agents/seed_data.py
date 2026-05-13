# agents/seed_data.py

from __future__ import annotations

from datetime import date, datetime, timedelta

from .db import SessionLocal
from .models import (
    Doctor,
    DoctorAvailability,
)


# =========================================================
# DOCTOR SEED DATA
# =========================================================

DOCTORS = [
    {
        "doctor_name": "Dr. Rao",
        "specialty": "Allergy & Immunology",
        "location": "Pune",
        "slot_mins": 30,
        "hours_weekday": "10:00-13:00;15:00-17:00",
        "hours_saturday": "10:00-14:00",
        "hours_sunday": None,
    },
    {
        "doctor_name": "Dr. Lee",
        "specialty": "General Practice",
        "location": "Pune",
        "slot_mins": 30,
        "hours_weekday": "10:00-13:00;15:00-17:00",
        "hours_saturday": "10:00-14:00",
        "hours_sunday": None,
    },
]


# =========================================================
# TIME SLOT GENERATOR
# =========================================================

def generate_slots(
    start_time: str,
    end_time: str,
    slot_mins: int,
):
    """
    Generate slots between two times.
    """

    slots = []

    current = datetime.strptime(
        start_time,
        "%H:%M"
    )

    end = datetime.strptime(
        end_time,
        "%H:%M"
    )

    while current < end:

        slot_start = current.time()

        current += timedelta(
            minutes=slot_mins
        )

        slot_end = current.time()

        slots.append(
            (
                slot_start,
                slot_end,
            )
        )

    return slots


# =========================================================
# CREATE DOCTORS
# =========================================================

def seed_doctors(db):
    """
    Insert doctors into DB.
    """

    for doctor_data in DOCTORS:

        existing = (
            db.query(Doctor)
            .filter(
                Doctor.doctor_name
                == doctor_data["doctor_name"]
            )
            .first()
        )

        if existing:
            print(
                f"Doctor already exists: "
                f"{doctor_data['doctor_name']}"
            )
            continue

        doctor = Doctor(**doctor_data)

        db.add(doctor)

    db.commit()

    print("Doctors seeded successfully.")


# =========================================================
# CREATE AVAILABILITY
# =========================================================

def seed_availability(
    db,
    days: int = 14,
):
    """
    Generate future availability slots.
    """

    doctors = db.query(Doctor).all()

    if not doctors:

        print("No doctors found.")
        return

    today = date.today()

    for doctor in doctors:

        for offset in range(days):

            current_date = (
                today + timedelta(days=offset)
            )

            weekday = current_date.weekday()

            # -----------------------------------------
            # Select working hours
            # -----------------------------------------

            # Monday-Friday
            if weekday <= 4:

                hours = doctor.hours_weekday

            # Saturday
            elif weekday == 5:

                hours = doctor.hours_saturday

            # Sunday
            else:

                hours = doctor.hours_sunday

            if not hours:
                continue

            # -----------------------------------------
            # Multiple ranges
            # Example:
            # 10:00-13:00;15:00-17:00
            # -----------------------------------------

            ranges = hours.split(";")

            for time_range in ranges:

                start_str, end_str = (
                    time_range.split("-")
                )

                slots = generate_slots(
                    start_str,
                    end_str,
                    doctor.slot_mins,
                )

                for start_time, end_time in slots:

                    # Avoid duplicates
                    existing = (
                        db.query(
                            DoctorAvailability
                        )
                        .filter(
                            DoctorAvailability.doctor_id
                            == doctor.id,

                            DoctorAvailability.available_date
                            == current_date,

                            DoctorAvailability.start_time
                            == start_time,

                            DoctorAvailability.end_time
                            == end_time,
                        )
                        .first()
                    )

                    if existing:
                        continue

                    availability = (
                        DoctorAvailability(
                            doctor_id=doctor.id,
                            available_date=current_date,
                            start_time=start_time,
                            end_time=end_time,
                            is_booked=False,
                        )
                    )

                    db.add(availability)

    db.commit()

    print(
        "Doctor availability seeded successfully."
    )


# =========================================================
# MAIN
# =========================================================

def main():

    db = SessionLocal()

    try:

        seed_doctors(db)

        seed_availability(
            db,
            days=30
        )

    finally:

        db.close()


if __name__ == "__main__":
    main()