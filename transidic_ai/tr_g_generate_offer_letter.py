import os
import re
import sys
from datetime import datetime
from tkinter import Tk
from tkinter.filedialog import askopenfilename
import textwrap

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader


# ==========================================
# CONFIG
# ==========================================
USERS_FOLDER = "users"
OFFERS_FOLDER = "offers"
LOGO_FOLDER = "logo"


# ==========================================
# PDF WRITER (FORMAL STYLE MATCHED TO APPOINTMENT)
# ==========================================
def write_pdf(txt_path, pdf_path, logo_path):

    if os.path.exists(pdf_path):
        try:
            os.remove(pdf_path)
        except:
            pass

    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4

    left_margin = 60
    right_margin = 60
    top_margin = 50
    bottom_margin = 50
    usable_width = width - left_margin - right_margin

    font = "Helvetica"
    bold = "Helvetica-Bold"

    normal_size = 11
    heading_size = 11
    small_size = 9
    line_spacing = 18

    COPYRIGHT = (
        "© 2018 Transidic Startup Studio (Pvt) Ltd. "
        "All rights reserved."
    )

    def draw_text(text, x, y, font_name=font, size=normal_size):
        c.setFont(font_name, size)

        wrapped = textwrap.wrap(text, width=95)

        for line in wrapped:
            if y < bottom_margin:
                c.showPage()
                y = height - top_margin
                c.setFont(font_name, size)

            c.drawString(x, y, line)
            y -= line_spacing

        return y

    def draw_label(label, value, x, y):
        c.setFont(bold, normal_size)
        label_w = c.stringWidth(label, bold, normal_size)

        c.drawString(x, y, label)
        c.setFont(font, normal_size)
        c.drawString(x + label_w + 5, y, value)

        return y - line_spacing

    y = height - top_margin

    # ==========================================
    # TOP LOGO (MATCHING APPOINTMENT STYLE)
    # ==========================================
    if os.path.exists(logo_path):
        try:
            logo = ImageReader(logo_path)
            logo_width = 120
            logo_height = 60

            x_position = (width - logo_width) / 2

            c.drawImage(
                logo,
                x_position,
                y - 60,
                width=logo_width,
                height=logo_height,
                preserveAspectRatio=True,
                mask='auto'
            )

            y -= 85

        except:
            pass

    # ==========================================
    # READ TXT
    # ==========================================
    with open(txt_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for line in lines:

        line = line.strip()

        if not line:
            y -= 6
            continue

        # LABELS
        if line.startswith("Offer Reference :"):
            y = draw_label("Offer Reference :", line.split(":", 1)[1].strip(), left_margin, y)

        elif line.startswith("Client Encryption Key :"):
            y = draw_label("Client Encryption Key :", line.split(":", 1)[1].strip(), left_margin, y)

        elif line.startswith("Ref :"):
            y = draw_label("Ref :", line.split(":", 1)[1].strip(), left_margin, y)

        # HEADINGS (FORMAL STYLE LIKE APPOINTMENT)
        elif line.startswith("##"):
            title = line.replace("##", "").strip()
            y -= 5
            c.setFont(bold, heading_size)
            c.drawString(left_margin, y, title)
            y -= line_spacing

        # NORMAL TEXT
        else:
            y = draw_text(line, left_margin, y)

    # ==========================================
    # FOOTER
    # ==========================================
    c.setFont(font, small_size)
    c.drawCentredString(width / 2, 25, COPYRIGHT)

    c.save()


# ==========================================
# HELPERS (UNCHANGED LOGIC)
# ==========================================
def extract_client_code(content):
    match = re.search(r"Client\s*:\s*(.*)", content)
    return match.group(1).strip() if match else "UNKNOWN"


def extract_descriptions(content):
    descriptions = []
    lines = content.splitlines()

    capture = False
    current = ""

    for line in lines:
        if line.startswith("|"):
            cols = line.split("|")
            if len(cols) > 3:
                item = cols[1].strip()
                desc = cols[2].strip()

                if item.isdigit():
                    if current.strip():
                        descriptions.append(" ".join(current.split()))
                    current = desc
                    capture = True
                else:
                    if capture:
                        current += " " + desc
        else:
            capture = False

    if current.strip():
        descriptions.append(" ".join(current.split()))

    return descriptions


def extract_total_due(content):
    match = re.search(r"\*\*TOTAL DUE:\s*\$([\d\.]+)\*\*", content)
    return float(match.group(1)) if match else 0.0


def extract_payment_instruction(content):
    return "*151*2*2*001637*AMOUNT#"


def sanitize_filename(text):
    return re.sub(r'[^A-Za-z0-9_-]', '_', text)


# ==========================================
# OFFER LETTER CREATOR (SIMPLIFIED TEXT OUTPUT)
# ==========================================
def create_offer_letter(recipient, client_code, descriptions,
                         amount_due, payment_instruction,
                         offer_dir, logo_path):

    os.makedirs(offer_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    offer_reference = f"{sanitize_filename(client_code)}_{timestamp}"

    txt_path = os.path.join(offer_dir, f"{offer_reference}.txt")
    pdf_path = os.path.join(offer_dir, f"{offer_reference}.pdf")

    payment_code = payment_instruction.replace("AMOUNT", str(round(amount_due, 2)))

    # ==========================================
    # WRITE SIMPLIFIED FORMAL OFFER TEXT
    # ==========================================
    with open(txt_path, "w", encoding="utf-8") as f:

        f.write(f"Offer Reference : {offer_reference}\n")
        f.write(f"Client Encryption Key : {client_code}\n")
        f.write("Ref : Request Facilitaton Fee\n\n")

        f.write("Dear Client,\n\n")
        f.write("We have received your Procurement Request and identified the following requirements: \n\n")

        for i, d in enumerate(descriptions, 1):
            f.write(f"{i}. {d}\n")

        f.write("\n## SERVICE FEE\n")
        f.write(f"A service fee of USD ${amount_due:.2f} applies for request facilitation.\n\n")

        f.write("This service fee includes providing you with a list of the top 3 service providers in our Database for each of your request/s.\n\n")
        
        f.write("## PAYMENT INSTRUCTIONS\n")
        f.write(f"{payment_code}\n")
        f.write("ECOCASH: 0779 553 948\n\n")

        f.write("Send proof of payment via WhatsApp: +263 785 261 617\n\n")
        f.write("Upon receipt of the proof of payment, you will immediately receive the list of the top 3 service providers for each of your request/s and you may contact the service provider you would like to work with.\n\n")

    
        f.write("## CONFIDENTIALITY\n")
        f.write("Your Request and related information will be handled confidentially. Your Client Encryption Key is used in all correspondances.\n\n")

        f.write("Thank you for choosing the Transidic Ai.\n\n")

        f.write("Kind regards,\nTransidic Startup Studio Private Limited\n")
        f.write("WhatsApp : +263 785 261 617\n")
        f.write("Email : transidicstudio@gmail.com\n")


    # ==========================================
    # GENERATE PDF
    # ==========================================
    write_pdf(txt_path, pdf_path, logo_path)

    print("\n✅ OFFER LETTER CREATED")
    print(txt_path)
    print(pdf_path)


# ==========================================
# MAIN
# ==========================================
def main():

    username = input("Enter username: ").strip()
    if not username:
        print("❌ Username required")
        return

    user_folder = os.path.join(USERS_FOLDER, username)

    if not os.path.exists(user_folder):
        print("❌ User not found")
        return

    offer_dir = os.path.join(user_folder, OFFERS_FOLDER)
    logo_path = os.path.join(user_folder, LOGO_FOLDER, "logo.png")

    Tk().withdraw()
    print("Select invoice file...")

    file_path = askopenfilename(filetypes=[("Text Files", "*.txt")])

    if not file_path:
        print("❌ No file selected")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    client_code = extract_client_code(content)
    descriptions = extract_descriptions(content)
    amount_due = extract_total_due(content)
    payment_instruction = extract_payment_instruction(content)

    create_offer_letter(
        username,
        client_code,
        descriptions,
        amount_due,
        payment_instruction,
        offer_dir,
        logo_path
    )


# ==========================================
# RUN
# ==========================================
if __name__ == "__main__":
    main()