with open("c:/GitHub/Siti/CutMob/app.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if "self.APP_VERSION =" in line:
        print(f"Line {idx+1}: {line.strip()}")
