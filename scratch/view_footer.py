with open("c:/GitHub/Siti/CutMob/app.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if "CutMob v2.0 - Premium" in line:
        print(f"Starts at: {idx+1}")
        for j in range(idx - 2, idx + 5):
            print(f"{j+1}: {lines[j]}", end="")
        break
