with open("c:/GitHub/Siti/CutMob/data_manager.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if "def load_db" in line:
        print(f"load_db starts at line: {idx+1}")
        for j in range(idx, idx+60):
            if j < len(lines):
                print(f"{j+1}: {lines[j]}", end="")
        break
