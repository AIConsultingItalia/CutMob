with open("c:/GitHub/Siti/CutMob/app.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if "def build_windows_installer" in line:
        print(f"Method starts at: {idx+1}")
        for j in range(idx, idx + 65):
            print(f"{j+1}: {lines[j]}", end="")
        break
