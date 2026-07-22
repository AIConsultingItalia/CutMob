with open("c:/GitHub/Siti/CutMob/app.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if "def check_license_startup" in line:
        print(f"Starts at line: {idx+1}")
        for j in range(idx, idx+150):
            if j < len(lines):
                print(f"{j+1}: {lines[j]}", end="")
        break
