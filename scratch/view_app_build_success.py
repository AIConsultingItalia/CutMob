with open("c:/GitHub/Siti/CutMob/app.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if "shutil.copy2(os.path.join(\"dist\", \"Setup_CutMob.exe\")" in line:
        print(f"Success block found at: {idx+1}")
        for j in range(idx - 2, idx + 8):
            print(f"{j+1}: {lines[j]}", end="")
        break
