import sys
sys.stdout.reconfigure(encoding='utf-8')

with open("c:/GitHub/Siti/CutMob/app.py", "r", encoding="utf-8") as f:
    content = f.read()

import re
for m in re.finditer(r"(impostazioni|settings|configurazione)", content, re.IGNORECASE):
    start = max(0, m.start() - 100)
    end = min(len(content), m.end() + 100)
    print(f"Match: {content[start:end].strip()}")
