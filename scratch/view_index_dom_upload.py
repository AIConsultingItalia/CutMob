with open("c:/GitHub/Siti/aiconsultingitalia/panel/panel_cutmob/index.php", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if "Auto-compilazione versione" in line:
        print(f"Block found at: {idx+1}")
        for j in range(idx, idx + 18):
            print(f"{j+1}: {lines[j]}", end="")
        break
