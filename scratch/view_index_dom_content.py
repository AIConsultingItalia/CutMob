with open("c:/GitHub/Siti/aiconsultingitalia/panel/panel_cutmob/index.php", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if "document.addEventListener(\"DOMContentLoaded\"" in line:
        print(f"DOM listener found at: {idx+1}")
        for j in range(idx, idx + 16):
            print(f"{j+1}: {lines[j]}", end="")
        break
