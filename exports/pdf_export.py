from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

def create_pdf_report(summary_text, key_metrics):
    """Create a PDF report with summary and key metrics"""
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, height - 100, "Team Orlando Water Polo Club - Financial Report")
    
    # Date
    c.setFont("Helvetica", 12)
    c.drawString(100, height - 130, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Summary section
    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, height - 180, "Executive Summary")
    
    # Summary text (word wrap)
    c.setFont("Helvetica", 10)
    text_lines = summary_text.split('\n')
    y_position = height - 210
    for line in text_lines:
        if y_position < 100:  # Start new page if needed
            c.showPage()
            y_position = height - 100
        # Simple word wrap for long lines
        words = line.split(' ')
        current_line = ""
        for word in words:
            if len(current_line + word) < 80:  # Rough character limit
                current_line += word + " "
            else:
                c.drawString(100, y_position, current_line.strip())
                y_position -= 15
                current_line = word + " "
        if current_line:
            c.drawString(100, y_position, current_line.strip())
            y_position -= 15
    
    # Key metrics section
    y_position -= 30
    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, y_position, "Key Metrics")
    y_position -= 20
    
    c.setFont("Helvetica", 10)
    for metric, value in key_metrics.items():
        c.drawString(100, y_position, f"{metric}: {value}")
        y_position -= 15
    
    c.save()
    return buffer.getvalue()