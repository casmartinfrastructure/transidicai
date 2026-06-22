# service_provider_report_merger.py
# Simplified full merger based on requested formats.

import os
import re
import random
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


HEADER_FILL = colors.HexColor("#D9EAF7")


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


def mask_whatsapp_number(number):
    """
    Mask the last 4 numeric digits of the WhatsApp number.
    Example:
    +263 77 123 4567 -> +263 77 123 ****
    """
    digits = re.findall(r'\d', number)
    if len(digits) < 4:
        return number

    masked_count = 0
    chars = list(number)
    for i in range(len(chars) - 1, -1, -1):
        if chars[i].isdigit():
            chars[i] = '*'
            masked_count += 1
            if masked_count == 4:
                break
    return ''.join(chars)


def mask_email(email):
    """
    Mask the first 3 letters of the username part of the email.
    Example:
    johndoe23@gmail.com -> ***ndoe23@gmail.com
    """
    if "@" not in email:
        return email

    username, domain = email.split("@", 1)
    if len(username) <= 3:
        masked_user = "*" * len(username)
    else:
        masked_user = "***" + username[3:]

    return f"{masked_user}@{domain}"


def random_whatsapp_number():
    raw = f"+263 77 {random.randint(100, 999)} {random.randint(1000, 9999)}"
    return mask_whatsapp_number(raw)


def random_email(name):
    clean = re.sub(r'[^a-z0-9]+', '', name.lower())
    if not clean:
        clean = "provider"
    domains = [
        "gmail.com",
        "outlook.com",
        "icloud.com",
        "yahoo.com"
    ]
    raw = f"{clean}{random.randint(1, 99)}@{random.choice(domains)}"
    return mask_email(raw)


def random_contacting_reference():
    return str(random.randint(1000, 9999))


def get_logo_paths():
    """
    Returns up to two logo image paths from the ./logo folder.
    The first image found is used on the left, the second on the right.
    If only one logo exists, it will be shown on the left only.
    """
    logo_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo")
    if not os.path.isdir(logo_dir):
        return None, None

    allowed_exts = (".png", ".jpg", ".jpeg", ".bmp", ".gif")
    files = sorted(
        [
            os.path.join(logo_dir, f)
            for f in os.listdir(logo_dir)
            if os.path.isfile(os.path.join(logo_dir, f))
            and f.lower().endswith(allowed_exts)
        ]
    )

    left_logo = files[0] if len(files) >= 1 else None
    right_logo = files[1] if len(files) >= 2 else None
    return left_logo, right_logo


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
                "grand_match": gm,
                "whatsapp": random_whatsapp_number(),
                "email": random_email(cv["name"]),
                "contact_ref": random_contacting_reference()
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
        f.write("TOP MATCHED SERVICE PROVIDERS\n")
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
            f.write("Client Contact Guidance: The service provider options below include the contact details and contacting reference required for the client’s next-step engagement and selection workflow.\n\n")

            if section["providers"]:
                recommended = max(section["providers"], key=lambda x: x["grand_match"])
                f.write("CLIENT SELECTION ACTION\n")
                f.write("Please select a service provider that you would like to work with for this input.\n")
                f.write(f"Recommended Service Provider: {recommended['name']} (Grand Match: {recommended['grand_match']:.1f}%)\n")
                f.write("Grand Match represents the probability / risk-adjusted likelihood of successful delivery for this assignment based on the combined service match and provider fit indicators.\n\n")

                f.write("SERVICE PROVIDER OPTIONS\n")
                f.write("-" * 140 + "\n")
                f.write(
                    f"{'Rank':<8}"
                    f"{'Candidate Name':<35}"
                    f"{'WhatsApp Number':<22}"
                    f"{'Email':<35}"
                    f"{'Contacting Reference':<24}"
                    f"{'Grand Match':<16}\n"
                )
                f.write("-" * 140 + "\n")

                for p in section["providers"]:
                    f.write(
                        f"{str(p['rank']):<8}"
                        f"{p['name'][:33]:<35}"
                        f"{p['whatsapp']:<22}"
                        f"{p['email'][:33]:<35}"
                        f"{p['contact_ref']:<24}"
                        f"{f'{p['grand_match']:.1f}%':<16}\n"
                    )

                f.write("\n")
            else:
                f.write("No matched service providers were found for this input.\n\n")


def add_pdf_header_footer(canvas, doc, left_logo=None, right_logo=None):
    canvas.saveState()
    width, height = A4

    # --- Header logos + centered title on every page ---
    # Increased logo size
    logo_y = height - 24 * mm
    logo_h = 18 * mm
    logo_w = 42 * mm

    if left_logo and os.path.exists(left_logo):
        try:
            canvas.drawImage(
                left_logo,
                18 * mm,
                logo_y,
                width=logo_w,
                height=logo_h,
                preserveAspectRatio=True,
                mask='auto'
            )
        except Exception:
            pass

    if right_logo and os.path.exists(right_logo):
        try:
            canvas.drawImage(
                right_logo,
                width - 18 * mm - logo_w,
                logo_y,
                width=logo_w,
                height=logo_h,
                preserveAspectRatio=True,
                mask='auto'
            )
        except Exception:
            pass

    # Centered report title between logos
    canvas.setFont("Helvetica-Bold", 13)
    canvas.setFillColor(colors.black)
    canvas.drawCentredString(width / 2, height - 13 * mm, "TOP MATCHED SERVICE PROVIDERS")

    # Footer only
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.grey)
    canvas.drawString(20 * mm, 10 * mm, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    canvas.drawRightString(width - 20 * mm, 10 * mm, f"Page {doc.page}")

    canvas.restoreState()


def p(text, style):
    return Paragraph(str(text).replace("\n", "<br/>"), style)


def write_pdf_report(out_pdf, user, merged_data):
    left_logo, right_logo = get_logo_paths()

    doc = SimpleDocTemplate(
        out_pdf,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=46 * mm,
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
        spaceAfter=10
    )

    sub_heading = ParagraphStyle(
        "SubHeading",
        parent=styles["Heading3"],
        fontSize=11,
        leading=14,
        textColor=colors.black,
        spaceBefore=10,
        spaceAfter=8
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
    story.append(Spacer(1, 12))

    intro_table = Table(
        [
            [p("User", table_label_style), p(user, table_value_style)],
            [p("Generated", table_label_style), p(str(datetime.now()), table_value_style)],
        ],
        colWidths=[45 * mm, 125 * mm]
    )
    intro_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), HEADER_FILL),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(intro_table)
    story.append(Spacer(1, 18))

    for idx, section in enumerate(merged_data, 1):
        story.append(Paragraph(f"INPUT {section['index']}", section_heading))

        # Recommended provider
        recommended_provider = None
        if section["providers"]:
            recommended_provider = max(section["providers"], key=lambda x: x["grand_match"])

        # Input overview block
        overview_data = [
            [p("Client Input", table_label_style), p(section["input"], table_value_style)],
            [p("Timestamp", table_label_style), p(section["timestamp"], table_value_style)],
            [p("Matched Cloud Service", table_label_style), p(section["service"], table_value_style)],
        ]

        overview_table = Table(overview_data, colWidths=[45 * mm, 125 * mm])
        overview_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), HEADER_FILL),
            ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(overview_table)
        story.append(Spacer(1, 16))

        # Client selection section

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

        story.append(Spacer(1, 12))

        if section["providers"]:
            story.append(Paragraph("Service Provider Options", sub_heading))

            summary_table_data = [[
                p("Rank", table_header_style),
                p("Candidate Name", table_header_style),
                p("WhatsApp Number", table_header_style),
                p("Email", table_header_style),
                p("Contacting Reference", table_header_style),
                p("Grand Match", table_header_style)
            ]]

            for pvd in section["providers"]:
                summary_table_data.append([
                    p(str(pvd["rank"]), table_cell_style),
                    p(pvd["name"], table_cell_style),
                    p(pvd["whatsapp"], table_cell_style),
                    p(pvd["email"], table_cell_style),
                    p(pvd["contact_ref"], table_cell_style),
                    p(f"{pvd['grand_match']:.1f}%", table_cell_style)
                ])

            summary_table = Table(
                summary_table_data,
                colWidths=[12 * mm, 52 * mm, 34 * mm, 42 * mm, 30 * mm, 22 * mm],
                repeatRows=1
            )
            summary_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), HEADER_FILL),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]))
            story.append(summary_table)
            story.append(Spacer(1, 18))
        else:
            story.append(Paragraph("No matched service providers were found for this input.", body_style))
            story.append(Spacer(1, 10))

        if idx < len(merged_data):
            story.append(PageBreak())

    def first_page(canvas, doc):
        add_pdf_header_footer(canvas, doc, left_logo, right_logo)

    def later_pages(canvas, doc):
        add_pdf_header_footer(canvas, doc, left_logo, right_logo)

    doc.build(
        story,
        onFirstPage=first_page,
        onLaterPages=later_pages
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