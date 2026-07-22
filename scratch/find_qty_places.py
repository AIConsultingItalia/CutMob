with open("c:/GitHub/Siti/CutMob/app.py", "r", encoding="utf-8") as f:
    content = f.read()

import re
# Cerca per parole chiave correlate all'esportazione report o salvataggio o visualizzazione pezzi
for m in re.finditer(r"(export_pdf_report|export_html_report|tree_pieces|refresh_pezzi)", content):
    start = max(0, m.start() - 100)
    end = min(len(content), m.end() + 100)
    print(f"Match for '{m.group(1)}':\n{content[start:end]}\n{'-'*40}")
