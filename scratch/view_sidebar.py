import sys
sys.stdout.reconfigure(encoding='utf-8')

with open("c:/GitHub/Siti/CutMob/app.py", "r", encoding="utf-8") as f:
    content = f.read()

import re
m = re.search(r"CutMob v2\.0", content)
if m:
    print(content[m.start()-1000:m.start()+1000])
