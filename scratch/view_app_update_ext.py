with open("c:/GitHub/Siti/CutMob/app.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if "Setup_CutMob" in line or "run_update" in line or "update_process" in line:
        print(f"Line {idx+1}: {line.strip()}")
