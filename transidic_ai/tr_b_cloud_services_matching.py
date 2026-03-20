import os
import csv
import json
import sys
import re
import numpy as np
from datetime import datetime
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import tkinter as tk
from tkinter import filedialog
import threading
import time


# ---------------- Loading Animation ----------------
loading = False

def loading_dots(message="Loading"):
    i = 0
    while loading:
        dots = "." * (i % 4)
        print(f"\r{message}{dots}   ", end="")
        time.sleep(0.5)
        i += 1
    print("\r", end="")


# ---------------- Safe input ----------------
def safe_input(prompt):
    try:
        return input(prompt)
    except KeyboardInterrupt:
        print("\nSession cancelled.")
        sys.exit(0)


# ---------------- Auto Correct Numbering ----------------
def auto_correct_numbering(file_path):
    if not os.path.exists(file_path):
        return

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    corrected_lines = []
    log_counter = 1

    for line in lines:
        if line.startswith("#############Log"):
            corrected_line = f"#############Log{log_counter}###########\n"
            corrected_lines.append(corrected_line)
            log_counter += 1
        else:
            corrected_lines.append(line)

    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(corrected_lines)

    print("🔄 Log numbering automatically corrected.\n")


# ---------------- Load cloud services and embeddings ----------------
def load_cloud_services(csv_path, model, user_name):

    user_folder = os.path.join("users", user_name)
    matches_folder = os.path.join(user_folder, "cloud_services_matches")
    os.makedirs(matches_folder, exist_ok=True)

    embeddings_path = os.path.join(matches_folder, "cloud_services_embeddings.json")

    if os.path.exists(embeddings_path):
        print("Loading precomputed cloud service embeddings...")
        with open(embeddings_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        cloud_services = data["services"]
        cloud_embeddings = np.array(data["embeddings"])
        return cloud_services, cloud_embeddings

    print("Computing cloud service embeddings...")

    global loading
    loading = True
    t = threading.Thread(target=loading_dots, args=("Computing embeddings",))
    t.start()

    cloud_services = []
    cloud_texts = []

    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            text = f"{row['Name']}: {row['Description']}"
            cloud_services.append(row['Name'])
            cloud_texts.append(text)

    cloud_embeddings = model.encode(cloud_texts, convert_to_numpy=True)

    loading = False
    t.join()

    save_data = {
        "services": cloud_services,
        "embeddings": cloud_embeddings.tolist()
    }

    with open(embeddings_path, "w", encoding="utf-8") as f:
        json.dump(save_data, f)

    print(f"Saved cloud embeddings to '{embeddings_path}'")
    return cloud_services, cloud_embeddings


# ---------------- Load user TXT inputs ----------------
def load_user_inputs(name):
    person_folder = os.path.join("users", name)
    os.makedirs(person_folder, exist_ok=True)

    root = tk.Tk()
    root.withdraw()
    root.overrideredirect(True)
    root.attributes('-topmost', True)

    txt_file_path = filedialog.askopenfilename(
        title="Select a TXT file",
        filetypes=[("Text Files", "*.txt")]
    )

    root.destroy()

    if not txt_file_path:
        print("No file selected. Exiting.")
        sys.exit(0)

    inputs = []
    input_timestamps = []

    current_date = None
    current_time = None

    with open(txt_file_path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()

            if stripped.startswith("Date:"):
                current_date = stripped.replace("Date:", "").strip()
            elif stripped.startswith("Time:"):
                current_time = stripped.replace("Time:", "").strip()
            elif stripped.startswith("Input:"):
                text = stripped.replace("Input:", "").strip()
                inputs.append(text)
                if current_date and current_time:
                    ts = f"{current_date} {current_time}"
                else:
                    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                input_timestamps.append(ts)
                current_date = None
                current_time = None

    return txt_file_path, inputs, input_timestamps


# ---------------- Match user inputs ----------------
def match_inputs_to_cloud_services(user_inputs, cloud_services, cloud_embeddings, model):
    input_embeddings = model.encode(user_inputs, convert_to_numpy=True)
    sims = cosine_similarity(input_embeddings, cloud_embeddings)

    matches = []

    for i, text in enumerate(user_inputs):
        best_idx = sims[i].argmax()
        matches.append({
            "input": text,
            "best_cloud_service": cloud_services[best_idx],
            "similarity": float(sims[i][best_idx])
        })

    return matches


# ---------------- Annotate + SAVE IN MATCHES FOLDER ----------------
def annotate_and_save_txt(txt_file, user_name, matches):

    matching_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    user_folder = os.path.join("users", user_name)
    matches_folder = os.path.join(user_folder, "cloud_services_matches")
    os.makedirs(matches_folder, exist_ok=True)

    # Create timestamped filename
    timestamp = datetime.now().strftime("%Y-%m-%d__%Hh-%Mm-%Ss")
    output_file = os.path.join(matches_folder, f"{timestamp}.txt")

    with open(txt_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    new_lines = []
    match_idx = 0

    for line in lines:
        new_lines.append(line)

        if line.strip().startswith("Input:") and match_idx < len(matches):
            m = matches[match_idx]

            new_lines.append(f"Matching Timestamp: {matching_timestamp}\n")
            new_lines.append(f"Matched Cloud Service: {m['best_cloud_service']}\n")
            new_lines.append(f"Similarity: {m['similarity']:.3f}\n\n")

            match_idx += 1

    with open(output_file, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    print(f"✅ Updated TXT saved to '{output_file}'\n")

    auto_correct_numbering(output_file)


# ---------------- Save matches JSON ----------------
def save_matches_json(user_name, matches):
    user_folder = os.path.join("users", user_name)
    cloud_services_folder = os.path.join(user_folder, "cloud_services")
    os.makedirs(cloud_services_folder, exist_ok=True)

    output_json = os.path.join(cloud_services_folder, f"{user_name}_cloud_matches.json")

    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(matches, f, indent=2)

    print(f"✅ Matches saved to '{output_json}'\n")


# ---------------- Main ----------------
def main():
    global loading

    print("Loading Sentence Transformer model (this happens once)...")

    loading = True
    t = threading.Thread(target=loading_dots, args=("Loading model",))
    t.start()

    model = SentenceTransformer("all-MiniLM-L6-v2")

    loading = False
    t.join()

    user_name = safe_input("Enter the user name: ").strip()

    cloud_csv = os.path.join("cloud_services", "cloud_services.csv")
    cloud_services, cloud_embeddings = load_cloud_services(cloud_csv, model, user_name)

    txt_file, user_inputs, input_timestamps = load_user_inputs(user_name)

    print(f"\nLoaded {len(user_inputs)} input(s) from '{txt_file}'\n")

    matches = match_inputs_to_cloud_services(
        user_inputs,
        cloud_services,
        cloud_embeddings,
        model
    )

    save_matches_json(user_name, matches)

    # ✅ In-place enrichment + save into cloud_services_matches folder
    annotate_and_save_txt(txt_file, user_name, matches)

    print(f"--- Matches for user '{user_name}' ---\n")
    for idx, m in enumerate(matches, start=1):
        print(f"{idx}. Input: {m['input']}")
        print(f"   Matched Cloud Service: {m['best_cloud_service']}")
        print(f"   Similarity Score: {m['similarity']:.3f}\n")


# ---------------- Run ----------------
if __name__ == "__main__":
    main()