with open("c:/GitHub/Siti/aiconsultingitalia/panel/panel_cutmob/api.php", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if "$download_link" in line:
        print(f"Line {idx+1}: {line.strip()}")
