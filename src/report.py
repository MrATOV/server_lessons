import os
import uuid
import tempfile
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle
from reportlab.rl_config import TTFSearchPath
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

font_dir = os.path.join(os.getcwd(), '.fonts')
font_regular = os.path.join(font_dir, 'LiberationSerif-Regular.ttf')
font_bold = os.path.join(font_dir, 'LiberationSerif-Bold.ttf')
font_italic = os.path.join(font_dir, 'LiberationSerif-Italic.ttf')
font_bold_italic = os.path.join(font_dir, 'LiberationSerif-BoldItalic.ttf')
font_consolas = os.path.join(font_dir, 'consolas.ttf')

TTFSearchPath.append(font_dir)

pdfmetrics.registerFont(TTFont('LiberationSerif', font_regular))
pdfmetrics.registerFont(TTFont('LiberationSerif-Bold', font_bold))
pdfmetrics.registerFont(TTFont('LiberationSerif-Italic', font_italic))
pdfmetrics.registerFont(TTFont('Consolas', font_consolas))

def generate_performance_report(performance_data: dict):
    temp_dir = os.path.join(os.getcwd(), '.reports')
    os.makedirs(temp_dir, exist_ok=True)

    fd, report_path = tempfile.mkstemp(
        suffix='.pdf',
        dir=temp_dir
    )
    os.close(fd)
    
    doc = SimpleDocTemplate(report_path, pagesize=letter)
    elements = []

    styles = getSampleStyleSheet()

    styles['Heading1'].fontName = 'LiberationSerif-Bold'
    styles['Heading1'].fontSize = 24
    styles['Heading1'].alignment = 1
    styles['Heading1'].spaceAfter = 24

    styles.add(ParagraphStyle(name='TestTitle',
                            fontName='LiberationSerif-Bold',
                            fontSize=18,
                            alignment=1,
                            spaceAfter=12))

    styles.add(ParagraphStyle(name='TestArgs', 
                            fontName='LiberationSerif-Italic',
                            fontSize=14,
                            alignment=1,
                            textColor=colors.black,
                            spaceAfter=12))

    styles['Normal'].fontName = 'LiberationSerif'
    styles['Normal'].fontSize = 12
    styles['Normal'].spaceAfter = 6

    styles.add(ParagraphStyle(name='TableHeader', fontName='LiberationSerif-Bold', fontSize=12, alignment=1))
    styles.add(ParagraphStyle(name='TableCell', fontName='LiberationSerif', fontSize=10, alignment=1))

    elements.append(Paragraph("Отчет о производительности", styles['Heading1']))

    for test_group in performance_data['test_list']:
        elements.append(Paragraph(test_group['title'], styles['TestTitle']))

        for test in test_group['data']:
            if test['args'] and test['args'].strip():
                elements.append(Paragraph(f"Параметры: {test['args']}", styles['TestArgs']))
            
            table_data = [
                ['Потоки', 'Время (мс)', 'Ускорение', 'Эффективность', 'Стоимость']
            ]
            
            for perf in test['performance']:
                table_data.append([
                    str(perf['thread']),
                    f"{perf['time']:.6f}",
                    f"{perf['acceleration']:.2f}",
                    f"{perf['efficiency']:.2f}",
                    f"{perf['cost']:.6f}"
                ])
            
            table = Table(table_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'LiberationSerif-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('FONTNAME', (0, 1), (-1, -1), 'LiberationSerif'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            
            elements.append(table)
            elements.append(Paragraph(" ", styles['Normal'])) 

    doc.build(elements)
    return report_path