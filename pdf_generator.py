import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import logging

logger = logging.getLogger(__name__)

# Register Unicode-compatible font if available, fallback gracefully
FONT_NAME = 'Helvetica'
try:
    font_paths = [
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
        '/usr/share/fonts/truetype/freefont/FreeSans.ttf'
    ]
    for path in font_paths:
        if os.path.exists(path):
            pdfmetrics.registerFont(TTFont('UnicodeFont', path))
            FONT_NAME = 'UnicodeFont'
            break
except Exception as e:
    logger.warning(f"Could not register unicode font: {e}")

def generate_invoice_pdf(order_id, user_id, product_name, spec, quantity, unit, unit_price, total_price, currency, filename):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName=FONT_NAME,
        fontSize=22,
        leading=26,
        textColor=colors.HexColor('#1B365D'),
        alignment=1, # Center
        spaceAfter=15
    )

    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=11,
        leading=14,
        textColor=colors.HexColor('#555555'),
        alignment=1,
        spaceAfter=20
    )

    header_style = ParagraphStyle(
        'HeaderStyle',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=10,
        leading=14,
        textColor=colors.black
    )

    table_header_style = ParagraphStyle(
        'TableHeaderStyle',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=10,
        leading=12,
        textColor=colors.white,
        alignment=1
    )

    table_body_style = ParagraphStyle(
        'TableBodyStyle',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=9,
        leading=12,
        textColor=colors.black,
        alignment=1
    )

    elements = []

    # Title & Header
    elements.append(Paragraph("<b>OFFICIAL PROFORMA INVOICE</b>", title_style))
    elements.append(Paragraph("<b>STEEL & METAL EXPORT COMPANY</b><br/>International Sales & Supply Department", subtitle_style))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#1B365D'), spaceAfter=20))

    # Meta Info Table
    meta_data = [
        [
            Paragraph(f"<b>Invoice No:</b> PRF-{order_id:06d}", header_style),
            Paragraph(f"<b>Customer ID:</b> USR-{user_id}", header_style)
        ],
        [
            Paragraph(f"<b>Currency:</b> {currency}", header_style),
            Paragraph(f"<b>Status:</b> Official Quote", header_style)
        ]
    ]
    meta_table = Table(meta_data, colWidths=[270, 270])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8F9FA')),
        ('PADDING', (0,0), (-1,-1), 8),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#DDDDDD')),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 20))

    # Order Table
    table_data = [
        [
            Paragraph("<b>Item Description</b>", table_header_style),
            Paragraph("<b>Specification</b>", table_header_style),
            Paragraph("<b>Quantity</b>", table_header_style),
            Paragraph("<b>Unit Price</b>", table_header_style),
            Paragraph("<b>Total Amount</b>", table_header_style)
        ],
        [
            Paragraph(product_name, table_body_style),
            Paragraph(spec or "-", table_body_style),
            Paragraph(f"{quantity} {unit}", table_body_style),
            Paragraph(f"{unit_price:,.2f} {currency}", table_body_style),
            Paragraph(f"{total_price:,.2f} {currency}", table_body_style)
        ]
    ]

    order_table = Table(table_data, colWidths=[130, 130, 80, 100, 100])
    order_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1B365D')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CCCCCC')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F9F9F9')])
    ]))
    elements.append(order_table)
    elements.append(Spacer(1, 25))

    # Total Summary
    total_data = [
        [
            Paragraph("<b>Total Amount Due:</b>", ParagraphStyle('TotLbl', parent=styles['Normal'], fontName=FONT_NAME, fontSize=12, alignment=2)),
            Paragraph(f"<b>{total_price:,.2f} {currency}</b>", ParagraphStyle('TotVal', parent=styles['Normal'], fontName=FONT_NAME, fontSize=12, textColor=colors.HexColor('#1B365D'), alignment=1))
        ]
    ]
    total_table = Table(total_data, colWidths=[380, 160])
    total_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#EBF3FA')),
        ('PADDING', (0,0), (-1,-1), 10),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#1B365D'))
    ]))
    elements.append(total_table)
    elements.append(Spacer(1, 30))

    # Terms & Conditions
    terms_text = (
        "<b>Terms & Notes:</b><br/>"
        "1. Price validity: 24 hours from invoice generation.<br/>"
        "2. Payment Terms: Telegraphic Transfer (T/T) or Letter of Credit (L/C) as agreed.<br/>"
        "3. Delivery & Freight: Subject to final dispatch arrangement.<br/>"
        "4. Contact Export Sales Department for further details."
    )
    elements.append(Paragraph(terms_text, ParagraphStyle('Terms', parent=styles['Normal'], fontName=FONT_NAME, fontSize=9, leading=13, textColor=colors.HexColor('#666666'))))

    doc.build(elements)
    logger.info(f"PDF Invoice generated successfully at {filename}")
    return filename
