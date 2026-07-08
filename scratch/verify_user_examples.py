import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from optimizer import CuttingOptimizer

def run_scenario(name, demands_list):
    print(f"\n--- SCENARIO: {name} ---")
    opt = CuttingOptimizer(kerf=4.0)
    
    # Barre standard a magazzino
    stocks = [
        {
            "id": "BAR_297",
            "width": 2800.0,
            "height": 297.0,
            "thickness": 18.0,
            "color_code": "COL",
            "color_desc": "Colore",
            "stock_type": "semilavorato_bar",
            "quantity": 10
        },
        {
            "id": "BAR_597",
            "width": 2800.0,
            "height": 597.0,
            "thickness": 18.0,
            "color_code": "COL",
            "color_desc": "Colore",
            "stock_type": "semilavorato_bar",
            "quantity": 10
        },
        {
            "id": "BAR_897",
            "width": 2800.0,
            "height": 897.0,
            "thickness": 18.0,
            "color_code": "COL",
            "color_desc": "Colore",
            "stock_type": "semilavorato_bar",
            "quantity": 10
        },
        {
            "id": "BAR_1197",
            "width": 2800.0,
            "height": 1197.0,
            "thickness": 18.0,
            "color_code": "COL",
            "color_desc": "Colore",
            "stock_type": "semilavorato_bar",
            "quantity": 10
        }
    ]
    
    # Altezze standard delle barre
    group_std_heights = {
        "18.0mm_COL": [297.0, 597.0, 897.0, 1197.0]
    }
    
    res = opt.optimize(stocks, demands_list, respect_grain=True, group_std_heights=group_std_heights)
    g_res = res["gruppi"]["18.0mm_COL"]
    
    print(f"Pezzi non piazzati: {len(g_res['unplaced_pieces'])}")
    for i, ub in enumerate(g_res["used_boards"]):
        board = ub["board"]
        # Eseguiamo la trasformazione a verticale per la visualizzazione fisica
        bw, bh = board["width"], board["height"]
        # Se visualizziamo in verticale:
        v_board_w = bh
        v_board_h = bw
        print(f"Barra utilizzata (visualizzata in verticale): {board['id']} (Larghezza={v_board_w} x Lunghezza={v_board_h})")
        print("Pezzi posizionati (visualizzati in verticale):")
        for p in ub["placed_pieces"]:
            # coord x_v = y_h, y_v = x_h, w_v = h_h, h_v = w_h
            px_v = p["y"]
            py_v = p["x"]
            pw_v = p["h"]
            ph_v = p["w"]
            print(f"  - {p['descrizione']}: coordinate (x={px_v}, y={py_v}) - dimensioni (Larghezza W={pw_v} x Altezza H={ph_v})")
        print("Tagli (visualizzati in verticale):")
        for cut in ub["cuts"]:
            cx1 = cut["y1"]
            cy1 = cut["x1"]
            cx2 = cut["y2"]
            cy2 = cut["x2"]
            c_type = "H" if cut["type"] == "V" else "V"
            print(f"  - Taglio {c_type}: da ({cx1}, {cy1}) a ({cx2}, {cy2})")

if __name__ == "__main__":
    # 1. 4 ante di altezza 897 e larghezza 597.
    # W = 597 (larghezza), H = 897 (altezza). Si aspetta l'uso della barra larga 597.
    run_scenario(
        "4 ante standard Larghezza 597 x Altezza 897 (ci si aspetta la barra 597)",
        [
            {
                "descrizione": "Anta Standard 597x897",
                "width": 597.0,
                "height": 897.0,
                "thickness": 18.0,
                "color_code": "COL",
                "color_desc": "Colore",
                "quantity": 4
            }
        ]
    )
    
    # 2. Ante fuori misura in larghezza, es: larghezza 560, altezza 897.
    # W = 560, H = 897. Si aspetta la barra larga 597 con riduzione larghezza a 560.
    run_scenario(
        "Anta FM Larghezza 560 x Altezza 897 (ci si aspetta la barra 597 + rifilo larghezza)",
        [
            {
                "descrizione": "Anta FM 560x897",
                "width": 560.0,
                "height": 897.0,
                "thickness": 18.0,
                "color_code": "COL",
                "color_desc": "Colore",
                "quantity": 1
            }
        ]
    )
    
    # 3. Ante fuori misura in altezza, es: larghezza 920, altezza 597.
    # W = 920, H = 597. Si aspetta la barra superiore 1197, rifilata a 597 (lunghezza) e poi a 920 (larghezza).
    run_scenario(
        "Anta FM Larghezza 920 x Altezza 597 (ci si aspetta la barra 1197 + riduzione larghezza)",
        [
            {
                "descrizione": "Anta FM 920x597",
                "width": 920.0,
                "height": 597.0,
                "thickness": 18.0,
                "color_code": "COL",
                "color_desc": "Colore",
                "quantity": 1
            }
        ]
    )
    
    # 4. Controllo residuo: pezzo da 297 su residuo/barra da 897 non consentito!
    # Ci si aspetta l'uso della barra 297 anche se è presente una barra 897.
    run_scenario(
        "Anta standard Larghezza 297 x Altezza 600 (deve usare BAR_297 anche se BAR_897 ha spazio)",
        [
            {
                "descrizione": "Anta Stretta 297x600",
                "width": 297.0,
                "height": 600.0,
                "thickness": 18.0,
                "color_code": "COL",
                "color_desc": "Colore",
                "quantity": 1
            }
        ]
    )
