import os
from tkinter import Tk, filedialog
from shutil import copyfile

# ==============================
# FILE UPLOAD WITH VISIBLE BUTTON
# ==============================
def select_file(title, extension=".png"):
    root = Tk()
    root.title("Select File")
    root.geometry("400x120")
    root.lift()
    root.attributes('-topmost', True)
    root.focus_force()

    from tkinter import Button, Label
    file_path = {"path": ""}

    def open_dialog():
        path = filedialog.askopenfilename(
            parent=root,
            title=title,
            filetypes=[("PNG Files", f"*{extension}")]
        )
        file_path["path"] = path
        root.quit()

    Label(root, text=title).pack(pady=10)
    Button(root, text="Select File", command=open_dialog, width=20).pack(pady=5)

    root.mainloop()
    root.destroy()
    return file_path["path"]

# ==============================
# MAIN PROGRAM
# ==============================
def main():
    # Ask for username
    user_name = input("Enter your username: ").strip()
    if not user_name:
        print("❌ Username cannot be empty. Exiting.")
        return

    # Base folder for all users
    base_folder = "users"
    user_folder = os.path.join(base_folder, user_name)
    logo_folder = os.path.join(user_folder, "logo")
    os.makedirs(logo_folder, exist_ok=True)

    # Upload logo
    print("Upload your logo (PNG file)")
    logo_path = select_file("Select PNG Logo")

    if not logo_path:
        print("❌ No file selected. Exiting.")
        return

    # Save logo in user's logo folder
    logo_filename = os.path.basename(logo_path)
    destination_path = os.path.join(logo_folder, logo_filename)
    copyfile(logo_path, destination_path)

    print(f"✅ Logo saved to: {destination_path}")

if __name__ == "__main__":
    main()