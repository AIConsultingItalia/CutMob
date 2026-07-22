with open("c:/GitHub/Siti/CutMob/app.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if "class FabbisognoDialog" in line:
        print(f"FabbisognoDialog starts at: {idx+1}")
        for j in range(idx - 10, idx + 2):
            print(f"{j+1}: {lines[j]}", end="")
        break
