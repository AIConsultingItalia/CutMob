import sys
sys.stdout.reconfigure(encoding='utf-8')

with open("c:/GitHub/Siti/CutMob/data_manager.py", "r", encoding="utf-8") as f:
    content = f.read()

# Trova dove viene letto/utilizzato "quantity" all'interno di export_pdf_report o export_html_report
import re
for m in re.finditer(r"\.get\(\s*['\"]quantity['\"].*?\)", content):
    start = max(0, m.start() - 150)
    end = min(len(content), m.end() + 150)
    # Mostra solo se fa parte di export
    context = content[start:end]
    if "report" in context or "pdf" in context or "html" in context or "pezzi" in context:
        print(f"Context at {m.start()}:\n{context}\n{'-'*60}")
