with open("c:/GitHub/Siti/aiconsultingitalia/panel/panel_cutmob/index.php", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if 'id="upload-version"' in line:
        print(f"Version input found at: {idx+1}")
        for j in range(idx - 3, idx + 4):
            print(f"{j+1}: {lines[j]}", end="")
        break
