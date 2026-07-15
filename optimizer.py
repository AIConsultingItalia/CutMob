import copy

class CuttingOptimizer:
    def __init__(self, kerf=5.0):
        self.kerf = kerf

    def _get_orientations(self, board, piece, respect_grain, use_sfrido, panel_grain_direction="verticale"):
        w_p = piece["width_raw"] + use_sfrido
        h_p = piece["height_raw"] + use_sfrido
        
        is_bar = board.get("stock_type") in ["semilavorato_bar", "remnant"]
        
        if is_bar:
            # Le barre vengono considerate a tinta unita e con rotazione bloccata per mantenere l'allineamento standard
            return [(w_p, h_p)]
            
        if not respect_grain:
            # Senza venatura sui pannelli: entrambe le rotazioni consentite
            return [(w_p, h_p), (h_p, w_p)]
            
        # Con venatura sui pannelli
        if panel_grain_direction == "orizzontale":
            return [(h_p, w_p)]
        else:
            return [(w_p, h_p)]

    def optimize(self, stocks, demands, respect_grain=True, min_semilavorato_width=300.0, min_semilavorato_height=300.0, group_std_heights=None, rifilo_verticale=0.0, rifilo_orizzontale=0.0, sfrido=0.0, machine_type="sezionatrice", panel_grain_direction="verticale"):
        """
        Ottimizza il taglio dei pezzi (demands) sulle barre a disposizione (stocks).
        
        Parametri:
        - stocks: lista di dizionari con keys:
            ['id', 'width', 'height', 'thickness', 'color_code', 'color_desc', 'is_semilavorato', 'stock_type']
        - demands: lista di dizionari con keys:
            ['descrizione', 'width', 'height', 'thickness', 'color_code', 'color_desc', 'quantity']
        - respect_grain: se True, non ruota i pezzi. Se False, permette la rotazione di 90 gradi.
        - min_semilavorato_width: larghezza minima per considerare un ritaglio come semilavorato riutilizzabile.
        - min_semilavorato_height: altezza minima per considerare un ritaglio come semilavorato riutilizzabile.
        - group_std_heights: dizionario opzionale con le altezze standard per ciascun gruppo di materiale.
        - rifilo_verticale: rifilo verticale per i pannelli (whole_board).
        - rifilo_orizzontale: rifilo orizzontale per i pannelli (whole_board).
        - sfrido: valore da sommare alla larghezza e altezza di ciascun pezzo demand.
        - machine_type: "sezionatrice" o "pantografo".
        
        Ritorna un dizionario con i risultati raggruppati per gruppo di materiale (Spessore + Colore)
        """
        # 1. Raggruppa stock e demands per materiale (Spessore_Colore)
        groups = {}
        
        # Inizializza i gruppi con le domande
        self.sfrido = sfrido
        self.panel_grain_direction = panel_grain_direction
        for d in demands:
            key = f"{d['thickness']}mm_{d['color_code']}"
            if key not in groups:
                groups[key] = {"stocks": [], "demands": []}
            
            is_bar_group = False
            if group_std_heights and key in group_std_heights:
                is_bar_group = True
            else:
                is_bar_group = any(s.get("stock_type") == "semilavorato_bar" for s in stocks if f"{s['thickness']}mm_{s['color_code']}" == key)
                
            if is_bar_group:
                w_raw = d["height"]  # H dell'anta diventa larghezza (asse X) del layout
                h_raw = d["width"]   # W dell'anta diventa altezza (asse Y) del layout
            else:
                w_raw = d["width"]
                h_raw = d["height"]
            
            # Moltiplica per la quantità per gestire i pezzi singoli nel loop
            for _ in range(d.get("quantity", 1)):
                groups[key]["demands"].append({
                    "descrizione": d["descrizione"],
                    "width": w_raw,
                    "height": h_raw,
                    "width_raw": w_raw,
                    "height_raw": h_raw,
                    "width_orig": d["width"],
                    "height_orig": d["height"],
                    "thickness": d["thickness"],
                    "color_code": d["color_code"],
                    "color_desc": d["color_desc"]
                })
                
        # Ordina lo stock per priorità di consumo: 1. Residui (remnant), 2. Barre pre-tagliate (semilavorato_bar), 3. Pannelli grandi (whole_board)
        def stock_priority(s):
            t = s.get("stock_type", "whole_board")
            if t == "remnant":
                return 0
            elif t == "semilavorato_bar":
                return 1
            else:
                return 2
                
        sorted_stocks = sorted(stocks, key=stock_priority)
        
        # Associa le barre di magazzino ai rispettivi gruppi (applicando il rifilo solo ai pannelli whole_board)
        for s in sorted_stocks:
            key = f"{s['thickness']}mm_{s['color_code']}"
            if key in groups:
                s_copy = copy.deepcopy(s)
                if s_copy.get("stock_type") == "whole_board":
                    s_copy["width_original_panel"] = s_copy["width"]
                    s_copy["height_original_panel"] = s_copy["height"]
                    s_copy["width"] = max(0.0, s_copy["width"] - rifilo_verticale)
                    s_copy["height"] = max(0.0, s_copy["height"] - rifilo_orizzontale)
                    s_copy["rifilo_verticale"] = rifilo_verticale
                    s_copy["rifilo_orizzontale"] = rifilo_orizzontale
                groups[key]["stocks"].append(s_copy)

        risultati_gruppi = {}
        totale_area_lastre = 0.0
        totale_area_pezzi = 0.0
        totale_area_scarto = 0.0

        min_semi_size = (min_semilavorato_width, min_semilavorato_height)

        # 2. Ottimizza ogni gruppo separatamente
        for key, g in groups.items():
            stocks_gruppo = g["stocks"]
            demands_gruppo = g["demands"]
            
            if not demands_gruppo:
                continue
                
            # Se non ci sono lastre a magazzino per questo materiale, i pezzi rimangono non piazzati
            if not stocks_gruppo:
                risultati_gruppi[key] = {
                    "used_boards": [],
                    "unplaced_pieces": demands_gruppo,
                    "summary": {
                        "total_boards_used": 0,
                        "efficiency": 0.0,
                        "used_area": 0.0,
                        "waste_area": 0.0,
                        "total_board_area": 0.0
                    }
                }
                continue

            std_heights = None
            if group_std_heights and key in group_std_heights:
                std_heights = group_std_heights[key]

            # Proviamo diversi solutori e ordinamenti delle domande per trovare il migliore
            best_layout = None
            best_score = (float('inf'), float('inf'), float('inf')) # (unplaced, boards_used, waste_area)

            # Rileva il rispetto della venatura per questo specifico gruppo
            if stocks_gruppo and "has_grain" in stocks_gruppo[0]:
                group_respect_grain = stocks_gruppo[0]["has_grain"]
            elif isinstance(respect_grain, dict):
                group_respect_grain = respect_grain.get(key, False)
            else:
                group_respect_grain = respect_grain

            # Strategie di ordinamento: altezza decrescente, area decrescente, larghezza decrescente
            sorting_strategies = [
                lambda p: (-p["height"], -p["width"]),
                lambda p: (-(p["width"] * p["height"]), -p["height"]),
                lambda p: (-p["width"], -p["height"])
            ]

            # Definiamo le configurazioni di solutori da provare
            if machine_type == "pantografo":
                solvers_config = [
                    ("nesting", None, None)
                ]
            else:
                solvers_config = [
                    ("guillotine", "BSSF", "SAS"),
                    ("guillotine", "BAF", "SAS"),
                    ("guillotine", "BSSF", "LAS"),
                    ("guillotine", "BAF", "LAS"),
                    ("guillotine", "BLSF", "SAS"),
                    ("guillotine", "BLSF", "LAS"),
                    ("shelf", None, None)
                ]

            for strategy in sorting_strategies:
                sorted_demands = sorted(demands_gruppo, key=strategy)
                
                for solver_type, rect_choice, split_heuristic in solvers_config:
                    # Copia profonda delle lastre per non sporcare i tentativi
                    available_stocks = copy.deepcopy(stocks_gruppo)
                    
                    if solver_type == "shelf":
                        used_boards, unplaced = self._solve_shelf_packing(
                            available_stocks, sorted_demands, group_respect_grain, min_semi_size, std_heights
                        )
                    elif solver_type == "nesting":
                        used_boards, unplaced = self._solve_nesting_packing(
                            available_stocks, sorted_demands, group_respect_grain, min_semi_size, std_heights
                        )
                    else:
                        used_boards, unplaced = self._solve_guillotine_packing(
                            available_stocks, sorted_demands, group_respect_grain, 
                            rect_choice, split_heuristic, min_semi_size, std_heights
                        )
                        
                    # Calcola il punteggio di questa soluzione
                    boards_used = len(used_boards)
                    total_waste_area = 0.0
                    for ub in used_boards:
                        total_waste_area += ub["waste_area"]
                    # Penalizziamo anche l'area dei pezzi non piazzati per essere consistenti
                    for up in unplaced:
                        total_waste_area += up["width"] * up["height"]

                    score = (len(unplaced), boards_used, total_waste_area)
                    
                    if score < best_score:
                        best_score = score
                        best_layout = (used_boards, unplaced)

            used_boards, unplaced = best_layout
            
            # Ripristina le dimensioni originali del pannello e shifta le coordinate dei pezzi/tagli/semilavorati
            for ub in used_boards:
                # Ordina stabilmente i tagli per livello gerarchico (progressione fisica dei tagli)
                if "cuts" in ub and ub["cuts"]:
                    ub["cuts"].sort(key=lambda c: c.get("level", 1))
                    for idx, c in enumerate(ub["cuts"]):
                        c["step"] = idx + 1

                board = ub["board"]
                if board.get("stock_type") == "whole_board":
                    rv = board.get("rifilo_verticale", 0.0)
                    rh = board.get("rifilo_orizzontale", 0.0)
                    if rv > 0 or rh > 0:
                        board["width"] = board.get("width_original_panel", board["width"])
                        board["height"] = board.get("height_original_panel", board["height"])
                        
                        # Shifta i pezzi posizionati
                        for p in ub["placed_pieces"]:
                            p["x"] += rv
                            p["y"] += rh
                            
                        # Shifta le linee di taglio
                        for c in ub["cuts"]:
                            c["x1"] += rv
                            c["x2"] += rv
                            c["y1"] += rh
                            c["y2"] += rh
                            
                        # Shifta i semilavorati
                        for s in ub["new_semilavorati"]:
                            if "x" in s and "y" in s:
                                s["x"] += rv
                                s["y"] += rh
            
            # Calcola riepilogo gruppo
            group_board_area = 0.0
            group_placed_area = 0.0
            for ub in used_boards:
                group_board_area += ub["board"]["width"] * ub["board"]["height"]
                group_placed_area += ub["used_area"]

            group_waste = group_board_area - group_placed_area
            group_efficiency = (group_placed_area / group_board_area * 100) if group_board_area > 0 else 0.0
            
            is_bar_group = False
            if group_std_heights and key in group_std_heights:
                is_bar_group = True
            else:
                is_bar_group = any(s.get("stock_type") == "semilavorato_bar" for s in stocks_gruppo)
                
            if is_bar_group:
                for up in unplaced:
                    up["width"] = up["height_raw"]  # W (larghezza)
                    up["height"] = up["width_raw"]  # H (altezza)
                for ub in used_boards:
                    for p in ub["placed_pieces"]:
                        p["width_original"] = p["h"]  # W (larghezza)
                        p["height_original"] = p["w"] # H (altezza)

            risultati_gruppi[key] = {
                "used_boards": used_boards,
                "unplaced_pieces": unplaced,
                "summary": {
                    "total_boards_used": len(used_boards),
                    "efficiency": round(group_efficiency, 2),
                    "used_area": round(group_placed_area, 2),
                    "waste_area": round(group_waste, 2),
                    "total_board_area": round(group_board_area, 2)
                }
            }
            
            totale_area_lastre += group_board_area
            totale_area_pezzi += group_placed_area
            totale_area_scarto += group_waste

        # Riepilogo generale di tutta la commessa
        efficienza_generale = (totale_area_pezzi / totale_area_lastre * 100) if totale_area_lastre > 0 else 0.0
        
        return {
            "gruppi": risultati_gruppi,
            "summary_generale": {
                "totale_area_lastre": round(totale_area_lastre, 2),
                "totale_area_pezzi": round(totale_area_pezzi, 2),
                "totale_area_scarto": round(totale_area_scarto, 2),
                "efficienza_media": round(efficienza_generale, 2)
            }
        }

    def _solve_shelf_packing(self, stocks, demands, respect_grain, min_semi_size, std_heights=None):
        """
        Algoritmo euristico Shelf 2D con tagli a ghigliottina standard.
        """
        used_boards = []
        unplaced = []

        # Scorri ogni pezzo da posizionare
        for piece in demands:
            placed = False
            
            # Cerca di inserirlo in una delle lastre già iniziate
            for ub in used_boards:
                if self._try_place_on_board(ub, piece, respect_grain, std_heights):
                    placed = True
                    break
            
            # Se non ci sta, prova ad avviare una nuova lastra dallo stock disponibile
            if not placed:
                new_board_index = -1
                for idx, board in enumerate(stocks):
                    is_whole = (board.get("stock_type") == "whole_board")
                    use_sfrido = self.sfrido if is_whole else 0.0
                    w_b, h_b = board["width"], board["height"]
                    orientations = self._get_orientations(board, piece, respect_grain, use_sfrido, self.panel_grain_direction)
                        
                    can_fit = False
                    for w, h in orientations:
                        if w <= w_b and h <= h_b:
                            if self._is_height_allowed(board, h, std_heights, is_used=False):
                                can_fit = True
                                break
                        
                    if can_fit:
                        new_board_index = idx
                        break
                
                if new_board_index != -1:
                    board = stocks.pop(new_board_index)
                    ub = {
                        "board": board,
                        "placed_pieces": [],
                        "shelves": [], # lista di dict: {"y": 0, "height": 720, "width_used": 0, "placed_count": 0}
                        "used_area": 0.0,
                        "waste_area": board["width"] * board["height"]
                    }
                    used_boards.append(ub)
                    self._try_place_on_board(ub, piece, respect_grain, std_heights)
                else:
                    unplaced.append(piece)

        # Calcola le statistiche finali per ciascuna lastra ed estrai i semilavorati
        for ub in used_boards:
            board = ub["board"]
            bw = board["width"]
            bh = board["height"]
            
            board_area = bw * bh
            ub["waste_area"] = round(board_area - ub["used_area"], 2)
            ub["efficiency"] = round((ub["used_area"] / board_area * 100), 2)
            
            # Calcola le linee di taglio per l'algoritmo Shelf
            ub["cuts"] = []
            for idx, shelf in enumerate(ub["shelves"]):
                if idx < len(ub["shelves"]) - 1:
                    cut_y = shelf["y"] + shelf["height"]
                    ub["cuts"].append({
                        "type": "H",
                        "x1": 0.0,
                        "y1": cut_y,
                        "x2": bw,
                        "y2": cut_y,
                        "level": 1,
                        "step": len(ub["cuts"]) + 1
                    })
                shelf_pieces = [p for p in ub["placed_pieces"] if abs(p["y"] - shelf["y"]) < 1e-2]
                shelf_pieces.sort(key=lambda p: p["x"])
                for p_idx, p in enumerate(shelf_pieces):
                    if p_idx < len(shelf_pieces) - 1:
                        cut_x = p["x"] + p["w"]
                        ub["cuts"].append({
                            "type": "V",
                            "x1": cut_x,
                            "y1": shelf["y"],
                            "x2": cut_x,
                            "y2": shelf["y"] + shelf["height"],
                            "level": 2,
                            "step": len(ub["cuts"]) + 1
                        })
            
            # Estrarre i semilavorati per l'algoritmo shelf
            ub["new_semilavorati"] = []
            for shelf in ub["shelves"]:
                w_res = bw - shelf["width_used"]
                h_res = shelf["height"]
                if w_res >= min_semi_size[0] and h_res >= min_semi_size[1]:
                    ub["new_semilavorati"].append({
                        "x": shelf["width_used"],
                        "y": shelf["y"],
                        "width": round(w_res, 2),
                        "height": round(h_res, 2),
                        "thickness": board["thickness"],
                        "color_code": board["color_code"],
                        "color_desc": board["color_desc"]
                    })
            
            current_y = 0
            if ub["shelves"]:
                last_shelf = ub["shelves"][-1]
                current_y = last_shelf["y"] + last_shelf["height"] + self.kerf
            
            h_res = bh - current_y
            if bw >= min_semi_size[0] and h_res >= min_semi_size[1]:
                ub["new_semilavorati"].append({
                    "x": 0.0,
                    "y": current_y,
                    "width": round(bw, 2),
                    "height": round(h_res, 2),
                    "thickness": board["thickness"],
                    "color_code": board["color_code"],
                    "color_desc": board["color_desc"]
                })

        return used_boards, unplaced

    def _try_place_on_board(self, ub, piece, respect_grain, std_heights=None):
        """
        Tenta di posizionare un pezzo su una determinata lastra usata.
        """
        board = ub["board"]
        bw = board["width"]
        bh = board["height"]
        
        is_whole = (board.get("stock_type") == "whole_board")
        use_sfrido = self.sfrido if is_whole else 0.0
        
        pw = piece["width_raw"] + use_sfrido
        ph = piece["height_raw"] + use_sfrido
        
        orientations = self._get_orientations(board, piece, respect_grain, use_sfrido, self.panel_grain_direction)

        # 1. Prova a inserire il pezzo in uno dei ripiani (shelves) esistenti
        for w, h in orientations:
            if not self._is_height_allowed(board, h, std_heights, is_used=True):
                continue
            for shelf in ub["shelves"]:
                needed_w = w if not shelf["placed_count"] else w + self.kerf
                if shelf["width_used"] + needed_w <= bw:
                    if h <= shelf["height"]:
                        x = shelf["width_used"] + (self.kerf if shelf["placed_count"] else 0)
                        y = shelf["y"]
                        
                        ub["placed_pieces"].append({
                            "descrizione": piece["descrizione"],
                            "x": x,
                            "y": y,
                            "w": w,
                            "h": h,
                            "width_original": pw,
                            "height_original": ph,
                            "rotated": (w != pw)
                        })
                        
                        shelf["width_used"] += needed_w
                        shelf["placed_count"] += 1
                        ub["used_area"] += w * h
                        return True

        # 2. Se non entra in nessun ripiano, prova a creare un NUOVO ripiano
        for w, h in orientations:
            if not self._is_height_allowed(board, h, std_heights, is_used=True):
                continue
            current_y = 0
            if ub["shelves"]:
                last_shelf = ub["shelves"][-1]
                current_y = last_shelf["y"] + last_shelf["height"] + self.kerf
                
            if current_y + h <= bh and w <= bw:
                new_shelf = {
                    "y": current_y,
                    "height": h,
                    "width_used": w,
                    "placed_count": 1
                }
                ub["shelves"].append(new_shelf)
                
                ub["placed_pieces"].append({
                    "descrizione": piece["descrizione"],
                    "x": 0.0,
                    "y": current_y,
                    "w": w,
                    "h": h,
                    "width_original": pw,
                    "height_original": ph,
                    "rotated": (w != pw)
                })
                
                ub["used_area"] += w * h
                return True
                
        return False

    def _solve_guillotine_packing(self, stocks, demands, respect_grain, rect_choice, split_heuristic, min_semi_size, std_heights=None):
        """
        Algoritmo Guillotine 2D con euristiche avanzate di inserimento e taglio.
        """
        used_boards = []
        unplaced = []

        for piece in demands:
            best_board_idx = -1
            best_rect_idx = -1
            best_score = float('inf')
            best_orientation = (0.0, 0.0)
            
            # Cerca il miglior rettangolo libero tra le lastre usate esistenti
            for b_idx, ub in enumerate(used_boards):
                is_whole = (ub["board"].get("stock_type") == "whole_board")
                use_sfrido = self.sfrido if is_whole else 0.0
                orientations = self._get_orientations(ub["board"], piece, respect_grain, use_sfrido, self.panel_grain_direction)
                for r_idx, r in enumerate(ub["free_rectangles"]):
                        
                    for w, h in orientations:
                        if w <= r["w"] and h <= r["h"]:
                            if self._is_height_allowed(ub["board"], h, std_heights, is_used=True):
                                # Calcola lo score a seconda dell'euristica scelta
                                if rect_choice == "BSSF":
                                    score = min(r["w"] - w, r["h"] - h)
                                elif rect_choice == "BLSF":
                                    score = max(r["w"] - w, r["h"] - h)
                                elif rect_choice == "BAF":
                                    score = (r["w"] * r["h"]) - (w * h)
                                else:
                                    score = min(r["w"] - w, r["h"] - h)
                                    
                                if score < best_score:
                                    best_score = score
                                    best_board_idx = b_idx
                                    best_rect_idx = r_idx
                                    best_orientation = (w, h)

            if best_board_idx != -1:
                ub = used_boards[best_board_idx]
                r = ub["free_rectangles"].pop(best_rect_idx)
                w, h = best_orientation
                
                is_whole = (ub["board"].get("stock_type") == "whole_board")
                use_sfrido = self.sfrido if is_whole else 0.0
                pw = piece["width_raw"] + use_sfrido
                ph = piece["height_raw"] + use_sfrido
                
                ub["placed_pieces"].append({
                    "descrizione": piece["descrizione"],
                    "x": r["x"],
                    "y": r["y"],
                    "w": w,
                    "h": h,
                    "width_original": pw,
                    "height_original": ph,
                    "rotated": (w != pw)
                })
                ub["used_area"] += w * h
                self._split_free_rectangle(ub, r, w, h, split_heuristic, level=r.get("level", 1))
            else:
                # Se non entra in nessuna lastra già avviata, prova a prenderne una dallo stock
                new_board_index = -1
                for idx, board in enumerate(stocks):
                    is_whole = (board.get("stock_type") == "whole_board")
                    use_sfrido = self.sfrido if is_whole else 0.0
                    w_b, h_b = board["width"], board["height"]
                    orientations = self._get_orientations(board, piece, respect_grain, use_sfrido, self.panel_grain_direction)
                        
                    can_fit = False
                    for w, h in orientations:
                        if w <= w_b and h <= h_b:
                            if self._is_height_allowed(board, h, std_heights, is_used=False):
                                can_fit = True
                                best_orientation = (w, h)
                                break
                    if can_fit:
                         new_board_index = idx
                         break
                         
                if new_board_index != -1:
                    board = stocks.pop(new_board_index)
                    is_whole = (board.get("stock_type") == "whole_board")
                    use_sfrido = self.sfrido if is_whole else 0.0
                    pw = piece["width_raw"] + use_sfrido
                    ph = piece["height_raw"] + use_sfrido
                    
                    ub = {
                        "board": board,
                        "placed_pieces": [],
                        "free_rectangles": [{"x": 0.0, "y": 0.0, "w": board["width"], "h": board["height"], "level": 1}],
                        "cuts": [],
                        "used_area": 0.0,
                        "waste_area": board["width"] * board["height"]
                    }
                    used_boards.append(ub)
                    
                    r = ub["free_rectangles"].pop(0)
                    w, h = best_orientation
                    ub["placed_pieces"].append({
                        "descrizione": piece["descrizione"],
                        "x": r["x"],
                        "y": r["y"],
                        "w": w,
                        "h": h,
                        "width_original": pw,
                        "height_original": ph,
                        "rotated": (w != pw)
                    })
                    ub["used_area"] += w * h
                    self._split_free_rectangle(ub, r, w, h, split_heuristic, level=1)
                else:
                    unplaced.append(piece)

        # Calcola le statistiche e filtra i semilavorati residui
        for ub in used_boards:
            board = ub["board"]
            board_area = board["width"] * board["height"]
            ub["waste_area"] = round(board_area - ub["used_area"], 2)
            ub["efficiency"] = round((ub["used_area"] / board_area * 100), 2)
            
            is_bar = board.get("stock_type") in ["semilavorato_bar", "remnant"]
            if is_bar and ub["placed_pieces"]:
                ub["cuts"] = []
                bw = board["width"]
                bh = board["height"]
                pieces = sorted(ub["placed_pieces"], key=lambda p: p["x"])
                
                # Raggruppiamo i pezzi adiacenti che hanno la stessa altezza
                groups = []
                current_group = [pieces[0]]
                for p in pieces[1:]:
                    if abs(p["h"] - current_group[0]["h"]) < 1e-2:
                        current_group.append(p)
                    else:
                        groups.append(current_group)
                        current_group = [p]
                groups.append(current_group)
                
                # Generiamo i tagli ottimizzati per ciascun gruppo
                for group in groups:
                    x_start = group[0]["x"]
                    x_end = group[-1]["x"] + group[-1]["w"]
                    h_group = group[0]["h"]
                    
                    # 1. Taglio verticale per separare il gruppo dal resto della barra
                    if x_end < bw - 1e-2:
                        ub["cuts"].append({
                            "type": "V",
                            "x1": x_end,
                            "y1": 0.0,
                            "x2": x_end,
                            "y2": bh,
                            "level": 1
                        })
                        
                    # 2. Taglio orizzontale di rifilo unico per l'intero gruppo
                    if bh - h_group >= self.kerf:
                        ub["cuts"].append({
                            "type": "H",
                            "x1": x_start,
                            "y1": h_group,
                            "x2": x_end,
                            "y2": h_group,
                            "level": 2
                        })
                        
                    # 3. Tagli verticali interni per separare i singoli pezzi
                    for p in group[:-1]:
                        cut_x = p["x"] + p["w"]
                        ub["cuts"].append({
                            "type": "V",
                            "x1": cut_x,
                            "y1": 0.0,
                            "x2": cut_x,
                            "y2": h_group,
                            "level": 3
                        })
            
            ub["new_semilavorati"] = []
            for r in ub["free_rectangles"]:
                if r["w"] >= min_semi_size[0] and r["h"] >= min_semi_size[1]:
                    ub["new_semilavorati"].append({
                        "x": r["x"],
                        "y": r["y"],
                        "width": round(r["w"], 2),
                        "height": round(r["h"], 2),
                        "thickness": board["thickness"],
                        "color_code": board["color_code"],
                        "color_desc": board["color_desc"]
                    })
                    
        return used_boards, unplaced

    def _split_free_rectangle(self, ub, r, w, h, split_heuristic, level=1):
        rx, ry, rw, rh = r["x"], r["y"], r["w"], r["h"]
        
        is_bar = ub.get("board", {}).get("stock_type") in ["semilavorato_bar", "remnant"]
        if is_bar:
            split_style = "VS"
        elif split_heuristic == "SAS":
            split_style = "VS" if (rw - w) < (rh - h) else "HS"
        elif split_heuristic == "LAS":
            split_style = "VS" if (rw - w) > (rh - h) else "HS"
        else:
            split_style = split_heuristic
            
        if split_style == "HS":
            # Taglio Orizzontale primario, Taglio Verticale secondario nella parte superiore
            if rh - h >= self.kerf:
                ub["cuts"].append({
                    "type": "H",
                    "x1": rx,
                    "y1": ry + h,
                    "x2": rx + rw,
                    "y2": ry + h,
                    "level": level,
                    "step": len(ub["cuts"]) + 1
                })
            if rw - w >= self.kerf:
                ub["cuts"].append({
                    "type": "V",
                    "x1": rx + w,
                    "y1": ry,
                    "x2": rx + w,
                    "y2": ry + h,
                    "level": level,
                    "step": len(ub["cuts"]) + 1
                })
                
            if rw - w - self.kerf > 0:
                ub["free_rectangles"].append({
                    "x": rx + w + self.kerf,
                    "y": ry,
                    "w": rw - w - self.kerf,
                    "h": h,
                    "level": level + 1
                })
            if rh - h - self.kerf > 0:
                ub["free_rectangles"].append({
                    "x": rx,
                    "y": ry + h + self.kerf,
                    "w": rw,
                    "h": rh - h - self.kerf,
                    "level": level + 1
                })
        else:
            # Taglio Verticale primario, Taglio Orizzontale secondario nella parte sinistra
            if rw - w >= self.kerf:
                ub["cuts"].append({
                    "type": "V",
                    "x1": rx + w,
                    "y1": ry,
                    "x2": rx + w,
                    "y2": ry + rh,
                    "level": level,
                    "step": len(ub["cuts"]) + 1
                })
            if rh - h >= self.kerf:
                ub["cuts"].append({
                    "type": "H",
                    "x1": rx,
                    "y1": ry + h,
                    "x2": rx + w,
                    "y2": ry + h,
                    "level": level,
                    "step": len(ub["cuts"]) + 1
                })
                
            if rw - w - self.kerf > 0:
                ub["free_rectangles"].append({
                    "x": rx + w + self.kerf,
                    "y": ry,
                    "w": rw - w - self.kerf,
                    "h": rh,
                    "level": level + 1
                })
            if rh - h - self.kerf > 0:
                ub["free_rectangles"].append({
                    "x": rx,
                    "y": ry + h + self.kerf,
                    "w": w,
                    "h": rh - h - self.kerf,
                    "level": level + 1
                })

    def _is_height_allowed(self, board, piece_h, std_heights, is_used=False):
        """
        Verifica se la larghezza dell'anta (rappresentata da piece_h nel layout orizzontale)
        è consentita sulla barra o residuo in base alle altezze standard.
        """
        if not board or board.get("stock_type") not in ["semilavorato_bar", "remnant"] or not std_heights:
            return True

        board_h = float(board.get("height", 0))

        # Se il pezzo supera l'altezza fisica della barra corrente, ovviamente non ci sta
        if piece_h > board_h:
            return False

        # Se la barra è già in uso, qualsiasi pezzo che ci sta fisicamente è ammesso
        if is_used:
            return True
            
        # Trova la larghezza standard target per il pezzo (piece_h)
        piece_target = None
        for sh in std_heights:
            if piece_h <= sh:
                piece_target = sh
                break
        if piece_target is None:
            piece_target = max(std_heights)
            
        # Trova la larghezza standard target per la barra/residuo (board)
        board_target = None
        for sh in std_heights:
            if board_h <= sh:
                board_target = sh
                break
        if board_target is None:
            board_target = max(std_heights)
            
        # Non possiamo iniziare una nuova barra se appartiene ad uno standard superiore
        # (es. pezzo da 297 su barra da 897)
        if board_target > piece_target:
            return False
            
        return True

    def _solve_nesting_packing(self, stocks, demands, respect_grain, min_semi_size, std_heights=None):
        """
        Algoritmo di Nesting (MaxRects) per Pantografo.
        Non impone vincoli di taglio a ghigliottina, consentendo il posizionamento libero.
        """
        used_boards = []
        unplaced = []
        
        for piece in demands:
            best_board_idx = -1
            best_rect_idx = -1
            best_score = float('inf')
            best_orientation = (0.0, 0.0)
            
            # Cerca tra i free_rectangles delle lastre già utilizzate
            for b_idx, ub in enumerate(used_boards):
                is_whole = (ub["board"].get("stock_type") == "whole_board")
                use_sfrido = self.sfrido if is_whole else 0.0
                orientations = self._get_orientations(ub["board"], piece, respect_grain, use_sfrido, self.panel_grain_direction)
                for r_idx, r in enumerate(ub["free_rectangles"]):
                        
                    for w, h in orientations:
                        if w <= r["w"] and h <= r["h"]:
                            if self._is_height_allowed(ub["board"], h, std_heights, is_used=True):
                                # Euristica Best Short Side Fit (BSSF)
                                score = min(r["w"] - w, r["h"] - h)
                                if score < best_score:
                                    best_score = score
                                    best_board_idx = b_idx
                                    best_rect_idx = r_idx
                                    best_orientation = (w, h)
                                    
            if best_board_idx != -1:
                ub = used_boards[best_board_idx]
                w, h = best_orientation
                r = ub["free_rectangles"][best_rect_idx]
                px, py = r["x"], r["y"]
                
                is_whole = (ub["board"].get("stock_type") == "whole_board")
                use_sfrido = self.sfrido if is_whole else 0.0
                pw = piece["width_raw"] + use_sfrido
                ph = piece["height_raw"] + use_sfrido
                
                ub["placed_pieces"].append({
                    "descrizione": piece["descrizione"],
                    "x": px,
                    "y": py,
                    "w": w,
                    "h": h,
                    "width_original": pw,
                    "height_original": ph,
                    "rotated": (w != pw)
                })
                ub["used_area"] += w * h
                
                # Aggiorna i free_rectangles per questa lastra
                self._split_maxrects_free_rectangles(ub["free_rectangles"], px, py, w, h)
            else:
                # Se non entra in nessuna lastra già avviata, prova a prenderne una nuova dallo stock
                new_board_index = -1
                for idx, board in enumerate(stocks):
                    is_whole = (board.get("stock_type") == "whole_board")
                    use_sfrido = self.sfrido if is_whole else 0.0
                    w_b, h_b = board["width"], board["height"]
                    orientations = self._get_orientations(board, piece, respect_grain, use_sfrido, self.panel_grain_direction)
                        
                    can_fit = False
                    for w, h in orientations:
                        if w <= w_b and h <= h_b:
                            if self._is_height_allowed(board, h, std_heights, is_used=False):
                                can_fit = True
                                best_orientation = (w, h)
                                break
                    if can_fit:
                        new_board_index = idx
                        break
                        
                if new_board_index != -1:
                    board = stocks.pop(new_board_index)
                    is_whole = (board.get("stock_type") == "whole_board")
                    use_sfrido = self.sfrido if is_whole else 0.0
                    pw = piece["width_raw"] + use_sfrido
                    ph = piece["height_raw"] + use_sfrido
                    w, h = best_orientation
                    
                    ub = {
                        "board": board,
                        "placed_pieces": [],
                        "free_rectangles": [{"x": 0.0, "y": 0.0, "w": board["width"], "h": board["height"]}],
                        "cuts": [], # Nessun taglio a ghigliottina
                        "used_area": 0.0,
                        "waste_area": board["width"] * board["height"]
                    }
                    used_boards.append(ub)
                    
                    px, py = 0.0, 0.0
                    ub["placed_pieces"].append({
                        "descrizione": piece["descrizione"],
                        "x": px,
                        "y": py,
                        "w": w,
                        "h": h,
                        "width_original": pw,
                        "height_original": ph,
                        "rotated": (w != pw)
                    })
                    ub["used_area"] += w * h
                    
                    self._split_maxrects_free_rectangles(ub["free_rectangles"], px, py, w, h)
                else:
                    unplaced.append(piece)
                    
        # Calcola statistiche e filtri semilavorati residui
        for ub in used_boards:
            board = ub["board"]
            board_area = board["width"] * board["height"]
            ub["waste_area"] = round(board_area - ub["used_area"], 2)
            ub["efficiency"] = round((ub["used_area"] / board_area * 100), 2)
            
            # Filtra i semilavorati dai free_rectangles
            # Per evitare semilavorati sovrapposti, li ordiniamo per area decrescente
            # e li prendiamo solo se non si sovrappongono con semilavorati già selezionati.
            ub["new_semilavorati"] = []
            candidate_semis = []
            for r in ub["free_rectangles"]:
                if r["w"] >= min_semi_size[0] and r["h"] >= min_semi_size[1]:
                    candidate_semis.append(r)
                    
            candidate_semis.sort(key=lambda r: -(r["w"] * r["h"]))
            selected_semis = []
            for r in candidate_semis:
                overlaps = False
                for sel in selected_semis:
                    if (r["x"] < sel["x"] + sel["w"] and r["x"] + r["w"] > sel["x"] and
                        r["y"] < sel["y"] + sel["h"] and r["y"] + r["h"] > sel["y"]):
                        overlaps = True
                        break
                if not overlaps:
                    selected_semis.append(r)
                    ub["new_semilavorati"].append({
                        "x": r["x"],
                        "y": r["y"],
                        "width": round(r["w"], 2),
                        "height": round(r["h"], 2),
                        "thickness": board["thickness"],
                        "color_code": board["color_code"],
                        "color_desc": board["color_desc"]
                    })
                    
        return used_boards, unplaced

    def _split_maxrects_free_rectangles(self, free_rectangles, px, py, w, h):
        """
        Suddivide tutti i rettangoli liberi che si sovrappongono con il pezzo posizionato [px, py, px+w, py+h].
        Prende in considerazione anche il kerf (spessore lama) per evitare che pezzi adiacenti si sovrappongano.
        """
        new_rects = []
        # La zona occupata dal pezzo più il kerf.
        ox1, oy1 = px, py
        ox2, oy2 = px + w + self.kerf, py + h + self.kerf
        
        rects_to_process = list(free_rectangles)
        free_rectangles.clear()
        
        for r in rects_to_process:
            rx1, ry1 = r["x"], r["y"]
            rx2, ry2 = r["x"] + r["w"], r["y"] + r["h"]
            
            # Controlla se c'è sovrapposizione
            if rx1 < ox2 and rx2 > ox1 and ry1 < oy2 and ry2 > oy1:
                # Genera i sottorettangoli
                # Sinistra
                if ox1 > rx1:
                    new_rects.append({"x": rx1, "y": ry1, "w": ox1 - rx1, "h": r["h"]})
                # Destra
                if ox2 < rx2:
                    new_rects.append({"x": ox2, "y": ry1, "w": rx2 - ox2, "h": r["h"]})
                # Sotto
                if oy1 > ry1:
                    new_rects.append({"x": rx1, "y": ry1, "w": r["w"], "h": oy1 - ry1})
                # Sopra
                if oy2 < ry2:
                    new_rects.append({"x": rx1, "y": oy2, "w": r["w"], "h": ry2 - oy2})
            else:
                free_rectangles.append(r)
                
        # Aggiungi i nuovi rettangoli generati
        for nr in new_rects:
            if nr["w"] > 0 and nr["h"] > 0:
                free_rectangles.append(nr)
                
        # Rimuovi i rettangoli contenuti interamente in altri
        pruned_rects = []
        for i, r1 in enumerate(free_rectangles):
            is_contained = False
            for j, r2 in enumerate(free_rectangles):
                if i != j:
                    if (r1["x"] >= r2["x"] and r1["y"] >= r2["y"] and
                        r1["x"] + r1["w"] <= r2["x"] + r2["w"] and
                        r1["y"] + r1["h"] <= r2["y"] + r2["h"]):
                        is_contained = True
                        break
            if not is_contained:
                pruned_rects.append(r1)
                
        free_rectangles[:] = pruned_rects
