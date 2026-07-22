import sys
sys.stdout.reconfigure(encoding='utf-8')

with open("c:/GitHub/Siti/CutMob/app.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if "f_version = ttk.Frame(tab_build)" in line:
        print(f"Build UI block starts at: {idx+1}")
        for j in range(idx - 4, idx + 18):
            print(f"{j+1}: {lines[j]}", end="")
        break
