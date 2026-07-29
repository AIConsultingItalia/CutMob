import sys
import os
sys.path.insert(0, r"c:\GitHub\Siti\CutMob")

from data_manager import DataManager

dm = DataManager(db_filename="test_database.json")
test_pdf = os.path.join(os.path.dirname(__file__), "test_export_report_check.pdf")

ub = {
    "board": {
        "id": "B1",
        "width": 747.0,
        "height": 2800.0,
        "thickness": 22.0,
        "color_code": "_FIN_01.A1.150_747x2800",
        "color_desc": "M. BIANCO",
        "stock_type": "semilavorato_bar"
    },
    "placed_pieces": [
        {"descrizione": "FIANCO FINITURA SP.22", "x": 0.0, "y": 0.0, "w": 2040.0, "h": 607.0},
        {"descrizione": "ANTA CON DESCRIZIONE MOLTO LUNGA", "x": 2044.0, "y": 174.0, "w": 717.0, "h": 447.0}
    ],
    "used_area": 2040.0 * 607.0 + 717.0 * 447.0,
    "cuts": []
}

res = dm._generate_layout_svg(ub, for_pdf=True)
print("SVG generato con successo! Contiene tspan:", "<tspan" in res)
