with open("c:/GitHub/Siti/aiconsultingitalia/panel/panel_cutmob/index.php", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if 'id="key-modal"' in line:
        print(f"key-modal starts at: {idx+1}")
        for j in range(idx - 6, idx + 4):
            print(f"{j+1}: {lines[j]}", end="")
        break
