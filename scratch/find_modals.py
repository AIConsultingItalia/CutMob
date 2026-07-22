with open("c:/GitHub/Siti/aiconsultingitalia/panel/panel_cutmob/index.php", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if "openClientModal" in line or "openLicenseModal" in line or "client-modal" in line:
        print(f"Line {idx+1}: {line.strip()}")
