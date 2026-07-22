with open("c:/GitHub/Siti/aiconsultingitalia/panel/panel_cutmob/index.php", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if "${c.ragione_sociale}" in line:
        print(f"JS row found at: {idx+1}")
        for j in range(idx - 2, idx + 12):
            print(f"{j+1}: {lines[j]}", end="")
        break
