import os
from datetime import datetime
import re
import sys

def confirm_exit():
    choice = input("\n⚠ Do you really want to exit? (yes/no): ").strip().lower()
    return choice in ("yes", "y")

def safe_input(prompt):
    while True:
        try:
            return input(prompt)
        except KeyboardInterrupt:
            print("\n")
            if confirm_exit():
                print("\n❌ Session exited by user.")
                sys.exit(0)
            print("\n✔ Continuing session...\n")
        except EOFError:
            print("\n")
            if confirm_exit():
                print("\n❌ Session exited by user.")
                sys.exit(0)
            print("\n✔ Continuing session...\n")

def get_user_input():
    print("Welcome to Transidic Ai!\n")

    user_name = safe_input("Please enter your name: \n> ").strip().capitalize()

    # =========================
    # CREATE USER LOG FOLDER (UPDATED)
    # =========================
    base_folder = "users"
    user_folder = os.path.join(base_folder, user_name)
    logs_folder = os.path.join(user_folder, f"{user_name}_logs")

    os.makedirs(logs_folder, exist_ok=True)

    # =========================
    # READ ALL EXISTING FILES (FOR DISPLAY ONLY)
    # =========================
    existing_inputs = []
    log_header_pattern = re.compile(r"#############Log(\d+)###########")

    for filename in os.listdir(logs_folder):
        if filename.endswith(".txt"):
            with open(os.path.join(logs_folder, filename), "r") as f:
                lines = f.readlines()
                for line in lines:
                    if line.startswith("Input:"):
                        existing_inputs.append(line.replace("Input:", "").strip())

    print(f"\nThere are currently {len(existing_inputs)} input(s):")
    for idx, item in enumerate(existing_inputs, start=1):
        print(f"{idx}. {item}")

    print("\n✔ Numbering check skipped (separate files mode).")

    # ==============================
    # MULTI-INPUT COLLECTION
    # ==============================
    new_inputs = []

    print("\nStart adding inputs.")

    input_counter = 1
    while True:
        user_input = safe_input(f"\nEnter input #{input_counter}:\n> ").strip()

        if user_input.lower() == "exit":
            if confirm_exit():
                print("\n❌ Input session cancelled.")
                return
            continue

        if user_input == "":
            print("⚠ Input cannot be empty.")
            continue

        new_inputs.append(user_input)
        input_counter += 1

        again = safe_input("\nAdd another input? (yes/no): ").strip().lower()
        if again not in ("yes", "y"):
            break

    print("\n======= INPUT SUMMARY =======")
    for idx, item in enumerate(new_inputs, start=1):
        print(f"{idx}. {item}")
    print("=============================\n")

    confirm = safe_input("Confirm and write these inputs to the file? (yes/no): ").strip().lower()
    if confirm not in ("yes", "y"):
        print("\n❌ Nothing was written to the file.")
        return

    # =========================
    # CREATE CLEAR TIMESTAMP
    # =========================
    timestamp = datetime.now().strftime("%Y-%m-%d__%Hh-%Mm-%Ss")

    file_path = os.path.join(logs_folder, f"{timestamp}.txt")

    # =========================
    # WRITE NEW FILE
    # =========================
    with open(file_path, "w") as f:
        f.write("TRANSIDIC AI\n")
        f.write("Developed by : Transidic Studio\n")
        f.write("Cloud Service Employed : Code++\n")
        f.write(f"User: {user_name}\n")
        f.write(f"Session: {timestamp}\n\n")

        log_number = 1
        for item in new_inputs:
            now = datetime.now()
            f.write(f"#############Log{log_number}###########\n")
            f.write(f"Date: {now.strftime('%Y-%m-%d')}\n")
            f.write(f"Time: {now.strftime('%H:%M:%S')}\n")
            f.write(f"Input: {item}\n\n")
            log_number += 1

    print(f"\n✔ {len(new_inputs)} input(s) successfully written.\n")
    print(f"Saved to: {file_path}")

# --- Run App ---
get_user_input()