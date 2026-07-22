with open("c:/GitHub/Siti/CutMob/app.py", "r", encoding="utf-8") as f:
    content = f.read()

import re
# Cerca pattern come VERSION = "1.0.0" o simili
for m in re.finditer(r"\b(VERSION|version)\s*=\s*['\"].*?['\"]", content):
    start = max(0, m.start() - 50)
    end = min(len(content), m.end() + 50)
    print(f"Match: {content[start:end]}")
