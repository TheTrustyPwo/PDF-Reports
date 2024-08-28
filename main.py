import os
import argparse
import numpy as np
import pandas as pd
from tqdm import tqdm
from io import BytesIO
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, Image, PageBreak

df, topics = None, None


def create_radar_chart(student_data, student_name):
    scores = [student_data[topic] for topic in topics]
    percentages = [int(s.split('/')[0]) / int(s.split('/')[1])
                   if int(s.split('/')[1]) != 0 else 0 for s in scores]

    angles = np.linspace(0, 2 * np.pi, len(topics), endpoint=False).tolist()
    percentages += percentages[:1]
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    ax.fill(angles, percentages, color='blue', alpha=0.25)
    ax.plot(angles, percentages, color='blue', linewidth=2)

    ax.set_yticklabels([])
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(topics, fontsize=10)

    buf = BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)
    return buf


def generate_feedback(student_data):
    feedback = []
    topics_to_improve = []
    topics_to_praise = []

    for topic in topics:
        score = student_data[topic].split('/')[0]
        try:
            score_percentage = int(score) / int(student_data[topic].split('/')[1]) * 100
        except ZeroDivisionError:
            score_percentage = 0

        if score_percentage < 50:
            topics_to_improve.append(topic)
        elif score_percentage > 80:
            topics_to_praise.append(topic)

    if topics_to_improve:
        feedback.append(f"You should improve on the following topics: {', '.join(topics_to_improve)}.")
    if topics_to_praise:
        feedback.append(f"Good job on the following topics: {', '.join(topics_to_praise)}.")

    if not topics_to_improve and not topics_to_praise:
        feedback.append("Your performance is consistent across all topics. Keep up the good work!")

    return "<br/>".join(feedback)


def generate_pdf_report(student_data, student_name, output_dir):
    file_name = os.path.join(output_dir, f'{student_name}_Report.pdf')
    document = SimpleDocTemplate(file_name, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=18)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(name="TitleStyle", fontSize=18, spaceAfter=20)
    title = Paragraph(f"Physics Quiz Report: {student_name}", title_style)

    general_info_data = [
        ['Quiz Performance', f"{student_data['Quiz Perf.']}%"],
        ['Attempted Questions', f"{student_data['Attempted qns']}"]
    ]

    general_info_table = Table(general_info_data, colWidths=[2.5 * inch, 2.5 * inch], hAlign='LEFT')
    general_info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
    ]))

    data = [['Topic', 'Score']] + [[topic, f"{student_data[topic]}"] for topic in topics]

    scores_table = Table(data, colWidths=[2.5 * inch, 2.5 * inch], hAlign='LEFT')
    scores_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
    ]))

    feedback_text = generate_feedback(student_data)

    radar_chart_file = create_radar_chart(student_data, student_name)
    radar_chart_img = Image(radar_chart_file, 5 * inch, 5 * inch)

    elements = [
        title,
        Spacer(1, 12),
        general_info_table,
        Spacer(1, 12),
        Paragraph('Detailed Topic Scores', styles['Heading2']),
        scores_table,
        Spacer(1, 12),
        Paragraph('Qualitative Feedback', styles['Heading2']),
        Paragraph(feedback_text, styles['Normal']),
        PageBreak(),
        Paragraph('Radar Chart', styles['Heading2']),
        radar_chart_img,
    ]
    document.build(elements)


def main():
    parser = argparse.ArgumentParser(description='Generate PDF reports from an Excel file.')
    parser.add_argument('filename', type=str, help='The path to the input Excel file.')
    parser.add_argument('output_dir', type=str, nargs='?', default='./output',
                        help='The directory to save output PDFs (default: ./output).')

    args = parser.parse_args()

    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)

    global df, topics
    df = pd.read_excel(args.filename, header=1)
    df['Quiz Perf.'] = df['Quiz Perf.'].apply(lambda x: round(float(str(x).strip('%')) * 100, 2))
    topics = df.columns[4:]

    for i, row in tqdm(df.iterrows(), total=df.shape[0], desc='Generating reports'):
        student_name = row.iat[0]
        generate_pdf_report(row, student_name, args.output_dir)


if __name__ == '__main__':
    main()
