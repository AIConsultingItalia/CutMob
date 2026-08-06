import sys
import os

sys.path.insert(0, os.path.abspath("c:/GitHub/Siti/CutMob"))
from optimizer import CuttingOptimizer

opt = CuttingOptimizer(kerf=5.0)

# Stock di barre con diverse altezze standard a magazzino
stocks = [
    {"id": "b1", "width": 2800.0, "height": 747.0, "thickness": 22.0, "color_code": "_FIN\\01.A1.152", "color_desc": "Test", "is_semilavorato": True, "stock_type": "semilavorato_bar"},
    {"id": "b2", "width": 2800.0, "height": 597.0, "thickness": 22.0, "color_code": "_FIN\\01.A1.152", "color_desc": "Test", "is_semilavorato": True, "stock_type": "semilavorato_bar"},
    {"id": "b3", "width": 2800.0, "height": 447.0, "thickness": 22.0, "color_code": "_FIN\\01.A1.152", "color_desc": "Test", "is_semilavorato": True, "stock_type": "semilavorato_bar"},
    {"id": "b4", "width": 2800.0, "height": 397.0, "thickness": 22.0, "color_code": "_FIN\\01.A1.152", "color_desc": "Test", "is_semilavorato": True, "stock_type": "semilavorato_bar"},
    {"id": "b5", "width": 2800.0, "height": 347.0, "thickness": 22.0, "color_code": "_FIN\\01.A1.152", "color_desc": "Test", "is_semilavorato": True, "stock_type": "semilavorato_bar"},
    {"id": "b6", "width": 2800.0, "height": 297.0, "thickness": 22.0, "color_code": "_FIN\\01.A1.152", "color_desc": "Test", "is_semilavorato": True, "stock_type": "semilavorato_bar"},
    {"id": "b6_2", "width": 2800.0, "height": 297.0, "thickness": 22.0, "color_code": "_FIN\\01.A1.152", "color_desc": "Test", "is_semilavorato": True, "stock_type": "semilavorato_bar"},
    {"id": "b7", "width": 2800.0, "height": 217.0, "thickness": 22.0, "color_code": "_FIN\\01.A1.152", "color_desc": "Test", "is_semilavorato": True, "stock_type": "semilavorato_bar"}
]

# Richiesta pezzi: 6 a misura esatta + 1 fuori misura (254)
demands = [
    {"descrizione": "Pezzo 747", "width": 2800.0, "height": 747.0, "thickness": 22.0, "color_code": "_FIN\\01.A1.152", "color_desc": "Test", "quantity": 1, "width_raw": 2800.0, "height_raw": 747.0},
    {"descrizione": "Pezzo 597", "width": 2800.0, "height": 597.0, "thickness": 22.0, "color_code": "_FIN\\01.A1.152", "color_desc": "Test", "quantity": 1, "width_raw": 2800.0, "height_raw": 597.0},
    {"descrizione": "Pezzo 447", "width": 2800.0, "height": 447.0, "thickness": 22.0, "color_code": "_FIN\\01.A1.152", "color_desc": "Test", "quantity": 1, "width_raw": 2800.0, "height_raw": 447.0},
    {"descrizione": "Pezzo 397", "width": 2800.0, "height": 397.0, "thickness": 22.0, "color_code": "_FIN\\01.A1.152", "color_desc": "Test", "quantity": 1, "width_raw": 2800.0, "height_raw": 397.0},
    {"descrizione": "Pezzo 347", "width": 2800.0, "height": 347.0, "thickness": 22.0, "color_code": "_FIN\\01.A1.152", "color_desc": "Test", "quantity": 1, "width_raw": 2800.0, "height_raw": 347.0},
    {"descrizione": "Pezzo 297", "width": 2800.0, "height": 297.0, "thickness": 22.0, "color_code": "_FIN\\01.A1.152", "color_desc": "Test", "quantity": 1, "width_raw": 2800.0, "height_raw": 297.0},
    {"descrizione": "Pezzo 254 Fuori Misura", "width": 2800.0, "height": 254.0, "thickness": 22.0, "color_code": "_FIN\\01.A1.152", "color_desc": "Test", "quantity": 1, "width_raw": 2800.0, "height_raw": 254.0}
]

res = opt.optimize(
    stocks=stocks,
    demands=demands,
    respect_grain=True,
    machine_type="sezionatrice_manuale",
    bar_strategy="misura_esatta"
)

print("RES:", res)
key = list(res["gruppi"].keys())[0]
used_boards = res["gruppi"][key]["used_boards"]
unplaced = res["gruppi"][key]["unplaced_pieces"]

print(f"--- RISULTATO OTTIMIZZAZIONE BARRE ({len(used_boards)} barre usate, {len(unplaced)} non piazzati) ---")
for idx, ub in enumerate(used_boards, 1):
    board = ub["board"]
    pieces = [p["descrizione"] for p in ub["placed_pieces"]]
    print(f"Barra {idx}: Misura Barra {board['width']}x{board['height']} -> Pezzi piazzati: {pieces}")

for p in unplaced:
    print("Non piazzato:", p["descrizione"])
