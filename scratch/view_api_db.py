with open("c:/GitHub/Siti/aiconsultingitalia/panel/panel_cutmob/api.php", "r", encoding="utf-8") as f:
    content = f.read()

import re
# Cerca la connessione al database
conn = re.search(r"\$db\s*=.*", content)
if conn:
    print(content[conn.start():conn.start()+800])
