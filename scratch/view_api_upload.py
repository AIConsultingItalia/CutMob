with open("c:/GitHub/Siti/aiconsultingitalia/panel/panel_cutmob/api.php", "r", encoding="utf-8") as f:
    content = f.read()

import re
m = re.search(r"action.*upload", content, re.IGNORECASE)
if m:
    print(content[m.start() - 100 : m.start() + 900])
else:
    print("Upload action not found in api.php")
