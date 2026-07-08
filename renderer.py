import tkinter as tk

class LayoutRenderer:
    def __init__(self):
        # Palette colori premium per i vari materiali e stati
        self.color_palette = {
            "board_bg": "#f5f6fa",        # Sfondo generale canvas
            "panel_raw": "#dcdde1",       # Pannello grezzo di sfondo (scarto)
            "piece_bg": "#487eb0",        # Pezzo posizionato (blu elegante)
            "piece_fg": "#ffffff",        # Testo pezzo
            "piece_border": "#273c75",    # Bordo pezzo
            "rotated_bg": "#e1b12c",      # Pezzo ruotato (giallo/oro)
            "rotated_border": "#44bd32",  # Bordo pezzo ruotato
            "cut_line": "#e84118",        # Linee di taglio (rosso)
            "text_color": "#2f3640",
            "semilavorato_bg": "#badc58",  # Semilavorato recuperabile (verde)
            "semilavorato_border": "#6ab04c",
            "semilavorato_fg": "#2c3e50"
        }

    def draw_layout(self, canvas, layout_data, padding=20):
        """
        Disegna lo schema di taglio sul Canvas di tkinter.
        
        Parametri:
        - canvas: widget tkinter.Canvas
        - layout_data: dizionario contenente la lastra e i pezzi posizionati.
        """
        # Svuota il canvas
        canvas.delete("all")
        
        if not layout_data:
            canvas.create_text(
                canvas.winfo_width() / 2, 
                canvas.winfo_height() / 2, 
                text="Nessun dato di taglio da visualizzare", 
                fill=self.color_palette["text_color"],
                font=("Segoe UI", 12)
            )
            return

        import copy
        layout_data = copy.deepcopy(layout_data)
        board = layout_data["board"]
        
        is_bar = (board.get("stock_type") == "semilavorato_bar") or \
                 (board.get("stock_type") == "remnant" and min(board["width"], board["height"]) < 1300.0)
                 
        if is_bar and board["width"] > board["height"]:
            bw, bh = board["width"], board["height"]
            board["width"] = bh
            board["height"] = bw
            
            for p in layout_data["placed_pieces"]:
                px, py, pw, ph = p["x"], p["y"], p["w"], p["h"]
                p["x"] = py
                p["y"] = px
                p["w"] = ph
                p["h"] = pw
                if "width_original" in p and "height_original" in p:
                    p["width_original"], p["height_original"] = p["height_original"], p["width_original"]
                
            for c in layout_data.get("cuts", []):
                cx1, cy1, cx2, cy2 = c["x1"], c["y1"], c["x2"], c["y2"]
                c["x1"] = cy1
                c["y1"] = cx1
                c["x2"] = cy2
                c["y2"] = cx2
                c["type"] = "V" if c["type"] == "H" else "H"
                
            for s in layout_data.get("new_semilavorati", []):
                sx, sy, sw, sh = s.get("x", 0), s.get("y", 0), s["width"], s["height"]
                s["x"] = sy
                s["y"] = sx
                s["width"] = sh
                s["height"] = sw

        pieces = layout_data["placed_pieces"]
        shelves = layout_data.get("shelves", [])
        
        bw = board["width"]
        bh = board["height"]
        
        # Dimensione attuale del Canvas
        canvas_w = canvas.winfo_width()
        canvas_h = canvas.winfo_height()
        
        # Se il canvas non è ancora stato disegnato a schermo, usa dimensioni di default
        if canvas_w <= 1:
            canvas_w = 600
        if canvas_h <= 1:
            canvas_h = 400
            
        # Calcola i fattori di scala per far entrare la lastra nel canvas lasciando del padding
        usable_w = canvas_w - (2 * padding)
        usable_h = canvas_h - (2 * padding)
        
        scale_x = usable_w / bw
        scale_y = usable_h / bh
        scale = min(scale_x, scale_y) # Scala uniforme per non deformare il disegno
        
        # Centra la lastra nel canvas
        offset_x = padding + (usable_w - (bw * scale)) / 2
        offset_y = padding + (usable_h - (bh * scale)) / 2
        
        # Helper per convertire coordinate reali in coordinate canvas
        def to_canvas_coords(x, y, w, h):
            cx1 = offset_x + (x * scale)
            cy1 = offset_y + (y * scale)
            cx2 = cx1 + (w * scale)
            cy2 = cy1 + (h * scale)
            return cx1, cy1, cx2, cy2

        # 1. Disegna il pannello grezzo di sfondo (le parti non coperte saranno "scarto")
        bx1, by1, bx2, by2 = to_canvas_coords(0, 0, bw, bh)
        is_virtual = (board.get("_source_type") == "barre_virtual") or (board.get("id") == "BARRA_VIRTUALE_DUMMY") or ("virtual" in str(board.get("id")).lower())
        
        panel_color = "#fce4e4" if is_virtual else self.color_palette["panel_raw"]
        outline_color = "#e84118" if is_virtual else "#7f8c8d"
        outline_width = 3 if is_virtual else 2
        
        canvas.create_rectangle(
            bx1, by1, bx2, by2,
            fill=panel_color,
            outline=outline_color,
            width=outline_width,
            tags="board"
        )
        
        # Etichetta dimensioni pannello
        color_desc = board.get("color_desc", "")
        color_suffix = f" - {color_desc}" if color_desc else ""
        qty_mult = layout_data.get("qty_multiplier", 1)
        qty_str = f" x {qty_mult}" if qty_mult > 1 else ""
        label_text = f"Lastra: {int(bh)} x {int(bw)} mm{color_suffix}{qty_str}"
        if is_virtual:
            label_text += " [MANCANTE - DA ACQUISTARE]"
            text_color = "#e84118"
        else:
            text_color = self.color_palette["text_color"]
            
        canvas.create_text(
            offset_x + (bw * scale) / 2,
            offset_y - 8,
            text=label_text,
            fill=text_color,
            font=("Segoe UI", 10, "bold")
        )

        # 1.5. Disegna i semilavorati recuperabili (prima dei pezzi per metterli in secondo piano se si sovrappongono leggermente)
        new_semis = layout_data.get("new_semilavorati", [])
        for s in new_semis:
            if "x" in s and "y" in s:
                sx1, sy1, sx2, sy2 = to_canvas_coords(s["x"], s["y"], s["width"], s["height"])
                canvas.create_rectangle(
                    sx1, sy1, sx2, sy2,
                    fill=self.color_palette["semilavorato_bg"],
                    outline=self.color_palette["semilavorato_border"],
                    width=1.5,
                    dash=(4, 2),
                    tags="semilavorato"
                )
                sw_canvas = sx2 - sx1
                sh_canvas = sy2 - sy1
                if sh_canvas > 20 and sw_canvas > 40:
                    canvas.create_text(
                        sx1 + sw_canvas / 2,
                        sy1 + sh_canvas / 2,
                        text=f"Recupero\n{int(s['width'])}x{int(s['height'])}",
                        fill=self.color_palette["semilavorato_fg"],
                        font=("Segoe UI", 8, "italic"),
                        width=sw_canvas - 4
                    )

        # 2. Disegna i pezzi posizionati
        for p in pieces:
            px1, py1, px2, py2 = to_canvas_coords(p["x"], p["y"], p["w"], p["h"])
            
            # Seleziona il colore a seconda che sia ruotato o meno
            is_rotated = p.get("rotated", False)
            bg_color = self.color_palette["rotated_bg"] if is_rotated else self.color_palette["piece_bg"]
            border_color = self.color_palette["rotated_border"] if is_rotated else self.color_palette["piece_border"]
            
            canvas.create_rectangle(
                px1, py1, px2, py2,
                fill=bg_color,
                outline=border_color,
                width=1.5,
                tags="piece"
            )
            
            # Calcola le dimensioni visive sul canvas per il testo
            pw_canvas = px2 - px1
            ph_canvas = py2 - py1
            
            desc_text = p.get("descrizione", "Pezzo")
            w_val = int(p["w"])
            h_val = int(p["h"])
            
            # Se il pezzo è piccolo/medio, uniamo descrizione e quote in un unico blocco multiriga centrato
            if ph_canvas < 55 or pw_canvas < 95:
                if ph_canvas > 28 and pw_canvas > 35:
                    # Mostra descrizione + quote su due righe
                    combined_text = f"{desc_text}\n{w_val}x{h_val}"
                    canvas.create_text(
                        px1 + pw_canvas / 2,
                        py1 + ph_canvas / 2,
                        text=combined_text,
                        fill=self.color_palette["piece_fg"],
                        font=("Segoe UI", 8, "bold"),
                        justify=tk.CENTER,
                        width=pw_canvas - 4
                    )
                elif ph_canvas > 15 and pw_canvas > 30:
                    # Se molto piccolo in altezza, mostra solo le quote
                    canvas.create_text(
                        px1 + pw_canvas / 2,
                        py1 + ph_canvas / 2,
                        text=f"{w_val}x{h_val}",
                        fill=self.color_palette["piece_fg"],
                        font=("Segoe UI", 7, "bold"),
                        width=pw_canvas - 2
                    )
            else:
                # Per pezzi grandi, teniamo i testi separati ma ottimizzati per evitare sovrapposizioni
                # 1. Descrizione (leggermente spostata verso l'alto per non toccare la larghezza in basso)
                canvas.create_text(
                    px1 + pw_canvas / 2,
                    py1 + ph_canvas / 2 - 5,
                    text=desc_text,
                    fill=self.color_palette["piece_fg"],
                    font=("Segoe UI", 9, "bold"),
                    width=pw_canvas - 20
                )
                
                # 2. Larghezza sul lato orizzontale (in basso, centrato orizzontalmente)
                canvas.create_text(
                    px1 + pw_canvas / 2,
                    py2 - 18,
                    text=str(w_val),
                    fill=self.color_palette["piece_fg"],
                    font=("Segoe UI", 8)
                )
                
                # 3. Altezza sul lato verticale (a sinistra, centrato verticalmente, ruotato di 90 gradi)
                canvas.create_text(
                    px1 + 18,
                    py1 + ph_canvas / 2,
                    text=str(h_val),
                    fill=self.color_palette["piece_fg"],
                    font=("Segoe UI", 8),
                    angle=90
                )

        # 3. Disegna le linee di taglio principali (Ghigliottina)
        cuts = layout_data.get("cuts", [])
        if cuts:
            for c in cuts:
                cx1, cy1, _, _ = to_canvas_coords(c["x1"], c["y1"], 0, 0)
                cx2, cy2, _, _ = to_canvas_coords(c["x2"], c["y2"], 0, 0)
                canvas.create_line(
                    cx1, cy1, cx2, cy2,
                    fill=self.color_palette["cut_line"],
                    dash=(5, 3),
                    width=1.5,
                    tags="cut"
                )
                
                # Disegna il numero dello step al centro della linea di taglio
                from data_manager import DataManager
                config = DataManager().config
                show_progression = config.get("show_cut_progression", True)
                
                step_num = c.get("step")
                if show_progression and step_num is not None:
                    mid_x = (cx1 + cx2) / 2
                    mid_y = (cy1 + cy2) / 2
                    canvas.create_oval(
                        mid_x - 9, mid_y - 9, mid_x + 9, mid_y + 9,
                        fill="#ffffff",
                        outline=self.color_palette["cut_line"],
                        width=1.5,
                        tags="cut_step"
                    )
                    canvas.create_text(
                        mid_x, mid_y,
                        text=str(step_num),
                        fill=self.color_palette["cut_line"],
                        font=("Segoe UI", 8, "bold"),
                        tags="cut_step"
                    )
        else:
            # Linee orizzontali dei ripiani (shelves) (vecchio algoritmo Shelf)
            for idx, shelf in enumerate(shelves):
                if idx < len(shelves) - 1:
                    cut_y = shelf["y"] + shelf["height"]
                    cx1, cy1, cx2, cy2 = to_canvas_coords(0, cut_y, bw, 0)
                    canvas.create_line(
                        cx1, cy1, cx2, cy1,
                        fill=self.color_palette["cut_line"],
                        dash=(5, 3),
                        width=1.5,
                        tags="cut"
                    )
                    
                # Disegna le linee verticali di ogni pezzo all'interno del ripiano
                shelf_pieces = [p for p in pieces if abs(p["y"] - shelf["y"]) < 1e-2]
                shelf_pieces.sort(key=lambda p: p["x"])
                
                for p_idx, p in enumerate(shelf_pieces):
                    if p_idx < len(shelf_pieces) - 1:
                        cut_x = p["x"] + p["w"]
                        cx1, cy1, cx2, cy2 = to_canvas_coords(cut_x, shelf["y"], 0, shelf["height"])
                        canvas.create_line(
                            cx1, cy1, cx1, cy2,
                            fill=self.color_palette["cut_line"],
                            dash=(5, 3),
                            width=1.5,
                            tags="cut"
                        )
