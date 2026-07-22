with open("c:/GitHub/Siti/CutMob/app.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if "def reload_order_table" in line:
        print(f"Starts at line: {idx+1}")
        # Print subsequent 50 lines
        for j in range(idx, idx+60):
            if j < len(lines):
                print(f"{j+1}: {lines[j]}", end="")
        break
