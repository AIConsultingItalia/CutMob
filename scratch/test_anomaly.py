import sys
import os
sys.path.insert(0, r"c:\GitHub\Siti\CutMob")

from optimizer import CuttingOptimizer

stocks = [
    {
        'id': 'stock_1',
        'width': 2800.0,
        'height': 747.0,
        'thickness': 22.0,
        'color_code': '_FIN_01.A1.150_747x2800',
        'color_desc': 'M. BIANCO',
        'is_semilavorato': True,
        'stock_type': 'semilavorato_bar'
    }
] * 5

demands = [
    {'descrizione': 'FIANCO FINITURA SP.22', 'width': 607.0, 'height': 2040.0, 'thickness': 22.0, 'color_code': '_FIN_01.A1.150_747x2800', 'color_desc': 'M. BIANCO', 'quantity': 1},
    {'descrizione': 'ANTA 720x57', 'width': 57.0, 'height': 720.0, 'thickness': 22.0, 'color_code': '_FIN_01.A1.150_747x2800', 'color_desc': 'M. BIANCO', 'quantity': 1},
    {'descrizione': 'ANTA 719x57', 'width': 57.0, 'height': 719.0, 'thickness': 22.0, 'color_code': '_FIN_01.A1.150_747x2800', 'color_desc': 'M. BIANCO', 'quantity': 1},
    {'descrizione': 'ANTA 719x47', 'width': 47.0, 'height': 719.0, 'thickness': 22.0, 'color_code': '_FIN_01.A1.150_747x2800', 'color_desc': 'M. BIANCO', 'quantity': 1},
    {'descrizione': 'ANTA 717x447', 'width': 447.0, 'height': 717.0, 'thickness': 22.0, 'color_code': '_FIN_01.A1.150_747x2800', 'color_desc': 'M. BIANCO', 'quantity': 1},
    {'descrizione': 'CIELO-FONDO', 'width': 28.0, 'height': 312.0, 'thickness': 22.0, 'color_code': '_FIN_01.A1.150_747x2800', 'color_desc': 'M. BIANCO', 'quantity': 2},
]

opt = CuttingOptimizer(kerf=4.0)
res = opt.optimize(stocks, demands, respect_grain=True, machine_type="sezionatrice", group_std_heights={'22.0mm__FIN_01.A1.150_747x2800': [747.0]})

ub = res['gruppi']['22.0mm__FIN_01.A1.150_747x2800']['used_boards'][0]
print("Pezzi posizionati:")
for p in ub['placed_pieces']:
    print(f"  {p['descrizione']}: X={p['x']}..{p['x']+p['w']}, Y={p['y']}..{p['y']+p['h']}")

print("\nTagli generati:")
for idx, c in enumerate(ub['cuts']):
    print(f"  Cut {idx+1}: {c['type']} at X1={c['x1']}, Y1={c['y1']}, X2={c['x2']}, Y2={c['y2']}")
