with open("c:/GitHub/Siti/CutMob/app.py", "r", encoding="utf-8") as f:
    content = f.read()

import re
m = re.search(r"class DbSettingsDialog", content)
if m:
    # Cerca la fine della classe DbSettingsDialog (es. la definizione della classe successiva o fine file)
    next_class_m = re.search(r"class ", content[m.end():])
    if next_class_m:
        print(content[m.start() + next_class_m.start() - 500 : m.start() + next_class_m.start() + 500])
    else:
        print(content[-1000:])
