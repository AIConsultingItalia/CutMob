import sys
import os
sys.path.insert(0, os.path.abspath("c:/GitHub/Siti/CutMob"))
from optimizer import CuttingOptimizer

opt = CuttingOptimizer(kerf=5.0)

stocks = [
    {"id": "b_1197", "width": 1197.0, "height": 2800.0, "thickness": 22.0, "color_code": "_FIN\\01.A1.152", "color_desc": "M. CERA", "is_semilavorato": True, "stock_type": "semilavorato_bar"},
    {"id": "b_897", "width": 897.0, "height": 2800.0, "thickness": 22.0, "color_code": "_FIN\\01.A1.152", "color_desc": "M. CERA", "is_semilavorato": True, "stock_type": "semilavorato_bar"},
    {"id": "b_747", "width": 747.0, "height": 2800.0, "thickness": 22.0, "color_code": "_FIN\\01.A1.152", "color_desc": "M. CERA", "is_semilavorato": True, "stock_type": "semilavorato_bar"},
    {"id": "b_597_1", "width": 597.0, "height": 2800.0, "thickness": 22.0, "color_code": "_FIN\\01.A1.152", "color_desc": "M. CERA", "is_semilavorato": True, "stock_type": "semilavorato_bar"},
    {"id": "b_597_2", "width": 597.0, "height": 2800.0, "thickness": 22.0, "color_code": "_FIN\\01.A1.152", "color_desc": "M. CERA", "is_semilavorato": True, "stock_type": "semilavorato_bar"},
    {"id": "b_447_1", "width": 447.0, "height": 2800.0, "thickness": 22.0, "color_code": "_FIN\\01.A1.152", "color_desc": "M. CERA", "is_semilavorato": True, "stock_type": "semilavorato_bar"},
    {"id": "b_447_2", "width": 447.0, "height": 2800.0, "thickness": 22.0, "color_code": "_FIN\\01.A1.152", "color_desc": "M. CERA", "is_semilavorato": True, "stock_type": "semilavorato_bar"},
    {"id": "b_397_1", "width": 397.0, "height": 2800.0, "thickness": 22.0, "color_code": "_FIN\\01.A1.152", "color_desc": "M. CERA", "is_semilavorato": True, "stock_type": "semilavorato_bar"},
    {"id": "b_397_2", "width": 397.0, "height": 2800.0, "thickness": 22.0, "color_code": "_FIN\\01.A1.152", "color_desc": "M. CERA", "is_semilavorato": True, "stock_type": "semilavorato_bar"},
    {"id": "b_330_1", "width": 330.0, "height": 2800.0, "thickness": 22.0, "color_code": "_FIN\\01.A1.152", "color_desc": "M. CERA", "is_semilavorato": True, "stock_type": "semilavorato_bar"},
    {"id": "b_330_2", "width": 330.0, "height": 2800.0, "thickness": 22.0, "color_code": "_FIN\\01.A1.152", "color_desc": "M. CERA", "is_semilavorato": True, "stock_type": "semilavorato_bar"},
    {"id": "b_297_1", "width": 297.0, "height": 2800.0, "thickness": 22.0, "color_code": "_FIN\\01.A1.152", "color_desc": "M. CERA", "is_semilavorato": True, "stock_type": "semilavorato_bar"},
    {"id": "b_297_2", "width": 297.0, "height": 2800.0, "thickness": 22.0, "color_code": "_FIN\\01.A1.152", "color_desc": "M. CERA", "is_semilavorato": True, "stock_type": "semilavorato_bar"}
]

# Pezzi esatti estratti dal PDF
demands = [
    {"descrizione": "ANTA 717x597", "width": 717.0, "height": 597.0, "thickness": 22.0, "color_code": "_FIN\\01.A1.152", "color_desc": "M. CERA", "quantity": 1, "width_raw": 717.0, "height_raw": 597.0},
    {"descrizione": "ANTA 717x447", "width": 717.0, "height": 447.0, "thickness": 22.0, "color_code": "_FIN\\01.A1.152", "color_desc": "M. CERA", "quantity": 1, "width_raw": 717.0, "height_raw": 447.0},
    {"descrizione": "ANTA 717x397", "width": 717.0, "height": 397.0, "thickness": 22.0, "color_code": "_FIN\\01.A1.152", "color_desc": "M. CERA", "quantity": 1, "width_raw": 717.0, "height_raw": 397.0},
    {"descrizione": "ANTA 357x597", "width": 357.0, "height": 597.0, "thickness": 22.0, "color_code": "_FIN\\01.A1.152", "color_desc": "M. CERA", "quantity": 1, "width_raw": 357.0, "height_raw": 597.0},
    {"descrizione": "FIANCO 720x330", "width": 720.0, "height": 330.0, "thickness": 22.0, "color_code": "_FIN\\01.A1.152", "color_desc": "M. CERA", "quantity": 1, "width_raw": 720.0, "height_raw": 330.0},
    {"descrizione": "ANTA 717x297", "width": 717.0, "height": 297.0, "thickness": 22.0, "color_code": "_FIN\\01.A1.152", "color_desc": "M. CERA", "quantity": 1, "width_raw": 717.0, "height_raw": 297.0},
    {"descrizione": "ANTA 717x254", "width": 717.0, "height": 254.0, "thickness": 22.0, "color_code": "_FIN\\01.A1.152", "color_desc": "M. CERA", "quantity": 1, "width_raw": 717.0, "height_raw": 254.0},
    {"descrizione": "FIANCO 360x330", "width": 360.0, "height": 330.0, "thickness": 22.0, "color_code": "_FIN\\01.A1.152", "color_desc": "M. CERA", "quantity": 1, "width_raw": 360.0, "height_raw": 330.0},
    {"descrizione": "ANTA 357x297", "width": 357.0, "height": 297.0, "thickness": 22.0, "color_code": "_FIN\\01.A1.152", "color_desc": "M. CERA", "quantity": 1, "width_raw": 357.0, "height_raw": 297.0},
    {"descrizione": "ANTA 357x447", "width": 357.0, "height": 447.0, "thickness": 22.0, "color_code": "_FIN\\01.A1.152", "color_desc": "M. CERA", "quantity": 1, "width_raw": 357.0, "height_raw": 447.0},
    {"descrizione": "ANTA 357x397", "width": 357.0, "height": 397.0, "thickness": 22.0, "color_code": "_FIN\\01.A1.152", "color_desc": "M. CERA", "quantity": 1, "width_raw": 357.0, "height_raw": 397.0},
    {"descrizione": "ANTA 357x254_1", "width": 357.0, "height": 254.0, "thickness": 22.0, "color_code": "_FIN\\01.A1.152", "color_desc": "M. CERA", "quantity": 1, "width_raw": 357.0, "height_raw": 254.0},
    {"descrizione": "ANTA 357x254_2", "width": 357.0, "height": 254.0, "thickness": 22.0, "color_code": "_FIN\\01.A1.152", "color_desc": "M. CERA", "quantity": 1, "width_raw": 357.0, "height_raw": 254.0}
]

group_std_heights = {'22.0mm__FIN\\01.A1.152': [297.0, 330.0, 397.0, 447.0, 597.0, 747.0, 897.0, 1197.0]}

res = opt.optimize(
    stocks=stocks,
    demands=demands,
    respect_grain=False,
    min_semilavorato_width=200.0,
    min_semilavorato_height=300.0,
    group_std_heights=group_std_heights,
    machine_type="sezionatrice_manuale",
    bar_strategy="misura_esatta"
)

print("RES:", res)
key = list(res["gruppi"].keys())[0]
used_boards = res["gruppi"][key]["used_boards"]
unplaced = res["gruppi"][key]["unplaced_pieces"]

print(f"\n--- RISULTATO ESATTO DAL PDF ({len(used_boards)} barre usate, {len(unplaced)} non piazzati) ---")
for idx, ub in enumerate(used_boards, 1):
    board = ub["board"]
    pieces = [f"{p['descrizione']} (w={p['w']}, h={p['h']})" for p in ub["placed_pieces"]]
    print(f"Layout {idx}: Barra {board['width']}x{board['height']} ({board['id']}) -> Pezzi: {pieces}")

for p in unplaced:
    print("Unplaced:", p["descrizione"], "W=", p["width"], "H=", p["height"])
