import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from optimizer import CuttingOptimizer

stocks = [
    {
        "id": "BAR1",
        "width": 2800.0,
        "height": 597.0,
        "thickness": 18.0,
        "color_code": "U708",
        "color_desc": "Grigio",
        "stock_type": "semilavorato_bar",
        "has_grain": False
    },
    {
        "id": "BAR2",
        "width": 2800.0,
        "height": 597.0,
        "thickness": 18.0,
        "color_code": "U708",
        "color_desc": "Grigio",
        "stock_type": "semilavorato_bar",
        "has_grain": False
    }
]

demands = [
    {
        "descrizione": "Anta 580",
        "width": 580.0,
        "height": 720.0,
        "thickness": 18.0,
        "color_code": "U708",
        "color_desc": "Grigio",
        "quantity": 2
    },
    {
        "descrizione": "Anta 560",
        "width": 560.0,
        "height": 720.0,
        "thickness": 18.0,
        "color_code": "U708",
        "color_desc": "Grigio",
        "quantity": 1
    }
]

group_std_heights = {
    "18.0mm_U708": [297.0, 347.0, 397.0, 447.0, 497.0, 547.0, 567.0, 597.0, 897.0]
}

opt = CuttingOptimizer(kerf=4.0)
opt.sfrido = 0.0
risultati = opt.optimize(
    stocks=stocks,
    demands=demands,
    respect_grain=True,
    group_std_heights=group_std_heights,
    machine_type="sezionatrice"
)

for key, g in risultati["gruppi"].items():
    print(f"Gruppo: {key}")
    print(f"Used boards: {len(g['used_boards'])}")
    for idx, ub in enumerate(g['used_boards']):
        print(f"  Board {idx+1} ({ub['board']['id']}):")
        for p in ub['placed_pieces']:
            print(f"    - {p['descrizione']}: pos={p['x']},{p['y']} dim={p['w']}x{p['h']} orig={p.get('width_original')}x{p.get('height_original')}")
    print("Unplaced:", g["unplaced_pieces"])
