from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime

def generate_booking_pdf(output_path, data: dict):
    """
    Generate a PDF summary of the appointment booking.
    `data` should include keys:
    name, doctor, appointment_date, appointment_start, appointment_end,
    appointment_duration_min, returning_patient, insurance_carrier,
    insurance_member_id, insurance_group, email, phone,
    problem, problem_description, booking_id, ts, thread_id
    """

    doc = SimpleDocTemplate(output_path, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    # Title
    story.append(Paragraph("Appointment Confirmation", styles["Title"]))
    story.append(Spacer(1, 12))

    # Patient & Appointment Table
    table_data = [
        ["Field", "Value"],
        ["Patient Name", data.get("name", "")],
        ["Doctor", data.get("doctor", "")],
        ["Date", data.get("appointment_date", "")],
        ["Start Time", data.get("appointment_start", "")],
        ["End Time", data.get("appointment_end", "")],
        ["Duration (min)", str(data.get("appointment_duration_min", ""))],
        ["Returning Patient", str(data.get("returning_patient", ""))],
        ["Insurance Carrier", data.get("insurance_carrier", "self-pay")],
        ["Member ID", data.get("insurance_member_id", "")],
        ["Group Number", data.get("insurance_group", "")],
        ["Email", data.get("email", "")],
        ["Phone", data.get("phone", "")],
        ["Problem", data.get("problem", "")],
        ["Problem Description", data.get("problem_description", "")],
        ["Booking ID", data.get("booking_id", "")],
        ["Thread ID", data.get("thread_id", "")],
        ["Timestamp", data.get("ts", datetime.now().isoformat(timespec="seconds"))],
    ]

    table = Table(table_data, colWidths=[150, 350])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2a9d8f")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
    ]))

    story.append(table)
    story.append(Spacer(1, 24))
    story.append(Paragraph("This document serves as confirmation of your scheduled appointment.", styles["Normal"]))

    doc.build(story)


# Example usage:
data = {
    "name": "raman",
    "doctor": "Dr. Rao",
    "appointment_date": "2025-09-11",
    "appointment_start": "10:00",
    "appointment_end": "11:00",
    "appointment_duration_min": 60,
    "returning_patient": False,
    "insurance_carrier": "self-pay",
    "insurance_member_id": "",
    "insurance_group": "",
    "email": "email@email.com",
    "phone": "1234567895",
    "problem": "cold",
    "problem_description": "Donald Trump is the president of USA.",
    "booking_id": "d4c2bfc9-a5a5-4ec5-8027-a2366af3e9c1",
    "ts": "2025-09-06T13:10:13",
    "thread_id": "a93482d8-299c-47ed-96db-e7acc5c192ff"
}

generate_booking_pdf("appointment_confirmation.pdf", data)
