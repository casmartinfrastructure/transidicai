import os
import csv
import sys

# ---------------- Safe input functions ----------------
def confirm_exit():
    choice = input("\n⚠ Do you really want to exit? (yes/no): ").strip().lower()
    return choice in ("yes", "y")

def safe_input(prompt, multiline=False):
    """
    If multiline=True, input ends when the user enters an empty line.
    """
    while True:
        try:
            if not multiline:
                return input(prompt)
            else:
                print(prompt + " (Press Enter twice to finish):")
                lines = []
                while True:
                    line = input()
                    if line == "":
                        break
                    lines.append(line)
                return " ".join(lines)
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

# ---------------- Populate Cloud Services Function ----------------
def populate_cloud_services():
    print("Welcome to Cloud Services Manager!\n")

    # =========================
    # GET USER NAME (NEW)
    # =========================
    user_name = safe_input("Please enter your name:\n> ").strip().capitalize()

    # =========================
    # CREATE USER CLOUD FOLDER (UPDATED)
    # =========================
    base_folder = "users"
    user_folder = os.path.join(base_folder, user_name)
    folder_path = os.path.join(user_folder, "cloud_services")

    os.makedirs(folder_path, exist_ok=True)

    csv_path = os.path.join(folder_path, "cloud_services.csv")

    # Create CSV if it doesn't exist, with headers
    if not os.path.isfile(csv_path):
        with open(csv_path, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Name", "Description"])
        print(f"✔ Created new CSV at '{csv_path}' with headers.\n")
    else:
        print(f"✔ CSV found at '{csv_path}'.\n")

    # Display existing cloud services
    print("Existing cloud services:\n")
    with open(csv_path, mode='r', newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        for idx, row in enumerate(reader):
            if idx == 0:  # skip header
                continue
            print(f"{idx}. Name: {row[0]}, Description: {row[1]}")
    print("\n")

    # ---------------- Adding new entries ----------------
    print("Start adding cloud services.\n")
    new_entries = []

    while True:
        name = safe_input("Enter Cloud Service Name:\n> ").strip()
        if name.lower() == "exit":
            if confirm_exit():
                print("\n❌ Input session cancelled.")
                break
            continue
        if not name:
            print("⚠ Name cannot be empty.")
            continue

        # Allow multiline descriptions
        description = safe_input("Enter Cloud Service Description:", multiline=True).strip()
        if description.lower() == "exit":
            if confirm_exit():
                print("\n❌ Input session cancelled.")
                break
        if not description:
            print("⚠ Description cannot be empty.")
            continue

        new_entries.append([name, description])
        again = safe_input("\nAdd another cloud service? (yes/no): ").strip().lower()
        if again not in ("yes", "y"):
            break

    if not new_entries:
        print("\n❌ No new entries added. Exiting.")
        return

    # ---------------- Confirm & write ----------------
    print("\n======= NEW ENTRIES =======")
    for idx, entry in enumerate(new_entries, start=1):
        print(f"{idx}. Name: {entry[0]}, Description: {entry[1]}")
    print("===========================\n")

    confirm = safe_input("Confirm and write these entries to the CSV? (yes/no): ").strip().lower()
    if not confirm.startswith("y"):
        print("\n❌ Entries not written. Exiting.")
        return

    # Append to CSV
    with open(csv_path, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(new_entries)

    print(f"\n✔ {len(new_entries)} cloud service(s) successfully written to '{csv_path}'.\n")

# ---------------- Run the function ----------------
if __name__ == "__main__":
    populate_cloud_services()