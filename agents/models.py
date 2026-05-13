from __future__ import annotations

from datetime import datetime, date, time
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    Time,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .db import Base


# =========================================================
# USERS
# =========================================================

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(100), nullable=False)

    email = Column(String(255), unique=True, nullable=False)

    # phone is nullable so Google-OAuth users (who have no phone) can be stored
    phone = Column(String(20), unique=True, nullable=True)

    # password_hash is nullable for OAuth-only accounts
    #password_hash = Column(Text, nullable=True)

    # Google OAuth fields
    google_id = Column(String(255), unique=True, nullable=False, index=True)

    profile_picture = Column(Text, nullable=True)

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    # Relationships
    patient_profile = relationship(
        "PatientProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete"
    )

    appointments = relationship(
        "Appointment",
        back_populates="user",
        cascade="all, delete"
    )


# =========================================================
# PATIENT PROFILE
# =========================================================

class PatientProfile(Base):
    __tablename__ = "patient_profiles"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )

    dob = Column(Date)

    insurance_carrier = Column(String(100))

    insurance_member_id = Column(String(100))

    insurance_group = Column(String(100))

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # Relationships
    user = relationship(
        "User",
        back_populates="patient_profile"
    )


# =========================================================
# DOCTORS
# =========================================================

class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True)

    doctor_name = Column(
        String(100),
        unique=True,
        nullable=False
    )

    specialty = Column(String(100))

    location = Column(String(100))

    slot_mins = Column(
        Integer,
        default=30
    )

    hours_weekday = Column(String(100))

    hours_saturday = Column(String(100))

    hours_sunday = Column(String(100))

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    # Relationships
    availability = relationship(
        "DoctorAvailability",
        back_populates="doctor",
        cascade="all, delete"
    )

    appointments = relationship(
        "Appointment",
        back_populates="doctor",
        cascade="all, delete"
    )


# =========================================================
# DOCTOR AVAILABILITY
# =========================================================

class DoctorAvailability(Base):
    __tablename__ = "doctor_availability"

    id = Column(Integer, primary_key=True, index=True)

    doctor_id = Column(
        Integer,
        ForeignKey("doctors.id", ondelete="CASCADE"),
        nullable=False
    )

    available_date = Column(
        Date,
        nullable=False
    )

    start_time = Column(
        Time,
        nullable=False
    )

    end_time = Column(
        Time,
        nullable=False
    )

    is_booked = Column(
        Boolean,
        default=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    # Relationships
    doctor = relationship(
        "Doctor",
        back_populates="availability"
    )


# =========================================================
# APPOINTMENTS
# =========================================================

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    doctor_id = Column(
        Integer,
        ForeignKey("doctors.id", ondelete="CASCADE"),
        nullable=False
    )

    appointment_date = Column(
        Date,
        nullable=False
    )

    appointment_start = Column(
        Time,
        nullable=False
    )

    appointment_end = Column(
        Time,
        nullable=False
    )

    appointment_duration_min = Column(Integer)

    returning_patient = Column(Boolean)

    problem = Column(String(255))

    problem_description = Column(Text)

    status = Column(
        String(30),
        default="pending"
    )

    booking_uuid = Column(
        UUID(as_uuid=True),
        default=uuid4,
        unique=True,
        nullable=False
    )

    thread_id = Column(
        UUID(as_uuid=True),
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    # Relationships
    user = relationship(
        "User",
        back_populates="appointments"
    )

    doctor = relationship(
        "Doctor",
        back_populates="appointments"
    )