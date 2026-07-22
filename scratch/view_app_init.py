with open("c:/GitHub/Siti/CutMob/app.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if "class CutMob" in line or "class App" in line:
        print(f"Class starts at line: {idx+1}")
        for j in range(idx, idx+120):
            if j < len(lines):
                print(f"{j+1}: {lines[j]}", end="")
        break
