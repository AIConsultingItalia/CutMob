import sys
sys.stdout.reconfigure(encoding='utf-8')

with open("c:/GitHub/Siti/CutMob/app.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if "def force_update_check" in line:
        print(f"force_update_check starts at: {idx+1}")
        for j in range(idx + 35, idx + 50):
            if j < len(lines):
                print(f"{j+1}: {lines[j]}", end="")
        break
