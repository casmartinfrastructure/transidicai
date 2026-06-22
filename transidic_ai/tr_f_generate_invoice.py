import os
import re
import csv
import textwrap
import hashlib
from datetime import datetime
from glob import glob
from reportlab.lib.pagesizes import A3
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from tkinter import Tk
from tkinter.filedialog import askopenfilename

# =========================
# CONFIG
# =========================
USER_LOGS = "users"  # changed from user_logs
BROAD_PROPOSAL_FOLDER = "broad_proposal"
INVOICE_FOLDER = "invoices"  # changed from invoice
CLIENT_MAP_FILE = os.path.join(USER_LOGS, "client_encryption_map.csv")
LOGO_FOLDER = "logo"

MAX_COL_WIDTHS = [4, 32, 17, 6, 21, 6, 6, 12, 15, 15, 10]

COLUMN_HEADERS = [
    "Item", "Description", "Cloud Service", "Cld %",
    "Consultant", "Con %", "Tot %",
    "Cloud Amt", "Consultant Amt", "Royalties", "Total"
]

SUMMARY_COL_WIDTHS = [17, 12]
SUMMARY_HEADERS = ["Payee", "Amount"]

# =========================
# FORMATTING UTILITIES
# =========================
def summary_table_border():
    return "+" + "+".join("-" * (w + 2) for w in SUMMARY_COL_WIDTHS) + "+"

def format_summary_line(values):
    return "| " + " | ".join(
        str(values[i]).ljust(SUMMARY_COL_WIDTHS[i])
        for i in range(len(values))
    ) + " |"

def format_summary_header():
    centered = [
        SUMMARY_HEADERS[i].center(SUMMARY_COL_WIDTHS[i])
        for i in range(len(SUMMARY_HEADERS))
    ]
    return "\n".join([
        summary_table_border(),
        format_summary_line(centered),
        summary_table_border()
    ])

def table_border():
    return "+" + "+".join("-" * (w + 2) for w in MAX_COL_WIDTHS) + "+"

def format_table_line(values):
    return "| " + " | ".join(
        str(values[i]).ljust(MAX_COL_WIDTHS[i])
        for i in range(len(values))
    ) + " |"

def format_header():
    centered = [
        COLUMN_HEADERS[i].center(MAX_COL_WIDTHS[i])
        for i in range(len(COLUMN_HEADERS))
    ]
    return "\n".join([
        table_border(),
        format_table_line(centered),
        table_border()
    ])

def format_row(**e):
    cloud_amt = e['cloud_prob']/100 * e['rate'] * e['hours']
    consultant_amt = e['consultant_prob']/100 * e['rate'] * e['hours']
    royalties = (1 - e['total_prob']/100) * e['rate'] * e['hours']
    cols = [
        str(e["item_no"]),
        e["description"],
        e["cloud_service"],
        f"{e['cloud_prob']:.1f}%",
        e["consultant_name"],
        f"{e['consultant_prob']:.1f}%",
        f"{e['total_prob']:.1f}%",
        f"${cloud_amt:.2f}",
        f"${consultant_amt:.2f}",
        f"${royalties:.2f}",
        f"${e['total']:.2f}"
    ]
    wrapped = [textwrap.wrap(c, w) or [""] for c, w in zip(cols, MAX_COL_WIDTHS)]
    lines = []
    for i in range(max(len(c) for c in wrapped)):
        row = [wrapped[j][i] if i < len(wrapped[j]) else "" for j in range(len(cols))]
        lines.append(format_table_line(row))
    lines.append(table_border())
    return "\n".join(lines)

# =========================
# ENCRYPTION
# =========================
def get_encrypted_client(username):
    os.makedirs(USER_LOGS, exist_ok=True)
    if not os.path.exists(CLIENT_MAP_FILE):
        with open(CLIENT_MAP_FILE, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(["original_user", "encrypted_name", "created_on"])
    with open(CLIENT_MAP_FILE, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["original_user"] == username:
                return row["encrypted_name"]
    encrypted = "BW-" + hashlib.sha256(username.encode()).hexdigest().upper()[:6]
    with open(CLIENT_MAP_FILE, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([username, encrypted, datetime.now().date()])
    return encrypted

# =========================
# UTILITIES
# =========================
def safe_float(v, d=0.0):
    try:
        return float(v)
    except:
        return d

def parse_prob(s):
    if not s:
        return 0.0
    s = s.replace("%", "").strip()
    try:
        v = float(s)
        return v * 100 if v <= 1 else v
    except:
        return 0.0

def split_logs(content):
    return re.findall(
        r"(#############Log\d+###########.*?)(?=#############Log\d+###########|$)",
        content, re.DOTALL
    )

# =========================
# PDF WRITER
# =========================
def write_pdf(txt_path, pdf_path, logo_path):
    if os.path.exists(pdf_path):
        try: os.remove(pdf_path)
        except PermissionError: raise RuntimeError(f"PDF file is currently open or locked: {pdf_path}")

    c = canvas.Canvas(pdf_path, pagesize=A3)
    width, height = A3
    left_margin = 40
    right_margin = 40
    usable_width = width - left_margin - right_margin
    top_margin = 40
    bottom_margin = 40
    font_name = "Courier"
    bold_font = "Courier-Bold"
    COPYRIGHT_TEXT = "© 2018 CONSTRUCTAXIS Smart Infrastructure. All rights reserved."

    def get_font_size():
        for size in [10, 9, 8, 7, 6]:
            c.setFont(font_name, size)
            if c.stringWidth(table_border(), font_name, size) <= usable_width:
                return size
        return 6

    font_size = get_font_size()
    line_spacing = font_size + 4

    def draw_mixed_text(line, x, y):
        parts = re.split(r"(\*\*.*?\*\*)", line)
        current_x = x
        for part in parts:
            if not part: continue
            if part.startswith("**") and part.endswith("**"):
                text = part[2:-2]
                c.setFont(bold_font, font_size)
            else:
                text = part
                c.setFont(font_name, font_size)
            c.drawString(current_x, y, text)
            current_x += c.stringWidth(text, c._fontname, font_size)
        return y - line_spacing

    def draw_wrapped(text, x, y):
        words = re.split(r'(\s+)', text)
        line = ""
        for w in words:
            test = line + w
            test_clean = re.sub(r"\*\*(.*?)\*\*", r"\1", test)
            c.setFont(font_name, font_size)
            if c.stringWidth(test_clean, font_name, font_size) <= usable_width:
                line = test
            else:
                y = draw_mixed_text(line, x, y)
                line = w.strip()
        if line:
            y = draw_mixed_text(line, x, y)
        return y

    with open(txt_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    y = height - top_margin
    c.setFont(font_name, font_size)
    c.drawString(left_margin, y, COPYRIGHT_TEXT)
    y -= line_spacing + 10

    if os.path.exists(logo_path):
        logo = ImageReader(logo_path)
        c.drawImage(logo, left_margin, y - 90, width=180, height=90, preserveAspectRatio=True, mask="auto")
        y -= 100

    for raw_line in lines:
        line = raw_line.rstrip("\n")
        if y < bottom_margin:
            c.showPage()
            y = height - top_margin
            c.setFont(font_name, font_size)
            c.drawString(left_margin, y, COPYRIGHT_TEXT)
            y -= line_spacing + 10
        if line.startswith("|") or line.startswith("+"):
            c.setFont(font_name, font_size)
            c.drawString(left_margin, y, line)
            y -= line_spacing
        else:
            y = draw_wrapped(line, left_margin, y)
            y -= 4

    c.save()

# =========================
# MAIN
# =========================
def main():
    recipient = input("Recipient full name: ").strip()
    if not recipient:
        print("❌ Recipient required.")
        return

    encrypted_client = get_encrypted_client(recipient)

    # Prompt for proposal file
    root = Tk()
    root.title("Select Proposal TXT File")
    root.attributes('-topmost', True)
    root.lift()
    print("Please select the broad proposal TXT file.")
    proposal_file = askopenfilename(filetypes=[("Text files", "*.txt")])
    root.destroy()

    if not proposal_file:
        print("❌ No proposal file selected.")
        return

    # Folder for invoices and logo inside user's folder
    user_folder = os.path.join(USER_LOGS, recipient)
    invoice_dir = os.path.join(user_folder, INVOICE_FOLDER)
    os.makedirs(invoice_dir, exist_ok=True)
    logo_path = os.path.join(user_folder, LOGO_FOLDER, "logo.png")

    # Rest of logic unchanged...
    prev_descriptions = set()
    existing_invoices = glob(os.path.join(invoice_dir, "*.txt"))
    for invoice_file in existing_invoices:
        with open(invoice_file, "r", encoding="utf-8") as f:
            for line in f:
                m = re.match(r"\|\s*\d+\s*\|\s*(.*?)\s*\|", line)
                if m:
                    prev_descriptions.add(m.group(1).strip())

    invoice_items = []
    total_amount = 0.0

    with open(proposal_file, "r", encoding="utf-8") as f:
        logs = split_logs(f.read())

    for idx, log in enumerate(logs, 1):
        desc_match = re.search(r"Input:\s*(.*)", log)
        desc = desc_match.group(1).strip() if desc_match else f"Input {idx}"

        if desc in prev_descriptions:
            continue

        cloud = re.search(r"Matched Cloud Service:\s*(.*)", log)
        cloud_p = re.search(r"Similarity:\s*(.*)", log)
        cloud_service = cloud.group(1).strip() if cloud else "N/A"
        cloud_prob = parse_prob(cloud_p.group(1)) if cloud_p else 0.0

        candidates = re.findall(
            r"Candidate Name:\s*(.*?)\n\s*Hourly rate\s*\$([\d\.]+).*?\n\s*Similarity to Input:\s*(.*?)\n",
            log, re.DOTALL
        )
        if not candidates:
            continue

        sel = candidates[0]
        rate = safe_float(sel[1])
        prob = parse_prob(sel[2])
        hours = 1
        total = rate * hours
        total_amount += total

        invoice_items.append({
            "item_no": len(invoice_items) + 1,
            "description": desc,
            "cloud_service": cloud_service,
            "cloud_prob": cloud_prob,
            "consultant_name": sel[0],
            "consultant_prob": prob,
            "total_prob": cloud_prob + prob,
            "rate": rate,
            "hours": hours,
            "total": total
        })

    if not invoice_items:
        print("❌ No new entries to invoice. All items are already invoiced.")
        return

    cloud_total = sum(item['cloud_prob']/100 * item['rate']*item['hours'] for item in invoice_items)
    royalties_total = sum((1 - item['total_prob']/100) * item['rate']*item['hours'] for item in invoice_items)
    consultant_totals = {}
    for item in invoice_items:
        amt = item['consultant_prob']/100 * item['rate']*item['hours']
        consultant_totals[item['consultant_name']] = consultant_totals.get(item['consultant_name'], 0) + amt

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    invoice_no = f"INV-{ts}"
    base_name = f"BIDWISE_{encrypted_client}_{invoice_no}"
    txt_file = os.path.join(invoice_dir, f"{base_name}.txt")

    with open(txt_file, "w", encoding="utf-8") as f:
        f.write("**THE EVERYTHING APP**\n")
        f.write("Developed by : Transidic Startup Studio\n")
        f.write("Cloud Service Employed : Code++\n\n")
        f.write("**INVOICE**\n")
        f.write(f"Invoice No: {invoice_no}\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("Cloud Service : Swift Bill\n")
        f.write(f"Client        : {encrypted_client}\n")
        f.write("Note: For security reasons, client names are encrypted to protect confidentiality.\n\n")
        f.write(format_header() + "\n")
        for item in invoice_items:
            f.write(format_row(**item) + "\n")
        f.write(f"\n**TOTAL DUE: ${total_amount:.2f}**\n\n")
        f.write(format_summary_header() + "\n")
        f.write(format_summary_line(["Cloud Service", f"${cloud_total:.2f}"]) + "\n")
        for c, amt in consultant_totals.items():
            f.write(format_summary_line([c, f"${amt:.2f}"]) + "\n")
        f.write(format_summary_line(["Royalties", f"${royalties_total:.2f}"]) + "\n")
        f.write(summary_table_border() + "\n")
        f.write(format_summary_line(["GRAND TOTAL", f"${total_amount:.2f}"]) + "\n")
        f.write(summary_table_border() + "\n\n")

        # Explanatory clauses unchanged
        f.write("**IMPORTANT CLARIFICATIONS**\n\n")
        f.write("•**Payments can be made via ECOCASH using this short code *151*2*2*001637*AMOUNT#**\n\n")
        f.write("• Payment of all invoices is respectfully requested within two (2) days "
                "from the date of issuance. We appreciate your prompt attention to this matter.\n\n")
        f.write("• Cloud Amount (Cloud Amt): Represents the hourly fee payable to the cloud service "
                "provider for the execution, processing, and operational delivery of the services rendered.\n\n")
        f.write("• Consultant Amount (Consultant Amt): Represents the hourly professional fees payable "
                "to the respective consultant for advisory, technical, or implementation services provided.\n\n")
        f.write("• Royalties: Represents the hourly intellectual property fee payable to the owner of "
                "the proprietary software, systems, or technologies utilised in the development and "
                "delivery of the solutions, in accordance with applicable copyright and licensing provisions.\n\n")
        f.write("• All fees and charges stated in this invoice are calculated on an hourly basis.\n\n")
        f.write("**REFUND & SERVICE CONTINUATION CLAUSE**\n")
        f.write("We offer a 100% refund should you find our services unsatisfactory. "
                "Additionally, and where applicable, clients may continue accessing selected services at no extra cost. "
                "Our aim is fairness, transparency, and client satisfaction.\n\n")
        f.write("**COPYRIGHT NOTICE**\n")
        f.write("© 2018 CONSTRUCTAXIS Smart Infrastructure. All rights reserved.\n\n")
        f.write("We sincerely appreciate your interest and the opportunity to work with you. "
                "Thank you for considering our services, and we look forward to supporting your objectives with professionalism and dedication.\n\n")
        f.write("Kind regards,\nSwiftBill\n")

    pdf_file = txt_file.replace(".txt", ".pdf")
    write_pdf(txt_file, pdf_file, logo_path)

    print("✅ Invoice created:")
    print(txt_file)
    print(pdf_file)

if __name__ == "__main__":
    main()