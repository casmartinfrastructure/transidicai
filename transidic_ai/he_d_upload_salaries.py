import os
import sys
import csv

# ==========================
# SAFETY INPUT FUNCTIONS
# ==========================

def confirm_exit():
    choice = input("\n⚠ Do you really want to exit? (yes/no): ").strip().lower()
    return choice in ("yes", "y")

def safe_input(prompt):
    while True:
        try:
            return input(prompt)
        except (KeyboardInterrupt, EOFError):
            print("\n")
            if confirm_exit():
                print("\n❌ Session exited by user.")
                sys.exit(0)
            print("\n✔ Continuing session...\n")

def safe_float_input(prompt):
    while True:
        val = safe_input(prompt)
        try:
            return float(val)
        except ValueError:
            print("⚠ Please enter a valid number (integer or decimal).")

# ==========================
# MAIN APP
# ==========================

def record_monthly_salary():
    print("\n💰 Monthly Salary & Hours Recording System\n")
    print("ℹ Standard: 40 hours/week × 4.33 weeks/month ≈ 173.2 hours/month.\n")

    # ---------------- USER INPUT ----------------
    user_name = safe_input("Enter the user name:\n> ").strip()

    # ---------------- CV folder (UPDATED) ----------------
    user_folder = os.path.join("users", user_name)
    cv_folder = os.path.join(user_folder, "my_resources")

    if not os.path.exists(cv_folder):
        print(f"❌ CV folder '{cv_folder}' not found. Please upload CVs first.")
        sys.exit(0)

    cv_files = os.listdir(cv_folder)
    valid_names = [os.path.splitext(f)[0].replace("_", " ").title() for f in cv_files if f.lower().endswith((".pdf", ".docx", ".txt"))]

    if not valid_names:
        print(f"❌ No CV files found in '{cv_folder}'. Please upload CVs first.")
        sys.exit(0)

    # ---------------- CSV setup (UPDATED LOCATION) ----------------
    output_csv = os.path.join(cv_folder, "monthly_salaries.csv")

    existing_data = {}
    if os.path.exists(output_csv):
        with open(output_csv, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                name_key = row["Name"].lower()
                existing_data[name_key] = {
                    "MonthlySalary": row.get("MonthlySalary", ""),
                    "MonthlyHours": row.get("MonthlyHours", "")
                }

    # ---------------- Check for missing info ----------------
    missing_entries = [n for n in valid_names if n.lower() not in existing_data or not existing_data[n.lower()]["MonthlySalary"]]
    if missing_entries:
        print("⚠ The following CV names do not have salary/hours recorded yet:")
        print(", ".join(missing_entries))
    else:
        print("✅ All CVs have recorded salary/hour info.")
    print()

    # ---------------- Highlight all CVs with status ----------------
    print("📂 Current CV list and status:")
    for n in valid_names:
        key = n.lower()
        if key not in existing_data or not existing_data[key]["MonthlySalary"]:
            status = "❌ Missing info"
        else:
            status = f"✅ Salary: {existing_data[key]['MonthlySalary']}, Hours: {existing_data[key]['MonthlyHours']}"
        print(f"• {n}: {status}")
    print()

    # ---------------- Main input loop ----------------
    while True:
        name_input = safe_input("Enter the name of the person (as in CV filename):\n> ").strip().title()
        if name_input == "":
            print("⚠ Name cannot be empty.")
            continue

        if name_input not in valid_names:
            print(f"❌ The name '{name_input}' does not exist in the CVs folder. Please check and try again.\n")
            continue

        key = name_input.lower()
        if key in existing_data and existing_data[key]["MonthlySalary"]:
            print(f"⚠ Existing data found for {name_input}:")
            print(f"• Monthly Salary: {existing_data[key]['MonthlySalary']}")
            print(f"• Monthly Hours: {existing_data[key]['MonthlyHours']}")
            update = safe_input("Do you want to update it? (yes/no): ").strip().lower()
            if update not in ("yes", "y"):
                print("⏭ Skipping update for this person.\n")
                continue

        salary = safe_float_input(f"Enter the expected monthly salary for {name_input} (USD):\n> ")

        hours_prompt = f"Enter the expected monthly working hours for {name_input} [Standard: 173.2]:\n> "
        hours_input = safe_input(hours_prompt).strip()
        if hours_input == "":
            monthly_hours = 173.2
        else:
            try:
                monthly_hours = float(hours_input)
            except ValueError:
                print("⚠ Invalid number entered. Using standard 173.2 hours.")
                monthly_hours = 173.2

        print(f"\nYou entered:\n• Name: {name_input}\n• Expected Monthly Salary: {salary} USD\n• Monthly Hours: {monthly_hours}")
        confirm = safe_input("Do you want to save this entry? (yes/no): ").strip().lower()
        if confirm not in ("yes", "y"):
            print("❌ Entry discarded.\n")
            again = safe_input("Do you want to enter another entry? (yes/no): ").strip().lower()
            if again not in ("yes", "y"):
                if confirm_exit():
                    print("\n✔ Session finished safely.")
                    break
            continue

        existing_data[key] = {
            "MonthlySalary": salary,
            "MonthlyHours": monthly_hours
        }

        with open(output_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["Name", "MonthlySalary", "MonthlyHours"])
            writer.writeheader()
            for n, data in existing_data.items():
                writer.writerow({
                    "Name": n.title(),
                    "MonthlySalary": data["MonthlySalary"],
                    "MonthlyHours": data["MonthlyHours"]
                })

        print(f"\n✅ Entry saved successfully in '{output_csv}'.\n")

        remaining_missing = [n for n in valid_names if n.lower() not in existing_data or not existing_data[n.lower()]["MonthlySalary"]]
        if not remaining_missing:
            print("🎉 All CVs have salary/hour info recorded.\n")

        again = safe_input("Do you want to enter another salary/hour? (yes/no): ").strip().lower()
        if again not in ("yes", "y"):
            if confirm_exit():
                print("\n✔ Session finished safely.")
                break


# ==========================
# RUN PROGRAM
# ==========================

if __name__ == "__main__":
    record_monthly_salary()