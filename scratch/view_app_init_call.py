with open("c:/GitHub/Siti/CutMob/app.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for j in range(45, 60):
    print(f"{j+1}: {lines[j]}", end="")
