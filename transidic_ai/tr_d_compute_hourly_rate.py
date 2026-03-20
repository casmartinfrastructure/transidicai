import os
import csv
import re
from datetime import datetime
import tkinter as tk
from tkinter import filedialog

# -----------------------
# CONFIG
# -----------------------
USERS_FOLDER = "users"

# -----------------------
# UTILITIES
# -----------------------
def normalize_name(name):
    return name.strip().lower()

def get_salary_info(name, salary_file_path):
    if not os.path.exists(salary_file_path):
        return None, None
    with open(salary_file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if normalize_name(row['Name']) == normalize_name(name):
                return float(row['MonthlySalary']), float(row['MonthlyHours'])
    return None, None

def calculate_hourly_rate(similarity, salary, hours):
    if hours == 0:
        return 0
    return (similarity * salary) / hours

# -----------------------
# FILE PICKER
# -----------------------
def pick_file(file_type_description, file_extension):
    """Open file dialog and ensure correct file type"""
    root = tk.Tk()
    
    # Force window to front
    root.withdraw()
    root.attributes('-topmost', True)
    root.update()
    
    file_path = filedialog.askopenfilename(
        parent=root,
        title=f"Select {file_type_description}",
        filetypes=[(file_type_description, f"*{file_extension}")]
    )

    root.destroy()  # Cleanly close root window

    if not file_path:
        print("❌ No file selected. Exiting.")
        exit()

    if not file_path.lower().endswith(file_extension):
        print(f"❌ Invalid file selected. Expected {file_extension}")
        exit()

    print(f"✅ Selected: {file_path}\n")
    return file_path

# -----------------------
# MAIN PROCESS
# -----------------------
def process_logs(username, salary_csv_path, input_file):

    # User folder
    user_folder = os.path.join(USERS_FOLDER, username)
    if not os.path.exists(user_folder):
        print(f"❌ User folder '{user_folder}' not found.")
        return

    # Create hourly_rates folder
    hourly_rates_folder = os.path.join(user_folder, "hourly_rates")
    os.makedirs(hourly_rates_folder, exist_ok=True)

    # Timestamped output file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(
        hourly_rates_folder,
        f"{username}_hourly_rates_{timestamp}.txt"
    )

    # Read input file
    with open(input_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Split logs
    logs = re.split(r'(#{5,}Log\d+#{5,})', content)
    new_content = ""

    # Header
    header = (
        "THE EVERYTHING APP\n"
        "Developed by : Transidic Studio\n"
        "Cloud Service Employed : Code++\n\n"
    )
    new_content += header

    # Process logs
    for i in range(1, len(logs), 2):
        log_header = logs[i]
        log_body = logs[i + 1]

        new_content += log_header + "\n"

        body_lines = log_body.splitlines()
        updated_body = []
        j = 0

        while j < len(body_lines):
            line = body_lines[j]
            updated_body.append(line)

            candidate_match = re.match(r'\s*Candidate Name:\s*(.+)', line)
            if candidate_match:
                candidate_name = candidate_match.group(1).strip()

                similarity_line = body_lines[j + 1] if j + 1 < len(body_lines) else ""
                similarity_match = re.search(r'Similarity to Input:\s*([0-9.]+)', similarity_line)

                if similarity_match:
                    similarity = float(similarity_match.group(1))
                    salary, hours = get_salary_info(candidate_name, salary_csv_path)

                    if salary is not None and hours is not None:
                        hourly_rate = calculate_hourly_rate(similarity, salary, hours)
                        updated_body.append(f"   Hourly rate ${hourly_rate:.2f}/hour")
                    else:
                        updated_body.append(f"   Hourly rate $0.00/hour")

            j += 1

        new_content += "\n".join(updated_body) + "\n\n"

    # Write output
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"✅ New hourly rates file created: {output_file}")

# -----------------------
# RUN
# -----------------------
if __name__ == "__main__":
    print("\n========== HOURLY RATE PROCESSOR ==========\n")

    # Username
    username = input("👤 Enter the username: ").strip()
    if not username:
        print("❌ Username cannot be empty.")
        exit()

    # STEP 1 - CSV
    print("\n📥 STEP 1: Please upload the SALARY CSV file.")
    print("👉 A file window will open now...\n")
    salary_csv_path = pick_file("CSV Files", ".csv")

    # STEP 2 - TXT
    print("\n📥 STEP 2: Please upload the CV MATCHING TXT file.")
    print("👉 A file window will open now...\n")
    input_file = pick_file("Text Files", ".txt")

    print("\n🚀 Processing...\n")

    process_logs(username, salary_csv_path, input_file)