with open("c:/GitHub/Siti/aiconsultingitalia/panel/panel_cutmob/api.php", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if "Setup_CutMob.exe" in line:
        print(f"panel_cutmob/api.php Line {idx+1}: {line.strip()}")
        
with open("c:/GitHub/Siti/aiconsultingitalia/panel/panel_cantierepro/api.php", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if "Setup_CutMob.exe" in line:
        print(f"panel_cantierepro/api.php Line {idx+1}: {line.strip()}")
