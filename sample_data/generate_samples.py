#!/usr/bin/env python3
"""Generate synthetic sample reports for testing.

Creates:
- PDF reports (digital)
- PNG image (scanned report simulation)
- DOCX report
"""
import io
from datetime import datetime
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from PIL import Image, ImageDraw, ImageFont


SAMPLE_DIR = Path(__file__).parent / "reports"


def create_cbc_report_pdf(filename: str, date: str, values: dict):
    """Create a synthetic CBC report PDF."""
    filepath = SAMPLE_DIR / filename
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=16)
    
    story.append(Paragraph("SYNTHETIC LAB REPORT - FOR TESTING ONLY", title_style))
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph(f"<b>Patient:</b> Test Patient (Synthetic)", styles['Normal']))
    story.append(Paragraph(f"<b>Date:</b> {date}", styles['Normal']))
    story.append(Paragraph(f"<b>Test:</b> Complete Blood Count (CBC)", styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    story.append(Paragraph("Results", styles['Heading2']))
    
    table_data = [['Test', 'Result', 'Unit', 'Reference Range']]
    for test, (value, unit, ref_range) in values.items():
        table_data.append([test, str(value), unit, ref_range])
    
    table = Table(table_data, colWidths=[2*inch, 1.2*inch, 1*inch, 1.5*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
    ]))
    story.append(table)
    
    story.append(Spacer(1, 0.5*inch))
    story.append(Paragraph(
        "<i>This is a SYNTHETIC report for testing purposes only. "
        "Not real patient data.</i>",
        styles['Normal']
    ))
    
    doc.build(story)
    buffer.seek(0)
    
    with open(filepath, 'wb') as f:
        f.write(buffer.read())
    
    print(f"Created: {filepath}")


def create_lipid_panel_pdf():
    """Create a synthetic lipid panel PDF."""
    filepath = SAMPLE_DIR / "lipid_panel_2024.pdf"
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=16)
    
    story.append(Paragraph("SYNTHETIC LAB REPORT - FOR TESTING ONLY", title_style))
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph("<b>Patient:</b> Test Patient (Synthetic)", styles['Normal']))
    story.append(Paragraph("<b>Date:</b> 2024-03-15", styles['Normal']))
    story.append(Paragraph("<b>Test:</b> Lipid Panel", styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    story.append(Paragraph("Results", styles['Heading2']))
    
    values = {
        'Total Cholesterol': ('195', 'mg/dL', '<200'),
        'HDL Cholesterol': ('55', 'mg/dL', '>40'),
        'LDL Cholesterol': ('118', 'mg/dL', '<100'),
        'Triglycerides': ('110', 'mg/dL', '<150'),
    }
    
    table_data = [['Test', 'Result', 'Unit', 'Reference Range']]
    for test, (value, unit, ref_range) in values.items():
        table_data.append([test, str(value), unit, ref_range])
    
    table = Table(table_data, colWidths=[2*inch, 1.2*inch, 1*inch, 1.5*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
    ]))
    story.append(table)
    
    story.append(Spacer(1, 0.5*inch))
    story.append(Paragraph("<i>SYNTHETIC report for testing only.</i>", styles['Normal']))
    
    doc.build(story)
    buffer.seek(0)
    
    with open(filepath, 'wb') as f:
        f.write(buffer.read())
    
    print(f"Created: {filepath}")


def create_scanned_image():
    """Create a synthetic scanned report image (PNG)."""
    filepath = SAMPLE_DIR / "metabolic_panel_scan.png"
    
    img = Image.new('RGB', (800, 600), color='white')
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
        font_bold = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
    except:
        font = ImageFont.load_default()
        font_bold = font
    
    draw.text((50, 30), "SYNTHETIC LAB REPORT - TESTING ONLY", fill='black', font=font_bold)
    draw.text((50, 60), "Patient: Test Patient (Synthetic)", fill='black', font=font)
    draw.text((50, 85), "Date: 2024-02-20", fill='black', font=font)
    draw.text((50, 110), "Test: Basic Metabolic Panel", fill='black', font=font)
    
    draw.line((50, 140, 750, 140), fill='black', width=2)
    
    y = 160
    draw.text((50, y), "Test", fill='black', font=font_bold)
    draw.text((250, y), "Result", fill='black', font=font_bold)
    draw.text((350, y), "Unit", fill='black', font=font_bold)
    draw.text((450, y), "Reference", fill='black', font=font_bold)
    
    results = [
        ("Glucose", "95", "mg/dL", "70-100"),
        ("Creatinine", "1.0", "mg/dL", "0.7-1.3"),
        ("Sodium", "140", "mEq/L", "136-145"),
        ("Potassium", "4.2", "mEq/L", "3.5-5.0"),
        ("BUN", "15", "mg/dL", "7-20"),
    ]
    
    y = 190
    for test, value, unit, ref in results:
        draw.text((50, y), test, fill='black', font=font)
        draw.text((250, y), value, fill='black', font=font)
        draw.text((350, y), unit, fill='black', font=font)
        draw.text((450, y), ref, fill='black', font=font)
        y += 30
    
    draw.text((50, 500), "This is a SYNTHETIC scanned report for OCR testing.", fill='gray', font=font)
    
    img.save(filepath)
    print(f"Created: {filepath}")


def create_docx_report():
    """Create a synthetic DOCX report."""
    try:
        from docx import Document
        from docx.shared import Inches, Pt
    except ImportError:
        print("python-docx not installed, skipping DOCX generation")
        return
    
    filepath = SAMPLE_DIR / "thyroid_panel.docx"
    
    doc = Document()
    
    doc.add_heading('SYNTHETIC LAB REPORT - FOR TESTING ONLY', 0)
    
    doc.add_paragraph('Patient: Test Patient (Synthetic)')
    doc.add_paragraph('Date: 2024-04-10')
    doc.add_paragraph('Test: Thyroid Function Panel')
    
    doc.add_heading('Results', level=1)
    
    table = doc.add_table(rows=4, cols=4)
    table.style = 'Table Grid'
    
    headers = table.rows[0].cells
    headers[0].text = 'Test'
    headers[1].text = 'Result'
    headers[2].text = 'Unit'
    headers[3].text = 'Reference'
    
    results = [
        ("TSH", "2.5", "mIU/L", "0.4-4.0"),
        ("Free T4", "1.2", "ng/dL", "0.8-1.8"),
        ("Free T3", "3.0", "pg/mL", "2.3-4.2"),
    ]
    
    for i, (test, value, unit, ref) in enumerate(results, 1):
        row = table.rows[i].cells
        row[0].text = test
        row[1].text = value
        row[2].text = unit
        row[3].text = ref
    
    doc.add_paragraph()
    doc.add_paragraph('This is a SYNTHETIC report for testing purposes only.')
    
    doc.save(filepath)
    print(f"Created: {filepath}")


def main():
    """Generate all sample reports."""
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    
    cbc_jan_values = {
        'Hemoglobin': (14.2, 'g/dL', '12.0-16.0'),
        'Hematocrit': (42.5, '%', '36-46'),
        'WBC': (7.5, '10^9/L', '4.5-11.0'),
        'RBC': (4.8, '10^12/L', '4.0-5.5'),
        'Platelets': (250, '10^9/L', '150-400'),
        'MCV': (88, 'fL', '80-100'),
        'MCH': (29.5, 'pg', '27-33'),
        'MCHC': (33.4, 'g/dL', '32-36'),
    }
    create_cbc_report_pdf("cbc_report_2024_01.pdf", "2024-01-15", cbc_jan_values)
    
    cbc_jun_values = {
        'Hemoglobin': (13.8, 'g/dL', '12.0-16.0'),
        'Hematocrit': (41.0, '%', '36-46'),
        'WBC': (8.2, '10^9/L', '4.5-11.0'),
        'RBC': (4.6, '10^12/L', '4.0-5.5'),
        'Platelets': (265, '10^9/L', '150-400'),
        'MCV': (89, 'fL', '80-100'),
        'MCH': (30.0, 'pg', '27-33'),
        'MCHC': (33.7, 'g/dL', '32-36'),
    }
    create_cbc_report_pdf("cbc_report_2024_06.pdf", "2024-06-20", cbc_jun_values)
    
    create_lipid_panel_pdf()
    
    create_scanned_image()
    
    create_docx_report()
    
    print("\nAll synthetic samples generated successfully!")


if __name__ == "__main__":
    main()
