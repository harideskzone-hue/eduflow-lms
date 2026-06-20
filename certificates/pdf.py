from io import BytesIO
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.colors import HexColor, white
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from django.conf import settings
from urllib.parse import urljoin


def build_certificate_pdf(certificate):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=landscape(A4))
    width, height = landscape(A4)

    # Base Colors
    navy = HexColor("#0F172A")
    gold = HexColor("#D4AF37")
    gold_light = HexColor("#F8E7A1")

    # 1. Background and Border
    pdf.setFillColor(white)
    pdf.rect(0, 0, width, height, fill=1, stroke=0)

    # Outer Navy Thick Border
    pdf.setStrokeColor(navy)
    pdf.setLineWidth(16)
    pdf.rect(30, 30, width - 60, height - 60)

    # Inner Gold Thin Border
    pdf.setStrokeColor(gold)
    pdf.setLineWidth(2)
    pdf.rect(42, 42, width - 84, height - 84)

    # 2. Top Seal
    seal_x = width / 2
    seal_y = height - 100
    
    # Outer Ring
    pdf.setFillColor(gold)
    pdf.setStrokeColor(gold_light)
    pdf.setLineWidth(2)
    pdf.circle(seal_x, seal_y, 40, fill=1, stroke=1)
    
    # Inner Navy Circle
    pdf.setFillColor(navy)
    pdf.circle(seal_x, seal_y, 32, fill=1, stroke=0)

    # Seal Text
    pdf.setFillColor(gold)
    pdf.setFont("Helvetica-Bold", 8)
    pdf.drawCentredString(seal_x, seal_y + 8, "EDUFLOW")
    pdf.drawCentredString(seal_x, seal_y - 2, "CERTIFIED")
    pdf.setFont("Helvetica", 6)
    pdf.drawCentredString(seal_x, seal_y - 12, "EXCELLENCE")

    # 3. Certificate Title
    pdf.setFillColor(navy)
    pdf.setFont("Times-Bold", 36)
    pdf.drawCentredString(width / 2, height - 200, "Certificate of Completion")

    # Gold Divider Line
    pdf.setStrokeColor(gold)
    pdf.setLineWidth(1.5)
    pdf.line(width / 2 - 100, height - 220, width / 2 + 100, height - 220)

    # 4. Presentation Text
    pdf.setFillColor(HexColor("#64748B"))
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawCentredString(width / 2, height - 260, "THIS IS PROUDLY PRESENTED TO")

    # 5. Recipient Name
    pdf.setFillColor(navy)
    pdf.setFont("Times-BoldItalic", 42)
    pdf.drawCentredString(width / 2, height - 315, certificate.student.get_full_name() or certificate.student.username)

    # 6. Achievement Statement
    pdf.setFillColor(HexColor("#64748B"))
    pdf.setFont("Helvetica", 14)
    pdf.drawCentredString(width / 2, height - 360, "Awarded for successful completion of")

    # 7. Course Title
    pdf.setFillColor(HexColor("#2563EB"))  # Blue emphasis
    pdf.setFont("Times-Bold", 26)
    pdf.drawCentredString(width / 2, height - 400, certificate.course.title)

    # 8. Bottom Meta Data
    bottom_y = 100
    pdf.setFillColor(navy)

    # Left: Issue Date
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(100, bottom_y + 15, "ISSUED ON")
    pdf.setFont("Helvetica", 12)
    pdf.drawString(100, bottom_y, certificate.issued_at.strftime('%B %d, %Y'))

    # Center: Certificate ID & Verification URL
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawCentredString(width / 2, bottom_y + 15, "CERTIFICATE NUMBER")
    pdf.setFont("Courier", 12)
    pdf.drawCentredString(width / 2, bottom_y, certificate.certificate_id)
    
    # Verification URL Placeholder (Simulated QR text)
    domain = getattr(settings, 'SITE_URL', 'https://eduflow.com')
    verify_url = urljoin(domain, f"/certificates/verify/{certificate.certificate_id}/")
    pdf.setFont("Helvetica", 9)
    pdf.setFillColor(HexColor("#64748B"))
    pdf.drawCentredString(width / 2, bottom_y - 20, f"Verify authenticity at: {verify_url}")

    # Right: Instructor Signature Proxy
    pdf.setFillColor(navy)
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawRightString(width - 100, bottom_y + 15, "ISSUED BY")
    pdf.setFont("Helvetica-Oblique", 14)
    pdf.drawRightString(width - 100, bottom_y, "EduFlow LMS")

    # Save PDF
    pdf.save()
    pdf_data = buffer.getvalue()
    buffer.close()

    return pdf_data
