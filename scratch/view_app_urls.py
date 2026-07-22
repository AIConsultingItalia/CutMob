with open("c:/GitHub/Siti/CutMob/app.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if "panel/panel_cutmob/api.php" in line:
        print(f"URL found at line: {idx+1}")
        print(f"  {line.strip()}")
