import os
import sys
import numpy as np
import re
import threading
import time

from datetime import datetime
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
from PyPDF2 import PdfReader
from docx import Document
import tkinter as tk
from tkinter import filedialog

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

def extract_name_from_filename(filename):
    base = os.path.splitext(filename)[0]
    return base.replace("_", " ").title()

def clean_text(text):
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return " ".join(lines)

# =========================
# EXPERIENCE ESTIMATION
# =========================
def estimate_experience(cv_text):
    text = cv_text.lower()

    years = re.findall(r"(\d+)\+?\s*(years|yrs)", text)
    if years:
        max_years = max([int(y[0]) for y in years])
        if max_years <= 2:
            return "junior"
        elif max_years <= 5:
            return "mid"
        else:
            return "senior"

    if "senior" in text or "lead" in text or "architect" in text:
        return "senior"
    if "junior" in text or "intern" in text:
        return "junior"

    return "mid"

def get_experience_factor(level):
    return {
        "junior": 1.4,
        "mid": 1.1,
        "senior": 0.85
    }[level]

# =========================
# TASK COMPLEXITY
# =========================
def estimate_task_complexity(text):
    text = text.lower()

    high_keywords = ["design", "architecture", "build system", "deploy", "ml", "ai", "research"]
    medium_keywords = ["implement", "develop", "api", "integration", "optimize"]

    score = 0

    for k in high_keywords:
        if k in text:
            score += 2

    for k in medium_keywords:
        if k in text:
            score += 1

    if score >= 4:
        return "high"
    elif score >= 2:
        return "medium"
    return "low"

def base_hours(level):
    return {
        "low": 4,
        "medium": 12,
        "high": 40
    }[level]

# =========================
# FILE LOADER
# =========================
def upload_txt_file():
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)

    file_path = filedialog.askopenfilename(
        title="Select TXT File",
        filetypes=[("Text Files", "*.txt")]
    )

    root.destroy()

    if not file_path:
        safe_exit("❌ No file selected.")

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
# MAIN FUNCTION (YOUR LOGIC)
# =========================
def append_cv_matching_to_txt(original_txt, user_name, model, cv_folder, cv_files):

    man_hours_folder = os.path.join("users", user_name, "man_hours")

    os.makedirs(man_hours_folder, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d__%Hh-%Mm-%Ss")

    man_hours_file = os.path.join(man_hours_folder, f"{timestamp}.txt")

    with open(original_txt, "r", encoding="utf-8") as f:
        lines = f.readlines()

    final_lines = []
    user_inputs = []

    for line in lines:
        final_lines.append(line)
        if line.strip().startswith("Input:"):
            user_inputs.append(line.replace("Input:", "").strip())

    # -----------------------------
    # PRECOMPUTE CV EMBEDDINGS
    # -----------------------------
    cv_embeddings = {}

    for cv in cv_files:
        cv_path = os.path.join(cv_folder, cv)
        cv_text = load_cv_text(cv_path)

        if cv_text and len(cv_text) >= MIN_CV_LENGTH:
            cv_embeddings[cv] = model.encode([cv_text], convert_to_numpy=True)

    updated_lines = []
    man_hours_output = []

    input_index = 0

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

            updated_lines.append("\nTop Matching CVs:\n\n")
            man_hours_output.append(
                f"\n================ INPUT ================\n{user_input}\n"
            )

            for idx, r in enumerate(top_results, start=1):

                cv_path = os.path.join(cv_folder, r["cv"])
                cv_text = load_cv_text(cv_path)

                exp_level = estimate_experience(cv_text)
                exp_factor = get_experience_factor(exp_level)

                task_level = estimate_task_complexity(user_input)
                base = base_hours(task_level)

                sim = r["score"]

                skill_factor = 1 + (1 - sim)

                estimated_hours = base * skill_factor * exp_factor

                updated_lines.append(f"{idx}. CV: {r['cv']}\n")
                updated_lines.append(f"   Candidate Name: {r['name']}\n")
                updated_lines.append(f"   Similarity: {sim:.3f}\n\n")

                man_hours_output.append(
                    f"{idx}. {r['name']} ({r['cv']})\n"
                    f"   Match Score: {sim:.3f}\n"
                    f"   Experience Level: {exp_level}\n"
                    f"   Task Complexity: {task_level}\n"
                    f"   Estimated Hours: {estimated_hours:.2f} hrs\n\n"
                )

            input_index += 1

    with open(man_hours_file, "w", encoding="utf-8") as f:
        f.writelines(man_hours_output)

    print(f"⏱️ Man Hours saved: {man_hours_file}")
# =========================
# MAIN PROGRAM
# =========================
def main():

    print("\n🔍 CV Matching + Man Hours System\n")

    user_name = input("Enter user name:\n> ").strip()
    if not user_name:
        safe_exit("❌ Username required.")

    txt_file = upload_txt_file()

    cv_folder, cv_files = get_cv_files(user_name)

    print(f"\n📂 Found {len(cv_files)} CVs")

    print("Loading model...")
    model = SentenceTransformer("all-MiniLM-L6-v2")

    append_cv_matching_to_txt(txt_file, user_name, model, cv_folder, cv_files)

    print("\n✅ Done.")

# =========================
# RUN
# =========================
if __name__ == "__main__":
    main()