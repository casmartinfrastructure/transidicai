import re
import os
from tkinter import Tk, filedialog
from datetime import datetime

# ==============================
# FILE UPLOAD WITH VISIBLE BUTTON
# ==============================
def select_file(title):
    root = Tk()
    root.title("Select File")
    root.geometry("400x120")
    root.lift()
    root.attributes('-topmost', True)
    root.focus_force()

    from tkinter import Button, Label
    file_path = {"path": ""}

    def open_dialog():
        file_path["path"] = filedialog.askopenfilename(
            parent=root,
            title=title,
            filetypes=[("Text Files", "*.txt")]
        )
        root.quit()

    Label(root, text=title).pack(pady=10)
    Button(root, text="Select File", command=open_dialog, width=20).pack(pady=5)

    root.mainloop()
    root.destroy()
    return file_path["path"]

# ==============================
# SPLIT LOG BLOCKS
# ==============================
def split_logs(content):
    pattern = r"(#############Log\d+###########.*?)(?=#############Log\d+###########|$)"
    return re.findall(pattern, content, re.DOTALL)

# ==============================
# EXTRACT CLOUD SERVICE INFO
# ==============================
def extract_cloud_info(log):
    service = re.search(r"Matched Cloud Service:\s*(.*)", log)
    similarity = re.search(r"Similarity:\s*(.*)", log)
    timestamp = re.search(r"Matching Timestamp:\s*(.*)", log)
    user_input = re.search(r"Input:\s*(.*)", log)

    return {
        "input": user_input.group(1).strip() if user_input else "",
        "service": service.group(1).strip() if service else "",
        "similarity": float(similarity.group(1).strip()) * 100 if similarity else 0.0,
        "timestamp": timestamp.group(1).strip() if timestamp else ""
    }

# ==============================
# EXTRACT CV INFO
# ==============================
def extract_cv_info(log):
    candidates = re.findall(
        r"Candidate Name:\s*(.*?)\n\s*Hourly rate\s*\$(.*?)/hour\s*\n\s*Similarity to Input:\s*(.*)",
        log
    )
    return [
        {"name": c[0], "rate": c[1], "similarity": float(c[2]) * 100 if c[2] else 0.0}
        for c in candidates
    ]

# ==============================
# CREATE ORGANOGRAM (UNCHANGED)
# ==============================
def create_organogram(user_name, cloud_service, cloud_similarity, candidates, log_number):
    while len(candidates) < 3:
        candidates.append({"name": "N/A", "rate": "0", "similarity": 0.0})

    c1, c2, c3 = candidates[:3]
    width = 40
    sep = "|"
    arrow = "↑↓"

    prob1 = cloud_similarity + c1['similarity']
    prob2 = cloud_similarity + c2['similarity']
    prob3 = cloud_similarity + c3['similarity']

    offer1 = f"{c1['name']} @ ${c1['rate']}/hr ({c1['similarity']:.1f}%)"
    offer2 = f"{c2['name']} @ ${c2['rate']}/hr ({c2['similarity']:.1f}%)"
    offer3 = f"{c3['name']} @ ${c3['rate']}/hr ({c3['similarity']:.1f}%)"

    org = "\n================= ORGANOGRAM =================\n\n"
    org += (
        f"{'Offer 1'.center(width)}{sep}"
        f"{'Offer 2'.center(width)}{sep}"
        f"{'Offer 3'.center(width)}\n"
    )
    org += (
        f"(Prob. Success = {cloud_similarity:.1f} + {c1['similarity']:.1f} = {prob1:.1f}%)".center(width) + sep +
        f"(Prob. Success = {cloud_similarity:.1f} + {c2['similarity']:.1f} = {prob2:.1f}%)".center(width) + sep +
        f"(Prob. Success = {cloud_similarity:.1f} + {c3['similarity']:.1f} = {prob3:.1f}%)".center(width) + "\n"
    )
    org += (
        f"Hourly Rate = ${c1['rate']}/hr".center(width) + sep +
        f"Hourly Rate = ${c2['rate']}/hr".center(width) + sep +
        f"Hourly Rate = ${c3['rate']}/hr".center(width) + "\n"
    )
    org += "-" * ((width + 1) * 3 - 1) + "\n"

    org += (
        f"{user_name.center(width)}{sep}"
        f"{user_name.center(width)}{sep}"
        f"{user_name.center(width)}\n"
    )
    org += (
        f"{arrow.center(width)}{sep}"
        f"{arrow.center(width)}{sep}"
        f"{arrow.center(width)}\n"
    )

    cloud_text = f"{cloud_service} ({cloud_similarity:.1f}%)"
    org += (
        f"{cloud_text.center(width)}{sep}"
        f"{cloud_text.center(width)}{sep}"
        f"{cloud_text.center(width)}\n"
    )
    org += (
        f"{arrow.center(width)}{sep}"
        f"{arrow.center(width)}{sep}"
        f"{arrow.center(width)}\n"
    )

    org += (
        f"{offer1.center(width)}{sep}"
        f"{offer2.center(width)}{sep}"
        f"{offer3.center(width)}\n"
    )
    org += "-" * ((width + 1) * 3 - 1) + "\n"

    return org

# ==============================
# MAIN PROGRAM
# ==============================
def main():
    user_name = input("Enter your username: ").strip()
    if not user_name:
        print("No username provided. Exiting.")
        return

    print("Upload TXT File (Combined Logs)")
    file_path = select_file("Select TXT File")

    if not file_path:
        print("File not selected.")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    logs = split_logs(content)

    # ✅ CHANGED: base folder now "users"
    base_folder = "users"
    person_folder = os.path.join(base_folder, user_name)
    broad_proposal_folder = os.path.join(person_folder, "broad_proposals")
    os.makedirs(broad_proposal_folder, exist_ok=True)

    # ✅ Always new timestamp file
    timestamp_file = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_output = os.path.join(
        broad_proposal_folder,
        f"{user_name}_broad_proposal_{timestamp_file}.txt"
    )

    with open(file_output, "w", encoding="utf-8") as f:
        f.write("THE EVERYTHING APP\n")
        f.write("Developed by : Transidic Studio\n")
        f.write("Cloud Service Employed : Code++\n\n")

        for i, log in enumerate(logs):
            cloud = extract_cloud_info(log)
            cvs = extract_cv_info(log)

            organogram = create_organogram(
                user_name,
                cloud["service"],
                cloud["similarity"],
                cvs,
                i + 1
            )

            text = f"""
#############Log{i+1}###########
Input:
{cloud['input']}

Matching Timestamp: {cloud['timestamp']}
Matched Cloud Service: {cloud['service']}
Similarity: {cloud['similarity']:.1f}%

Top Matching CVs:
"""
            for idx, c in enumerate(cvs, 1):
                text += f"""
{idx}. Candidate Name: {c['name']}
   Hourly rate ${c['rate']}/hour
   Similarity to Input: {c['similarity']:.1f}%
"""

            text += organogram
            f.write(text)
            f.write(f"\n--- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n\n")

    print("✅ Done.")
    print("Saved to:", file_output)

if __name__ == "__main__":
    main()