from pathlib import Path
from datetime import datetime
from typing import Any, Dict, Optional

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

def _val(x: Optional[str]) -> str:
    return "" if x is None else str(x)

def generate_booking_pdf(output_path: Path, data: Dict[str, Any]) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(str(output_path), pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("Appointment Confirmation", styles["Title"]))
    story.append(Spacer(1, 10))
    story.append(Paragraph(f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles["Normal"]))
    story.append(Spacer(1, 16))

    table_data = [
        ["Field", "Value"],
        ["Patient Name", _val(data.get("name"))],
        ["Doctor", _val(data.get("doctor"))],
        ["Date", _val(data.get("appointment_date"))],
        ["Start Time", _val(data.get("appointment_start"))],
        ["End Time", _val(data.get("appointment_end"))],
        ["Duration (min)", _val(data.get("appointment_duration_min"))],
        ["Returning Patient", _val(data.get("returning_patient"))],
        ["Payment/Carrier", _val(data.get("insurance_carrier", "self-pay"))],
        ["Member ID", _val(data.get("insurance_member_id"))],
        ["Group Number", _val(data.get("insurance_group"))],
        ["Email", _val(data.get("email"))],
        ["Phone", _val(data.get("phone"))],
        ["Problem", _val(data.get("problem"))],
        ["Problem Description", _val(data.get("problem_description"))],
        ["Booking ID", _val(data.get("booking_id"))],
        ["Thread ID", _val(data.get("thread_id"))],
        ["Timestamp", _val(data.get("ts"))],
    ]

    table = Table(table_data, colWidths=[150, 350])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2a9d8f")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.grey),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
    ]))

    story.append(table)
    story.append(Spacer(1, 18))
    story.append(Paragraph(
        "This document serves as confirmation of your scheduled appointment. "
        "Please bring any necessary documents and arrive 10 minutes early.",
        styles["Normal"]
    ))

    doc.build(story)
    return output_path
