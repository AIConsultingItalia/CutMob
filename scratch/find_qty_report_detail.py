import sys
sys.stdout.reconfigure(encoding='utf-8')

with open("c:/GitHub/Siti/CutMob/data_manager.py", "r", encoding="utf-8") as f:
    content = f.read()

# Trova la definizione di export_pdf_report e export_html_report
import re
for m in re.finditer(r"def (export_pdf_report|export_html_report)\(self,.*?\):", content):
    print(f"Found method: {m.group(1)} at position {m.start()}")
    # Estrai i successivi 4000 caratteri
    sub = content[m.start():m.start()+8000]
    # Cerca occorrenze di quantity in questa sotto-stringa
    for m2 in re.finditer(r"\bquantity\b", sub):
        context_start = max(0, m2.start() - 100)
        context_end = min(len(sub), m2.end() + 100)
        print(f"  Qty usage inside {m.group(1)}:\n  {sub[context_start:context_end].strip()}")
        print("  " + "-"*40)
