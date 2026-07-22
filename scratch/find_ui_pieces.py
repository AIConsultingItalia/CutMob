with open("c:/GitHub/Siti/CutMob/app.py", "r", encoding="utf-8") as f:
    content = f.read()

# Trova tutti i posti in cui viene visualizzata la quantità del pezzo, ad es. ".get("quantity"
import re
for m in re.finditer(r"\.get\(\s*['\"]quantity['\"].*?\)", content):
    start = max(0, m.start() - 60)
    end = min(len(content), m.end() + 60)
    print(f"Context at {m.start()}:\n{content[start:end]}\n{'-'*40}")
