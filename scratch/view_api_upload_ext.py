with open("c:/GitHub/Siti/aiconsultingitalia/panel/panel_cutmob/api.php", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if "action === 'upload_program'" in line:
        print(f"Action starts at: {idx+1}")
        for j in range(idx, idx + 45):
            print(f"{j+1}: {lines[j]}", end="")
        break
