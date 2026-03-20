import os
import csv
import secrets
from datetime import datetime

# ---------------- Generate short, clean encryption key ----------------
def generate_short_key(username):
    # Take first 2 letters of username (uppercase)
    prefix = username[:2].upper()
    # Generate 5-character alphanumeric string (letters + numbers, no ambiguous chars)
    rand_str = ''.join(secrets.choice('ABCDEFGHJKLMNPQRSTUVWXYZ23456789') for _ in range(5))
    return f"{prefix}-{rand_str}"

# ---------------- Main user creation function ----------------
def create_user():
    # ---------------- GET USER NAME ----------------
    user_name = input("Enter user name:\n> ").strip()
    if not user_name:
        print("❌ User name cannot be empty.")
        return

    # ---------------- CREATE BASE FOLDER ----------------
    base_folder = "users"
    os.makedirs(base_folder, exist_ok=True)

    # ---------------- CREATE USER FOLDER ----------------
    user_folder = os.path.join(base_folder, user_name)
    os.makedirs(user_folder, exist_ok=True)

    # ---------------- GENERATE UNIQUE ID ----------------
    user_id = secrets.token_hex(4)  # short unique ID (8 hex characters)

    # ---------------- GENERATE CLEAN SHORT ENCRYPTION KEY ----------------
    encryption_key = generate_short_key(user_name)

    # ---------------- CREATE USER DETAILS FILE ----------------
    # Now filename is based on encryption key
    user_file_path = os.path.join(user_folder, f"{encryption_key}.txt")
    with open(user_file_path, "w") as f:
        f.write("USER DETAILS\n")
        f.write("=====================\n")
        f.write(f"Name: {user_name}\n")
        f.write(f"Unique ID: {user_id}\n")
        f.write(f"Encryption Key: {encryption_key}\n")
        f.write(f"Created At: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # ---------------- CREATE / UPDATE MASTER CSV ----------------
    master_csv_path = os.path.join(base_folder, "master_log.csv")
    file_exists = os.path.isfile(master_csv_path)

    with open(master_csv_path, "a", newline="") as f:
        writer = csv.writer(f)
        # Write header if CSV is new
        if not file_exists:
            writer.writerow(["Name", "Unique ID", "Encryption Key", "Created At"])
        writer.writerow([
            user_name,
            user_id,
            encryption_key,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ])

    # ---------------- SUCCESS MESSAGE ----------------
    print("\n✅ User successfully created!")
    print(f"📁 Folder: {user_folder}")
    print(f"📄 User details saved in: {user_file_path}")
    print(f"📊 Master log updated: {master_csv_path}")
    print(f"🔑 Generated Key: {encryption_key}")

# ---------------- RUN ----------------
if __name__ == "__main__":
    create_user()