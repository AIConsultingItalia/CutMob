import sys
sys.stdout.reconfigure(encoding='utf-8')

with open("c:/GitHub/Siti/CutMob/app.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if "btn_build_win = ttk.Button" in line:
        print(f"Build UI found at: {idx+1}")
        for j in range(idx - 5, idx + 8):
            print(f"{j+1}: {lines[j]}", end="")
        break
