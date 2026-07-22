with open("c:/GitHub/Siti/CutMob/data_manager.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx in range(440, 600):
    if idx < len(lines):
        print(f"{idx+1}: {lines[idx]}", end="")
