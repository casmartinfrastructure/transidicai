# service_provider_report_merger.py
# Simplified full merger based on requested formats.

import os
import re
from datetime import datetime
from tkinter import Tk
from tkinter.filedialog import askopenfilename

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib import colors
from reportlab.lib.units import mm


def safe_float(s):
    try:
        return float(s)
    except:
        return 0.0


def parse_a(txt):
    logs = []
    parts = re.split(r'#############Log\d+###########', txt)
    for p in parts[1:]:
        m = re.search(
            r'Input:\s*(.*?)\n\s*Matching Timestamp:\s*(.*?)\nMatched Cloud Service:\s*(.*?)\nSimilarity:\s*([\d.]+)%',
            p,
            re.S
        )
        if not m:
            continue

        inp = m.group(1).strip()
        ts = m.group(2).strip()
        svc = m.group(3).strip()
        sim = safe_float(m.group(4))

        cvs = []
        for cm in re.finditer(
            r'Candidate Name:\s*(.*?)\n\s*Hourly rate \$([\d.]+)/hour\s*\n\s*Similarity to Input:\s*([\d.]+)%',
            p,
            re.S
        ):
            cvs.append({
                "name": cm.group(1).strip(),
                "rate": safe_float(cm.group(2)),
                "sim": safe_float(cm.group(3))
            })

        logs.append({
            "input": inp,
            "timestamp": ts,
            "service": svc,
            "cloud": sim,
            "cvs": cvs
        })
    return logs


def parse_b(txt):
    d = {}
    blocks = re.split(r'=+\s*INPUT\s*=+', txt)
    for b in blocks[1:]:
        lines = [x.rstrip() for x in b.strip().splitlines() if x.strip()]
        if not lines:
            continue

        inp = lines[0]
        cvs = []
        i = 1
        while i < len(lines):
            m = re.match(r'(\d+)\.\s+(.*?)\s+\(', lines[i])
            if m:
                name = m.group(2).strip()
                score = safe_float(lines[i + 1].split(":")[1]) * 100
                exp = lines[i + 2].split(":")[1].strip().title()
                comp = lines[i + 3].split(":")[1].strip().title()
                hrs = safe_float(lines[i + 4].split(":")[1].replace("hrs", ""))
                cvs.append({
                    "name": name,
                    "score": score,
                    "exp": exp,
                    "complex": comp,
                    "hours": hrs
                })
                i += 5
            else:
                i += 1
        d[inp] = cvs
    return d


def build_merged_report_data(A, B):
    merged = []

    for idx, log in enumerate(A, 1):
        extras = B.get(log["input"], [])
        providers = []

        for j, cv in enumerate(log["cvs"], 1):
            extra = next((e for e in extras if e["name"].lower() == cv["name"].lower()), {})
            hrs = extra.get("hours", 0)
            cost = cv["rate"] * hrs
            gm = log["cloud"] + cv["sim"]

            providers.append({
                "rank": j,
                "name": cv["name"],
                "rate": cv["rate"],
                "sim": cv["sim"],
                "exp": extra.get("exp", "N/A"),
                "complex": extra.get("complex", "N/A"),
                "hours": hrs,
                "cost": cost,
                "grand_match": gm
            })

        merged.append({
            "index": idx,
            "input": log["input"],
            "timestamp": log["timestamp"],
            "service": log["service"],
            "cloud_match": log["cloud"],
            "providers": providers
        })

    return merged


def write_txt_report(out_txt, user, merged_data):
    with open(out_txt, "w", encoding="utf8") as f:
        f.write("SERVICE PROVIDER REPORT\n")
        f.write("Developed by : Transidic Studio\n\n")
        f.write(f"User: {user}\n")
        f.write(f"Generated: {datetime.now()}\n\n")

        for section in merged_data:
            f.write("=" * 70 + "\n")
            f.write(f"INPUT {section['index']}\n")
            f.write("=" * 70 + "\n\n")

            f.write(section["input"] + "\n\n")
            f.write(f"Timestamp: {section['timestamp']}\n")
            f.write(f"Matched Cloud Service: {section['service']}\n")
            f.write(f"Cloud Service Match: {section['cloud_match']:.1f}%\n")
            f.write("Contacting Reference: To be released upon successful payment for the selected service provider. This reference will be used to facilitate formal provider contact and post-engagement feedback.\n\n")

            if section["providers"]:
                recommended = max(section["providers"], key=lambda x: x["grand_match"])
                f.write("CLIENT SELECTION ACTION\n")
                f.write("Please select a service provider that you would like to work with for this input.\n")
                f.write(f"Recommended Service Provider: {recommended['name']} (Grand Match: {recommended['grand_match']:.1f}%)\n")
                f.write("Grand Match represents the probability / risk-adjusted likelihood of successful delivery for this assignment based on the combined service match and provider fit indicators.\n\n")

            for p in section["providers"]:
                f.write("-" * 50 + "\n")
                f.write(f"TOP CV MATCH {p['rank']}\n")
                f.write("-" * 50 + "\n")
                f.write(f"Candidate Name: {p['name']}\n")
                f.write(f"Hourly Rate: ${p['rate']:.2f}/hour\n")
                f.write(f"Similarity to Input: {p['sim']:.1f}%\n")
                f.write(f"Experience Level: {p['exp']}\n")
                f.write(f"Task Complexity: {p['complex']}\n")
                f.write(f"Estimated Hours: {p['hours']:.2f}\n")
                f.write(f"Estimated Completion Cost: ${p['cost']:.2f}\n")
                f.write(f"Grand Match: {p['grand_match']:.1f}%\n\n")


def add_pdf_header_footer(canvas, doc):
    canvas.saveState()
    width, height = A4

    canvas.setFont("Helvetica-Bold", 11)
    canvas.drawString(20 * mm, height - 15 * mm, "Service Provider Report")

    canvas.setFont("Helvetica", 9)
    canvas.drawRightString(width - 20 * mm, height - 15 * mm, "Developed by : Transidic Studio")

    canvas.setStrokeColor(colors.grey)
    canvas.line(20 * mm, height - 18 * mm, width - 20 * mm, height - 18 * mm)

    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.grey)
    canvas.drawString(20 * mm, 10 * mm, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    canvas.drawRightString(width - 20 * mm, 10 * mm, f"Page {doc.page}")

    canvas.restoreState()


def p(text, style):
    return Paragraph(str(text).replace("\n", "<br/>"), style)


def write_pdf_report(out_pdf, user, merged_data):
    doc = SimpleDocTemplate(
        out_pdf,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=25 * mm,
        bottomMargin=18 * mm
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=18,
        leading=22,
        textColor=colors.black,
        spaceAfter=12
    )

    subtitle_style = ParagraphStyle(
        "SubtitleStyle",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontSize=10,
        leading=14,
        textColor=colors.grey,
        spaceAfter=18
    )

    section_heading = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontSize=14,
        leading=18,
        textColor=colors.black,
        spaceBefore=10,
        spaceAfter=8
    )

    sub_heading = ParagraphStyle(
        "SubHeading",
        parent=styles["Heading3"],
        fontSize=11,
        leading=14,
        textColor=colors.black,
        spaceBefore=8,
        spaceAfter=6
    )

    body_style = ParagraphStyle(
        "BodyStyle",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        alignment=TA_JUSTIFY,
        spaceAfter=6,
        wordWrap='CJK'
    )

    small_style = ParagraphStyle(
        "SmallStyle",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        alignment=TA_LEFT,
        spaceAfter=4,
        wordWrap='CJK'
    )

    table_label_style = ParagraphStyle(
        "TableLabelStyle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        alignment=TA_LEFT,
        wordWrap='CJK'
    )

    table_value_style = ParagraphStyle(
        "TableValueStyle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        alignment=TA_LEFT,
        wordWrap='CJK'
    )

    table_header_style = ParagraphStyle(
        "TableHeaderStyle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        alignment=TA_CENTER,
        wordWrap='CJK',
        textColor=colors.black
    )

    table_cell_style = ParagraphStyle(
        "TableCellStyle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        alignment=TA_LEFT,
        wordWrap='CJK'
    )

    decision_style = ParagraphStyle(
        "DecisionStyle",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        alignment=TA_JUSTIFY,
        spaceAfter=6,
        wordWrap='CJK'
    )

    story = []

    # Cover / Intro
    story.append(Paragraph("SERVICE PROVIDER REPORT", title_style))
    story.append(Paragraph("Developed by : Transidic Studio", subtitle_style))
    story.append(Spacer(1, 6))

    intro_table = Table(
        [
            [p("User", table_label_style), p(user, table_value_style)],
            [p("Generated", table_label_style), p(str(datetime.now()), table_value_style)],
            [
                p("Purpose", table_label_style),
                p(
                    "This report presents the matched cloud service and service provider options for each client request, together with the estimated hours, hourly rates, estimated completion costs, and overall match indicators to support provider selection.",
                    table_value_style
                )
            ]
        ],
        colWidths=[45 * mm, 125 * mm]
    )
    intro_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#EDEDED")),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(intro_table)
    story.append(Spacer(1, 14))

    story.append(Paragraph("Client Guidance", section_heading))
    story.append(Paragraph(
        "For each input request, this report shows the matched cloud service and the candidate service providers identified for that request. "
        "Each provider section includes the hourly rate, similarity to the input, experience level, task complexity, estimated hours, estimated completion cost, and grand match. "
        "The report is intended to help the client compare available providers and select the service provider they would like to work with. "
        "For ease of decision-making, a recommended service provider is shown for each input based on the highest grand match score.",
        body_style
    ))
    story.append(Paragraph(
        "Grand Match should be read as a practical probability-of-success indicator or risk-adjusted success score for the assignment. "
        "A higher Grand Match suggests a stronger combined fit between the client input, the matched cloud service context, and the provider’s relevance to the task, thereby indicating a lower execution risk and a stronger likelihood of successful delivery.",
        body_style
    ))
    story.append(Paragraph(
        "A Contacting Reference is also associated with each input. This reference is intentionally withheld at this stage and will only be released after payment has been completed for the specific service provider selected by the client. "
        "Once released, the Contacting Reference will be used for official provider engagement, coordination, and structured client feedback on the assignment.",
        body_style
    ))
    story.append(Spacer(1, 8))

    for idx, section in enumerate(merged_data, 1):
        story.append(Paragraph(f"INPUT {section['index']}", section_heading))

        # Recommended provider
        recommended_provider = None
        if section["providers"]:
            recommended_provider = max(section["providers"], key=lambda x: x["grand_match"])

        # Input overview block with wrapped text
        overview_data = [
            [p("Client Input", table_label_style), p(section["input"], table_value_style)],
            [p("Timestamp", table_label_style), p(section["timestamp"], table_value_style)],
            [p("Matched Cloud Service", table_label_style), p(section["service"], table_value_style)],
            [p("Cloud Service Match", table_label_style), p(f"{section['cloud_match']:.1f}%", table_value_style)],
            [
                p("Contacting Reference", table_label_style),
                p(
                    "To be released upon successful payment for the selected service provider. This reference will be used by the client to formally contact the appointed service provider and to submit engagement feedback through the relevant workflow.",
                    table_value_style
                )
            ]
        ]

        overview_table = Table(overview_data, colWidths=[45 * mm, 125 * mm])
        overview_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F2F2F2")),
            ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(overview_table)
        story.append(Spacer(1, 10))

        # Client selection section
        story.append(Paragraph("Client Selection Action", sub_heading))
        story.append(Paragraph(
            "Please select a service provider that you would like to work with for this input. "
            "Your selection should be based on the provider profile, estimated completion cost, estimated hours, experience level, task complexity, and Grand Match score presented below.",
            decision_style
        ))

        if recommended_provider:
            story.append(Paragraph(
                f"<b>Recommended Service Provider:</b> {recommended_provider['name']}",
                decision_style
            ))
            story.append(Paragraph(
                f"<b>Recommended Grand Match:</b> {recommended_provider['grand_match']:.1f}%",
                decision_style
            ))
            story.append(Paragraph(
                "This recommendation is based on the highest Grand Match recorded for this input. "
                "In practical terms, Grand Match reflects the risk-adjusted probability of successful delivery by combining the cloud-service alignment and the provider’s similarity to the task. "
                "A stronger Grand Match indicates a stronger fit and a more favorable execution outlook for the engagement.",
                decision_style
            ))
        else:
            story.append(Paragraph(
                "No recommended service provider is available for this input because no matched provider records were found.",
                decision_style
            ))

        story.append(Spacer(1, 8))

        if section["providers"]:
            story.append(Paragraph("Service Provider Options", sub_heading))

            # Summary comparison table for quick client review
            summary_table_data = [[
                p("Rank", table_header_style),
                p("Candidate Name", table_header_style),
                p("Hourly Rate", table_header_style),
                p("Estimated Hours", table_header_style),
                p("Estimated Cost", table_header_style),
                p("Grand Match", table_header_style)
            ]]

            for pvd in section["providers"]:
                summary_table_data.append([
                    p(str(pvd["rank"]), table_cell_style),
                    p(pvd["name"], table_cell_style),
                    p(f"${pvd['rate']:.2f}/hour", table_cell_style),
                    p(f"{pvd['hours']:.2f}", table_cell_style),
                    p(f"${pvd['cost']:.2f}", table_cell_style),
                    p(f"{pvd['grand_match']:.1f}%", table_cell_style)
                ])

            summary_table = Table(
                summary_table_data,
                colWidths=[12 * mm, 60 * mm, 28 * mm, 24 * mm, 28 * mm, 22 * mm],
                repeatRows=1
            )
            summary_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#D9EAF7")),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]))
            story.append(summary_table)
            story.append(Spacer(1, 12))

            # Full detail for each provider
            for pvd in section["providers"]:
                story.append(Paragraph(f"TOP SERVICE PROVIDER {pvd['rank']}", sub_heading))

                provider_table = Table(
                    [
                        [p("Candidate Name", table_label_style), p(pvd["name"], table_value_style)],
                        [p("Hourly Rate", table_label_style), p(f"${pvd['rate']:.2f}/hour", table_value_style)],
                        [p("Similarity to Input", table_label_style), p(f"{pvd['sim']:.1f}%", table_value_style)],
                        [p("Experience Level", table_label_style), p(pvd["exp"], table_value_style)],
                        [p("Task Complexity", table_label_style), p(pvd["complex"], table_value_style)],
                        [p("Estimated Hours", table_label_style), p(f"{pvd['hours']:.2f}", table_value_style)],
                        [p("Estimated Completion Cost", table_label_style), p(f"${pvd['cost']:.2f}", table_value_style)],
                        [p("Grand Match", table_label_style), p(f"{pvd['grand_match']:.1f}%", table_value_style)]
                    ],
                    colWidths=[55 * mm, 115 * mm]
                )

                provider_table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F7F7F7")),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]))

                story.append(provider_table)
                story.append(Spacer(1, 10))
        else:
            story.append(Paragraph("No matched service providers were found for this input.", body_style))
            story.append(Spacer(1, 8))

        if idx < len(merged_data):
            story.append(PageBreak())

    doc.build(
        story,
        onFirstPage=add_pdf_header_footer,
        onLaterPages=add_pdf_header_footer
    )


def main():
    user = input("User name: ").strip().capitalize()
    outdir = os.path.join("users", user, "Service Provider Report")
    os.makedirs(outdir, exist_ok=True)

    Tk().withdraw()
    fa = askopenfilename(title="Select Report A", filetypes=[("Text", "*.txt")])
    fb = askopenfilename(title="Select Report B", filetypes=[("Text", "*.txt")])

    if not fa or not fb:
        print("Cancelled")
        return

    with open(fa, encoding="utf8") as f:
        A = parse_a(f.read())

    with open(fb, encoding="utf8") as f:
        B = parse_b(f.read())

    merged_data = build_merged_report_data(A, B)

    timestamp = datetime.now().strftime("%Y-%m-%d__%Hh-%Mm-%Ss")

    out_txt = os.path.join(outdir, f"Service Provider Report - {timestamp}.txt")
    out_pdf = os.path.join(outdir, f"Service Provider Report - {timestamp}.pdf")

    write_txt_report(out_txt, user, merged_data)
    write_pdf_report(out_pdf, user, merged_data)

    print("Saved TXT:", out_txt)
    print("Saved PDF:", out_pdf)


if __name__ == "__main__":
    main()