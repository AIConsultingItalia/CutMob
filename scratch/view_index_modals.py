with open("c:/GitHub/Siti/aiconsultingitalia/panel/panel_cutmob/index.php", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx in range(129, 249):
    if idx < len(lines):
        print(f"{idx+1}: {lines[idx]}", end="")
