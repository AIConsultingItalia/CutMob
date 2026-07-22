with open("c:/GitHub/Siti/CutMob/app.py", "r", encoding="utf-8") as f:
    content = f.read()

import re
for m in re.finditer(r"def (\w+)\(self\):", content):
    if 44000 < m.start() < 47500:
        print(f"Def {m.group(1)} at {m.start()}")
