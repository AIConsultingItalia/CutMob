with open("c:/GitHub/Siti/CutMob/app.py", "r", encoding="utf-8") as f:
    content = f.read()

import re
for m in re.finditer(r"(versione|version|v[0-9]\.[0-9])", content, re.IGNORECASE):
    start = max(0, m.start() - 50)
    end = min(len(content), m.end() + 50)
    print(f"Match: {content[start:end].strip()}")
