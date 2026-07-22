with open("c:/GitHub/Siti/aiconsultingitalia/panel/panel_cutmob/index.php", "r", encoding="utf-8") as f:
    lines = f.readlines()

for j in range(710, 759):
    if j < len(lines):
        print(f"{j+1}: {lines[j]}", end="")
