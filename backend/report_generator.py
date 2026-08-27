from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import inch
import os


def generate_report(
    report_id,
    product_name,
    manufacturer_name,
    manufacturer_address,
    net_quantity,
    mrp,
    manufacturing_date,
    consumer_care_details,
    is_compliant,
    violations
):
    # Create reports folder
    os.makedirs("reports", exist_ok=True)

    # PDF file location
    pdf_path = f"reports/report_{report_id}.pdf"

    # Create PDF
    document = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        rightMargin=50,
        leftMargin=50,
        topMargin=50,
        bottomMargin=50
    )

    styles = getSampleStyleSheet()

    title_style = styles["Title"]
    title_style.alignment = TA_CENTER

    story = []

    # Title
    story.append(
        Paragraph(
            "Legal Metrology Compliance Report",
            title_style
        )
    )

    story.append(Spacer(1, 20))

    # Product information
    story.append(
        Paragraph(
            f"<b>Product Name:</b> {product_name or 'Not Available'}",
            styles["Normal"]
        )
    )

    story.append(Spacer(1, 10))

    story.append(
        Paragraph(
            f"<b>Manufacturer:</b> {manufacturer_name or 'Not Available'}",
            styles["Normal"]
        )
    )

    story.append(Spacer(1, 10))

    story.append(
        Paragraph(
            f"<b>Manufacturer Address:</b> "
            f"{manufacturer_address or 'Not Available'}",
            styles["Normal"]
        )
    )

    story.append(Spacer(1, 10))

    story.append(
        Paragraph(
            f"<b>Net Quantity:</b> {net_quantity or 'Not Available'}",
            styles["Normal"]
        )
    )

    story.append(Spacer(1, 10))

    story.append(
        Paragraph(
            f"<b>MRP:</b> {mrp or 'Not Available'}",
            styles["Normal"]
        )
    )

    story.append(Spacer(1, 10))

    story.append(
        Paragraph(
            f"<b>Manufacturing Date:</b> "
            f"{manufacturing_date or 'Not Available'}",
            styles["Normal"]
        )
    )

    story.append(Spacer(1, 10))

    story.append(
        Paragraph(
            f"<b>Consumer Care Details:</b> "
            f"{consumer_care_details or 'Not Available'}",
            styles["Normal"]
        )
    )

    story.append(Spacer(1, 20))

    # Compliance status
    status = "COMPLIANT" if is_compliant else "NON-COMPLIANT"

    story.append(
        Paragraph(
            f"<b>Compliance Status:</b> {status}",
            styles["Heading2"]
        )
    )

    story.append(Spacer(1, 15))

    # Violations
    story.append(
        Paragraph(
            "<b>Violations:</b>",
            styles["Heading3"]
        )
    )

    story.append(Spacer(1, 5))

    if violations:
        story.append(
            Paragraph(
                violations,
                styles["Normal"]
            )
        )
    else:
        story.append(
            Paragraph(
                "No violations detected.",
                styles["Normal"]
            )
        )

    # Build PDF
    document.build(story)

    return pdf_path