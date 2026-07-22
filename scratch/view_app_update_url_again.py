with open("c:/GitHub/Siti/CutMob/app.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if "def check_for_updates_async" in line:
        print(f"Starts at: {idx+1}")
        for j in range(idx, idx + 15):
            print(f"{j+1}: {lines[j]}", end="")
        break
