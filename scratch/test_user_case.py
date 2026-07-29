import sys
import os
sys.path.insert(0, r"c:\GitHub\Siti\CutMob")

from optimizer import CuttingOptimizer

stocks = [
    {
        'id': 'stock_1',
        'width': 2800.0,
        'height': 597.0,
        'thickness': 22.0,
        'color_code': '_FIN_01.A1.150_597x2800',
        'color_desc': 'M. BIANCO',
        'is_semilavorato': True,
        'stock_type': 'semilavorato_bar'
    }
] * 10

demands = [
    {'descrizione': 'ANTA 1317', 'width': 597.0, 'height': 1317.0, 'thickness': 22.0, 'color_code': '_FIN_01.A1.150_597x2800', 'color_desc': 'M. BIANCO', 'quantity': 1},
    {'descrizione': 'ANTA 717', 'width': 597.0, 'height': 717.0, 'thickness': 22.0, 'color_code': '_FIN_01.A1.150_597x2800', 'color_desc': 'M. BIANCO', 'quantity': 5},
    {'descrizione': 'ANTA 332x447', 'width': 447.0, 'height': 332.0, 'thickness': 22.0, 'color_code': '_FIN_01.A1.150_597x2800', 'color_desc': 'M. BIANCO', 'quantity': 1},
    {'descrizione': 'ANTA 177x447', 'width': 447.0, 'height': 177.0, 'thickness': 22.0, 'color_code': '_FIN_01.A1.150_597x2800', 'color_desc': 'M. BIANCO', 'quantity': 2},
    {'descrizione': 'ANTA 720x57', 'width': 57.0, 'height': 720.0, 'thickness': 22.0, 'color_code': '_FIN_01.A1.150_597x2800', 'color_desc': 'M. BIANCO', 'quantity': 1},
    {'descrizione': 'ANTA 719x57', 'width': 57.0, 'height': 719.0, 'thickness': 22.0, 'color_code': '_FIN_01.A1.150_597x2800', 'color_desc': 'M. BIANCO', 'quantity': 1},
    {'descrizione': 'ANTA 719x47', 'width': 47.0, 'height': 719.0, 'thickness': 22.0, 'color_code': '_FIN_01.A1.150_597x2800', 'color_desc': 'M. BIANCO', 'quantity': 1},
    {'descrizione': 'ANTA 57x597', 'width': 597.0, 'height': 57.0, 'thickness': 22.0, 'color_code': '_FIN_01.A1.150_597x2800', 'color_desc': 'M. BIANCO', 'quantity': 2},
    {'descrizione': 'CIELO-FONDO', 'width': 28.0, 'height': 312.0, 'thickness': 22.0, 'color_code': '_FIN_01.A1.150_597x2800', 'color_desc': 'M. BIANCO', 'quantity': 4},
]

group_std_heights = {'22.0mm__FIN_01.A1.150_597x2800': [597.0]}

opt = CuttingOptimizer(kerf=5.0)
res = opt.optimize(stocks, demands, respect_grain=True, machine_type="sezionatrice", group_std_heights=group_std_heights)

for g_key, val in res['gruppi'].items():
    print(f"Group: {g_key}")
    used_boards = val['used_boards']
    print(f"Barre usate: {len(used_boards)}")
    for idx, ub in enumerate(used_boards):
        print(f"\n--- LAYOUT {idx + 1} ---")
        for p in ub['placed_pieces']:
            print(f"  Pezzo: {p.get('descrizione')} | X={p['x']}, Y={p['y']}, W={p['w']}, H={p['h']}")
