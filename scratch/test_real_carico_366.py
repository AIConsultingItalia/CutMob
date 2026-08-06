import json
import sys
import os

sys.path.insert(0, os.path.abspath("c:/GitHub/Siti/CutMob"))
from optimizer import CuttingOptimizer

db = json.load(open('C:/CutMob/DbDati/database.json', encoding='utf-8'))
commessa = [c for c in db.get('commesse', []) if c.get('nome') == 'Carico 366'][0]

print("Commesse nel database:")
for c in db.get('commesse', []):
    print("Commessa:", c.get("nome"), "demands count:", len(c.get("demands", [])))
    for d in c.get("demands", []):
        print("  -", d.get("descrizione"), "color:", repr(d.get("color_code")), "W=", d.get("width"), "H=", d.get("height"), "qty=", d.get("quantity"))

opt = CuttingOptimizer(kerf=5.0)

# Costruiamo group_std_heights come fa app.py
group_std_heights = {}
for item in semilavorati:
    key = f"{item['thickness']}mm_{item['color_code']}"
    std_h = min(item["width"], item["height"])
    if key not in group_std_heights:
        group_std_heights[key] = set()
    group_std_heights[key].add(std_h)

for k in group_std_heights:
    group_std_heights[k] = sorted(list(group_std_heights[k]))

res = opt.optimize(
    stocks=semilavorati,
    demands=demands_152,
    respect_grain=True,
    group_std_heights=group_std_heights,
    machine_type="sezionatrice_manuale",
    bar_strategy="misura_esatta"
)

key = list(res["gruppi"].keys())[0]
used_boards = res["gruppi"][key]["used_boards"]

print(f"\n--- RISULTATO REAL CARICO 366 ({len(used_boards)} barre usate) ---")
for idx, ub in enumerate(used_boards, 1):
    board = ub["board"]
    pieces = [f"{p['descrizione']} (W={p['w']}, H={p['h']})" for p in ub["placed_pieces"]]
    print(f"Layout {idx}: Barra {board['width']}x{board['height']} ({board.get('id')}) -> Pezzi: {pieces}")
