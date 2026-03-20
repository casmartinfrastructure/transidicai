import os
import sys
import numpy as np
from datetime import datetime
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
from PyPDF2 import PdfReader
from docx import Document
import tkinter as tk
from tkinter import filedialog
import threading
import time

# =========================
# CONFIG
# =========================
TOP_K = 3
MIN_CV_LENGTH = 50

# =========================
# UTILITIES
# =========================
def safe_exit(msg):
    print(msg)
    sys.exit(0)

def safe_input(prompt):
    try:
        return input(prompt)
    except KeyboardInterrupt:
        safe_exit("\n❌ Session cancelled.")

def extract_name_from_filename(filename):
    base = os.path.splitext(filename)[0]
    return base.replace("_", " ").title()

def clean_text(text):
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return " ".join(lines)

# =========================
# LOADING DOTS
# =========================
loading = False

def loading_dots(message="Processing"):
    i = 0
    while loading:
        dots = "." * (i % 4)
        print(f"\r{message}{dots}   ", end="")
        time.sleep(0.5)
        i += 1
    print("\r", end="")

# =========================
# TXT UPLOAD
# =========================
def upload_txt_file():
    root = tk.Tk()
    root.withdraw()
    root.overrideredirect(True)
    root.attributes('-topmost', True)

    file_path = filedialog.askopenfilename(
        title="Select TXT File",
        filetypes=[("Text Files", "*.txt")]
    )

    root.destroy()

    if not file_path:
        safe_exit("❌ No file selected. Exiting.")

    print(f"✅ TXT file loaded: {file_path}")
    return file_path

# =========================
# CV READERS
# =========================
def read_pdf(path):
    reader = PdfReader(path)
    return clean_text(" ".join(page.extract_text() or "" for page in reader.pages))

def read_docx(path):
    doc = Document(path)
    return clean_text(" ".join(p.text for p in doc.paragraphs))

def load_cv_text(path):
    if path.lower().endswith(".pdf"):
        return read_pdf(path)
    if path.lower().endswith(".docx"):
        return read_docx(path)
    return ""

# =========================
# GET CV FILES
# =========================
def get_cv_files(user_name):
    folder = os.path.join("users", user_name, "my_resources")

    if not os.path.exists(folder):
        safe_exit(f"❌ Folder '{folder}' not found.")

    files = [f for f in os.listdir(folder) if f.lower().endswith((".pdf", ".docx"))]

    if not files:
        safe_exit("❌ No CVs found.")

    return folder, files

# =========================
# MAIN CV APPEND LOGIC
# =========================
def append_cv_matching_to_txt(original_txt, user_name, model, cv_folder, cv_files):

    output_folder = os.path.join("users", user_name, "cv_matching")
    os.makedirs(output_folder, exist_ok=True)

    # Timestamped output file
    timestamp_file = datetime.now().strftime("%Y-%m-%d__%Hh-%Mm-%Ss")
    output_file = os.path.join(output_folder, f"{timestamp_file}.txt")

    with open(original_txt, "r", encoding="utf-8") as f:
        lines = f.readlines()

    final_lines = []
    user_inputs = []

    # Collect Inputs
    for line in lines:
        final_lines.append(line)
        if line.strip().startswith("Input:"):
            user_input = line.replace("Input:", "").strip()
            user_inputs.append(user_input)

    # Precompute CV embeddings
    cv_embeddings = {}
    for cv in cv_files:
        cv_path = os.path.join(cv_folder, cv)
        cv_text = load_cv_text(cv_path)

        if cv_text and len(cv_text) >= MIN_CV_LENGTH:
            cv_embeddings[cv] = model.encode([cv_text], convert_to_numpy=True)

    # Append CV matching under each Input
    input_index = 0
    updated_lines = []

    for line in final_lines:
        updated_lines.append(line)

        if line.strip().startswith("Input:") and input_index < len(user_inputs):
            user_input = user_inputs[input_index]
            user_embedding = model.encode([user_input], convert_to_numpy=True)

            scores = []

            for cv, emb in cv_embeddings.items():
                sim = cosine_similarity(user_embedding, emb)[0][0]
                scores.append({
                    "cv": cv,
                    "name": extract_name_from_filename(cv),
                    "score": float(sim)
                })

            scores.sort(key=lambda x: x["score"], reverse=True)
            top_results = scores[:TOP_K]

            # Append under same log (Cloud Services / Input section)
            updated_lines.append("\nTop Matching CVs:\n\n")

            for idx, r in enumerate(top_results, start=1):
                updated_lines.append(f"{idx}. CV: {r['cv']}\n")
                updated_lines.append(f"   Candidate Name: {r['name']}\n")
                updated_lines.append(f"   Similarity to Input: {r['score']:.3f}\n\n")

            input_index += 1

    # Write timestamped output
    with open(output_file, "w", encoding="utf-8") as f:
        f.writelines(updated_lines)

    print(f"✅ Updated TXT saved to: {output_file}\n")

# =========================
# MAIN PROGRAM
# =========================
def main():
    global loading

    print("\n🔍 CV Matching Enhancer\n")

    user_name = safe_input("Enter user name:\n> ").strip()
    if not user_name:
        safe_exit("❌ Name cannot be empty.")

    txt_file = upload_txt_file()

    cv_folder, cv_files = get_cv_files(user_name)

    print(f"\n📂 Found {len(cv_files)} CV(s)\n")

    # Load model
    loading = True
    t = threading.Thread(target=loading_dots, args=("Loading model",))
    t.start()

    model = SentenceTransformer("all-MiniLM-L6-v2")

    loading = False
    t.join()

    # Append CV matching into TXT and save timestamped version
    append_cv_matching_to_txt(txt_file, user_name, model, cv_folder, cv_files)

    print("📊 CV matching appended successfully.\n")


# =========================
# RUN
# =========================
if __name__ == "__main__":
    main()