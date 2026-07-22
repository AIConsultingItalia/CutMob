with open("c:/GitHub/Siti/CutMob/app.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if "current_version = \"2.0\"" in line:
        print(f"Starts at: {idx+1}")
        for j in range(idx - 2, idx + 5):
            print(f"{j+1}: {lines[j]}", end="")
        break
