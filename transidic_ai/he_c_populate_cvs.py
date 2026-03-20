import os
import sys
import shutil
import tkinter as tk
from tkinter import filedialog


# ---------------- Safe input ----------------
def safe_input(prompt):
    try:
        return input(prompt)
    except KeyboardInterrupt:
        print("\nSession cancelled.")
        sys.exit(0)


# ---------------- CV Upload Function ----------------
def upload_user_cvs(user_name):
    user_folder = os.path.join("users", user_name)
    resources_folder = os.path.join(user_folder, "my_resources")

    os.makedirs(resources_folder, exist_ok=True)

    while True:
        # Create clean popup (same style as your original)
        root = tk.Tk()
        root.withdraw()
        root.overrideredirect(True)
        root.attributes('-topmost', True)

        file_path = filedialog.askopenfilename(
            title="Select a CV",
            filetypes=[
                ("PDF files", "*.pdf"),
                ("Word Documents", "*.docx"),
                ("All Files", "*.*")
            ]
        )

        root.destroy()

        if not file_path:
            print("No file selected.")
        else:
            filename = os.path.basename(file_path)
            destination = os.path.join(resources_folder, filename)

            # Prevent overwriting files
            base, ext = os.path.splitext(filename)
            counter = 1
            while os.path.exists(destination):
                destination = os.path.join(resources_folder, f"{base}_{counter}{ext}")
                counter += 1

            shutil.copy(file_path, destination)
            print(f"✅ CV saved to: {destination}")

        another = safe_input("Do you want to upload another CV? (y/n): ").strip().lower()
        if another != 'y':
            break


# ---------------- Main ----------------
def main():
    user_name = safe_input("Enter the user name: ").strip()

    upload_user_cvs(user_name)

    print("\n✅ All CVs uploaded successfully.")


# ---------------- Run ----------------
if __name__ == "__main__":
    main()