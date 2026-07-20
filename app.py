import os
import sys
import copy
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from data_manager import DataManager
from optimizer import CuttingOptimizer
from renderer import LayoutRenderer

class CutMobApp:
    def __init__(self, root):
        self.root = root
        self.APP_VERSION = "2.1.5"
        self.root.title("CutMob - Ottimizzatore di Taglio Pannelli")
        self.root.geometry("1100x700")
        self.root.minsize(900, 600)
        
        # Inizializza DataManager e Renderer
        self.data_manager = DataManager()
        
        # Controllo della licenza all'avvio
        if not self.check_license_startup():
            self.root.destroy()
            sys.exit(0)
            
        self.renderer = LayoutRenderer()
        self.optimizer = CuttingOptimizer()
        
        # Stato dell'applicazione e filtri
        self.current_order = []
        self.optimization_results = None
        self.selected_group_key = None
        self.selected_board_idx = 0
        self.panel_production_list = []
        self.current_commessa_id = None
        self.current_commessa_name = ""
        self.current_commessa_status = "Aperta"
        self.filters_barre = {}
        self.filters_semi = {}
        self.filters_commesse = {}
        self.filters_pieces = {}
        self.last_html_export_path = None
        self.last_pdf_export_path = None
        
        # Configura lo stile grafico premium
        self._configure_styles()
        
        # Costruisci l'interfaccia
        self._create_widgets()
        
        # Carica dati iniziali
        self.reload_magazzino_tables()
        self.update_client_display()
        self.update_import_features()
        
        # Avvia il controllo degli aggiornamenti in asincrono
        self.latest_version_info = None
        self.check_for_updates_async()
        
        # Associa i tasti globali
        self.root.bind_all("<F1>", self.show_help_dialog)
        self.root.bind_all("<F4>", self.toggle_cut_progression)

    def update_client_display(self):
        client_name = self.data_manager.config.get("client_name", "")
        if client_name:
            self.root.title(f"CutMob Panel per {client_name}")
            self.lbl_client.configure(text=f"per {client_name}")
        else:
            self.root.title("CutMob Panel")
            self.lbl_client.configure(text="")

    def update_import_features(self):
        import_enabled = self.data_manager.config.get("import_enabled", True)
        state = tk.NORMAL if import_enabled else tk.DISABLED
        
        self.btn_import_barre.configure(state=state)
        self.btn_import_semi.configure(state=state)
        
        # Aggiorna anche lo stato di import_csv in base alla commessa corrente
        self.on_commessa_status_change()

    def _configure_styles(self):
        self.style = ttk.Style(self.root)
        self.style.theme_use("clam")
        
        # Palette colori premium
        self.bg_primary = "#f5f6fa"
        self.bg_card = "#ffffff"
        self.accent_color = "#273c75"
        self.accent_light = "#487eb0"
        self.text_color = "#2f3640"
        
        self.root.configure(bg=self.bg_primary)
        
        # Configurazione stili widget
        self.style.configure(".", font=("Segoe UI", 10), background=self.bg_primary, foreground=self.text_color)
        self.style.configure("TFrame", background=self.bg_primary)
        self.style.configure("Card.TFrame", background=self.bg_card, relief="flat", borderwidth=0)
        
        # Notebook (Tab)
        self.style.configure("TNotebook", background=self.bg_primary, borderwidth=0)
        self.style.configure("TNotebook.Tab", background=self.bg_primary, foreground=self.text_color, 
                             padding=[15, 6], font=("Segoe UI", 10, "bold"), borderwidth=0)
        self.style.map("TNotebook.Tab",
                       background=[("selected", self.accent_color), ("active", self.accent_light)],
                       foreground=[("selected", "#ffffff"), ("active", "#ffffff")])
        
        # Pulsanti
        self.style.configure("TButton", font=("Segoe UI", 10, "bold"), borderwidth=0, padding=[12, 6],
                             background=self.accent_color, foreground="#ffffff")
        self.style.map("TButton",
                       background=[("active", self.accent_light), ("disabled", "#bdc3c7")],
                       foreground=[("active", "#ffffff"), ("disabled", "#7f8c8d")])
        
        self.style.configure("Accent.TButton", background=self.accent_light, foreground="#ffffff")
        self.style.configure("Danger.TButton", background="#e84118", foreground="#ffffff")
        self.style.map("Danger.TButton", background=[("active", "#c23616")])
        
        # Treeview (Tabelle)
        self.style.configure("Treeview", font=("Segoe UI", 9), rowheight=24, background="#ffffff", fieldbackground="#ffffff")
        self.style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"), background="#dcdde1", relief="flat")
        self.style.map("Treeview", background=[("selected", self.accent_light)], foreground=[("selected", "#ffffff")])

    def _create_widgets(self):
        # Layout principale: Sidebar a sinistra + Area Contenuto a destra
        self.main_pane = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, bg=self.bg_primary, bd=0, sashwidth=4)
        self.main_pane.pack(fill=tk.BOTH, expand=True)
        
        # --- SIDEBAR (Impostazioni e Parametri) ---
        sidebar = ttk.Frame(self.main_pane, style="Card.TFrame", padding=15)
        self.main_pane.add(sidebar, width=290)
        
        f_title = ttk.Frame(sidebar, style="Card.TFrame")
        f_title.pack(fill=tk.X, pady=(0, 5))
        lbl_title = ttk.Label(f_title, text="CutMob Panel", font=("Segoe UI", 16, "bold"), foreground=self.accent_color, background=self.bg_card)
        lbl_title.pack(side=tk.LEFT)
        btn_settings = ttk.Button(f_title, text="⚙️", width=3, command=self.show_db_settings_dialog)
        btn_settings.pack(side=tk.RIGHT)
        
        
        
        # Carica il logo AIConsulting sotto il titolo
        logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.png")
        if os.path.exists(logo_path):
            try:
                from PIL import Image, ImageTk
                img_pil = Image.open(logo_path)
                orig_w, orig_h = img_pil.size
                
                # Ridimensiona proporzionalmente a target_w = 150px (pari alla larghezza del testo)
                target_w = 150
                ratio = target_w / orig_w
                target_h = int(orig_h * ratio)
                
                # Ridimensionamento ad alta qualità
                img_resized = img_pil.resize((target_w, target_h), Image.Resampling.LANCZOS)
                self.logo_img = ImageTk.PhotoImage(img_resized)
                
                brand_frame = ttk.Frame(sidebar, style="Card.TFrame")
                brand_frame.pack(anchor=tk.W, pady=(0, 5))
                
                lbl_by = ttk.Label(brand_frame, text="By", font=("Segoe UI", 10, "italic"), foreground="#7f8c8d", background=self.bg_card)
                lbl_by.pack(side=tk.LEFT, padx=(0, 10))
                
                lbl_logo = ttk.Label(brand_frame, image=self.logo_img, background=self.bg_card)
                lbl_logo.pack(side=tk.LEFT)
            except Exception as e:
                print(f"Errore caricamento logo con Pillow: {e}. Provo fallback.")
                try:
                    self.logo_img = tk.PhotoImage(file=logo_path)
                    orig_w = self.logo_img.width()
                    target_w = 150
                    scale = round(orig_w / target_w)
                    if scale < 1:
                        scale = 1
                    self.logo_img = self.logo_img.subsample(scale, scale)
                    
                    brand_frame = ttk.Frame(sidebar, style="Card.TFrame")
                    brand_frame.pack(anchor=tk.W, pady=(0, 5))
                    
                    lbl_by = ttk.Label(brand_frame, text="By", font=("Segoe UI", 10, "italic"), foreground="#7f8c8d", background=self.bg_card)
                    lbl_by.pack(side=tk.LEFT, padx=(0, 10))
                    
                    lbl_logo = ttk.Label(brand_frame, image=self.logo_img, background=self.bg_card)
                    lbl_logo.pack(side=tk.LEFT)
                except Exception as ex:
                    print(f"Errore fallback logo: {ex}")
        
        self.lbl_client = ttk.Label(sidebar, text="", font=("Segoe UI", 11, "bold"), foreground=self.accent_color, background=self.bg_card, wraplength=230)
        self.lbl_client.pack(anchor=tk.W, pady=(0, 2))
        
        # Parametri di Ottimizzazione
        lbl_section = ttk.Label(sidebar, text="PARAMETRI DI TAGLIO", font=("Segoe UI", 9, "bold"), foreground="#7f8c8d", background=self.bg_card)
        lbl_section.pack(anchor=tk.W, pady=(5, 2))
        
        # Spessore lama (Kerf)
        config = self.data_manager.config
        ttk.Label(sidebar, text="Kerf (spessore lama mm):", background=self.bg_card).pack(anchor=tk.W, pady=(2, 0))
        self.ent_kerf = ttk.Entry(sidebar)
        self.ent_kerf.insert(0, str(config.get("default_kerf", "5.0")))
        self.ent_kerf.pack(fill=tk.X, pady=(1, 3))

        # Rifili (Verticale & Orizzontale)
        ttk.Label(sidebar, text="Rifilo Orizzontale (mm):", background=self.bg_card).pack(anchor=tk.W, pady=(2, 0))
        self.ent_rifilo_h = ttk.Entry(sidebar)
        self.ent_rifilo_h.insert(0, str(config.get("default_rifilo_h", "0")))
        self.ent_rifilo_h.pack(fill=tk.X, pady=(1, 3))

        ttk.Label(sidebar, text="Rifilo Verticale (mm):", background=self.bg_card).pack(anchor=tk.W, pady=(2, 0))
        self.ent_rifilo_v = ttk.Entry(sidebar)
        self.ent_rifilo_v.insert(0, str(config.get("default_rifilo_v", "0")))
        self.ent_rifilo_v.pack(fill=tk.X, pady=(1, 3))

        # Sfrido
        ttk.Label(sidebar, text="Sfrido pezzi (mm):", background=self.bg_card).pack(anchor=tk.W, pady=(2, 0))
        self.ent_sfrido = ttk.Entry(sidebar)
        self.ent_sfrido.insert(0, str(config.get("default_sfrido", "10")))
        self.ent_sfrido.pack(fill=tk.X, pady=(1, 3))

        # Tipo Macchina
        ttk.Label(sidebar, text="Tipo Macchinario:", background=self.bg_card).pack(anchor=tk.W, pady=(2, 0))
        self.cmb_macchina = ttk.Combobox(sidebar, values=["Sezionatrice", "Pantografo"], state="readonly")
        
        default_macch = config.get("default_macchina", "sezionatrice")
        if default_macch.lower() == "pantografo":
            self.cmb_macchina.set("Pantografo")
        else:
            self.cmb_macchina.set("Sezionatrice")
        self.cmb_macchina.pack(fill=tk.X, pady=(1, 4))
        
        # Venatura (Grain) - Rimosso dalla UI maschera sinistra per richiesta utente
        self.var_grain = tk.BooleanVar(value=True)
        
        # Scelta origine dei materiali
        lbl_stock = ttk.Label(sidebar, text="Usa magazzino:", background=self.bg_card)
        lbl_stock.pack(anchor=tk.W, pady=(3, 0))
        
        self.stock_frame = tk.Frame(sidebar, background=self.bg_card, bd=1, relief="solid", highlightthickness=0)
        self.stock_frame.pack(fill=tk.X, pady=(1, 4))
        
        self.var_stock_residuo = tk.BooleanVar(value=config.get("default_use_residuo", True))
        self.var_stock_pannello = tk.BooleanVar(value=config.get("default_use_barra", True))
        self.var_stock_barra = tk.BooleanVar(value=config.get("default_use_pannello", True))
        
        chk_residuo = tk.Checkbutton(self.stock_frame, text="Residuo (♻️)", variable=self.var_stock_residuo,
                                     command=self.update_vis_tabs_visibility,
                                     background=self.bg_card, activebackground=self.bg_card, fg=self.text_color, font=("Segoe UI", 9))
        chk_residuo.pack(anchor=tk.W, padx=5, pady=2)
        
        chk_pannello = tk.Checkbutton(self.stock_frame, text="Barra (📁)", variable=self.var_stock_pannello,
                                      command=self.update_vis_tabs_visibility,
                                      background=self.bg_card, activebackground=self.bg_card, fg=self.text_color, font=("Segoe UI", 9))
        chk_pannello.pack(anchor=tk.W, padx=5, pady=2)
        
        chk_barra = tk.Checkbutton(self.stock_frame, text="Pannello (🪵)", variable=self.var_stock_barra,
                                   command=self.update_vis_tabs_visibility,
                                   background=self.bg_card, activebackground=self.bg_card, fg=self.text_color, font=("Segoe UI", 9))
        chk_barra.pack(anchor=tk.W, padx=5, pady=2)
        
        # Dimensioni minime semilavorato recuperabile
        ttk.Label(sidebar, text="Largh. min. recupero (mm):", background=self.bg_card).pack(anchor=tk.W, pady=(3, 0))
        self.ent_min_w = ttk.Entry(sidebar)
        self.ent_min_w.insert(0, str(config.get("default_min_w", "300")))
        self.ent_min_w.pack(fill=tk.X, pady=(1, 3))
        
        ttk.Label(sidebar, text="Alt. min. recupero (mm):", background=self.bg_card).pack(anchor=tk.W, pady=(3, 0))
        self.ent_min_h = ttk.Entry(sidebar)
        self.ent_min_h.insert(0, str(config.get("default_min_h", "300")))
        self.ent_min_h.pack(fill=tk.X, pady=(1, 5))
        
        # Pulsanti Azione Globale
        lbl_actions = ttk.Label(sidebar, text="AZIONI", font=("Segoe UI", 9, "bold"), foreground="#7f8c8d", background=self.bg_card)
        lbl_actions.pack(anchor=tk.W, pady=(4, 2))
        
        btn_optimize = ttk.Button(sidebar, text="OTTIMIZZA", style="TButton", command=self.run_optimization)
        btn_optimize.pack(fill=tk.X, pady=2)
        
        self.btn_consume = ttk.Button(sidebar, text="CONSUMA MATERIALI", style="Accent.TButton", command=self.consume_materials, state=tk.DISABLED)
        self.btn_consume.pack(fill=tk.X, pady=2)
        
        # Frame Esporta HTML con pulsante Apri Cartella
        f_export_html = ttk.Frame(sidebar, style="Card.TFrame")
        f_export_html.pack(fill=tk.X, pady=2)
        self.btn_export = ttk.Button(f_export_html, text="ESPORTA REPORT HTML", style="TButton", command=self.export_report, state=tk.DISABLED)
        self.btn_export.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.btn_open_html_dir = ttk.Button(f_export_html, text="📂", width=3, command=self.open_html_dir, state=tk.DISABLED)
        self.btn_open_html_dir.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Frame Esporta PDF con pulsante Apri Cartella
        f_export_pdf = ttk.Frame(sidebar, style="Card.TFrame")
        f_export_pdf.pack(fill=tk.X, pady=2)
        self.btn_export_pdf = ttk.Button(f_export_pdf, text="ESPORTA REPORT PDF", style="TButton", command=self.export_pdf_report, state=tk.DISABLED)
        self.btn_export_pdf.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.btn_open_pdf_dir = ttk.Button(f_export_pdf, text="📂", width=3, command=self.open_pdf_dir, state=tk.DISABLED)
        self.btn_open_pdf_dir.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Label per notifica aggiornamento disponibile (nascosto di default)
        self.lbl_update_available = tk.Label(
            sidebar, 
            text="🔴 AGGIORNAMENTO DISPONIBILE", 
            font=("Segoe UI", 9, "bold"), 
            fg="#e84118", 
            bg=self.bg_card,
            cursor="hand2"
        )
        self.lbl_update_available.bind("<Button-1>", lambda e: self.prompt_and_run_update())
        
        # Info scorciatoia Manuale d'Uso e tasti rapidi (Box in evidenza)
        f_shortcuts = tk.Frame(sidebar, bg="#eef2f7", bd=1, relief="flat", highlightbackground="#cbd5e1", highlightthickness=1)
        f_shortcuts.pack(side=tk.BOTTOM, fill=tk.X, pady=(5, 0))
        
        lbl_manual_shortcut = tk.Label(
            f_shortcuts, 
            text="💡 SCORCIATOIE RAPIDE\n\n[F1] Manuale d'Uso\n[F3] Attiva Selezione\n[F4] Progressione Taglio\n[F5] Duplica / Modifica\n[Tasto dx] Filtra Colonne", 
            font=("Segoe UI", 9, "bold"), 
            fg=self.accent_color, 
            bg="#eef2f7",
            justify=tk.LEFT,
            anchor="w",
            cursor="hand2"
        )
        lbl_manual_shortcut.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)
        lbl_manual_shortcut.bind("<Button-1>", lambda e: self.show_help_dialog())
        
        # Footer
        lbl_footer = ttk.Label(sidebar, text=f"CutMob v{self.APP_VERSION} - Premium", font=("Segoe UI", 8, "italic"), foreground="#bdc3c7", background=self.bg_card)
        lbl_footer.pack(side=tk.BOTTOM, pady=2)
        
        # --- AREA CONTENUTO (Tabs) ---
        self.content_frame = ttk.Frame(self.main_pane)
        self.main_pane.add(self.content_frame, stretch="always")
        
        self.notebook = ttk.Notebook(self.content_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Crea i 5 Tab principali
        self._create_tab_magazzino()
        self._create_tab_ordini()
        self._create_tab_visualizzatore()
        self._create_tab_produzione_pannelli()
        self._create_tab_report()

    # ==================== CREAZIONE TAB INTERFACCIA ====================
    
    def _create_tab_magazzino(self):
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="Magazzino (Stock)")
        
        # Tab diviso in due: Tabelle Barre e Tabelle Semilavorati
        paned = tk.PanedWindow(tab, orient=tk.VERTICAL, bg=self.bg_primary, bd=0, sashwidth=4)
        paned.pack(fill=tk.BOTH, expand=True)
        
        # 1. Barre Standard
        frame_barre = ttk.Frame(paned)
        paned.add(frame_barre, stretch="always")
        
        lbl_barre = ttk.Label(frame_barre, text="Pannelli Standard (Barre Vergini)", font=("Segoe UI", 11, "bold"), foreground=self.accent_color)
        lbl_barre.pack(anchor=tk.W, pady=(0, 2))
        lbl_barre_help = ttk.Label(frame_barre, text="(Tasto destro sul nome della colonna per cercare/filtrare)", font=("Segoe UI", 8, "italic"), foreground="#7f8c8d")
        lbl_barre_help.pack(anchor=tk.W, pady=(0, 5))
        
        # Toolbar Barre
        tb_barre = ttk.Frame(frame_barre)
        tb_barre.pack(fill=tk.X, pady=(0, 5))
        self.btn_import_barre = ttk.Button(tb_barre, text="Importa CSV", command=lambda: self.import_stock_csv("barre"))
        self.btn_import_barre.pack(side=tk.LEFT, padx=2)
        ttk.Button(tb_barre, text="Aggiungi Pannello", command=self.add_barre_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(tb_barre, text="Modifica Selezionata", command=self.edit_barre_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(tb_barre, text="Rimuovi Selezionata", command=lambda: self.remove_stock_item("barre")).pack(side=tk.LEFT, padx=2)
        ttk.Button(tb_barre, text="Annulla Filtri", style="Accent.TButton", command=self.clear_filters_barre).pack(side=tk.LEFT, padx=2)
        
        # Treeview Barre
        cols_barre = ("id", "tipo", "dim", "thick", "color_code", "color_desc", "grain", "qty")
        self.tree_barre = ttk.Treeview(frame_barre, columns=cols_barre, show="headings", height=6)
        self.tree_barre.pack(fill=tk.BOTH, expand=True)
        self.tree_barre.heading("id", text="ID Pannello")
        self.tree_barre.heading("tipo", text="Tipo")
        self.tree_barre.heading("dim", text="Dimensioni (H ↕ x W mm)")
        self.tree_barre.heading("thick", text="Spessore (mm)")
        self.tree_barre.heading("color_code", text="Cod. Colore")
        self.tree_barre.heading("color_desc", text="Finitura / Colore")
        self.tree_barre.heading("grain", text="Venatura")
        self.tree_barre.heading("qty", text="Quantità")
        self.tree_barre.column("id", width=80, anchor=tk.CENTER)
        self.tree_barre.column("tipo", width=100, anchor=tk.CENTER)
        self.tree_barre.column("dim", width=180, anchor=tk.CENTER)
        self.tree_barre.column("thick", width=100, anchor=tk.CENTER)
        self.tree_barre.column("color_code", width=100, anchor=tk.CENTER)
        self.tree_barre.column("color_desc", width=250, anchor=tk.W)
        self.tree_barre.column("grain", width=100, anchor=tk.CENTER)
        self.tree_barre.column("qty", width=80, anchor=tk.CENTER)
        
        self.tree_barre.bind("<Double-1>", self.edit_barre_dialog)
        self.tree_barre.bind("<Button-3>", lambda e: self.on_heading_right_click(e, "barre"))
        self.tree_barre.bind("<F5>", lambda e: self.open_bulk_edit_dialog("barre"))
        
        # Configura ordinamento al clic sulle intestazioni
        for col in cols_barre:
            self.tree_barre.heading(col, command=lambda _col=col: self._sort_treeview_column(self.tree_barre, _col, False))
        
        # Scrollbar Barre
        sc_barre = ttk.Scrollbar(self.tree_barre, orient=tk.VERTICAL, command=self.tree_barre.yview)
        self.tree_barre.configure(yscrollcommand=sc_barre.set)
        sc_barre.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 2. Semilavorati
        frame_semi = ttk.Frame(paned)
        paned.add(frame_semi, stretch="always")
        
        lbl_semi = ttk.Label(frame_semi, text="Barre / Recuperati (Pezzi Riutilizzabili)", font=("Segoe UI", 11, "bold"), foreground=self.accent_color)
        lbl_semi.pack(anchor=tk.W, pady=(10, 2))
        lbl_semi_help = ttk.Label(frame_semi, text="(Tasto destro sul nome della colonna per cercare/filtrare)", font=("Segoe UI", 8, "italic"), foreground="#7f8c8d")
        lbl_semi_help.pack(anchor=tk.W, pady=(0, 5))
        
        # Toolbar Semilavorati
        tb_semi = ttk.Frame(frame_semi)
        tb_semi.pack(fill=tk.X, pady=(0, 5))
        self.btn_import_semi = ttk.Button(tb_semi, text="Importa CSV", command=lambda: self.import_stock_csv("semilavorati"))
        self.btn_import_semi.pack(side=tk.LEFT, padx=2)
        ttk.Button(tb_semi, text="Aggiungi Semilavorato", command=self.add_semi_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(tb_semi, text="Modifica Selezionato", command=self.edit_semi_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(tb_semi, text="Rimuovi Selezionato", command=lambda: self.remove_stock_item("semilavorati")).pack(side=tk.LEFT, padx=2)
        ttk.Button(tb_semi, text="Annulla Filtri", style="Accent.TButton", command=self.clear_filters_semi).pack(side=tk.LEFT, padx=2)
        
        # Treeview Semilavorati
        cols_semi = ("id", "tipo", "dim", "thick", "color_code", "color_desc", "grain", "qty")
        self.tree_semi = ttk.Treeview(frame_semi, columns=cols_semi, show="headings", height=6)
        self.tree_semi.pack(fill=tk.BOTH, expand=True)
        self.tree_semi.heading("id", text="ID Pezzo")
        self.tree_semi.heading("tipo", text="Tipo")
        self.tree_semi.heading("dim", text="Dimensioni (H ↕ x W mm)")
        self.tree_semi.heading("thick", text="Spessore (mm)")
        self.tree_semi.heading("color_code", text="Cod. Colore")
        self.tree_semi.heading("color_desc", text="Finitura / Colore")
        self.tree_semi.heading("grain", text="Venatura")
        self.tree_semi.heading("qty", text="Quantità")
        self.tree_semi.column("id", width=80, anchor=tk.CENTER)
        self.tree_semi.column("tipo", width=110, anchor=tk.CENTER)
        self.tree_semi.column("dim", width=180, anchor=tk.CENTER)
        self.tree_semi.column("thick", width=100, anchor=tk.CENTER)
        self.tree_semi.column("color_code", width=100, anchor=tk.CENTER)
        self.tree_semi.column("color_desc", width=220, anchor=tk.W)
        self.tree_semi.column("grain", width=100, anchor=tk.CENTER)
        self.tree_semi.column("qty", width=80, anchor=tk.CENTER)
        
        self.tree_semi.bind("<Double-1>", self.edit_semi_dialog)
        self.tree_semi.bind("<Button-3>", lambda e: self.on_heading_right_click(e, "semilavorati"))
        self.tree_semi.bind("<F5>", lambda e: self.open_bulk_edit_dialog("semilavorati"))
        
        # Configura ordinamento al clic sulle intestazioni
        for col in cols_semi:
            self.tree_semi.heading(col, command=lambda _col=col: self._sort_treeview_column(self.tree_semi, _col, False))
            
        # Scrollbar Semilavorati
        sc_semi = ttk.Scrollbar(self.tree_semi, orient=tk.VERTICAL, command=self.tree_semi.yview)
        self.tree_semi.configure(yscrollcommand=sc_semi.set)
        sc_semi.pack(side=tk.RIGHT, fill=tk.Y)

    def _create_tab_ordini(self):
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="Commessa / Ordine")
        
        # PanedWindow per dividere a sinistra l'elenco commesse e a destra il dettaglio pezzi
        paned = tk.PanedWindow(tab, orient=tk.HORIZONTAL, bg=self.bg_primary, bd=0, sashwidth=4)
        paned.pack(fill=tk.BOTH, expand=True)
        
        # --- LATO SINISTRO: GESTIONE COMMESSE ---
        frame_commesse = ttk.Frame(paned, padding=(0, 0, 5, 0))
        paned.add(frame_commesse, width=320, minsize=250)
        
        lbl_commesse = ttk.Label(frame_commesse, text="Commesse Salvate", font=("Segoe UI", 11, "bold"), foreground=self.accent_color)
        lbl_commesse.pack(anchor=tk.W, pady=(0, 2))
        lbl_commesse_help = ttk.Label(frame_commesse, text="(Tasto destro sul nome della colonna per cercare/filtrare)", font=("Segoe UI", 8, "italic"), foreground="#7f8c8d")
        lbl_commesse_help.pack(anchor=tk.W, pady=(0, 5))
        
        # Toolbar Commesse
        tb_commesse = ttk.Frame(frame_commesse)
        tb_commesse.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(tb_commesse, text="Nuova", command=self.new_commessa_action).pack(side=tk.LEFT, padx=1)
        ttk.Button(tb_commesse, text="Salva", command=self.save_commessa_action).pack(side=tk.LEFT, padx=1)
        ttk.Button(tb_commesse, text="Elimina", command=self.delete_commessa_action).pack(side=tk.LEFT, padx=1)
        ttk.Button(tb_commesse, text="Chiudi", command=self.close_commessa_action).pack(side=tk.LEFT, padx=1)
        ttk.Button(tb_commesse, text="Annulla Filtri", style="Accent.TButton", command=self.clear_filters_commesse).pack(side=tk.LEFT, padx=1)
        
        # Treeview Commesse
        cols_commesse = ("id", "nome", "stato")
        self.tree_commesse = ttk.Treeview(frame_commesse, columns=cols_commesse, show="headings", height=15)
        self.tree_commesse.pack(fill=tk.BOTH, expand=True)
        self.tree_commesse.heading("id", text="ID")
        self.tree_commesse.heading("nome", text="Nome Commessa")
        self.tree_commesse.heading("stato", text="Stato")
        self.tree_commesse.column("id", width=40, anchor=tk.CENTER)
        self.tree_commesse.column("nome", width=180, anchor=tk.W)
        self.tree_commesse.column("stato", width=80, anchor=tk.CENTER)
        
        self.tree_commesse.bind("<<TreeviewSelect>>", self.on_commessa_select)
        self.tree_commesse.bind("<Button-3>", lambda e: self.on_heading_right_click(e, "commesse"))
        
        # Configura ordinamento al clic sulle intestazioni
        for col in cols_commesse:
            self.tree_commesse.heading(col, command=lambda _col=col: self._sort_treeview_column(self.tree_commesse, _col, False))
            
        # Scrollbar Commesse
        sc_commesse = ttk.Scrollbar(self.tree_commesse, orient=tk.VERTICAL, command=self.tree_commesse.yview)
        self.tree_commesse.configure(yscrollcommand=sc_commesse.set)
        sc_commesse.pack(side=tk.RIGHT, fill=tk.Y)
        
        # --- LATO DESTRO: DETTAGLIO COMMESSA CORRENTE ---
        frame_dettaglio = ttk.Frame(paned, padding=(5, 0, 0, 0))
        paned.add(frame_dettaglio, stretch="always")
        
        # Info commessa attiva
        self.lbl_commessa_info = ttk.Label(frame_dettaglio, text="Nuova Commessa (Non Salvata)", font=("Segoe UI", 11, "bold"), foreground=self.accent_color)
        self.lbl_commessa_info.pack(anchor=tk.W, pady=(0, 2))
        self.lbl_pieces_help = ttk.Label(frame_dettaglio, text="(Tasto destro sul nome della colonna per cercare/filtrare)", font=("Segoe UI", 8, "italic"), foreground="#7f8c8d")
        self.lbl_pieces_help.pack(anchor=tk.W, pady=(0, 5))
        
        # Toolbar Ordini
        tb = ttk.Frame(frame_dettaglio)
        tb.pack(fill=tk.X, pady=(0, 5))
        
        self.btn_import_csv = ttk.Button(tb, text="Importa CSV", command=self.import_csv_dialog)
        self.btn_import_csv.pack(side=tk.LEFT, padx=2)
        self.btn_add_piece = ttk.Button(tb, text="Aggiungi Pezzo", command=self.add_piece_dialog)
        self.btn_add_piece.pack(side=tk.LEFT, padx=2)
        self.btn_edit_piece = ttk.Button(tb, text="Modifica Pezzo", command=self.edit_piece_dialog)
        self.btn_edit_piece.pack(side=tk.LEFT, padx=2)
        self.btn_remove_piece = ttk.Button(tb, text="Rimuovi Selezionato", command=self.remove_piece_from_order)
        self.btn_remove_piece.pack(side=tk.LEFT, padx=2)
        self.btn_clear_order = ttk.Button(tb, text="Svuota Lista", command=self.clear_order_list)
        self.btn_clear_order.pack(side=tk.LEFT, padx=2)
        self.btn_select_all = ttk.Button(tb, text="Seleziona Tutti", command=self.select_all_pieces)
        self.btn_select_all.pack(side=tk.LEFT, padx=2)
        self.btn_deselect_all = ttk.Button(tb, text="Deseleziona", command=self.deselect_all_pieces)
        self.btn_deselect_all.pack(side=tk.LEFT, padx=2)
        
        self.btn_clear_filters_pieces = ttk.Button(tb, text="Annulla Filtri", style="Accent.TButton", command=self.clear_filters_pieces)
        self.btn_clear_filters_pieces.pack(side=tk.LEFT, padx=2)
        
        self.btn_calc_req = ttk.Button(tb, text="Calcola Fabbisogno", style="Accent.TButton", command=self.calculate_requirements)
        self.btn_calc_req.pack(side=tk.RIGHT, padx=2)
        
        # Treeview pezzi
        cols = ("idx", "desc", "dim", "thick", "color_code", "color_desc", "qty")
        self.tree_pieces = ttk.Treeview(frame_dettaglio, columns=cols, show="headings")
        self.tree_pieces.pack(fill=tk.BOTH, expand=True)
        self.tree_pieces.heading("idx", text="N°")
        self.tree_pieces.heading("desc", text="Descrizione Pezzo")
        self.tree_pieces.heading("dim", text="Dimensioni (H ↕ x W mm)")
        self.tree_pieces.heading("thick", text="Spessore (mm)")
        self.tree_pieces.heading("color_code", text="Cod. Colore")
        self.tree_pieces.heading("color_desc", text="Desc. Colore")
        self.tree_pieces.heading("qty", text="Quantità")
        self.tree_pieces.column("idx", width=40, anchor=tk.CENTER)
        self.tree_pieces.column("desc", width=180, anchor=tk.W)
        self.tree_pieces.column("dim", width=150, anchor=tk.CENTER)
        self.tree_pieces.column("thick", width=80, anchor=tk.CENTER)
        self.tree_pieces.column("color_code", width=80, anchor=tk.CENTER)
        self.tree_pieces.column("color_desc", width=200, anchor=tk.W)
        self.tree_pieces.column("qty", width=80, anchor=tk.CENTER)
        
        self.tree_pieces.bind("<Double-1>", self.edit_piece_dialog)
        self.tree_pieces.bind("<Button-3>", lambda e: self.on_heading_right_click(e, "pezzi"))
        self.tree_pieces.bind("<F5>", lambda e: self.open_bulk_edit_dialog("pezzi"))
        self.tree_pieces.bind("<F3>", self.toggle_pieces_green)
        self.tree_pieces.tag_configure("green_item", background="#d4edda", foreground="#155724")
        
        # Configura ordinamento al clic sulle intestazioni
        for col in cols:
            self.tree_pieces.heading(col, command=lambda _col=col: self._sort_treeview_column(self.tree_pieces, _col, False))
            
        # Scrollbar
        sc = ttk.Scrollbar(self.tree_pieces, orient=tk.VERTICAL, command=self.tree_pieces.yview)
        self.tree_pieces.configure(yscrollcommand=sc.set)
        sc.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.reload_commesse_table()

    def _create_tab_visualizzatore(self):
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="Visualizzatore Layout")
        
        # Inizializza mapping gruppi
        self.group_display_mapping = {}
        
        # Pannello superiore di controllo gruppo
        top_bar = ttk.Frame(tab, padding=5)
        top_bar.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(top_bar, text="Gruppo Materiale:").pack(side=tk.LEFT, padx=5)
        self.cb_groups = ttk.Combobox(top_bar, state="readonly", width=50)
        self.cb_groups.pack(side=tk.LEFT, padx=5)
        self.cb_groups.bind("<<ComboboxSelected>>", self.on_group_selected)
        
        # Notebook secondario per separare Barre, Pannelli e Residui
        self.vis_notebook = ttk.Notebook(tab)
        self.vis_notebook.pack(fill=tk.BOTH, expand=True)
        
        # TAB 1: TAGLIO BARRE STANDARD
        self.frame_vis_barre = ttk.Frame(self.vis_notebook, padding=5)
        
        barre_ctrl = ttk.Frame(self.frame_vis_barre, padding=2)
        barre_ctrl.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(barre_ctrl, text="🪵 SCHEMA TAGLIO PANNELLI", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT, padx=2)
        
        self.btn_prev_bar = ttk.Button(barre_ctrl, text="<<", width=4, command=self.prev_bar)
        self.btn_prev_bar.pack(side=tk.LEFT, padx=(15, 2))
        self.lbl_bar_counter = ttk.Label(barre_ctrl, text="0 / 0", font=("Segoe UI", 9, "bold"))
        self.lbl_bar_counter.pack(side=tk.LEFT, padx=5)
        self.btn_next_bar = ttk.Button(barre_ctrl, text=">>", width=4, command=self.next_bar)
        self.btn_next_bar.pack(side=tk.LEFT, padx=2)
        
        self.lbl_bar_details = ttk.Label(barre_ctrl, text="Nessun layout", font=("Segoe UI", 9, "italic"), foreground=self.accent_light)
        self.lbl_bar_details.pack(side=tk.RIGHT, padx=5)
        
        canvas_container_bar = ttk.Frame(self.frame_vis_barre, borderwidth=1, relief="solid")
        canvas_container_bar.pack(fill=tk.BOTH, expand=True)
        self.canvas_barre = tk.Canvas(canvas_container_bar, bg="#f5f6fa", bd=0, highlightthickness=0)
        self.canvas_barre.pack(fill=tk.BOTH, expand=True)
        
        # TAB 2: TAGLIO PANNELLI SEMILAVORATI
        self.frame_vis_pannelli = ttk.Frame(self.vis_notebook, padding=5)
        
        pannelli_ctrl = ttk.Frame(self.frame_vis_pannelli, padding=2)
        pannelli_ctrl.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(pannelli_ctrl, text="📁 SCHEMA TAGLIO BARRE", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT, padx=2)
        
        self.btn_prev_pan = ttk.Button(pannelli_ctrl, text="<<", width=4, command=self.prev_pan)
        self.btn_prev_pan.pack(side=tk.LEFT, padx=(15, 2))
        self.lbl_pan_counter = ttk.Label(pannelli_ctrl, text="0 / 0", font=("Segoe UI", 9, "bold"))
        self.lbl_pan_counter.pack(side=tk.LEFT, padx=5)
        self.btn_next_pan = ttk.Button(pannelli_ctrl, text=">>", width=4, command=self.next_pan)
        self.btn_next_pan.pack(side=tk.LEFT, padx=2)
        
        self.lbl_pan_details = ttk.Label(pannelli_ctrl, text="Nessun layout", font=("Segoe UI", 9, "italic"), foreground=self.accent_light)
        self.lbl_pan_details.pack(side=tk.RIGHT, padx=5)
        
        canvas_container_pan = ttk.Frame(self.frame_vis_pannelli, borderwidth=1, relief="solid")
        canvas_container_pan.pack(fill=tk.BOTH, expand=True)
        self.canvas_pannelli = tk.Canvas(canvas_container_pan, bg="#f5f6fa", bd=0, highlightthickness=0)
        self.canvas_pannelli.pack(fill=tk.BOTH, expand=True)
        
        # TAB 3: TAGLIO RESIDUI
        self.frame_vis_residui = ttk.Frame(self.vis_notebook, padding=5)
        
        residui_ctrl = ttk.Frame(self.frame_vis_residui, padding=2)
        residui_ctrl.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(residui_ctrl, text="♻️ SCHEMA TAGLIO RESIDUI", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT, padx=2)
        
        self.btn_prev_res = ttk.Button(residui_ctrl, text="<<", width=4, command=self.prev_res)
        self.btn_prev_res.pack(side=tk.LEFT, padx=(15, 2))
        self.lbl_res_counter = ttk.Label(residui_ctrl, text="0 / 0", font=("Segoe UI", 9, "bold"))
        self.lbl_res_counter.pack(side=tk.LEFT, padx=5)
        self.btn_next_res = ttk.Button(residui_ctrl, text=">>", width=4, command=self.next_res)
        self.btn_next_res.pack(side=tk.LEFT, padx=2)
        
        self.lbl_res_details = ttk.Label(residui_ctrl, text="Nessun layout", font=("Segoe UI", 9, "italic"), foreground=self.accent_light)
        self.lbl_res_details.pack(side=tk.RIGHT, padx=5)
        
        canvas_container_res = ttk.Frame(self.frame_vis_residui, borderwidth=1, relief="solid")
        canvas_container_res.pack(fill=tk.BOTH, expand=True)
        self.canvas_residui = tk.Canvas(canvas_container_res, bg="#f5f6fa", bd=0, highlightthickness=0)
        self.canvas_residui.pack(fill=tk.BOTH, expand=True)
        
        # Rilega eventi di ridimensionamento
        self.canvas_barre.bind("<Configure>", lambda e: self.redraw_barre())
        self.canvas_pannelli.bind("<Configure>", lambda e: self.redraw_pannelli())
        self.canvas_residui.bind("<Configure>", lambda e: self.redraw_residui())
        
        # Sincronizza i tab all'avvio
        self.update_vis_tabs_visibility()

    def update_vis_tabs_visibility(self):
        if not hasattr(self, 'vis_notebook'):
            return
            
        # Determina la visibilità iniziale in base alle checkbox
        show_barra = self.var_stock_barra.get()
        show_pannello = self.var_stock_pannello.get()
        show_residuo = self.var_stock_residuo.get()
        
        # Se ci sono risultati, assicura la visibilità dei tab in cui sono state usate lastre
        if self.optimization_results and "gruppi" in self.optimization_results:
            for g_data in self.optimization_results["gruppi"].values():
                for ub in g_data.get("used_boards", []):
                    b = ub["board"]
                    src = b.get("_source_type")
                    b_id = str(b.get("id", "")).upper()
                    
                    if src:
                        if src in ["barra_real", "barra_virtual"]:
                            show_barra = True
                        elif src in ["pannello_real", "pannello_virtual"]:
                            show_pannello = True
                        elif src in ["residuo_real"]:
                            show_residuo = True
                    else:
                        if b_id.startswith("S_REC_"):
                            show_residuo = True
                        elif b_id.startswith("B") or "BARRA" in b_id:
                            show_barra = True
                        else:
                            show_pannello = True
        
        # Rimuove tutti i tab per sicurezza
        for frame in [self.frame_vis_barre, self.frame_vis_pannelli, self.frame_vis_residui]:
            try:
                self.vis_notebook.forget(frame)
            except Exception:
                pass
            
        # Aggiunge i tab attivi
        if show_barra:
            self.vis_notebook.add(self.frame_vis_barre, text="Taglio Pannelli (🪵)")
        if show_pannello:
            self.vis_notebook.add(self.frame_vis_pannelli, text="Taglio Barre (📁)")
        if show_residuo:
            self.vis_notebook.add(self.frame_vis_residui, text="Taglio Residui (♻️)")

    def _create_tab_report(self):
        tab = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(tab, text="Report e Statistiche")
        
        # Sdoppia in due aree: Statistiche a sinistra, Log di testo a destra
        paned = tk.PanedWindow(tab, orient=tk.HORIZONTAL, bg=self.bg_primary, bd=0, sashwidth=4)
        paned.pack(fill=tk.BOTH, expand=True)
        
        # Statistiche sintetiche
        frame_stats = ttk.Frame(paned, padding=10)
        paned.add(frame_stats, stretch="always")
        
        lbl_stats_title = ttk.Label(frame_stats, text="Riepilogo Prestazioni", font=("Segoe UI", 12, "bold"), foreground=self.accent_color)
        lbl_stats_title.pack(anchor=tk.W, pady=(0, 15))
        
        self.lbl_stat_efficiency = ttk.Label(frame_stats, text="Efficienza Media: N/D", font=("Segoe UI", 11, "bold"))
        self.lbl_stat_efficiency.pack(anchor=tk.W, pady=5)
        
        self.lbl_stat_boards = ttk.Label(frame_stats, text="Pannelli Consumati: N/D", font=("Segoe UI", 10))
        self.lbl_stat_boards.pack(anchor=tk.W, pady=3)
        
        self.lbl_stat_placed = ttk.Label(frame_stats, text="Pezzi Posizionati: N/D", font=("Segoe UI", 10))
        self.lbl_stat_placed.pack(anchor=tk.W, pady=3)
        
        self.lbl_stat_unplaced = ttk.Label(frame_stats, text="Pezzi Rimanenti (Non Ottimizzati): N/D", font=("Segoe UI", 10))
        self.lbl_stat_unplaced.pack(anchor=tk.W, pady=3)
        
        self.lbl_stat_recoveries = ttk.Label(frame_stats, text="Pezzi Recuperati (Nuovi Semilavorati): N/D", font=("Segoe UI", 10))
        self.lbl_stat_recoveries.pack(anchor=tk.W, pady=3)
        
        # Log di testo / Riepilogo esteso
        frame_log = ttk.Frame(paned, padding=10)
        paned.add(frame_log, stretch="always")
        
        lbl_log_title = ttk.Label(frame_log, text="Dettaglio Elaborazione", font=("Segoe UI", 12, "bold"), foreground=self.accent_color)
        lbl_log_title.pack(anchor=tk.W, pady=(0, 5))
        
        self.txt_log = tk.Text(frame_log, font=("Consolas", 9), bg="#ffffff", fg="#2f3640", wrap=tk.WORD, borderwidth=1, relief="solid")
        self.txt_log.pack(fill=tk.BOTH, expand=True)
        
        sc = ttk.Scrollbar(self.txt_log, orient=tk.VERTICAL, command=self.txt_log.yview)
        self.txt_log.configure(yscrollcommand=sc.set)
        sc.pack(side=tk.RIGHT, fill=tk.Y)

    # ==================== LOGICA DI OTTIMIZZAZIONE E FLUSSO DATI ====================
    
    def reload_magazzino_tables(self):
        # 1. Svuota
        for item in self.tree_barre.get_children():
            self.tree_barre.delete(item)
        for item in self.tree_semi.get_children():
            self.tree_semi.delete(item)
            
        # 2. Ricarica da DataManager
        self.data_manager.db = self.data_manager.load_db()
        
        # Popola barre
        barre = sorted(self.data_manager.get_barre(), key=lambda b: (b.get("width", 0.0), b.get("height", 0.0)))
        for b in barre:
            match = True
            for col_name, filter_val in self.filters_barre.items():
                val_to_check = ""
                if col_name == "id":
                    val_to_check = str(b["id"])
                elif col_name == "tipo":
                    val_to_check = "♻️ residuo" if b["id"].startswith("S_REC_") else "🪵 pannello"
                elif col_name == "dim":
                    dim_val = f"{int(b['height'])} x {int(b['width'])}"
                    dim_val_alt = f"{int(b['height'])} ↕ x {int(b['width'])}"
                    if filter_val not in dim_val.lower() and filter_val not in dim_val_alt.lower():
                        match = False
                        break
                    continue
                elif col_name == "thick":
                    val_to_check = str(b["thickness"])
                elif col_name == "color_code":
                    val_to_check = str(b["color_code"])
                elif col_name == "color_desc":
                    val_to_check = str(b["color_desc"])
                elif col_name == "grain":
                    val_to_check = "sì" if b.get("has_grain") else "no"
                elif col_name == "qty":
                    val_to_check = str(b.get("quantity", 1))
                
                if filter_val not in val_to_check.lower():
                    match = False
                    break
            if not match:
                continue
                
            is_rec = b["id"].startswith("S_REC_")
            tipo_str = "♻️ Residuo" if is_rec else "🪵 Pannello"
            dim_str = f"{int(b['height'])} ↕ x {int(b['width'])}" if b.get("has_grain", False) else f"{int(b['height'])} x {int(b['width'])}"
            grain_str = "Sì" if b.get("has_grain", False) else "No"
            self.tree_barre.insert("", tk.END, values=(
                b["id"],
                tipo_str,
                dim_str,
                b["thickness"],
                b["color_code"],
                b["color_desc"],
                grain_str,
                b.get("quantity", 1)
            ))
            
        # Popola semilavorati
        semis = sorted(self.data_manager.get_semilavorati(), key=lambda s: (s.get("width", 0.0), s.get("height", 0.0)))
        for s in semis:
            match = True
            for col_name, filter_val in self.filters_semi.items():
                val_to_check = ""
                if col_name == "id":
                    val_to_check = str(s["id"])
                elif col_name == "tipo":
                    val_to_check = "♻️ residuo" if s["id"].startswith("S_REC_") else "📦 barra"
                elif col_name == "dim":
                    dim_val = f"{int(s['height'])} x {int(s['width'])}"
                    dim_val_alt = f"{int(s['height'])} ↕ x {int(s['width'])}"
                    if filter_val not in dim_val.lower() and filter_val not in dim_val_alt.lower():
                        match = False
                        break
                    continue
                elif col_name == "thick":
                    val_to_check = str(s["thickness"])
                elif col_name == "color_code":
                    val_to_check = str(s["color_code"])
                elif col_name == "color_desc":
                    val_to_check = str(s["color_desc"])
                elif col_name == "grain":
                    val_to_check = "sì" if s.get("has_grain") else "no"
                elif col_name == "qty":
                    val_to_check = str(s.get("quantity", 1))
                
                if filter_val not in val_to_check.lower():
                    match = False
                    break
            if not match:
                continue
                
            is_rec = s["id"].startswith("S_REC_")
            dim_str = f"{int(s['height'])} ↕ x {int(s['width'])}" if s.get("has_grain", False) else f"{int(s['height'])} x {int(s['width'])}"
            tipo_str = "♻️ Residuo" if is_rec else "📦 Barra"
            grain_str = "Sì" if s.get("has_grain", False) else "No"
            self.tree_semi.insert("", tk.END, values=(
                s["id"],
                tipo_str,
                dim_str,
                s["thickness"],
                s["color_code"],
                s["color_desc"],
                grain_str,
                s.get("quantity", 1)
            ))
            
        # Ricarica la combobox dei materiali in produzione se esiste
        if hasattr(self, 'cb_prod_materiale'):
            self.populate_prod_materials()
        if hasattr(self, 'tree_prod_pannelli'):
            self.reload_prod_panels_table()

    def reload_order_table(self):
        # Ordina la commessa per Colore, Spessore, Larghezza, Altezza
        self.current_order.sort(key=lambda p: (
            p.get("color_code", ""),
            float(p.get("thickness", 0.0)),
            float(p.get("width", 0.0)),
            float(p.get("height", 0.0))
        ))
        
        for item in self.tree_pieces.get_children():
            self.tree_pieces.delete(item)
            
        for idx, p in enumerate(self.current_order):
            # Formatta la quantità visualizzata
            qty_val = p.get("quantity", 1)
            qt_orig = p.get("qt_origine")
            if qt_orig is not None:
                qty_display = f"{qty_val} ({str(qt_orig).replace('.', ',')})"
            else:
                qty_display = str(qty_val)

            # Filtro pezzi
            match = True
            for col_name, filter_val in self.filters_pieces.items():
                val_to_check = ""
                if col_name == "idx":
                    val_to_check = str(idx + 1)
                elif col_name == "desc":
                    val_to_check = str(p["descrizione"])
                elif col_name == "dim":
                    val_to_check = f"{int(p['height'])} x {int(p['width'])}"
                elif col_name == "thick":
                    val_to_check = str(p["thickness"])
                elif col_name == "color_code":
                    val_to_check = str(p["color_code"])
                elif col_name == "color_desc":
                    val_to_check = str(p["color_desc"])
                elif col_name == "qty":
                    val_to_check = qty_display
                
                if filter_val not in val_to_check.lower():
                    match = False
                    break
            if not match:
                continue

            dim_str = f"{int(p['height'])} x {int(p['width'])}"
            tags = ("green_item",) if p.get("is_green", False) else ()
            self.tree_pieces.insert("", tk.END, values=(
                idx + 1,
                p["descrizione"],
                dim_str,
                p["thickness"],
                p["color_code"],
                p["color_desc"],
                qty_display
            ), tags=tags)

    def toggle_cut_progression(self, event=None):
        current = self.data_manager.config.get("show_cut_progression", True)
        new_val = not current
        self.data_manager.config["show_cut_progression"] = new_val
        self.data_manager.save_config(self.data_manager.config)
        
        # Forza il ridisegno dei canvas
        try:
            self.redraw_barre()
        except Exception:
            pass
        try:
            self.redraw_pannelli()
        except Exception:
            pass
        try:
            self.redraw_residui()
        except Exception:
            pass

    def check_for_updates_async(self):
        import threading
        def run_check():
            import urllib.request
            import json
            try:
                # Determina l'OS corrente per l'aggiornamento
                os_name = "mac" if sys.platform == "darwin" else "windows"
                piva = self.data_manager.config.get("client_cf_piva", "")
                ver = self.APP_VERSION
                url = f"https://panel.aiconsultingitalia.com/panel_cutmob/api.php?action=get_latest_version&prodotto=CutMob&os={os_name}&partita_iva={piva}&version={ver}"
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=5) as response:
                    res_data = json.loads(response.read().decode('utf-8'))
                    if res_data.get("status") == "success":
                        info = res_data.get("data")
                        self.latest_version_info = info
                        self.root.after(0, self.evaluate_version_check)
            except Exception as e:
                print(f"Errore controllo versione: {e}")
                
        threading.Thread(target=run_check, daemon=True).start()

    def evaluate_version_check(self):
        if not self.latest_version_info:
            return
        
        current_version = self.APP_VERSION # La versione attuale visualizzata in barra
        latest_version = self.latest_version_info.get("version", "2.0")
        
        def parse_ver(v):
            try:
                return [int(x) for x in v.strip('v').split('.')]
            except Exception:
                return [0, 0]
                
        if parse_ver(latest_version) > parse_ver(current_version):
            msg = f"Nuova versione disponibile (v{latest_version}).\nVuoi scaricare e installare l'aggiornamento ora?"
            ans = messagebox.askyesno("Aggiornamento Disponibile", msg)
            if ans:
                self.run_update_process()
            else:
                self.show_update_available_label()

    def show_update_available_label(self):
        try:
            self.lbl_update_available.pack(side=tk.BOTTOM, fill=tk.X, pady=(5, 5))
            self.blink_update_label(True)
        except Exception:
            pass

    def blink_update_label(self, state):
        if not hasattr(self, 'lbl_update_available') or not self.lbl_update_available.winfo_exists():
            return
        color = "#e84118" if state else "#2f3640"
        self.lbl_update_available.configure(fg=color)
        self.root.after(800, lambda: self.blink_update_label(not state))

    def prompt_and_run_update(self):
        if self.latest_version_info:
            latest_version = self.latest_version_info.get("version", "")
            msg = f"Vuoi scaricare e installare la nuova versione di CutMob (v{latest_version}) adesso?"
            if messagebox.askyesno("Aggiornamento", msg):
                self.run_update_process()

    def run_update_process(self):
        # Finestra di progresso del download
        progress_dialog = tk.Toplevel(self.root)
        progress_dialog.title("CutMob - Download Aggiornamento")
        progress_dialog.geometry("400x150")
        progress_dialog.resizable(False, False)
        progress_dialog.transient(self.root)
        progress_dialog.grab_set()
        
        lbl_msg = tk.Label(progress_dialog, text="Download dell'aggiornamento in corso...", font=("Segoe UI", 10))
        lbl_msg.pack(pady=20)
        
        progress = ttk.Progressbar(progress_dialog, mode="indeterminate", length=300)
        progress.pack(pady=10)
        progress.start(10)
        
        import threading
        def download_and_restart():
            import urllib.request
            import shutil
            import subprocess
            import os
            
            try:
                download_url = self.latest_version_info.get("url")
                temp_dir = r"C:\CutMob\Temp"
                os.makedirs(temp_dir, exist_ok=True)
                
                if download_url.endswith(".dmg"):
                    ext = ".dmg"
                elif download_url.endswith(".zip"):
                    ext = ".zip"
                else:
                    ext = ".exe"
                    
                dest_file = os.path.join(temp_dir, "update_installer" + ext)
                
                req = urllib.request.Request(download_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=30) as response, open(dest_file, 'wb') as out_file:
                    shutil.copyfileobj(response, out_file)
                
                progress_dialog.destroy()
                
                if ext == ".zip":
                    messagebox.showinfo("Aggiornamento", "Download completato con successo!\nL'applicazione verrà chiusa per completare l'estrazione e l'aggiornamento.")
                    
                    extract_path = os.path.join(temp_dir, "extracted")
                    if os.path.exists(extract_path):
                        shutil.rmtree(extract_path, ignore_errors=True)
                    os.makedirs(extract_path, exist_ok=True)
                    
                    import zipfile
                    with zipfile.ZipFile(dest_file, 'r') as zip_ref:
                        zip_ref.extractall(extract_path)
                    
                    bat_path = os.path.join(temp_dir, "update.bat")
                    src_folder = os.path.join(extract_path, "CutMob")
                    if not os.path.exists(src_folder):
                        src_folder = extract_path
                        
                    with open(bat_path, "w", encoding="cp1252") as f:
                        f.write(f'@echo off\n')
                        f.write(f'title Aggiornamento CutMob in corso...\n')
                        f.write(f'echo Attendere l\'installazione dell\'aggiornamento...\n')
                        f.write(f'timeout /t 2 /nobreak > nul\n')
                        f.write(f'xcopy /y /e /h /r "{src_folder}\\*.*" "C:\\CutMob\\"\n')
                        f.write(f'start C:\\CutMob\\CutMob.exe\n')
                        f.write(f'exit\n')
                    
                    subprocess.Popen([bat_path], shell=True)
                    
                elif ext == ".exe":
                    messagebox.showinfo("Aggiornamento", "Download completato con successo!\nL'applicazione verrà chiusa per avviare l'installazione.")
                    subprocess.Popen([dest_file], shell=True)
                else:
                    messagebox.showinfo("Aggiornamento", f"Download completato!\nIl file è stato scaricato in:\n{dest_file}\nAprilo per completare l'installazione.")
                    if hasattr(os, 'startfile'):
                        os.startfile(temp_dir)
                    else:
                        subprocess.Popen(['open', temp_dir])
                
                self.root.destroy()
                sys.exit(0)
            except Exception as e:
                progress_dialog.destroy()
                messagebox.showerror("Errore Aggiornamento", f"Si è verificato un errore durante il download o l'estrazione: {e}")
                
        threading.Thread(target=download_and_restart, daemon=True).start()

    def check_license_startup(self):
        from license_manager import verifica_chiave_licenza
        from datetime import datetime
        
        config = self.data_manager.config
        license_enabled = config.get("license_enabled", True)
        
        if not license_enabled:
            return True
            
        key_str = self.data_manager.load_license_key()
        client_name = config.get("client_name", "")
        client_cf_piva = config.get("client_cf_piva", "")
        
        is_valid = False
        msg = "Licenza non trovata."
        lic_data = None
        if key_str:
            is_valid, msg, lic_data = verifica_chiave_licenza(key_str, client_name, client_cf_piva)
            
        if is_valid:
            # Controllo anti-manomissione orologio di sistema
            today_str = datetime.now().strftime("%Y-%m-%d")
            last_run = config.get("last_run_date", "")
            
            if last_run and today_str < last_run:
                messagebox.showerror(
                    "Errore Licenza", 
                    "Rilevata alterazione dell'orologio di sistema!\n"
                    "Il programma verrà chiuso. Ripristinare l'ora corretta."
                )
                return False
                
            # Aggiorna la data dell'ultimo avvio corretto
            config["last_run_date"] = max(today_str, last_run) if last_run else today_str
            self.data_manager.save_config(config)
            
            exp_date = lic_data.get("data_fine", "")
            self.root.title(f"CutMob - Ottimizzatore di Taglio (Licenza attiva fino a {exp_date})")
            return True
            
        dialog = tk.Toplevel(self.root)
        dialog.title("CutMob - Attivazione Licenza")
        dialog.geometry("550x330")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        def on_close():
            dialog.destroy()
            self.root.destroy()
            sys.exit(0)
        dialog.protocol("WM_DELETE_WINDOW", on_close)
        
        var_key = tk.StringVar()
        var_status = tk.StringVar(value=f"Stato: {msg}")
        var_license_enabled = tk.BooleanVar(value=True)
        
        lbl_title = tk.Label(dialog, text="Attivazione Licenza CutMob", font=("Segoe UI", 14, "bold"), fg="#273c75")
        lbl_title.pack(pady=15)
        
        lbl_status = tk.Label(dialog, textvariable=var_status, font=("Segoe UI", 10, "italic"), fg="#e84118")
        lbl_status.pack(pady=5)
        
        frame_input = tk.Frame(dialog)
        frame_input.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(frame_input, text="Incolla qui il codice di licenza ricevuto via email:").pack(anchor=tk.W)
        ent_key = tk.Entry(frame_input, textvariable=var_key, font=("Consolas", 10))
        ent_key.pack(fill=tk.X, pady=5)
        
        frame_flag = tk.Frame(dialog)
        frame_flag.pack(fill=tk.X, padx=20, pady=5)
        
        chk_license = tk.Checkbutton(
            frame_flag, 
            text="Abilita Controllo Licenza (protetto da password)", 
            variable=var_license_enabled,
            state="disabled",
            disabledforeground="#7f8c8d"
        )
        chk_license.pack(side=tk.LEFT)
        
        def unlock_flag(event):
            pwd = simpledialog.askstring("Sblocco di sicurezza", "Inserire la password di sblocco licenza:", show="*")
            if pwd == "Rdf20276498!":
                chk_license.configure(state="normal")
                messagebox.showinfo("Sblocco", "Controllo licenza sbloccato. Ora puoi disattivarlo.")
            elif pwd is not None:
                messagebox.showerror("Errore", "Password non valida.")
                
        chk_license.bind("<Double-1>", unlock_flag)
        
        success_activation = [False]
        
        def activate():
            key = var_key.get().strip()
            if not key:
                messagebox.showerror("Errore", "Inserire una chiave di licenza.")
                return
                
            valida, err_msg, data = verifica_chiave_licenza(key)
            if valida:
                self.data_manager.save_license_key(key)
                config["client_name"] = data.get("ragione_sociale", "")
                config["client_cf_piva"] = data.get("partita_iva", "")
                config["license_enabled"] = True
                self.data_manager.save_config(config)
                
                messagebox.showinfo("Attivazione", f"Licenza attivata con successo per {data.get('ragione_sociale')}!\nScadenza: {data.get('data_fine')}")
                success_activation[0] = True
                dialog.destroy()
            else:
                messagebox.showerror("Errore Attivazione", err_msg)
                
        def bypass_or_close():
            if not var_license_enabled.get():
                config["license_enabled"] = False
                self.data_manager.save_config(config)
                messagebox.showinfo("Bypass Licenza", "Controllo licenza disattivato. Il programma si avvierà normalmente.")
                success_activation[0] = True
                dialog.destroy()
            else:
                on_close()
                
        frame_buttons = tk.Frame(dialog)
        frame_buttons.pack(pady=15)
        
        btn_activate = tk.Button(frame_buttons, text="Attiva Licenza", command=activate, bg="#273c75", fg="white", font=("Segoe UI", 10, "bold"), padx=10, pady=5)
        btn_activate.pack(side=tk.LEFT, padx=10)
        
        btn_close = tk.Button(frame_buttons, text="Annulla / Esci", command=bypass_or_close, font=("Segoe UI", 10), padx=10, pady=5)
        btn_close.pack(side=tk.LEFT, padx=10)
        
        ent_key.focus_set()
        self.root.wait_window(dialog)
        return success_activation[0]

    def show_help_dialog(self, event=None):
        dialog = tk.Toplevel(self.root)
        dialog.title("CutMob - Manuale d'Uso e Istruzioni")
        dialog.geometry("750x650")
        dialog.minsize(600, 500)
        dialog.grab_set()
        
        # Stile barra di ricerca superiore
        search_frame = ttk.Frame(dialog, padding=10, style="TFrame")
        search_frame.pack(fill=tk.X)
        
        ttk.Label(search_frame, text="Cerca nel manuale:").pack(side=tk.LEFT, padx=(5, 5))
        ent_search = ttk.Entry(search_frame, width=30)
        ent_search.pack(side=tk.LEFT, padx=5)
        
        # Container per il testo e scrollbar
        text_frame = ttk.Frame(dialog, padding=10, style="TFrame")
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        txt_manual = tk.Text(text_frame, font=("Segoe UI", 10), bg="#ffffff", fg=self.text_color, wrap=tk.WORD, bd=1, relief="solid")
        txt_manual.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        sc = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=txt_manual.yview)
        txt_manual.configure(yscrollcommand=sc.set)
        sc.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Definizione tag di stile
        txt_manual.tag_configure("header1", font=("Segoe UI", 14, "bold"), foreground=self.accent_color, spacing1=10, spacing3=5)
        txt_manual.tag_configure("header2", font=("Segoe UI", 12, "bold"), foreground=self.accent_light, spacing1=8, spacing3=3)
        manual_text = r"""CUTMOB - MANUALE D'USO E GUIDA OPERATIVA
=========================================

Benvenuto in CutMob, l'ottimizzatore professionale di taglio bidimensionale per pannelli e barre. Questo manuale funge sia da riferimento tecnico che da guida operativa passo-passo per assisterti in tutte le fasi di lavorazione.

Scorciatoie Rapide Globali:
• [F1] : Apre questo manuale d'uso in qualunque momento.
• [F3] : Attiva/Disattiva la selezione parziale (colore verde) sulle righe dei pezzi selezionati.
• [F4] : Mostra/Nascondi il numero progressivo di taglio sullo schema grafico e sui report.
• [F5] : Apre la griglia stile Excel per duplicare e modificare in serie i record selezionati.
• [Tasto dx mouse] : Consente di cercare e filtrare i dati cliccando sulle intestazioni delle tabelle.

=========================================
GUIDA OPERATIVA PASSO-PASSO
=========================================

FASE 1: INSTALLAZIONE E AGGIORNAMENTO
---------------------------------------
L'installazione e gli aggiornamenti di CutMob sono gestiti in modo centralizzato dall'installer unico "Setup_CutMob.exe".
1. Posizionamento: Il programma deve essere installato e risiedere sempre nel percorso fisso "C:\CutMob".
2. Nuova Installazione: Se esegui il setup su un nuovo computer, l'installer creerà la struttura delle cartelle ("C:\CutMob\DbDati", "C:\CutMob\Report\HTML", "C:\CutMob\Report\PDF") e inizializzerà un database vuoto. Al primo avvio ti verrà richiesta la chiave di attivazione licenza.
3. Aggiornamento Software: Se l'installer rileva una chiave di licenza attiva in "C:\CutMob\DbDati\licenza.key", procederà in modalità "Solo Aggiornamento". Aggiornerà i file eseguibili del programma ma preserverà intatti i tuoi dati storici, database delle commesse e file di configurazione personali.
4. Attivazione Licenza: Incolla il codice di licenza ricevuto nell'apposita schermata di attivazione all'avvio. La licenza è legata ai dati cliente ("Ragione Sociale" e "Partita IVA/C.F.") configurati nelle impostazioni di sistema.

FASE 2: CONFIGURAZIONE E PARAMETRI MACCHINA
---------------------------------------------
Prima di procedere ai tagli, assicurati di configurare correttamente i parametri macchina:
1. Accedi alle Impostazioni: Clicca sul pulsante con l'ingranaggio (⚙️) in alto a destra. L'accesso è protetto da password amministratore per prevenire modifiche accidentali da parte degli operatori.
2. Parametri di Taglio: Imposta il "Kerf" (spessore lama della sezionatrice, es. 5 mm), i "Rifili" (margini asportati dai quattro lati del pannello prima dell'ottimizzazione) e lo "Sfrido" (tollerranza aggiunta ad ogni pezzo, applicata solo sui pannelli grandi interii).
3. Selezione Macchina:
   - "Sezionatrice": Ottimizza i tagli in modo continuo da un lato all'altro della lastra (tagli a ghigliottina, indicati per squadratrici o sezionatrici orizzontali/verticali).
   - "Pantografo": Esegue nesting libero tramite algoritmo MaxRects, ottimizzando il posizionamento senza vincoli di taglio passante (ideale per centri di lavoro CNCFASE 3: GESTIONE DEL MAGAZZINO E CARICAMENTO CODICI
-----------------------------------------------------
Per poter calcolare le commesse, devi caricare i formati di magazzino disponibili:
1. Formati e Tabelle: Nella scheda "Magazzino (Stock)" sono presenti due tabelle distinte:
   - "Pannelli Standard (Barre Vergini)": Le lastre grezze di fornitura. Possono essere interi ("🪵 Pannello") o scarti riutilizzabili grandi ("♻️ Residuo", con prefisso "S_REC_").
   - "Barre / Semilavorati (Pezzi Riutilizzabili)": I semilavorati pre-tagliati ad altezza finita (es. 2800x720 mm) o residui di lavorazioni passate ("♻️ Residuo", con prefisso "S_REC_").
2. Inserimento e Modifica Manuale: Cliccando su "Aggiungi Pannello" o "Aggiungi Semilavorato" viene mostrato un selettore "Tipo Materiale" che consente di definire se si tratta di un pezzo intero o di un residuo di recupero.
   - Scegliendo "Residuo (♻️)", il codice ID inserito riceve automaticamente il prefisso "S_REC_".
   - Scegliendo "Pannello" o "Barra", l'eventuale prefisso "S_REC_" viene rimosso dal codice.
   La maschera si apre completamente vuota senza valori predefiniti per garantire un inserimento pulito.
3. Controllo ID Duplicati: All'atto del salvataggio, il sistema verifica che il codice ID inserito sia univoco nel database, impedendo la creazione di doppioni.
4. Importazione Massiva CSV: Puoi importare interi elenchi di magazzino tramite file CSV. Facendo clic su "Importa CSV", la finestra si aprirà direttamente nelle cartelle predefinite di rete ("C:\Report\Pannelli" per pannelli e "C:\Report\Barre" per semilavorati).

FASE 4: COMPILAZIONE DELLA COMMESSA (ORDINE DI TAGLIO)
--------------------------------------------------------
Nella scheda "Commessa / Ordine" prepari la distinta dei pezzi da produrre:
1. Gestione Commessa: Puoi creare una "Nuova" commessa, salvarla nel database interno ("Salva"), o cancellarla ("Elimina"). 
2. Stato Commessa: Una commessa può essere impostata su "Chiusa". Se chiusa, viene congelata: non potrai più modificarne i pezzi, importare CSV o avviare ottimizzazioni, garantendo la tracciabilità delle lavorazioni già spedite.
3. Inserimento Pezzi: Aggiungi i pezzi da tagliare specificando Descrizione, Larghezza, Altezza, Spessore, Codice Colore e Quantità. Puoi inserire i dati a mano (form pulito), importarli tramite CSV (la cartella di partenza predefinita è "C:\Report\Elem_Cutmob") o duplicarli.
4. Selezione Parziale (F3): Se vuoi tagliare solo una parte della commessa, seleziona le righe interessate e premi [F3] per evidenziarle in verde. I calcoli e l'ottimizzazione verranno eseguiti solo su queste righe.

FASE 5: DUPLICAZIONE E MODIFICA MASSIVA (TASTO F5)
----------------------------------------------------
Se hai necessità di duplicare o modificare rapidamente più righe contemporaneamente nelle tabelle dei Pannelli, dei Semilavorati o dei Pezzi dell'Ordine:
1. Selezione: Seleziona una o più righe tenendo premuto Ctrl o Shift.
2. Apertura Griglia (F5): Premi il tasto [F5]. Si aprirà una finestra di dialogo contenente una griglia stile foglio Excel con i dati delle righe selezionate.
3. Colonna Tipo per Magazzino: Anche per i Pannelli, la griglia F5 include la colonna "Tipo" con il menu a discesa per cambiare velocemente la natura dei record (Pannello o Residuo).
4. Ridimensionamento Dinamico: Se le celle sono troppo strette, allarga la finestra trascinando i bordi laterali: tutte le colonne di input si espanderanno automaticamente in larghezza per garantire la massima leggibilità.
5. Conferma (F5): Premi nuovamente [F5] o clicca su "Inserisci Record (F5)". Il sistema validerà i campi, controllerà che non ci siano ID duplicati nel database e inserirà in blocco i nuovi record duplicati, aggiornando le tabelle di partenza.

FASE 6: ELABORAZIONE E OTTIMIZZAZIONE DEL TAGLIO
--------------------------------------------------
1. Impostazione Filtri Magazzino: Nella sidebar sinistra seleziona quali materiali considerare per il calcolo ("Residuo ♻️", "Barra 📁", "Pannello 🪵").
2. Esecuzione: Clicca su "Calcola Fabbisogno" nella scheda Commessa. Un indicatore grafico di caricamento ("Elaborazione in corso...") disabiliterà temporaneamente lo schermo.
3. Priorità e Logiche di Consumo: Se il flag "Residuo ♻️" è attivo, tutti i residui idonei (sia dell'elenco Pannelli che dell'elenco Barre) vengono inseriti all'inizio della lista e consumati per primi per ridurre lo scarto. Se il flag non è attivo, essi non vengono considerati nel calcolo. Successivamente vengono consumate le barre standard e infine i pannelli interi standard. Se un pezzo è troppo grande per le barre abilitate, il sistema attiva automaticamente i pannelli grezzi per quel specifico colore.
4. Doppio Passaggio (Pannelli Virtuali): Se mancano barre semilavorate a magazzino, il sistema calcolerà quante barre "virtuali" servono e genererà un primo piano di taglio contrassegnato con "[PER PANNELLI]" per ricavare tali barre partendo dai pannelli standard interi.

FASE 7: VISUALIZZAZIONE LAYOUT E SCALA DISEGNO
------------------------------------------------
1. Schede Visualizzatore: Nel tab "Visualizzatore Layout" trovi tre sottoschede separate per "Taglio Pannelli", "Taglio Barre" e "Taglio Residui".
2. Navigazione: Scorri le lastre generate con i pulsanti "<<" e ">>" sotto il disegno.
3. Formato Misure H x W: Nel disegno della lastra, la quota in testa viene visualizzata nel formato Altezza x Larghezza (H x W, es. 2800 x 2070 mm) coerentemente con l'ordinamento delle tabelle scritte.
4. Raggruppamento Layout Identici: Se l'algoritmo genera schemi di taglio identici (stesso posizionamento dei pezzi, stessi tagli, stesso materiale), la grafica li mostra **una sola volta**.
   - Il contatore delle lastre mostra solo i layout unici (es. 1 / 2 invece di 1 / 8).
   - In testa alla lastra viene stampato il moltiplicatore (es. "Lastra: 2800 x 2070 - Grigio x 4").
   - L'etichetta dei dettagli riporta la dicitura evidenziata "[x4 IDENTICHE]" per indicare all'operatore che lo schema va replicato 4 volte su 4 pannelli distinti.

FASE 8: ESPORTAZIONE DEI REPORT E SCARICO MAGAZZINO
-----------------------------------------------------
1. Esportazione PDF: Clicca su "ESPORTA REPORT PDF" nella sidebar. Il sistema crea un file HTML temporaneo e lo converte in PDF tramite Google Chrome headless salvandolo in "C:\CutMob\Report\PDF".
2. Raggruppamento nei Report: Anche nei report HTML e PDF i layout identici vengono accorpati. Ciascuno schema univoco viene stampato una sola volta contrassegnato da un badge scuro "X 4 LASTRE IDENTICHE", riducendo il numero di fogli da stampare in officina.
3. Apertura Rapida: Clicca sull'icona della cartella (📂) nella sidebar per aprire direttamente la directory contenente l'ultimo PDF generato.
4. Scarico Magazzino e Ritorno Scarti: Cliccando su "Consuma Materiali", il sistema aggiorna le giacenze reali:
   - Rimuove o decrementa i materiali consumati.
   - Registra i nuovi residui generati, inserendoli nella lista di appartenenza del pannello/barra genitore (i residui da pannello tornano nell'elenco dei Pannelli; i residui da barre tornano in quello dei Semilavorati).
   - Contrassegna la commessa come "Chiusa".

=========================================
INFORMAZIONI E REGOLE DI CALCOLO AVANZATE
=========================================

1. REGOLE DI ASSOCIAZIONE DELLE BARRE (Comanda la Larghezza W)
---------------------------------------------------------------
Le barre semilavorate standard sono pre-bordate sui due lati lunghi. 
• La larghezza (W) rappresenta l'altezza standard delle ante che vengono prodotte. Nel calcolo delle barre, comanda sempre la larghezza W.
• Se si produce un'anta larga 597, l'algoritmo preleva la barra di larghezza 597 (lunghezza 2800).
• Blocco Rotazione: La rotazione è disabilitata per tutti i tagli effettuati su barre standard (semilavorato_bar) e relativi residui (remnant). Questo garantisce che la larghezza dell'anta (es. 597) rimanga allineata alla larghezza della barra specifica (es. 597), escludendo lavorazioni su barre di categorie superiori (es. 747) a tinta unita.

2. VINCOLO ALTEZZE STANDARD
---------------------------
L'ottimizzatore estrae dinamicamente le altezze standard note del materiale ed evita di inserire pezzi in barre appartenenti a standard superiori (un pezzo con larghezza 397 non verrà mai posizionato su una barra da 747, a meno che non manchino barre da 397 o 597 e si operi in regime di deficit).

3. APPLICAZIONE SFRIDO E TOLLERANZE DI TAGLIO
----------------------------------------------
Lo "Sfrido" impostato nella configurazione (es. 10 mm) è un margine aggiunto alle dimensioni di ogni pezzo per consentire una rifilatura finale.
• Applicazione: Lo sfrido viene calcolato ed aggiunto unicamente quando i pezzi vengono tagliati a partire da Pannelli Standard grezzi interi.
• Esclusione: Sulle barre semilavorate standard e sui residui di magazzino, lo sfrido non viene applicato (vale 0.0 mm) per preservare i bordi esistenti e ricavare i pezzi a misura reale.

4. DIFFERENZA DETTAGLIATA TRA SEZIONATRICE E PANTOGRAFO
-------------------------------------------------------
• 🪚 Sezionatrice (Taglio a Ghigliottina / Guillotine Cutting):
  I tagli devono essere passanti (da bordo a bordo del pannello o sottomodulo). Non è possibile eseguire intagli a "L" o fermare la lama a metà pannello. Utilizza combinazioni di euristiche di ghigliottina 2D e Shelf Packing. Nel visualizzatore e nei report compaiono linee tratteggiate rosse numerate (attivabili con F4) per indicare la sequenza di taglio.
• 🌀 Pantografo (Nesting Libero / MaxRects):
  Elimina il vincolo del taglio passante. I pezzi possono essere posizionati in qualsiasi punto libero della lastra, anche nidificati l'uno dentro l'altro. Utilizza l'algoritmo MaxRects con euristica Best Short Side Fit (BSSF). Indicato per centri di lavoro CNC router dotati di piano aspirante.
"""
        
        # Inserimento e formattazione testo
        for line in manual_text.split("\n"):
            if line.startswith("CUTMOB") or line.startswith("====================="):
                txt_manual.insert(tk.END, line + "\n", "header1")
            elif line.strip() and line.strip()[0].isdigit() and ("." in line or ")" in line) and len(line) < 60:
                txt_manual.insert(tk.END, line + "\n", "header2")
            elif line.startswith("•") or line.startswith("  -"):
                txt_manual.insert(tk.END, line + "\n", "bullet")
            else:
                txt_manual.insert(tk.END, line + "\n")
                
        txt_manual.config(state=tk.DISABLED)
        
        # Logica di ricerca nel testo
        def search_text(event=None):
            txt_manual.tag_remove("highlight", "1.0", tk.END)
            query = ent_search.get().strip().lower()
            if not query:
                return
                
            start_pos = "1.0"
            count = 0
            while True:
                pos = txt_manual.search(query, start_pos, nocase=True, stopindex=tk.END)
                if not pos:
                    break
                end_pos = f"{pos}+{len(query)}c"
                txt_manual.tag_add("highlight", pos, end_pos)
                start_pos = end_pos
                count += 1
                
            if count > 0:
                first_pos = txt_manual.tag_ranges("highlight")
                if first_pos:
                    txt_manual.see(first_pos[0])
            else:
                messagebox.showinfo("Ricerca", "Nessuna corrispondenza trovata.")
                
        ent_search.bind("<Return>", search_text)
        ttk.Button(search_frame, text="Cerca", command=search_text).pack(side=tk.LEFT, padx=5)
        
        # Pulsante chiusura in basso
        btn_frame = ttk.Frame(dialog, padding=10, style="TFrame")
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="Chiudi", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)

    def _prompt_and_filter_semis(self, raw_semis, stock_source):
        """
        Controlla se ci sono residui di taglio (prefisso S_REC_) e chiede all'utente se usarli.
        Ritorna (filtered_semis, procedi) dove:
        - filtered_semis è la lista filtrata e ordinata di semilavorati
        - procedi è False se l'utente ha cliccato Annulla, altrimenti True
        """
        if stock_source == "Solo Barre Standard" or not raw_semis:
            return raw_semis, True
            
        has_rec = any(s["id"].startswith("S_REC_") for s in raw_semis)
        if not has_rec:
            return raw_semis, True
            
        risposta = messagebox.askyesnocancel(
            "Utilizzo Residui di Taglio",
            "Nel magazzino semilavorati sono presenti residui di taglio (ID con prefisso S_REC_).\n\n"
            "• Clicca 'Sì' per utilizzarli ed elaborarli per primi\n"
            "• Clicca 'No' per escluderli e procedere solo con i Pannelli pre-tagliati\n"
            "• Clicca 'Annulla' per interrompere il calcolo"
        )
        
        if risposta is None:
            return [], False
            
        filtered_semis = []
        for s in raw_semis:
            is_rec = s["id"].startswith("S_REC_")
            if is_rec:
                if risposta: # risposta è True
                    filtered_semis.append(s)
            else:
                filtered_semis.append(s)
                
        # Se risposta è True, posiziona i residui di taglio (S_REC_) all'inizio
        if risposta:
            filtered_semis.sort(key=lambda s: not s["id"].startswith("S_REC_"))
            
        return filtered_semis, True

    def run_optimization(self):
        if not self.current_order:
            messagebox.showwarning("Attenzione", "La lista dei pezzi da tagliare è vuota. Aggiungi dei pezzi o importa un file CSV.")
            return
            
        # Rileva se ci sono record verdi
        green_demands = [p for p in self.current_order if p.get("is_green", False)]
        if green_demands:
            optimization_order = copy.deepcopy(green_demands)
        else:
            # Se nessun record è verde, elaboriamo tutti i pezzi presenti
            optimization_order = copy.deepcopy(self.current_order)
            
        # Legge parametri dall'interfaccia
        try:
            kerf = float(self.ent_kerf.get().replace(",", "."))
            rifilo_h = float(self.ent_rifilo_h.get().replace(",", "."))
            rifilo_v = float(self.ent_rifilo_v.get().replace(",", "."))
            sfrido = float(self.ent_sfrido.get().replace(",", "."))
            min_w = float(self.ent_min_w.get().replace(",", "."))
            min_h = float(self.ent_min_h.get().replace(",", "."))
        except ValueError:
            messagebox.showerror("Errore", "I valori dei parametri devono essere numerici.")
            return
            
        macchina = self.cmb_macchina.get().lower()
            
        respect_grain = self.var_grain.get()
        
        # Prepara stock (barre + semilavorati)
        # Sincronizza per essere sicuri
        self.data_manager.db = self.data_manager.load_db()
        raw_semis = self.data_manager.get_semilavorati()
        raw_barre = self.data_manager.get_barre()
        
        use_residuo = self.var_stock_residuo.get()
        use_pannello = self.var_stock_pannello.get()
        use_barra = self.var_stock_barra.get()
        
        panel_grain_direction = "verticale"
        if use_barra:
            # Mostra la scelta solo se almeno uno dei pannelli coinvolti ha la venatura attiva
            order_keys = {(p["thickness"], p["color_code"]) for p in optimization_order}
            has_grain_panels = any(
                b.get("has_grain", False) for b in raw_barre
                if (b["thickness"], b["color_code"]) in order_keys
            )
            if has_grain_panels:
                panel_grain_direction = self.ask_panel_grain_direction()
        
        if not (use_residuo or use_pannello or use_barra):
            messagebox.showerror("Errore", "Selezionare almeno un tipo di materiale da utilizzare nel magazzino (Residuo, Pannello o Barra).")
            return
            
        color_grain_map = self.get_color_grain_map()
        # Calcola le altezze standard per ciascun gruppo
        group_std_heights = {}
        for s in raw_semis:
            if not s["id"].startswith("S_REC_"):
                key = f"{s['thickness']}mm_{s['color_code']}"
                if key not in group_std_heights:
                    group_std_heights[key] = set()
                std_h = min(float(s["width"]), float(s["height"]))
                group_std_heights[key].add(std_h)
        for k in group_std_heights:
            group_std_heights[k] = sorted(list(group_std_heights[k]))

        respect_grain_dict = {}
        for p in optimization_order:
            key = f"{p['thickness']}mm_{p['color_code']}"
            matching_semi = next((s for s in raw_semis if f"{s['thickness']}mm_{s['color_code']}" == key), None)
            if matching_semi:
                respect_grain_dict[key] = matching_semi.get("has_grain", False)
            else:
                respect_grain_dict[key] = color_grain_map.get(p["color_code"], False)

        stocks = []
        
        # 1. Residui (se selezionati e idonei)
        if use_residuo:
            all_residui = [s for s in raw_semis if s["id"].startswith("S_REC_")]
            for r in all_residui:
                r["_origin_table"] = "semilavorati"
            
            barre_residui = [b for b in raw_barre if b["id"].startswith("S_REC_")]
            for r in barre_residui:
                r["_origin_table"] = "barre"
            
            combined_residui = all_residui + barre_residui
            suitable_residui = self.get_suitable_residui(combined_residui, optimization_order, respect_grain_dict, group_std_heights)
            for s in suitable_residui:
                qty = int(s.get("quantity", 1))
                for _ in range(qty):
                    item = copy.deepcopy(s)
                    item["stock_type"] = "remnant"
                    item["has_grain"] = s.get("has_grain", False)
                    item["_origin_table"] = s.get("_origin_table", "semilavorati")
                    key = f"{item['thickness']}mm_{item['color_code']}"
                    self.orient_stock_item(item, group_std_heights.get(key, []))
                    stocks.append(item)
                        
        # 2. Pannelli (se selezionati)
        if use_pannello:
            for s in raw_semis:
                if not s["id"].startswith("S_REC_"):
                    qty = int(s.get("quantity", 1))
                    for _ in range(qty):
                        item = copy.deepcopy(s)
                        item["stock_type"] = "semilavorato_bar"
                        item["has_grain"] = s.get("has_grain", False)
                        item["_origin_table"] = "semilavorati"
                        key = f"{item['thickness']}mm_{item['color_code']}"
                        self.orient_stock_item(item, group_std_heights.get(key, []))
                        stocks.append(item)
                        
        # 3. Barre (se selezionate)
        if use_barra:
            for b in raw_barre:
                if not b["id"].startswith("S_REC_"):
                    qty = int(b.get("quantity", 1))
                    for _ in range(qty):
                        item = copy.deepcopy(b)
                        item["stock_type"] = "whole_board"
                        item["has_grain"] = b.get("has_grain", False)
                        item["_origin_table"] = "barre"
                        stocks.append(item)
        
        if not stocks:
            risposta = messagebox.askyesno(
                "Magazzino Vuoto",
                "Non ci sono materiali disponibili nel magazzino per le selezioni correnti (le quantità sono a 0 o non ci sono elementi).\n\n"
                "Vuoi visualizzare comunque i layout di taglio usando pannelli virtuali (come nel Calcolo Fabbisogni)?"
            )
            if risposta:
                self.calculate_requirements()
            return
            
        # Mostra dialog di caricamento e imposta cursore watch
        loading = LoadingDialog(self.root, "Ottimizzazione e disposizione tagli in corso...")
        self.root.config(cursor="watch")
        self.root.update()
        
        try:
            # Gli standard heights e respect grain sono già precalcolati all'inizio

            # Avvia ottimizzazione
            self.optimizer.kerf = kerf
            self.optimization_results = self.optimizer.optimize(
                stocks=stocks,
                demands=optimization_order,
                respect_grain=respect_grain_dict,
                min_semilavorato_width=min_w,
                min_semilavorato_height=min_h,
                group_std_heights=group_std_heights,
                rifilo_verticale=rifilo_v,
                rifilo_orizzontale=rifilo_h,
                sfrido=sfrido,
                machine_type=macchina,
                panel_grain_direction=panel_grain_direction
            )
            
            # Abilita bottoni
            self.btn_consume.config(state=tk.NORMAL)
            self.btn_export.config(state=tk.NORMAL)
            self.btn_export_pdf.config(state=tk.NORMAL)
            
            # Popola combobox gruppi
            self.populate_groups_combobox()
                
            # Genera log e statistiche
            self.update_report_tab()
            self.update_vis_tabs_visibility()
        finally:
            loading.destroy()
            self.root.config(cursor="")
        
        # Controlla se ci sono pezzi non piazzati per mancanza di stock
        has_unplaced = False
        if self.optimization_results and "gruppi" in self.optimization_results:
            for key, g in self.optimization_results["gruppi"].items():
                if g.get("unplaced_pieces"):
                    has_unplaced = True
                    break
                    
        if has_unplaced:
            risposta = messagebox.askyesno(
                "Materiale Insufficiente",
                "Alcuni pezzi non sono stati posizionati perché il materiale in magazzino è insufficiente o assente per quel colore/spessore.\n\n"
                "Vuoi visualizzare comunque i layout di taglio completi usando pannelli virtuali (come nel Calcolo Fabbisogni)?"
            )
            if risposta:
                self.calculate_requirements()
                return
        
        messagebox.showinfo("Ottimizzazione Completata", "Calcolo terminato con successo! Esamina i layout di taglio e le statistiche nei relativi tab.")

    def orient_stock_item(self, item, std_heights):
        """
        Orienta orizzontalmente sia le barre standard sia i residui di barra (Y-axis = altezza standard, X-axis = lunghezza).
        """
        if item.get("stock_type") == "semilavorato_bar":
            # Standard bar template: width in DB is standard height, height is length (2800)
            # We always want width to be length and height to be standard height
            if item["width"] < item["height"]:
                item["width"], item["height"] = item["height"], item["width"]
        elif item.get("stock_type") == "remnant" and std_heights:
            # Remnant in a bar group: Y-axis (height) must be the standard height
            # Check if ID tells us the standard height
            id_str = str(item.get("id", ""))
            std_h = None
            if id_str.startswith("S_REC_H"):
                try:
                    parts = id_str.split("_")
                    for p in parts:
                        if p.startswith("H"):
                            std_h = float(p[1:])
                            break
                except Exception:
                    pass
            
            if std_h is not None:
                if abs(item["width"] - std_h) < 1e-2:
                    item["width"], item["height"] = item["height"], item["width"]
            else:
                # Fallback to matching with std_heights
                w_in = any(abs(item["width"] - sh) < 1e-2 for sh in std_heights)
                h_in = any(abs(item["height"] - sh) < 1e-2 for sh in std_heights)
                if w_in and not h_in:
                    item["width"], item["height"] = item["height"], item["width"]
                elif not w_in and h_in:
                    pass
                elif w_in and h_in:
                    if item["width"] < item["height"]:
                        item["width"], item["height"] = item["height"], item["width"]
                else:
                    if item["width"] < item["height"]:
                        item["width"], item["height"] = item["height"], item["width"]

    def _is_height_allowed_simple(self, board, piece_h, std_heights):
        if not board or not std_heights:
            return True
            
        board_h = float(board.get("height", 0))
        if piece_h > board_h:
            return False
        return True

    def get_suitable_residui(self, raw_semis, demands, respect_grain_dict, group_std_heights):
        suitable = []
        for s in raw_semis:
            if not s["id"].startswith("S_REC_"):
                continue
            key = f"{s['thickness']}mm_{s['color_code']}"
            group_demands = [d for d in demands if f"{d['thickness']}mm_{d['color_code']}" == key]
            if not group_demands:
                continue
                
            std_heights = group_std_heights.get(key, [])
            
            s_copy = copy.deepcopy(s)
            s_copy["stock_type"] = "remnant"
            self.orient_stock_item(s_copy, std_heights)
            
            is_suitable = False
            respect_grain = respect_grain_dict.get(key, False)
            is_bar_group = bool(std_heights)
            
            for d in group_demands:
                if is_bar_group:
                    w_p = d["height"]
                    h_p = d["width"]
                    if w_p <= s_copy["width"] and h_p <= s_copy["height"]:
                        if self._is_height_allowed_simple(s_copy, h_p, std_heights):
                            is_suitable = True
                            break
                else:
                    w_p = d["width"]
                    h_p = d["height"]
                    if respect_grain:
                        if w_p <= s_copy["width"] and h_p <= s_copy["height"]:
                            is_suitable = True
                            break
                    else:
                        if (w_p <= s_copy["width"] and h_p <= s_copy["height"]) or (h_p <= s_copy["width"] and w_p <= s_copy["height"]):
                            is_suitable = True
                            break
            if is_suitable:
                suitable.append(s)
        return suitable

    def calculate_requirements(self):
        if getattr(self, "current_commessa_status", "Aperta") == "Chiusa":
            messagebox.showerror("Errore", "La commessa corrente è CHIUSA (prodotta) e non è più soggetta a calcolo.")
            return
        # Rileva se ci sono record verdi
        green_demands = [p for p in self.current_order if p.get("is_green", False)]
        if green_demands:
            optimization_order = copy.deepcopy(green_demands)
        else:
            # Se nessun record è verde, elaboriamo tutti i pezzi presenti
            optimization_order = copy.deepcopy(self.current_order)

        # Legge parametri dall'interfaccia
        try:
            kerf = float(self.ent_kerf.get().replace(",", "."))
            rifilo_h = float(self.ent_rifilo_h.get().replace(",", "."))
            rifilo_v = float(self.ent_rifilo_v.get().replace(",", "."))
            sfrido = float(self.ent_sfrido.get().replace(",", "."))
            min_w = float(self.ent_min_w.get().replace(",", "."))
            min_h = float(self.ent_min_h.get().replace(",", "."))
        except ValueError:
            messagebox.showerror("Errore", "I valori dei parametri devono essere numerici.")
            return
            
        macchina = self.cmb_macchina.get().lower()
            
        respect_grain = self.var_grain.get()
        
        # Carica stock corrente
        self.data_manager.db = self.data_manager.load_db()
        raw_semis = self.data_manager.get_semilavorati()
        raw_barre = self.data_manager.get_barre()
        
        use_residuo = self.var_stock_residuo.get()
        use_pannello = self.var_stock_pannello.get()
        use_barra = self.var_stock_barra.get()
        
        panel_grain_direction = "verticale"
        if use_barra:
            # Mostra la scelta solo se almeno uno dei pannelli coinvolti ha la venatura attiva
            order_keys = {(p["thickness"], p["color_code"]) for p in optimization_order}
            has_grain_panels = any(
                b.get("has_grain", False) for b in raw_barre
                if (b["thickness"], b["color_code"]) in order_keys
            )
            if has_grain_panels:
                panel_grain_direction = self.ask_panel_grain_direction()
        
        if not (use_residuo or use_pannello or use_barra):
            messagebox.showerror("Errore", "Selezionare almeno un tipo di materiale da utilizzare nel magazzino (Residuo, Pannello o Barra).")
            return
            
        # Mostra dialog di caricamento e imposta cursore watch
        loading = LoadingDialog(self.root, "Calcolo dei fabbisogni di commessa in corso...")
        self.root.config(cursor="watch")
        self.root.update()
        
        try:
            color_grain_map = self.get_color_grain_map()
            # Trova tutti i gruppi di materiali presenti nell'ordine
            material_groups = set()
            for p in optimization_order:
                group_key = (p["thickness"], p["color_code"], p["color_desc"])
                material_groups.add(group_key)
                
            # Calcola le altezze standard e rispetto venatura per ciascun gruppo
            group_std_heights = {}
            respect_grain_dict = {}
            for thickness, color_code, color_desc in material_groups:
                group_key = f"{thickness}mm_{color_code}"
                group_semis = [s for s in raw_semis if str(s["thickness"]) == str(thickness) and s["color_code"] == color_code]
                group_pannelli = [s for s in group_semis if not s["id"].startswith("S_REC_")]
                std_heights = sorted(list(set(min(float(b["width"]), float(b["height"])) for b in group_pannelli)))
                group_std_heights[group_key] = std_heights
                
                if group_semis:
                    respect_grain_dict[group_key] = group_semis[0].get("has_grain", False)
                else:
                    respect_grain_dict[group_key] = color_grain_map.get(color_code, False)

            # Filtriamo i residui idonei a livello globale
            if use_residuo:
                suitable_residui_global = self.get_suitable_residui(raw_semis, optimization_order, respect_grain_dict, group_std_heights)
            else:
                suitable_residui_global = []

            # Costruisce lo stock simulato per il primo passaggio
            simulated_stock = []
            simulated_barre_reali_per_gruppo = {}
            group_use_barra_dict = {}
            
            for thickness, color_code, color_desc in material_groups:
                group_key = f"{thickness}mm_{color_code}"
                # Filtra semilavorati e barre esistenti per questo materiale
                group_semis = [s for s in raw_semis if str(s["thickness"]) == str(thickness) and s["color_code"] == color_code]
                group_residui = [s for s in suitable_residui_global if str(s["thickness"]) == str(thickness) and s["color_code"] == color_code]
                group_pannelli = [s for s in group_semis if not s["id"].startswith("S_REC_")]
                group_barre_reali = [b for b in raw_barre if str(b["thickness"]) == str(thickness) and b["color_code"] == color_code]
                
                # Trova barra standard di riferimento
                if group_barre_reali:
                    ref_bar_template = group_barre_reali[0]
                else:
                    default_w = 2800.0
                    default_h = 2070.0
                    if raw_barre:
                        default_w = raw_barre[0]["width"]
                        default_h = raw_barre[0]["height"]
                    ref_bar_template = {
                        "id": "Barra Standard",
                        "width": default_w,
                        "height": default_h,
                        "thickness": thickness,
                        "color_code": color_code,
                        "color_desc": color_desc,
                        "has_grain": False
                    }
                
                # La venatura per le barre (semilavorati) viene presa dal record della barra se presente, altrimenti da color_grain_map
                group_respect_grain = False
                if group_semis:
                    group_respect_grain = group_semis[0].get("has_grain", False)
                else:
                    group_respect_grain = color_grain_map.get(color_code, False)

                # Estraiamo le altezze standard presenti nell'archivio per questo gruppo spessore/colore
                std_heights = sorted(list(set(min(float(b["width"]), float(b["height"])) for b in group_pannelli)))

                # 1. Aggiungi Residui reali (se selezionati)
                if use_residuo:
                    for idx, s in enumerate(group_residui):
                        qty = int(s.get("quantity", 1))
                        for q_idx in range(qty):
                            item = copy.deepcopy(s)
                            item["_source_type"] = "residuo_real"
                            item["_unique_index"] = f"residuo_real_{s['id']}_{idx}_{q_idx}"
                            item["stock_type"] = "remnant"
                            item["has_grain"] = s.get("has_grain", False)
                            self.orient_stock_item(item, std_heights)
                            simulated_stock.append(item)
                            
                # 2. Aggiungi Pannelli reali (se selezionati)
                if use_pannello:
                    for idx, s in enumerate(group_pannelli):
                        qty = int(s.get("quantity", 1))
                        for q_idx in range(qty):
                            item = copy.deepcopy(s)
                            item["_source_type"] = "pannello_real"
                            item["_unique_index"] = f"pannello_real_{s['id']}_{idx}_{q_idx}"
                            item["stock_type"] = "semilavorato_bar"
                            item["has_grain"] = s.get("has_grain", False)
                            self.orient_stock_item(item, std_heights)
                            simulated_stock.append(item)
                            
                # 3. Aggiungi Pannelli virtuali (se selezionati)
                if use_pannello:
                    # 3a. Copie virtuali dei pannelli reali esistenti (se presenti)
                    if group_pannelli:
                        unique_panels = []
                        seen_sizes = set()
                        for p in group_pannelli:
                            size_key = (p["width"], p["height"])
                            if size_key not in seen_sizes:
                                seen_sizes.add(size_key)
                                unique_panels.append(p)
                                
                        for idx, p in enumerate(unique_panels):
                            for q_idx in range(100):
                                item = copy.deepcopy(p)
                                item["_source_type"] = "pannello_virtual"
                                item["_unique_index"] = f"pannello_virtual_{p['id']}_{idx}_{q_idx}"
                                item["stock_type"] = "semilavorato_bar"
                                item["has_grain"] = p.get("has_grain", False)
                                self.orient_stock_item(item, std_heights)
                                if not str(item["id"]).endswith("[Virtuale]"):
                                    item["id"] = f"{item['id']} [Virtuale]"
                                simulated_stock.append(item)
                    
                    # 3b. Generazione dinamica di pannelli virtuali ad altezza prodotto finale
                    # per ciascuna altezza unica dei pezzi nell'ordine (allineando alle altezze standard)
                    group_demands = [p for p in self.current_order if str(p["thickness"]) == str(thickness) and p["color_code"] == color_code]
                    W_bar = max(ref_bar_template["width"], ref_bar_template["height"])
                    H_bar = min(ref_bar_template["width"], ref_bar_template["height"])
                    
                    # Estraiamo le altezze standard presenti nell'archivio per questo gruppo spessore/colore
                    std_heights = sorted(list(set(min(float(b["width"]), float(b["height"])) for b in group_pannelli)))
                    max_std_h = max(std_heights) if std_heights else 0.0
                    
                    # Controlliamo se ci sono elementi che non entrano nelle barre standard per dimensioni
                    has_tall_pieces = False
                    for p in group_demands:
                        can_fit_in_bar = False
                        if group_respect_grain:
                            if p["width"] <= max_std_h and p["height"] <= W_bar:
                                can_fit_in_bar = True
                        else:
                            if (p["width"] <= max_std_h and p["height"] <= W_bar) or (p["height"] <= max_std_h and p["width"] <= W_bar):
                                can_fit_in_bar = True
                        if not can_fit_in_bar:
                            has_tall_pieces = True
                            break
                                
                    group_use_barra = use_barra or has_tall_pieces
                    group_use_barra_dict[group_key] = group_use_barra
                    
                    unique_heights = set()
                    for p in group_demands:
                        h_val = p["height"]
                        if std_heights:
                            covered = [std_h for std_h in std_heights if std_h >= h_val]
                            if covered:
                                h_val = min(covered)
                        unique_heights.add(h_val)
                        
                        if not group_respect_grain:
                            w_val = p["width"]
                            if std_heights:
                                covered = [std_h for std_h in std_heights if std_h >= w_val]
                                if covered:
                                    w_val = min(covered)
                            unique_heights.add(w_val)
                            
                    for idx, h in enumerate(sorted(unique_heights)):
                        # Genera la barra virtuale (pannello_virtual) solo se è entro la massima altezza standard
                        # (altrimenti verrà tagliata direttamente dal pannello_virtual generato al punto 5)
                        if h <= H_bar and (not std_heights or h <= max_std_h):
                            for q_idx in range(100):
                                item = {
                                    "id": f"Pannello H{int(h)} [Virtuale]",
                                    "width": W_bar,
                                    "height": h,
                                    "thickness": thickness,
                                    "color_code": color_code,
                                    "color_desc": color_desc,
                                    "has_grain": group_respect_grain,
                                    "_source_type": "pannello_virtual",
                                    "_unique_index": f"pannello_virtual_dyn_{int(h)}_{idx}_{q_idx}",
                                    "stock_type": "semilavorato_bar"
                                }
                                simulated_stock.append(item)
                             
                else:
                    group_use_barra_dict[group_key] = use_barra
                            
                # 4. Aggiungi Barre reali (se selezionate o auto-abilitate)
                group_real_bars_simulated = []
                if group_use_barra:
                    for idx, b in enumerate(group_barre_reali):
                        qty = int(b.get("quantity", 1))
                        for q_idx in range(qty):
                            item = copy.deepcopy(b)
                            item["_source_type"] = "barra_real"
                            item["_unique_index"] = f"barra_real_{b['id']}_{idx}_{q_idx}"
                            item["stock_type"] = "whole_board"
                            item["has_grain"] = b.get("has_grain", False)
                            simulated_stock.append(item)
                            group_real_bars_simulated.append(item)
                simulated_barre_reali_per_gruppo[f"{thickness}mm_{color_code}"] = group_real_bars_simulated
                
                # 5. Aggiungi Barre virtuali (se selezionate o auto-abilitate)
                if group_use_barra:
                    bars_for_virtual = group_barre_reali if group_barre_reali else [ref_bar_template]
                    for idx, b in enumerate(bars_for_virtual):
                        for q_idx in range(100):
                            item = copy.deepcopy(b)
                            item["_source_type"] = "barra_virtual"
                            item["_unique_index"] = f"barra_virtual_{b['id']}_{idx}_{q_idx}"
                            item["stock_type"] = "whole_board"
                            item["has_grain"] = b.get("has_grain", False)
                            if not str(item["id"]).endswith("[Virtuale]"):
                                item["id"] = f"{item['id']} [Virtuale]"
                            simulated_stock.append(item)

            # Avvia l'ottimizzatore per il Primo Passaggio
            sim_optimizer = CuttingOptimizer(kerf=kerf)
            first_pass_results = sim_optimizer.optimize(
                stocks=simulated_stock,
                demands=optimization_order,
                respect_grain=respect_grain_dict,
                min_semilavorato_width=min_w,
                min_semilavorato_height=min_h,
                group_std_heights=group_std_heights,
                rifilo_verticale=rifilo_v,
                rifilo_orizzontale=rifilo_h,
                sfrido=sfrido,
                machine_type=macchina,
                panel_grain_direction=panel_grain_direction
            )
            
            # Elabora i risultati e calcola il secondo passaggio
            fabbisogno_report = []
            global_sufficient = True
            final_gruppi = {}
            
            for thickness, color_code, color_desc in sorted(material_groups):
                key = f"{thickness}mm_{color_code}"
                group_demands = [p for p in optimization_order if str(p["thickness"]) == str(thickness) and p["color_code"] == color_code]
                total_demands_qty = sum(int(p.get("quantity", 1)) for p in group_demands)
                
                # Conteggio disponibilità reali a magazzino
                group_semis = [s for s in raw_semis if str(s["thickness"]) == str(thickness) and s["color_code"] == color_code]
                group_residui = [s for s in group_semis if s["id"].startswith("S_REC_")]
                group_pannelli = [s for s in group_semis if not s["id"].startswith("S_REC_")]
                group_barre_reali = [b for b in raw_barre if str(b["thickness"]) == str(thickness) and b["color_code"] == color_code]
                
                avail_residui_qty = sum(int(s.get("quantity", 1)) for s in group_residui)
                avail_pannelli_qty = sum(int(s.get("quantity", 1)) for s in group_pannelli)
                avail_barre_qty = sum(int(b.get("quantity", 1)) for b in group_barre_reali)
                
                # Inizializza statistiche per questo gruppo
                pieces_from_residui = 0
                pannelli_real_used = 0
                pannelli_virtual_used_boards = []
                
                barre_real_used_direct = 0
                barre_virtual_used_direct_counts = {}
                
                unplaced_pieces = []
                used_boards_first_pass = []
                
                group_use_barra = group_use_barra_dict.get(key, False)
                
                if key in first_pass_results["gruppi"]:
                    g_res = first_pass_results["gruppi"][key]
                    unplaced_pieces = g_res["unplaced_pieces"]
                    
                    # Carica ref_bar_template per questo gruppo
                    group_barre_reali = [b for b in raw_barre if str(b["thickness"]) == str(thickness) and b["color_code"] == color_code]
                    if group_barre_reali:
                        ref_bar_template = group_barre_reali[0]
                    else:
                        default_w = 2800.0
                        default_h = 2070.0
                        if raw_barre:
                            default_w = raw_barre[0]["width"]
                            default_h = raw_barre[0]["height"]
                        ref_bar_template = {
                            "id": "Barra Standard",
                            "width": default_w,
                            "height": default_h,
                            "thickness": thickness,
                            "color_code": color_code,
                            "color_desc": color_desc,
                            "has_grain": False
                        }
                    
                    std_heights = group_std_heights.get(key, [])
                    max_std_h = max(std_heights) if std_heights else 0.0
                    W_bar = max(ref_bar_template["width"], ref_bar_template["height"])
                    
                    panel_w = ref_bar_template.get("width", 0.0)
                    panel_h = ref_bar_template.get("height", 0.0)
                    
                    group_respect_grain = respect_grain_dict.get(key, False)
                    
                    for up in unplaced_pieces:
                        up["unproducible_reason"] = "Mancano pannelli standard di riferimento nel database"
                        if ref_bar_template:
                            fits_panel = False
                            if group_respect_grain:
                                if up["width_orig"] <= panel_w and up["height_orig"] <= panel_h:
                                    fits_panel = True
                            else:
                                if (up["width_orig"] <= panel_w and up["height_orig"] <= panel_h) or (up["height_orig"] <= panel_w and up["width_orig"] <= panel_h):
                                    fits_panel = True
                                    
                            if not fits_panel:
                                up["unproducible_reason"] = f"Supera le dimensioni del pannello standard ({int(panel_w)}x{int(panel_h)})"
                            else:
                                if not group_use_barra:
                                    up["unproducible_reason"] = f"Supera le dimensioni delle barre standard (altezza max {int(max_std_h)} o lunghezza max {int(W_bar)})"
                                else:
                                    up["unproducible_reason"] = "Spazio insufficiente o vincoli di taglio"
                    
                    for ub in g_res["used_boards"]:
                        board = ub["board"]
                        src_type = board.get("_source_type")
                        
                        if src_type == "residuo_real":
                            pieces_from_residui += len(ub["placed_pieces"])
                            used_boards_first_pass.append(ub)
                        elif src_type == "pannello_real":
                            pannelli_real_used += 1
                            used_boards_first_pass.append(ub)
                        elif src_type == "pannello_virtual":
                            pannelli_virtual_used_boards.append(ub)
                            used_boards_first_pass.append(ub)
                        elif src_type == "barra_real":
                            barre_real_used_direct += 1
                            used_boards_first_pass.append(ub)
                        elif src_type == "barra_virtual":
                            b_id = board.get("id", "Barra")
                            w = int(board.get("width", 0))
                            h = int(board.get("height", 0))
                            display_name = f"Barra Standard ({w}x{h})" if ("dummy" in b_id.lower() or "virtual" in b_id.lower() or "barra standard" in b_id.lower()) else f"{b_id} ({w}x{h})"
                            barre_virtual_used_direct_counts[display_name] = barre_virtual_used_direct_counts.get(display_name, 0) + 1
                            used_boards_first_pass.append(ub)
                            
                # SECONDO PASSAGGIO: taglio dei pannelli virtuali dalle barre standard
                barre_real_used_for_panels = 0
                barre_virtual_used_for_panels_counts = {}
                used_boards_second_pass = []
                
                if pannelli_virtual_used_boards and group_use_barra:
                    second_pass_demands = []
                    for ub in pannelli_virtual_used_boards:
                        board = ub["board"]
                        # Rimuoviamo la dicitura [Virtuale] dall'ID per la descrizione della domanda
                        clean_id = str(board.get("id", "Virt")).replace(" [Virtuale]", "")
                        second_pass_demands.append({
                            "descrizione": f"Pannello {clean_id}",
                            "width": board["width"],
                            "height": board["height"],
                            "thickness": board["thickness"],
                            "color_code": board["color_code"],
                            "color_desc": board["color_desc"],
                            "quantity": 1
                        })
                        
                    # Trova barre reali rimanenti
                    used_real_bar_indices = set(
                        ub["board"]["_unique_index"] for ub in used_boards_first_pass
                        if ub["board"].get("_source_type") == "barra_real"
                    )
                    group_real_bars_simulated = simulated_barre_reali_per_gruppo.get(key, [])
                    remaining_barre_reali = [
                        copy.deepcopy(b) for b in group_real_bars_simulated
                        if b["_unique_index"] not in used_real_bar_indices
                    ]
                    
                    # Costruisce lo stock per il secondo passaggio
                    second_pass_stock = []
                    group_respect_grain = color_grain_map.get(color_code, False)
                    for b in remaining_barre_reali:
                        b["_source_type"] = "barra_real"
                        b["stock_type"] = "whole_board"
                        b["has_grain"] = group_respect_grain
                        second_pass_stock.append(b)
                        
                    # Aggiunge 100 copie virtuali delle barre
                    if group_barre_reali:
                        ref_bar_template = group_barre_reali[0]
                    else:
                        default_w = 2800.0
                        default_h = 2070.0
                        if raw_barre:
                            default_w = raw_barre[0]["width"]
                            default_h = raw_barre[0]["height"]
                        ref_bar_template = {
                            "id": "Barra Standard",
                            "width": default_w,
                            "height": default_h,
                            "thickness": thickness,
                            "color_code": color_code,
                            "color_desc": color_desc,
                            "has_grain": group_respect_grain
                        }
                    bars_for_virtual = group_barre_reali if group_barre_reali else [ref_bar_template]
                    for idx, b in enumerate(bars_for_virtual):
                        for q_idx in range(100):
                            item = copy.deepcopy(b)
                            item["_source_type"] = "barra_virtual"
                            item["_unique_index"] = f"barra_virtual_p_{b['id']}_{idx}_{q_idx}"
                            item["stock_type"] = "whole_board"
                            item["has_grain"] = group_respect_grain
                            if not str(item["id"]).endswith("[Virtuale]"):
                                item["id"] = f"{item['id']} [Virtuale]"
                            second_pass_stock.append(item)
                            
                    # Ottimizza il secondo passaggio
                    second_pass_results = sim_optimizer.optimize(
                        stocks=second_pass_stock,
                        demands=second_pass_demands,
                        respect_grain=respect_grain_dict,
                        min_semilavorato_width=min_w,
                        min_semilavorato_height=min_h,
                        panel_grain_direction=panel_grain_direction
                    )
                    
                    if key in second_pass_results["gruppi"]:
                        g_res_sec = second_pass_results["gruppi"][key]
                        for ub in g_res_sec["used_boards"]:
                            board = ub["board"]
                            orig_id = board.get("id", "Barra")
                            if not "[PER PANNELLI]" in orig_id:
                                board["id"] = f"{orig_id} [PER PANNELLI]"
                                
                            src_type = board.get("_source_type")
                            if src_type == "barra_real":
                                barre_real_used_for_panels += 1
                            elif src_type == "barra_virtual":
                                w = int(board.get("width", 0))
                                h = int(board.get("height", 0))
                                display_name = f"Barra Standard ({w}x{h})" if ("dummy" in orig_id.lower() or "virtual" in orig_id.lower() or "barra standard" in orig_id.lower()) else f"{orig_id.split(' [Virtuale]')[0]} ({w}x{h})"
                                barre_virtual_used_for_panels_counts[display_name] = barre_virtual_used_for_panels_counts.get(display_name, 0) + 1
                            used_boards_second_pass.append(ub)
                
                # Combina usati dei due passaggi
                merged_used_boards = used_boards_first_pass + used_boards_second_pass
                
                # Calcola totali riepilogo
                pannelli_virtual_needed = len(pannelli_virtual_used_boards)
                total_barre_real_used = barre_real_used_direct + barre_real_used_for_panels
                total_barre_virtual_needed = sum(barre_virtual_used_direct_counts.values()) + sum(barre_virtual_used_for_panels_counts.values())
                
                extra_needed_merged = {}
                for name, qty in barre_virtual_used_direct_counts.items():
                    extra_needed_merged[name] = extra_needed_merged.get(name, 0) + qty
                for name, qty in barre_virtual_used_for_panels_counts.items():
                    extra_needed_merged[name] = extra_needed_merged.get(name, 0) + qty
                    
                # Determina stato del gruppo
                # Se ci sono deficit di barre standard, o se non abbiamo potuto piazzare alcuni pezzi
                if total_barre_virtual_needed > 0 or len(unplaced_pieces) > 0:
                    status = "INSUFFICIENTE"
                    global_sufficient = False
                else:
                    status = "Sufficiente"
                    
                fabbisogno_report.append({
                    "thickness": thickness,
                    "color_code": color_code,
                    "color_desc": color_desc,
                    "total_demands": total_demands_qty,
                    
                    "avail_residui": avail_residui_qty,
                    "pieces_from_residui": pieces_from_residui,
                    
                    "avail_pannelli": avail_pannelli_qty,
                    "pannelli_real_used": pannelli_real_used,
                    "pannelli_virtual_needed": pannelli_virtual_needed,
                    
                    "avail_barre": avail_barre_qty,
                    "barre_real_used_direct": barre_real_used_direct,
                    "barre_virtual_needed_direct": sum(barre_virtual_used_direct_counts.values()),
                    "barre_real_used_for_panels": barre_real_used_for_panels,
                    "barre_virtual_needed_for_panels": sum(barre_virtual_used_for_panels_counts.values()),
                    
                    "total_barre_real_used": total_barre_real_used,
                    "total_barre_virtual_needed": total_barre_virtual_needed,
                    "extra_needed": extra_needed_merged,
                    "total_extra_needed": total_barre_virtual_needed,
                    
                    "unplaced_count": len(unplaced_pieces),
                    "unplaced_list": unplaced_pieces,
                    "status": status
                })
                
                # Calcola riepilogo gruppo per final_gruppi
                group_board_area = 0.0
                group_placed_area = 0.0
                for ub in merged_used_boards:
                    group_board_area += ub["board"]["width"] * ub["board"]["height"]
                    group_placed_area += ub["used_area"]
                group_waste = group_board_area - group_placed_area
                group_efficiency = (group_placed_area / group_board_area * 100) if group_board_area > 0 else 0.0
                
                final_gruppi[key] = {
                    "used_boards": merged_used_boards,
                    "unplaced_pieces": unplaced_pieces,
                    "summary": {
                        "total_boards_used": len(merged_used_boards),
                        "efficiency": round(group_efficiency, 2),
                        "used_area": round(group_placed_area, 2),
                        "waste_area": round(group_waste, 2),
                        "total_board_area": round(group_board_area, 2)
                    }
                }
                
            # Costruisce il summary generale
            totale_area_lastre = sum(g["summary"]["total_board_area"] for g in final_gruppi.values())
            totale_area_pezzi = sum(g["summary"]["used_area"] for g in final_gruppi.values())
            totale_area_scarto = totale_area_lastre - totale_area_pezzi
            efficienza_generale = (totale_area_pezzi / totale_area_lastre * 100) if totale_area_lastre > 0 else 0.0
            
            self.optimization_results = {
                "gruppi": final_gruppi,
                "summary_generale": {
                    "totale_area_lastre": round(totale_area_lastre, 2),
                    "totale_area_pezzi": round(totale_area_pezzi, 2),
                    "totale_area_scarto": round(totale_area_scarto, 2),
                    "efficienza_media": round(efficienza_generale, 2)
                }
            }
            
            # Abilita bottoni di esportazione ma disabilita Consuma (poiché è virtuale)
            self.btn_consume.config(state=tk.DISABLED)
            self.btn_export.config(state=tk.NORMAL)
            self.btn_export_pdf.config(state=tk.NORMAL)
            
            # Popola combobox gruppi
            self.populate_groups_combobox()
                
            # Genera log e statistiche nel tab Report
            self.update_report_tab()
            self.update_vis_tabs_visibility()
        finally:
            loading.destroy()
            self.root.config(cursor="")
            
        # Mostra il dialogo con i risultati del fabbisogno
        FabbisognoDialog(self.root, fabbisogno_report, global_sufficient)

    def update_report_tab(self):
        if not self.optimization_results:
            return
            
        summary = self.optimization_results["summary_generale"]
        
        # Aggiorna label veloci
        self.lbl_stat_efficiency.config(text=f"Efficienza Media: {summary['efficienza_media']}%")
        self.lbl_stat_boards.config(text=f"Area Barre Usate: {summary['totale_area_lastre'] / 1e6:.2f} m²")
        self.lbl_stat_placed.config(text=f"Area Pezzi Tagliati: {summary['totale_area_pezzi'] / 1e6:.2f} m²")
        
        # Calcola statistiche pezzi posizionati, non piazzati e nuovi semilavorati
        tot_placed = 0
        tot_unplaced = 0
        tot_recoveries = 0
        
        log_text = []
        log_text.append("=========================================")
        log_text.append("          REPORT DI TAGLIO CUTMOB        ")
        log_text.append("=========================================\n")
        log_text.append(f"Efficienza Generale: {summary['efficienza_media']}%")
        log_text.append(f"Area Barre Totale: {summary['totale_area_lastre']} mm²")
        log_text.append(f"Area Pezzi Totale: {summary['totale_area_pezzi']} mm²")
        log_text.append(f"Area Scarto Totale: {summary['totale_area_scarto']} mm²\n")
        
        for gk, g in self.optimization_results["gruppi"].items():
            parts = gk.split("_", 1)
            thickness_str = parts[0] if parts else gk
            color_code_str = parts[1] if len(parts) > 1 else "N/D"
            color_desc = "N/D"
            if g.get("used_boards"):
                color_desc = g["used_boards"][0]["board"].get("color_desc", "N/D")
            elif g.get("unplaced_pieces"):
                color_desc = g["unplaced_pieces"][0].get("color_desc", "N/D")
            log_text.append(f"--- GRUPPO MATERIALE: Spessore {thickness_str} | Colore: {color_code_str} - {color_desc} ---")
            log_text.append(f"  Efficienza gruppo: {g['summary']['efficiency']}%")
            log_text.append(f"  Barre usate: {g['summary']['total_boards_used']}")
            
            placed_in_group = sum(len(ub["placed_pieces"]) for ub in g["used_boards"])
            tot_placed += placed_in_group
            log_text.append(f"  Pezzi posizionati: {placed_in_group}")
            
            unplaced_in_group = len(g["unplaced_pieces"])
            tot_unplaced += unplaced_in_group
            log_text.append(f"  Pezzi non piazzati: {unplaced_in_group}")
            if unplaced_in_group > 0:
                for up in g["unplaced_pieces"]:
                    log_text.append(f"    - {up['descrizione']} ({int(up['width'])}x{int(up['height'])} mm)")
            
            new_semis_in_group = sum(len(ub.get("new_semilavorati", [])) for ub in g["used_boards"])
            tot_recoveries += new_semis_in_group
            log_text.append(f"  Semilavorati recuperati: {new_semis_in_group}")
            
            for b_idx, ub in enumerate(g["used_boards"]):
                is_virtual = (ub["board"].get("_source_type") == "barre_virtual") or (ub["board"].get("id") == "BARRA_VIRTUALE_DUMMY") or ("virtual" in str(ub["board"].get("id")).lower())
                virtual_suffix = " [MANCANTE - DA ACQUISTARE]" if is_virtual else ""
                color_desc = ub["board"].get("color_desc", "N/D")
                log_text.append(f"    Barra {b_idx + 1} ({ub['board']['id']} - {color_desc} - {int(ub['board']['width'])}x{int(ub['board']['height'])} mm){virtual_suffix}:")
                log_text.append(f"      Efficienza: {ub['efficiency']}%")
                log_text.append(f"      Pezzi posizionati ({len(ub['placed_pieces'])}):")
                for p in ub["placed_pieces"]:
                    rot_str = " (Ruotato)" if p["rotated"] else ""
                    log_text.append(f"        - {p['descrizione']}: pos={int(p['x'])},{int(p['y'])} dim={int(p['w'])}x{int(p['h'])}{rot_str}")
                
                if ub.get("new_semilavorati"):
                    log_text.append(f"      Semilavorati recuperati ({len(ub['new_semilavorati'])}):")
                    for s in ub["new_semilavorati"]:
                        log_text.append(f"        - Recupero {int(s['width'])}x{int(s['height'])} mm")
                
                if ub.get("cuts"):
                    log_text.append(f"      Sequenza Tagli Sezionatrice ({len(ub['cuts'])}):")
                    sorted_cuts = sorted(ub["cuts"], key=lambda c: c.get("step", 0))
                    for c in sorted_cuts:
                        tipo = "Orizzontale (guide Y)" if c["type"] == "H" else "Verticale (guide X)"
                        quota = int(c["y1"]) if c["type"] == "H" else int(c["x1"])
                        lunghezza = int(abs(c["x2"] - c["x1"])) if c["type"] == "H" else int(abs(c["y2"] - c["y1"]))
                        log_text.append(f"        Step {c.get('step', '')}: Taglio {tipo} a {quota} mm (Lunghezza: {lunghezza} mm)")
            log_text.append("")
            
        self.lbl_stat_placed.config(text=f"Pezzi Posizionati: {tot_placed}")
        self.lbl_stat_unplaced.config(text=f"Pezzi Rimanenti (Non Ottimizzati): {tot_unplaced}")
        self.lbl_stat_recoveries.config(text=f"Pezzi Recuperati (Nuovi Semilavorati): {tot_recoveries}")
        
        # Scrivi log nel widget
        self.txt_log.delete("1.0", tk.END)
        self.txt_log.insert(tk.END, "\n".join(log_text))

    def populate_groups_combobox(self):
        self.group_display_mapping = {}
        display_values = []
        if not self.optimization_results or "gruppi" not in self.optimization_results:
            self.cb_groups.config(values=[])
            self.selected_group_key = None
            return
            
        for key in sorted(self.optimization_results["gruppi"].keys()):
            g_data = self.optimization_results["gruppi"][key]
            color_desc = "N/D"
            if g_data["used_boards"]:
                color_desc = g_data["used_boards"][0]["board"].get("color_desc", "N/D")
            elif g_data["unplaced_pieces"]:
                color_desc = g_data["unplaced_pieces"][0].get("color_desc", "N/D")
            else:
                parts = key.split("_")
                for p in self.current_order:
                    if str(p["thickness"]) + "mm" == parts[0] and p["color_code"] == parts[1]:
                        color_desc = p.get("color_desc", "N/D")
                        break
            
            display_name = f"{key} ({color_desc})"
            self.group_display_mapping[display_name] = key
            display_values.append(display_name)
            
        self.cb_groups.config(values=display_values)
        if display_values:
            self.cb_groups.current(0)
            self.on_group_selected(None)
        else:
            self.selected_group_key = None

    def _are_layouts_identical(self, l1, l2):
        b1 = l1["board"]
        b2 = l2["board"]
        if b1.get("width") != b2.get("width") or b1.get("height") != b2.get("height"):
            return False
        if b1.get("thickness") != b2.get("thickness") or b1.get("color_code") != b2.get("color_code"):
            return False
            
        p1 = sorted(l1.get("placed_pieces", []), key=lambda p: (p.get("x", 0), p.get("y", 0), p.get("w", 0), p.get("h", 0)))
        p2 = sorted(l2.get("placed_pieces", []), key=lambda p: (p.get("x", 0), p.get("y", 0), p.get("w", 0), p.get("h", 0)))
        if len(p1) != len(p2):
            return False
            
        for i in range(len(p1)):
            item1 = p1[i]
            item2 = p2[i]
            if item1.get("x") != item2.get("x") or item1.get("y") != item2.get("y"):
                return False
            if item1.get("w") != item2.get("w") or item1.get("h") != item2.get("h"):
                return False
            if item1.get("rotated") != item2.get("rotated") or item1.get("descrizione") != item2.get("descrizione"):
                return False
                
        s1 = sorted(l1.get("new_semilavorati", []), key=lambda s: (s.get("x", 0), s.get("y", 0), s.get("width", 0), s.get("height", 0)))
        s2 = sorted(l2.get("new_semilavorati", []), key=lambda s: (s.get("x", 0), s.get("y", 0), s.get("width", 0), s.get("height", 0)))
        if len(s1) != len(s2):
            return False
        for i in range(len(s1)):
            item1 = s1[i]
            item2 = s2[i]
            if item1.get("x") != item2.get("x") or item1.get("y") != item2.get("y"):
                return False
            if item1.get("width") != item2.get("width") or item1.get("height") != item2.get("height"):
                return False
                
        c1 = sorted(l1.get("cuts", []), key=lambda c: (c.get("x1", 0), c.get("y1", 0), c.get("x2", 0), c.get("y2", 0)))
        c2 = sorted(l2.get("cuts", []), key=lambda c: (c.get("x1", 0), c.get("y1", 0), c.get("x2", 0), c.get("y2", 0)))
        if len(c1) != len(c2):
            return False
        for i in range(len(c1)):
            item1 = c1[i]
            item2 = c2[i]
            if item1.get("x1") != item2.get("x1") or item1.get("y1") != item2.get("y1"):
                return False
            if item1.get("x2") != item2.get("x2") or item1.get("y2") != item2.get("y2"):
                return False
        return True

    def _group_layouts(self, layout_list):
        grouped = []
        for lay in layout_list:
            found = False
            for gb in grouped:
                if self._are_layouts_identical(gb, lay):
                    gb["qty_multiplier"] = gb.get("qty_multiplier", 1) + 1
                    found = True
                    break
            if not found:
                lay_copy = copy.deepcopy(lay)
                lay_copy["qty_multiplier"] = 1
                grouped.append(lay_copy)
        return grouped

    def on_group_selected(self, event):
        display_name = self.cb_groups.get()
        self.selected_group_key = self.group_display_mapping.get(display_name, display_name)
        
        # Dividi le tavole in Barre, Pannelli e Residui
        if self.optimization_results and self.selected_group_key:
            g = self.optimization_results["gruppi"].get(self.selected_group_key, {"used_boards": []})
            boards = g["used_boards"]
            
            def board_type(board):
                st = board.get("stock_type")
                if st == "whole_board":
                    return "bar"
                elif st == "semilavorato_bar":
                    return "pan"
                elif st == "remnant":
                    return "res"
                    
                # Fallback se stock_type non è presente
                src = board.get("_source_type")
                if src:
                    if src in ["barra_real", "barra_virtual"]:
                        return "bar"
                    elif src in ["pannello_real", "pannello_virtual"]:
                        return "pan"
                    elif src in ["residuo_real"]:
                        return "res"
                
                b_id = str(board.get("id", "")).upper()
                if b_id.startswith("S_REC_"):
                    return "res"
                elif b_id.startswith("B") or "BARRA" in b_id:
                    return "bar"
                else:
                    return "pan"
                
            self.list_barre = self._group_layouts([b for b in boards if board_type(b["board"]) == "bar"])
            self.list_pannelli = self._group_layouts([b for b in boards if board_type(b["board"]) == "pan"])
            self.list_residui = self._group_layouts([b for b in boards if board_type(b["board"]) == "res"])
        else:
            self.list_barre = []
            self.list_pannelli = []
            self.list_residui = []
            
        self.selected_bar_idx = 0
        self.selected_panel_idx = 0
        self.selected_residuo_idx = 0
        
        self.redraw_barre()
        self.redraw_pannelli()
        self.redraw_residui()

    def prev_bar(self):
        if self.selected_bar_idx > 0:
            self.selected_bar_idx -= 1
            self.redraw_barre()
            
    def next_bar(self):
        if hasattr(self, 'list_barre') and self.selected_bar_idx < len(self.list_barre) - 1:
            self.selected_bar_idx += 1
            self.redraw_barre()
            
    def prev_pan(self):
        if self.selected_panel_idx > 0:
            self.selected_panel_idx -= 1
            self.redraw_pannelli()
            
    def next_pan(self):
        if hasattr(self, 'list_pannelli') and self.selected_panel_idx < len(self.list_pannelli) - 1:
            self.selected_panel_idx += 1
            self.redraw_pannelli()

    def prev_res(self):
        if self.selected_residuo_idx > 0:
            self.selected_residuo_idx -= 1
            self.redraw_residui()
            
    def next_res(self):
        if hasattr(self, 'list_residui') and self.selected_residuo_idx < len(self.list_residui) - 1:
            self.selected_residuo_idx += 1
            self.redraw_residui()

    def redraw_barre(self):
        if not self.optimization_results or not self.selected_group_key or not hasattr(self, 'list_barre') or not self.list_barre:
            self.renderer.draw_layout(self.canvas_barre, None)
            self.lbl_bar_counter.config(text="0 / 0")
            if self.optimization_results and self.selected_group_key:
                g = self.optimization_results["gruppi"].get(self.selected_group_key, {})
                if g.get("unplaced_pieces"):
                    self.lbl_bar_details.config(text="Nessun layout (Materiale non disponibile in magazzino)", foreground="#e84118")
                else:
                    self.lbl_bar_details.config(text="Nessun layout per questo gruppo", foreground=self.accent_light)
            else:
                self.lbl_bar_details.config(text="Nessun layout di pannello", foreground=self.accent_light)
            return
            
        if self.selected_bar_idx >= len(self.list_barre):
            self.selected_bar_idx = len(self.list_barre) - 1
            
        board_data = self.list_barre[self.selected_bar_idx]
        self.renderer.draw_layout(self.canvas_barre, board_data)
        self.lbl_bar_counter.config(text=f"{self.selected_bar_idx + 1} / {len(self.list_barre)}")
        
        b = board_data["board"]
        qty = board_data.get("qty_multiplier", 1)
        qty_str = f" [x{qty} IDENTICHE]" if qty > 1 else ""
        is_virtual = (b.get("_source_type") == "barra_virtual") or (b.get("id") == "BARRA_VIRTUALE_DUMMY") or ("virtual" in str(b.get("id")).lower())
        virtual_str = " [MANCANTE - DA ACQUISTARE]" if is_virtual else ""
        color_desc = b.get("color_desc") or b.get("color_code", "")
        color_str = f" | Colore: {color_desc}" if color_desc else ""
        details = f"{b['id']}{qty_str}{virtual_str}: {int(b['height'])}x{int(b['width'])}{color_str} | Efficienza: {board_data['efficiency']}%"
        self.lbl_bar_details.config(text=details)
        if is_virtual:
            self.lbl_bar_details.config(foreground="#e84118")
        else:
            self.lbl_bar_details.config(foreground=self.accent_light)
        
    def redraw_pannelli(self):
        if not self.optimization_results or not self.selected_group_key or not hasattr(self, 'list_pannelli') or not self.list_pannelli:
            self.renderer.draw_layout(self.canvas_pannelli, None)
            self.lbl_pan_counter.config(text="0 / 0")
            if self.optimization_results and self.selected_group_key:
                g = self.optimization_results["gruppi"].get(self.selected_group_key, {})
                if g.get("unplaced_pieces"):
                    self.lbl_pan_details.config(text="Nessun layout (Materiale non disponibile in magazzino)", foreground="#e84118")
                else:
                    self.lbl_pan_details.config(text="Nessun layout per questo gruppo", foreground=self.accent_light)
            else:
                self.lbl_pan_details.config(text="Nessun layout di barra", foreground=self.accent_light)
            return
            
        if self.selected_panel_idx >= len(self.list_pannelli):
            self.selected_panel_idx = len(self.list_pannelli) - 1
            
        board_data = self.list_pannelli[self.selected_panel_idx]
        self.renderer.draw_layout(self.canvas_pannelli, board_data)
        self.lbl_pan_counter.config(text=f"{self.selected_panel_idx + 1} / {len(self.list_pannelli)}")
        
        b = board_data["board"]
        qty = board_data.get("qty_multiplier", 1)
        qty_str = f" [x{qty} IDENTICHE]" if qty > 1 else ""
        is_virtual = (b.get("_source_type") == "pannello_virtual") or ("virtual" in str(b.get("id")).lower())
        virtual_str = " [VIRTUALE - DA PRODURRE]" if is_virtual else ""
        color_desc = b.get("color_desc") or b.get("color_code", "")
        color_str = f" | Colore: {color_desc}" if color_desc else ""
        details = f"{b['id']}{qty_str}{virtual_str}: {int(b['height'])}x{int(b['width'])}{color_str} | Efficienza: {board_data['efficiency']}%"
        self.lbl_pan_details.config(text=details)
        if is_virtual:
            self.lbl_pan_details.config(foreground="#487eb0")
        else:
            self.lbl_pan_details.config(foreground=self.accent_light)
 
    def redraw_residui(self):
        if not self.optimization_results or not self.selected_group_key or not hasattr(self, 'list_residui') or not self.list_residui:
            self.renderer.draw_layout(self.canvas_residui, None)
            self.lbl_res_counter.config(text="0 / 0")
            if self.optimization_results and self.selected_group_key:
                g = self.optimization_results["gruppi"].get(self.selected_group_key, {})
                if g.get("unplaced_pieces"):
                    self.lbl_res_details.config(text="Nessun layout (Materiale non disponibile in magazzino)", foreground="#e84118")
                else:
                    self.lbl_res_details.config(text="Nessun layout per questo gruppo", foreground=self.accent_light)
            else:
                self.lbl_res_details.config(text="Nessun layout di residuo", foreground=self.accent_light)
            return
            
        if self.selected_residuo_idx >= len(self.list_residui):
            self.selected_residuo_idx = len(self.list_residui) - 1
            
        board_data = self.list_residui[self.selected_residuo_idx]
        self.renderer.draw_layout(self.canvas_residui, board_data)
        self.lbl_res_counter.config(text=f"{self.selected_residuo_idx + 1} / {len(self.list_residui)}")
        
        b = board_data["board"]
        qty = board_data.get("qty_multiplier", 1)
        qty_str = f" [x{qty} IDENTICHE]" if qty > 1 else ""
        color_desc = b.get("color_desc") or b.get("color_code", "")
        color_str = f" | Colore: {color_desc}" if color_desc else ""
        details = f"{b['id']}{qty_str}: {int(b['height'])}x{int(b['width'])}{color_str} | Efficienza: {board_data['efficiency']}%"
        self.lbl_res_details.config(text=details)
        self.lbl_res_details.config(foreground=self.accent_light)

    def _create_tab_produzione_pannelli(self):
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="Produzione Barre (🪵->📁)")
        
        # Sdoppia in due aree: Tabella a sinistra, Controlli a destra
        paned = tk.PanedWindow(tab, orient=tk.HORIZONTAL, bg=self.bg_primary, bd=0, sashwidth=4)
        paned.pack(fill=tk.BOTH, expand=True)
        
        # LATO SINISTRO: Tabella dei pannelli da produrre
        frame_list = ttk.Frame(paned, padding=10)
        paned.add(frame_list, stretch="always")
        
        lbl_list_title = ttk.Label(frame_list, text="Lista Barre da Produrre", font=("Segoe UI", 11, "bold"), foreground=self.accent_color)
        lbl_list_title.pack(anchor=tk.W, pady=(0, 5))
        
        # Treeview
        cols = ("material", "width", "height", "stock", "prod_qty")
        self.tree_prod_pannelli = ttk.Treeview(frame_list, columns=cols, show="headings", height=15)
        self.tree_prod_pannelli.heading("material", text="Materiale")
        self.tree_prod_pannelli.heading("width", text="Altezza (mm)")
        self.tree_prod_pannelli.heading("height", text="Larghezza (mm)")
        self.tree_prod_pannelli.heading("stock", text="Stock Reale")
        self.tree_prod_pannelli.heading("prod_qty", text="Barre da Produrre")
        
        self.tree_prod_pannelli.column("material", width=320, anchor=tk.W)
        self.tree_prod_pannelli.column("width", width=120, anchor=tk.CENTER)
        self.tree_prod_pannelli.column("height", width=120, anchor=tk.CENTER)
        self.tree_prod_pannelli.column("stock", width=100, anchor=tk.CENTER)
        self.tree_prod_pannelli.column("prod_qty", width=150, anchor=tk.CENTER)
        
        self.tree_prod_pannelli.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(frame_list, orient=tk.VERTICAL, command=self.tree_prod_pannelli.yview)
        self.tree_prod_pannelli.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree_prod_pannelli.bind("<<TreeviewSelect>>", self.on_prod_panel_selected)
        
        # LATO DESTRO: Controlli di produzione
        frame_ctrl = ttk.Frame(paned, padding=10)
        paned.add(frame_ctrl, minsize=350)
        
        # Card Form per aggiungere/modificare
        card_form = ttk.LabelFrame(frame_ctrl, text=" Aggiungi / Modifica Barra ", padding=10)
        card_form.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(card_form, text="Materiale:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.cb_prod_materiale = ttk.Combobox(card_form, state="readonly", width=45)
        self.cb_prod_materiale.grid(row=0, column=1, columnspan=2, sticky=tk.EW, pady=5)
        
        ttk.Label(card_form, text="Larghezza (mm):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.ent_prod_w = ttk.Entry(card_form)
        self.ent_prod_w.grid(row=1, column=1, columnspan=2, sticky=tk.EW, pady=5)
        
        ttk.Label(card_form, text="Altezza (mm):").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.ent_prod_h = ttk.Entry(card_form)
        self.ent_prod_h.grid(row=2, column=1, columnspan=2, sticky=tk.EW, pady=5)
        
        ttk.Label(card_form, text="Qta da Produrre:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.ent_prod_qty = ttk.Entry(card_form)
        self.ent_prod_qty.grid(row=3, column=1, columnspan=2, sticky=tk.EW, pady=5)
        
        btn_form_frame = ttk.Frame(card_form)
        btn_form_frame.grid(row=4, column=0, columnspan=3, pady=(10, 5))
        
        ttk.Button(btn_form_frame, text="Aggiungi / Aggiorna", command=self.add_or_update_prod_panel).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_form_frame, text="Rimuovi", command=self.remove_prod_panel).pack(side=tk.LEFT, padx=5)
        
        # Card Azioni
        card_actions = ttk.LabelFrame(frame_ctrl, text=" Azioni di Produzione ", padding=15)
        card_actions.pack(fill=tk.X)
        
        self.btn_prod_calc = ttk.Button(card_actions, text="🪵 Calcola Fabbisogno Pannelli", command=self.calculate_prod_requirements, style="Accent.TButton")
        self.btn_prod_calc.pack(fill=tk.X, pady=5)
        
        self.btn_prod_consume = ttk.Button(card_actions, text="⚙️ Consuma Materiali (Scarico/Carico)", command=self.consume_prod_materials, state=tk.DISABLED)
        self.btn_prod_consume.pack(fill=tk.X, pady=5)
        
        # Variabili temporanee per memorizzare i risultati dell'ultimo calcolo di produzione pannelli
        self.last_prod_report = None
        
        # Popola combobox materiali
        self.populate_prod_materials()

    def populate_prod_materials(self):
        if not hasattr(self, 'cb_prod_materiale'):
            return
        raw_semis = self.data_manager.get_semilavorati()
        raw_barre = self.data_manager.get_barre()
        
        materials = set()
        for s in raw_semis:
            materials.add((s["thickness"], s["color_code"], s["color_desc"]))
        for b in raw_barre:
            materials.add((b["thickness"], b["color_code"], b["color_desc"]))
            
        display_values = []
        self.prod_materials_mapping = {}
        for thickness, code, desc in sorted(materials):
            display_name = f"{thickness}mm_{code} ({desc})"
            display_values.append(display_name)
            self.prod_materials_mapping[display_name] = (thickness, code, desc)
            
        self.cb_prod_materiale.config(values=display_values)
        if display_values:
            self.cb_prod_materiale.current(0)

    def on_prod_panel_selected(self, event):
        selected = self.tree_prod_pannelli.selection()
        if not selected:
            return
        item_values = self.tree_prod_pannelli.item(selected[0], "values")
        if not item_values:
            return
            
        material_str, height_str, width_str, stock_str, qty_str = item_values
        
        for val in self.cb_prod_materiale['values']:
            if val.startswith(material_str):
                self.cb_prod_materiale.set(val)
                break
                
        self.ent_prod_w.delete(0, tk.END)
        self.ent_prod_w.insert(0, width_str)
        self.ent_prod_h.delete(0, tk.END)
        self.ent_prod_h.insert(0, height_str)
        self.ent_prod_qty.delete(0, tk.END)
        self.ent_prod_qty.insert(0, qty_str)

    def add_or_update_prod_panel(self):
        material_display = self.cb_prod_materiale.get()
        if not material_display:
            messagebox.showerror("Errore", "Selezionare un materiale.")
            return
            
        thickness, color_code, color_desc = self.prod_materials_mapping[material_display]
        
        try:
            w = float(self.ent_prod_w.get().replace(",", "."))
            h = float(self.ent_prod_h.get().replace(",", "."))
            qty = int(self.ent_prod_qty.get())
            if w <= 0 or h <= 0 or qty <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Errore", "Dimensioni e quantità devono essere numeri positivi.")
            return
            
        found = False
        for p in self.panel_production_list:
            if str(p["thickness"]) == str(thickness) and p["color_code"] == color_code and p["width"] == w and p["height"] == h:
                p["quantity_to_produce"] = qty
                found = True
                break
                
        if not found:
            self.panel_production_list.append({
                "thickness": thickness,
                "color_code": color_code,
                "color_desc": color_desc,
                "width": w,
                "height": h,
                "quantity_to_produce": qty
            })
            
        self.reload_prod_panels_table()
        self.ent_prod_w.delete(0, tk.END)
        self.ent_prod_h.delete(0, tk.END)
        self.ent_prod_qty.delete(0, tk.END)

    def remove_prod_panel(self):
        selected = self.tree_prod_pannelli.selection()
        if not selected:
            messagebox.showwarning("Attenzione", "Selezionare un elemento dalla lista per rimuoverlo.")
            return
            
        item_values = self.tree_prod_pannelli.item(selected[0], "values")
        material_str, height_str, width_str, _, _ = item_values
        
        w = float(width_str)
        h = float(height_str)
        
        new_list = []
        for p in self.panel_production_list:
            material_key = f"{p['thickness']}mm_{p['color_code']} ({p['color_desc']})"
            if material_key == material_str and p["width"] == w and p["height"] == h:
                continue
            new_list.append(p)
            
        self.panel_production_list = new_list
        self.reload_prod_panels_table()

    def reload_prod_panels_table(self):
        if not hasattr(self, 'tree_prod_pannelli'):
            return
            
        # 1. Carica tutti i semilavorati correnti dal database che sono PANNELLI (no S_REC_)
        raw_semis = self.data_manager.get_semilavorati()
        db_panels = [s for s in raw_semis if not s["id"].startswith("S_REC_")]
        
        # Mappa i pannelli attuali in produzione per spessore, colore e dimensioni
        # per preservare le quantità da produrre impostate dall'utente
        existing_map = {}
        for p in self.panel_production_list:
            key = (str(p["thickness"]), p["color_code"], float(p["width"]), float(p["height"]))
            existing_map[key] = p["quantity_to_produce"]
            
        # Costruisce la nuova lista di produzione
        new_prod_list = []
        
        # Aggiunge tutti i pannelli del database
        db_panel_keys = set()
        for s in db_panels:
            key = (str(s["thickness"]), s["color_code"], float(s["width"]), float(s["height"]))
            db_panel_keys.add(key)
            
            qty_to_prod = existing_map.get(key, 0)
            new_prod_list.append({
                "thickness": s["thickness"],
                "color_code": s["color_code"],
                "color_desc": s["color_desc"],
                "width": s["width"],
                "height": s["height"],
                "quantity_to_produce": qty_to_prod
            })
            
        # Aggiunge eventuali pannelli custom (non presenti nel DB) ma con quantità da produrre > 0
        for p in self.panel_production_list:
            key = (str(p["thickness"]), p["color_code"], float(p["width"]), float(p["height"]))
            if key not in db_panel_keys and p["quantity_to_produce"] > 0:
                new_prod_list.append(p)
                
        self.panel_production_list = new_prod_list
        
        # 2. Pulisce la tabella ed inserisce i dati
        for item in self.tree_prod_pannelli.get_children():
            self.tree_prod_pannelli.delete(item)
            
        for p in self.panel_production_list:
            stock_qty = 0
            for s in db_panels:
                if (str(s["thickness"]) == str(p["thickness"]) and 
                    s["color_code"] == p["color_code"] and 
                    float(s["width"]) == float(p["width"]) and 
                    float(s["height"]) == float(p["height"])):
                    stock_qty += int(s.get("quantity", 0))
                    
            material_key = f"{p['thickness']}mm_{p['color_code']} ({p['color_desc']})"
            self.tree_prod_pannelli.insert("", tk.END, values=(
                material_key,
                int(p["height"]),
                int(p["width"]),
                stock_qty,
                p["quantity_to_produce"]
            ))

    def calculate_prod_requirements(self):
        # Filtra solo i pannelli con quantità da produrre > 0
        panels_to_produce = [p for p in self.panel_production_list if p["quantity_to_produce"] > 0]
        if not panels_to_produce:
            messagebox.showwarning("Attenzione", "La lista dei pannelli con quantità da produrre > 0 è vuota. Specifica la quantità da produrre per almeno un pannello.")
            return
            
        panel_grain_direction = "verticale"
        raw_barre = self.data_manager.get_barre()
        order_keys = {(p["thickness"], p["color_code"]) for p in panels_to_produce}
        has_grain_panels = any(
            b.get("has_grain", False) for b in raw_barre
            if (b["thickness"], b["color_code"]) in order_keys
        )
        if has_grain_panels:
            panel_grain_direction = self.ask_panel_grain_direction()
            
        try:
            kerf = float(self.ent_kerf.get().replace(",", "."))
            rifilo_h = float(self.ent_rifilo_h.get().replace(",", "."))
            rifilo_v = float(self.ent_rifilo_v.get().replace(",", "."))
            sfrido = float(self.ent_sfrido.get().replace(",", "."))
            min_w = float(self.ent_min_w.get().replace(",", "."))
            min_h = float(self.ent_min_h.get().replace(",", "."))
            respect_grain = self.var_grain.get()
        except ValueError:
            messagebox.showerror("Errore", "I valori dei parametri devono essere numerici.")
            return
            
        macchina = self.cmb_macchina.get().lower()
            
        color_grain_map = self.get_color_grain_map()
        
        # Mostra dialog di caricamento e imposta cursore watch
        loading = LoadingDialog(self.root, "Calcolo fabbisogno pannelli in corso...")
        self.root.config(cursor="watch")
        self.root.update()
        
        try:
            # Carica stock standard
            self.data_manager.db = self.data_manager.load_db()
            raw_barre = self.data_manager.get_barre()
            
            prod_by_material = {}
            for p in panels_to_produce:
                key = (p["thickness"], p["color_code"], p["color_desc"])
                if key not in prod_by_material:
                    prod_by_material[key] = []
                prod_by_material[key].append(p)
                
            final_gruppi = {}
            prod_report = []
            
            sim_optimizer = CuttingOptimizer(kerf=kerf)
            
            for (thickness, color_code, color_desc), p_list in prod_by_material.items():
                key = f"{thickness}mm_{color_code}"
                group_respect_grain = color_grain_map.get(color_code, False)
                
                demands = []
                for p in p_list:
                    for q_idx in range(p["quantity_to_produce"]):
                        demands.append({
                            "descrizione": f"Pannello {int(p['width'])}x{int(p['height'])}",
                            "width": p["width"],
                            "height": p["height"],
                            "thickness": p["thickness"],
                            "color_code": p["color_code"],
                            "color_desc": p["color_desc"]
                        })
                        
                group_barre_reali = [b for b in raw_barre if str(b["thickness"]) == str(thickness) and b["color_code"] == color_code]
                
                if group_barre_reali:
                    ref_bar_template = group_barre_reali[0]
                else:
                    default_w = 2800.0
                    default_h = 2070.0
                    if raw_barre:
                        default_w = raw_barre[0]["width"]
                        default_h = raw_barre[0]["height"]
                    ref_bar_template = {
                        "id": "Barra Standard",
                        "width": default_w,
                        "height": default_h,
                        "thickness": thickness,
                        "color_code": color_code,
                        "color_desc": color_desc,
                        "has_grain": group_respect_grain
                    }
                    
                # Costruisce lo stock (reale + virtuale) per la produzione di questo spessore/colore
                simulated_stock = []
                for idx, b in enumerate(group_barre_reali):
                    qty = int(b.get("quantity", 0))
                    for q_idx in range(qty):
                        item = copy.deepcopy(b)
                        item["_source_type"] = "barra_real"
                        item["_unique_index"] = f"barra_real_{b['id']}_{idx}_{q_idx}"
                        item["stock_type"] = "whole_board"
                        item["has_grain"] = b.get("has_grain", False)
                        simulated_stock.append(item)
                        
                # 100 virtuali come deficit
                bars_for_virtual = group_barre_reali if group_barre_reali else [ref_bar_template]
                for idx, b in enumerate(bars_for_virtual):
                    for q_idx in range(100):
                        item = copy.deepcopy(b)
                        item["_source_type"] = "barra_virtual"
                        item["_unique_index"] = f"barra_virtual_prod_{b['id']}_{idx}_{q_idx}"
                        item["stock_type"] = "whole_board"
                        item["has_grain"] = b.get("has_grain", False)
                        if not str(item["id"]).endswith("[Virtuale]"):
                            item["id"] = f"{item['id']} [Virtuale]"
                        simulated_stock.append(item)
                        
                respect_grain_dict = {key: group_respect_grain}
                # Ottimizza
                results = sim_optimizer.optimize(
                    stocks=simulated_stock,
                    demands=demands,
                    respect_grain=respect_grain_dict,
                    min_semilavorato_width=min_w,
                    min_semilavorato_height=min_h,
                    rifilo_verticale=rifilo_v,
                    rifilo_orizzontale=rifilo_h,
                    sfrido=sfrido,
                    machine_type=macchina,
                    panel_grain_direction=panel_grain_direction
                )
                
                used_boards = []
                unplaced = []
                if key in results["gruppi"]:
                    used_boards = results["gruppi"][key]["used_boards"]
                    unplaced = results["gruppi"][key]["unplaced_pieces"]
                    
                # Conta reali e virtuali usati
                barre_real_used = 0
                barre_virtual_used = 0
                barre_virtual_counts = {}
                
                for ub in used_boards:
                    board = ub["board"]
                    src_type = board.get("_source_type")
                    if src_type == "barra_real":
                        barre_real_used += 1
                    elif src_type == "barra_virtual":
                        barre_virtual_used += 1
                        w = int(board.get("width", 0))
                        h = int(board.get("height", 0))
                        b_id = board.get("id", "Barra")
                        display_name = f"Barra Standard ({w}x{h})" if ("dummy" in b_id.lower() or "virtual" in b_id.lower() or "barra standard" in b_id.lower()) else f"{b_id.split(' [Virtuale]')[0]} ({w}x{h})"
                        barre_virtual_counts[display_name] = barre_virtual_counts.get(display_name, 0) + 1
                        
                final_gruppi[key] = {
                    "used_boards": used_boards,
                    "unplaced_pieces": unplaced,
                    "summary": {
                        "total_boards_used": len(used_boards),
                        "efficiency": results["gruppi"][key]["summary"]["efficiency"] if used_boards else 0.0,
                        "used_area": results["gruppi"][key]["summary"]["used_area"] if used_boards else 0.0,
                        "waste_area": results["gruppi"][key]["summary"]["waste_area"] if used_boards else 0.0,
                        "total_board_area": results["gruppi"][key]["summary"]["total_board_area"] if used_boards else 0.0
                    }
                }
                
                prod_report.append({
                    "thickness": thickness,
                    "color_code": color_code,
                    "color_desc": color_desc,
                    "barre_real_used": barre_real_used,
                    "barre_virtual_used": barre_virtual_used,
                    "barre_virtual_counts": barre_virtual_counts,
                    "used_boards": used_boards,
                    "unplaced_count": len(unplaced)
                })
                
            # Calcola totali generali per summary_generale
            totale_area_lastre = sum(g["summary"]["total_board_area"] for g in final_gruppi.values())
            totale_area_pezzi = sum(g["summary"]["used_area"] for g in final_gruppi.values())
            totale_area_scarto = totale_area_lastre - totale_area_pezzi
            efficienza_generale = (totale_area_pezzi / totale_area_lastre * 100) if totale_area_lastre > 0 else 0.0
            
            self.optimization_results = {
                "gruppi": final_gruppi,
                "summary_generale": {
                    "totale_area_lastre": round(totale_area_lastre, 2),
                    "totale_area_pezzi": round(totale_area_pezzi, 2),
                    "totale_area_scarto": round(totale_area_scarto, 2),
                    "efficienza_media": round(efficienza_generale, 2)
                }
            }
            
            # Forza la visualizzazione dei tab di visualizzazione ad avere solo Barre
            self.var_stock_barra.set(True)
            self.var_stock_pannello.set(False)
            self.var_stock_residuo.set(False)
            self.update_vis_tabs_visibility()
            
            # Popola combobox gruppi
            self.populate_groups_combobox()
            
            summary_lines = []
            summary_lines.append("=== RIEPILOGO PRODUZIONE BARRE ===")
            tot_real_used = 0
            tot_virt_needed = 0
            for item in prod_report:
                summary_lines.append(f"\nMateriale: {item['thickness']}mm {item['color_desc']} ({item['color_code']})")
                summary_lines.append(f"  - Pannelli in stock utilizzati: {item['barre_real_used']}")
                summary_lines.append(f"  - Pannelli mancanti (da acquistare): {item['barre_virtual_used']}")
                for name, qty in item['barre_virtual_counts'].items():
                    summary_lines.append(f"    * {qty}x {name}")
                tot_real_used += item['barre_real_used']
                tot_virt_needed += item['barre_virtual_used']
                
            summary_lines.append("\n====================================")
            summary_lines.append(f"Totale Pannelli Stock Utilizzati: {tot_real_used}")
            summary_lines.append(f"Totale Pannelli Mancanti: {tot_virt_needed}")
            
            self.last_prod_report = prod_report
            self.btn_prod_consume.config(state=tk.NORMAL)
            
            for idx in range(self.notebook.index("end")):
                if self.notebook.tab(idx, "text") == "Visualizzatore Layout":
                    self.notebook.select(idx)
                    break
        finally:
            loading.destroy()
            self.root.config(cursor="")
            
        messagebox.showinfo("Fabbisogno Produzione Calcolato", "\n".join(summary_lines))

    def consume_prod_materials(self):
        if not hasattr(self, 'last_prod_report') or not self.last_prod_report:
            return
            
        confirm = messagebox.askyesno(
            "Conferma Consumo Produzione",
            "Questa operazione aggiornerà il database del magazzino:\n"
            "• Decrementerà/eliminerà i pannelli standard grezzi utilizzati.\n"
            "• Incrementerà/aggiungerà le barre semilavorate prodotte.\n\n"
            "Vuoi procedere?"
        )
        if not confirm:
            return
            
        self.data_manager.db = self.data_manager.load_db()
        barre = self.data_manager.get_barre()
        semilavorati = self.data_manager.get_semilavorati()
        
        used_bar_ids = []
        for item in self.last_prod_report:
            for ub in item["used_boards"]:
                board = ub["board"]
                if board.get("_source_type") == "barra_real":
                    clean_id = board["id"].split(" [PER PANNELLI]")[0]
                    used_bar_ids.append(clean_id)
                    
        from collections import Counter
        used_counts = Counter(used_bar_ids)
        
        nuove_barre = []
        for b in barre:
            b_id = b.get("id")
            if b_id in used_counts:
                curr_qty = int(b.get("quantity", 0))
                new_qty = curr_qty - used_counts[b_id]
                if new_qty > 0:
                    b["quantity"] = new_qty
                    nuove_barre.append(b)
            else:
                nuove_barre.append(b)
                
        self.data_manager.set_barre(nuove_barre)
        
        import time
        for idx, p in enumerate(self.panel_production_list):
            if p["quantity_to_produce"] <= 0:
                continue
            found = False
            for s in semilavorati:
                if (not s["id"].startswith("S_REC_") and 
                    str(s["thickness"]) == str(p["thickness"]) and 
                    s["color_code"] == p["color_code"] and 
                    float(s["width"]) == float(p["width"]) and 
                    float(s["height"]) == float(p["height"])):
                    s["quantity"] = int(s.get("quantity", 0)) + p["quantity_to_produce"]
                    found = True
                    break
                    
            if not found:
                new_id = f"S_PANEL_{int(time.time())}_{idx}"
                semilavorati.append({
                    "id": new_id,
                    "width": p["width"],
                    "height": p["height"],
                    "thickness": p["thickness"],
                    "color_code": p["color_code"],
                    "color_desc": p["color_desc"],
                    "has_grain": True,
                    "quantity": p["quantity_to_produce"]
                })
                
        self.data_manager.set_semilavorati(semilavorati)
        self.data_manager.save_db()
        
        # Resetta le quantità da produrre a 0 per preservare la lista di pannelli
        for p in self.panel_production_list:
            p["quantity_to_produce"] = 0
            
        self.last_prod_report = None
        self.reload_prod_panels_table()
        self.btn_prod_consume.config(state=tk.DISABLED)
        
        self.reload_magazzino_tables()
        
        for tab_idx in range(self.notebook.index("end")):
            if self.notebook.tab(tab_idx, "text") == "Magazzino (Stock)":
                self.notebook.select(tab_idx)
                break
                
        messagebox.showinfo("Produzione Completata", "Materiali consumati con successo! Il magazzino è stato aggiornato.")

    def consume_materials(self):
        if not self.optimization_results:
            return
            
        confirm = messagebox.askyesno(
            "Conferma Consumo",
            "Questa operazione aggiornerà il database, eliminando le barre e i semilavorati consumati nel calcolo ed inserendo i nuovi semilavorati generati dal recupero.\n\nProcedere?"
        )
        if not confirm:
            return
            
        # Raccoglie tutte le used_boards di tutti i gruppi
        tutte_used = []
        for g in self.optimization_results["gruppi"].values():
            tutte_used.extend(g["used_boards"])
            
        # Aggiorna DB
        self.data_manager.consume_materials(tutte_used)
        
        # Chiude automaticamente la commessa se associata
        if self.current_commessa_id is not None:
            self.data_manager.close_commessa(self.current_commessa_id)
            self.current_commessa_status = "Chiusa"
            self.reload_commesse_table()
            self.on_commessa_status_change()
            
        # Disabilita bottone per evitare doppio click
        self.btn_consume.config(state=tk.DISABLED)
        
        # Ricarica tabelle inventario
        self.reload_magazzino_tables()
        
        messagebox.showinfo("Sincronizzazione Magazzino", "Il magazzino è stato aggiornato correttamente nel database JSON locale e la commessa associata è stata chiusa.")

    def export_report(self):
        if not self.optimization_results:
            return
            
        initial_dir = r"C:\CutMob\Report\HTML"
        try:
            os.makedirs(initial_dir, exist_ok=True)
        except Exception:
            pass
            
        filepath = filedialog.asksaveasfilename(
            defaultextension=".html",
            filetypes=[("File HTML", "*.html"), ("Tutti i file", "*.*")],
            title="Salva Report di Ottimizzazione",
            initialdir=initial_dir
        )
        if not filepath:
            return
            
        success = self.data_manager.export_html_report(self.optimization_results, filepath)
        if success:
            self.last_html_export_path = filepath
            self.btn_open_html_dir.config(state=tk.NORMAL)
            messagebox.showinfo("Report Esportato", f"Il report HTML con schemi vettoriali SVG è stato salvato in:\n{filepath}")
        else:
            messagebox.showerror("Errore", "Impossibile salvare il report in questo percorso.")
            
    def export_pdf_report(self):
        if not self.optimization_results:
            return
            
        import time
        # Crea cartella se non esiste
        folder = r"C:\CutMob\Report\PDF"
        try:
            os.makedirs(folder, exist_ok=True)
        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile creare la cartella {folder}:\n{e}")
            return
            
        timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"Report_CutMob_{timestamp}.pdf"
        filepath = os.path.join(folder, filename)
        
        # Cursore di caricamento
        self.root.config(cursor="watch")
        self.root.update()
        
        try:
            success = self.data_manager.export_pdf_report(self.optimization_results, filepath)
            if success:
                self.last_pdf_export_path = filepath
                self.btn_open_pdf_dir.config(state=tk.NORMAL)
                messagebox.showinfo("Report PDF Esportato", f"Il report PDF è stato salvato con successo in:\n{filepath}")
            else:
                messagebox.showerror("Errore PDF", "Errore nella generazione del report PDF con Chrome Headless.")
        finally:
            self.root.config(cursor="")

    def open_html_dir(self):
        if self.last_html_export_path:
            folder = os.path.dirname(os.path.abspath(self.last_html_export_path))
            if os.path.exists(folder):
                os.startfile(folder)

    def open_pdf_dir(self):
        if self.last_pdf_export_path:
            folder = os.path.dirname(os.path.abspath(self.last_pdf_export_path))
            if os.path.exists(folder):
                os.startfile(folder)
            
    # ==================== AZIONI DI INPUT GESTIONE DATI ====================
    
    def import_stock_csv(self, stock_type):
        dialog_kwargs = {
            "filetypes": [("File CSV", "*.csv"), ("Tutti i file", "*.*")],
            "title": f"Importa file CSV per {'Barre' if stock_type == 'barre' else 'Semilavorati'}"
        }
        if stock_type == "barre":
            dialog_kwargs["initialdir"] = r"C:\Report\Pannelli"
        elif stock_type == "semilavorati":
            dialog_kwargs["initialdir"] = r"C:\Report\Barre"
            
        filepath = filedialog.askopenfilename(**dialog_kwargs)
        if not filepath:
            return
            
        # Chiedi la quantità da assegnare a tutti gli elementi importati
        qty = simpledialog.askinteger("Quantità Comune", "Inserisci la quantità da assegnare a tutti gli elementi importati dal CSV:", minvalue=1)
        if qty is None:
            return
            
        if not messagebox.askyesno("Prima Conferma", f"Sei sicuro di voler assegnare la quantità {qty} a TUTTI gli elementi importati dal CSV?"):
            return
        if not messagebox.askyesno("Seconda Conferma (ATTENZIONE)", f"Confermi di voler sovrascrivere tutte le quantità presenti nel CSV con il valore {qty}?"):
            return
            
        try:
            if stock_type == "barre":
                nuove_barre = self.data_manager.import_barre_csv(filepath)
                barre = self.data_manager.get_barre()
                
                # Applica la quantità comune inserita
                for nb in nuove_barre:
                    nb["quantity"] = qty
                
                # Identificatore di unicità per saltare record già presenti nel database
                # Usiamo float() per larghezza, altezza e spessore per renderli confrontabili correttamente
                chiavi_esistenti = {
                    (b["id"], float(b["width"]), float(b["height"]), float(b["thickness"]))
                    for b in barre
                }
                
                barre_da_aggiungere = []
                barre_gia_presenti_count = 0
                for nb in nuove_barre:
                    nb_key = (nb["id"], float(nb["width"]), float(nb["height"]), float(nb["thickness"]))
                    if nb_key not in chiavi_esistenti:
                        barre_da_aggiungere.append(nb)
                        # Aggiungiamo al set per evitare duplicati all'interno dello stesso CSV
                        chiavi_esistenti.add(nb_key)
                    else:
                        barre_gia_presenti_count += 1
                
                if barre_da_aggiungere:
                    self.data_manager.set_barre(barre + barre_da_aggiungere)
                
                msg = f"Importate con successo {len(barre_da_aggiungere)} nuove barre dal file CSV."
                if barre_gia_presenti_count > 0:
                    msg += f"\n({barre_gia_presenti_count} barre duplicate/già presenti sono state saltate)."
                messagebox.showinfo("CSV Importato", msg)
            else:
                nuovi_semis = self.data_manager.import_semilavorati_csv(filepath)
                if not nuovi_semis:
                    messagebox.showinfo("CSV Importato", "Il file CSV non contiene semilavorati validi.")
                    return
                
                # Applica la quantità comune inserita
                for ns in nuovi_semis:
                    ns["quantity"] = qty
                
                # Chiedi all'utente se desidera aggiungere o sostituire
                scelta = messagebox.askyesnocancel(
                    "Importazione Semilavorati",
                    "Vuoi aggiungere i semilavorati importati a quelli già presenti in magazzino?\n\n"
                    "• Clicca 'Sì' per AGGIUNGERE (e unire le quantità dei pezzi identici)\n"
                    "• Clicca 'No' per SOSTITUIRE completamente il magazzino semilavorati corrente\n"
                    "• Clicca 'Annulla' per annullare l'importazione"
                )
                
                if scelta is None:
                    return
                
                if scelta:
                    # Aggiunge / Unisce
                    semis = self.data_manager.get_semilavorati()
                    semis_dict = {s["id"]: s for s in semis}
                    for ns in nuovi_semis:
                        if ns["id"] in semis_dict:
                            # Somma la quantità se l'elemento esiste già
                            semis_dict[ns["id"]]["quantity"] = semis_dict[ns["id"]].get("quantity", 0) + ns.get("quantity", 0)
                        else:
                            semis_dict[ns["id"]] = ns
                    self.data_manager.set_semilavorati(list(semis_dict.values()))
                    messagebox.showinfo("CSV Importato", f"Importati e uniti con successo {len(nuovi_semis)} semilavorati.")
                else:
                    # Sostituisce
                    self.data_manager.set_semilavorati(nuovi_semis)
                    messagebox.showinfo("CSV Importato", f"Sostituiti con successo i semilavorati correnti con {len(nuovi_semis)} elementi importati.")
                
            self.reload_magazzino_tables()
        except Exception as e:
            messagebox.showerror("Errore CSV", f"Impossibile importare il file CSV:\n{e}")

    def reload_commesse_table(self):
        # Pulisce la tabella delle commesse
        for item in self.tree_commesse.get_children():
            self.tree_commesse.delete(item)
            
        commesse = self.data_manager.get_commesse()
        for c in commesse:
            match = True
            for col_name, filter_val in self.filters_commesse.items():
                val_to_check = ""
                if col_name == "id":
                    val_to_check = str(c["id"])
                elif col_name == "nome":
                    val_to_check = str(c["nome"])
                elif col_name == "stato":
                    val_to_check = str(c.get("stato", "Aperta"))
                
                if filter_val not in val_to_check.lower():
                    match = False
                    break
            if not match:
                continue
            self.tree_commesse.insert("", tk.END, values=(
                c["id"],
                c["nome"],
                c.get("stato", "Aperta")
            ))

    def on_commessa_select(self, event=None):
        selected = self.tree_commesse.selection()
        if not selected:
            return
            
        vals = self.tree_commesse.item(selected[0], "values")
        if not vals:
            return
        commessa_id = int(vals[0])
        
        # Cerca la commessa nel database
        commesse = self.data_manager.get_commesse()
        commessa = next((c for c in commesse if c["id"] == commessa_id), None)
        if not commessa:
            return
            
        self.current_commessa_id = commessa["id"]
        self.current_commessa_name = commessa["nome"]
        self.current_commessa_status = commessa.get("stato", "Aperta")
        self.current_order = copy.deepcopy(commessa["pezzi"])
        
        self.reload_order_table()
        self.on_commessa_status_change()

    def on_commessa_status_change(self):
        status = getattr(self, "current_commessa_status", "Aperta")
        state = tk.DISABLED if status == "Chiusa" else tk.NORMAL
        
        import_enabled = self.data_manager.config.get("import_enabled", True)
        if not import_enabled:
            self.btn_import_csv.config(state=tk.DISABLED)
        else:
            self.btn_import_csv.config(state=state)
            
        self.btn_add_piece.config(state=state)
        self.btn_edit_piece.config(state=state)
        self.btn_remove_piece.config(state=state)
        self.btn_clear_order.config(state=state)
        self.btn_select_all.config(state=state)
        self.btn_deselect_all.config(state=state)
        self.btn_calc_req.config(state=state)
        
        if self.current_commessa_id is not None:
            text = f"Commessa: ID {self.current_commessa_id} - {self.current_commessa_name} ({self.current_commessa_status})"
        else:
            text = "Nuova Commessa (Non Salvata)"
        self.lbl_commessa_info.config(text=text)

    def new_commessa_action(self):
        # Deseleziona la commessa corrente nel treeview
        self.tree_commesse.selection_set("")
        
        self.current_commessa_id = None
        self.current_commessa_name = ""
        self.current_commessa_status = "Aperta"
        self.current_order = []
        
        self.reload_order_table()
        self.on_commessa_status_change()

    def save_commessa_action(self):
        if getattr(self, "current_commessa_status", "Aperta") == "Chiusa":
            messagebox.showerror("Errore", "Questa commessa è CHIUSA e non può essere salvata o modificata.")
            return
            
        if self.current_commessa_id is None:
            # Chiede il nome all'operatore
            nome = simpledialog.askstring("Nuova Commessa", "Inserisci il nome della commessa:", parent=self.root)
            if not nome:
                return
            self.current_commessa_name = nome.strip()
            
        # Salva la commessa
        try:
            commessa = self.data_manager.save_commessa(
                self.current_commessa_id,
                self.current_commessa_name,
                self.current_order,
                self.current_commessa_status
            )
            self.current_commessa_id = commessa["id"]
            self.current_commessa_name = commessa["nome"]
            self.current_commessa_status = commessa["stato"]
            
            messagebox.showinfo("Salvataggio", f"Commessa '{self.current_commessa_name}' salvata con successo con ID {self.current_commessa_id}.")
            self.reload_commesse_table()
            self.on_commessa_status_change()
            
            # Seleziona la commessa appena salvata nel Treeview senza far scattare un caricamento duplicato
            for item in self.tree_commesse.get_children():
                vals = self.tree_commesse.item(item, "values")
                if vals and int(vals[0]) == self.current_commessa_id:
                    self.tree_commesse.selection_set(item)
                    break
        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile salvare la commessa: {e}")

    def delete_commessa_action(self):
        selected = self.tree_commesse.selection()
        if not selected:
            messagebox.showwarning("Attenzione", "Seleziona una commessa dall'elenco a sinistra per eliminarla.")
            return
            
        vals = self.tree_commesse.item(selected[0], "values")
        if not vals:
            return
        commessa_id = int(vals[0])
        
        # Cerca il nome
        commesse = self.data_manager.get_commesse()
        commessa = next((c for c in commesse if c["id"] == commessa_id), None)
        nome_commessa = commessa["nome"] if commessa else f"ID {commessa_id}"
        
        confirm = messagebox.askyesno(
            "Conferma Eliminazione",
            f"Sei sicuro di voler eliminare definitivamente la commessa '{nome_commessa}'?"
        )
        if not confirm:
            return
            
        try:
            self.data_manager.delete_commessa(commessa_id)
            if self.current_commessa_id == commessa_id:
                self.new_commessa_action()
            self.reload_commesse_table()
            messagebox.showinfo("Eliminata", "Commessa eliminata correttamente dal database.")
        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile eliminare la commessa: {e}")

    def close_commessa_action(self):
        selected = self.tree_commesse.selection()
        # Se non è selezionato nulla, proviamo a chiudere quella correntemente attiva se salvata
        if not selected:
            if self.current_commessa_id is not None:
                commessa_id = self.current_commessa_id
                nome_commessa = self.current_commessa_name
            else:
                messagebox.showwarning("Attenzione", "Seleziona una commessa salvata dall'elenco a sinistra o salva quella corrente prima di poterla chiudere.")
                return
        else:
            vals = self.tree_commesse.item(selected[0], "values")
            if not vals:
                return
            commessa_id = int(vals[0])
            commesse = self.data_manager.get_commesse()
            commessa = next((c for c in commesse if c["id"] == commessa_id), None)
            nome_commessa = commessa["nome"] if commessa else f"ID {commessa_id}"
            
        confirm = messagebox.askyesno(
            "Conferma Chiusura",
            f"Sei sicuro di voler chiudere e marcare come prodotta la commessa '{nome_commessa}'?\n"
            "Una volta chiusa, non sarà più modificabile né soggetta a calcolo."
        )
        if not confirm:
            return
            
        try:
            self.data_manager.close_commessa(commessa_id)
            if self.current_commessa_id == commessa_id:
                self.current_commessa_status = "Chiusa"
                self.on_commessa_status_change()
            self.reload_commesse_table()
            messagebox.showinfo("Chiusa", f"Commessa '{nome_commessa}' chiusa con successo.")
        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile chiudere la commessa: {e}")

    def import_csv_dialog(self):
        if getattr(self, "current_commessa_status", "Aperta") == "Chiusa":
            messagebox.showerror("Errore", "La commessa corrente è CHIUSA e non può essere modificata.")
            return
        filepath = filedialog.askopenfilename(
            filetypes=[("File CSV", "*.csv"), ("Tutti i file", "*.*")],
            title="Importa file CSV ordini",
            initialdir=r"C:\Report\Elem_Cutmob"
        )
        if not filepath:
            return
            
        try:
            pezzi = self.data_manager.import_csv(filepath)
            self.current_order.extend(pezzi)
            self.reload_order_table()
            messagebox.showinfo("CSV Importato", f"Importati con successo {len(pezzi)} pezzi dal file CSV.")
        except Exception as e:
            messagebox.showerror("Errore CSV", f"Impossibile importare il file CSV:\n{e}")

    def clear_order_list(self):
        if getattr(self, "current_commessa_status", "Aperta") == "Chiusa":
            messagebox.showerror("Errore", "La commessa corrente è CHIUSA e non può essere modificata.")
            return
        if not self.current_order:
            return
        if messagebox.askyesno("Conferma", "Vuoi svuotare interamente l'elenco dei pezzi ordinati?"):
            self.current_order = []
            self.reload_order_table()

    def remove_piece_from_order(self):
        if getattr(self, "current_commessa_status", "Aperta") == "Chiusa":
            messagebox.showerror("Errore", "La commessa corrente è CHIUSA e non può essere modificata.")
            return
        selected = self.tree_pieces.selection()
        if not selected:
            messagebox.showwarning("Seleziona pezzo", "Seleziona un pezzo dalla lista per rimuoverlo.")
            return
            
        # Visto che supportiamo selezione multipla
        indices_to_remove = []
        for item in selected:
            vals = self.tree_pieces.item(item, "values")
            # Valore 0 contiene idx (1-based), quindi convertiamo in 0-based index
            indices_to_remove.append(int(vals[0]) - 1)
            
        # Rimuove partendo dall'indice più alto per evitare sfasamento degli indici
        indices_to_remove.sort(reverse=True)
        for idx in indices_to_remove:
            self.current_order.pop(idx)
            
        self.reload_order_table()

    def remove_stock_item(self, stock_type):
        tree = self.tree_barre if stock_type == "barre" else self.tree_semi
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Seleziona elemento", "Seleziona un elemento della tabella per rimuoverlo.")
            return
            
        confirm = messagebox.askyesno("Conferma rimozione", "Sei sicuro di voler eliminare gli elementi selezionati dal magazzino?")
        if not confirm:
            return
            
        # ID da rimuovere
        ids_to_remove = {tree.item(item, "values")[0] for item in selected}
        
        # Carica stock, filtra e salva
        if stock_type == "barre":
            stocks = self.data_manager.get_barre()
            nuovi_stocks = [item for item in stocks if item["id"] not in ids_to_remove]
            self.data_manager.set_barre(nuovi_stocks)
        else:
            stocks = self.data_manager.get_semilavorati()
            nuovi_stocks = [item for item in stocks if item["id"] not in ids_to_remove]
            self.data_manager.set_semilavorati(nuovi_stocks)
            
        self.reload_magazzino_tables()

    # ==================== DIALOG AGGIUNTA DATI MANUALI ====================
    
    def add_barre_dialog(self):
        self.show_barre_dialog(edit_index=None)

    def edit_barre_dialog(self, event=None):
        selected = self.tree_barre.selection()
        if not selected:
            if event is None:
                messagebox.showwarning("Seleziona elemento", "Seleziona una barra dalla tabella per modificarla.")
            return
        
        item_id = self.tree_barre.item(selected[0], "values")[0]
        barre = self.data_manager.get_barre()
        item_idx = -1
        for idx, b in enumerate(barre):
            if b["id"] == item_id:
                item_idx = idx
                break
        
        if item_idx == -1:
            messagebox.showerror("Errore", "Elemento non trovato nel database.")
            return
            
        self.show_barre_dialog(edit_index=item_idx)

    def show_barre_dialog(self, edit_index=None):
        dialog = tk.Toplevel(self.root)
        is_edit = edit_index is not None
        dialog.title("Modifica Pannello" if is_edit else "Aggiungi Pannello")
        dialog.geometry("350x580")
        dialog.grab_set()
        
        barre = self.data_manager.get_barre()
        current_item = barre[edit_index] if is_edit else None
        
        # Form
        fields = [
            ("ID Pannello (es. B2):", "ent_id", current_item["id"] if is_edit else ""),
            ("Larghezza (mm):", "ent_w", str(current_item["width"]) if is_edit else ""),
            ("Altezza (mm) ↕ (Senso Venatura):", "ent_h", str(current_item["height"]) if is_edit else ""),
            ("Spessore (mm):", "ent_t", str(current_item["thickness"]) if is_edit else ""),
            ("Cod. Colore (es. U708):", "ent_cc", current_item["color_code"] if is_edit else ""),
            ("Desc. Colore (es. Grigio):", "ent_cd", current_item["color_desc"] if is_edit else ""),
            ("Quantità:", "ent_q", str(current_item.get("quantity", 1)) if is_edit else "")
        ]
        
        entries = {}
        for idx, (label_text, var_name, default) in enumerate(fields):
            ttk.Label(dialog, text=label_text).pack(anchor=tk.W, padx=15, pady=(4, 1))
            entry = ttk.Entry(dialog)
            entry.insert(0, default)
            entry.pack(fill=tk.X, padx=15)
            entries[var_name] = entry
            
        # grain
        initial_grain = current_item.get("has_grain", False) if is_edit else False
        var_grain = tk.BooleanVar(value=initial_grain)
        chk = tk.Checkbutton(dialog, text="Ha venatura (Evita rotazioni in ottimizzazione)", variable=var_grain)
        chk.pack(anchor=tk.W, padx=15, pady=4)

        # type selector
        ttk.Label(dialog, text="Tipo Materiale:").pack(anchor=tk.W, padx=15, pady=(4, 1))
        combo_type = ttk.Combobox(dialog, values=["Pannello (🪵)", "Residuo (♻️)"], state="readonly")
        
        initial_type = "Pannello (🪵)"
        if is_edit:
            st = current_item.get("stock_type", "whole_board")
            if st == "remnant" or current_item["id"].startswith("S_REC_"):
                initial_type = "Residuo (♻️)"
        combo_type.set(initial_type)
        combo_type.pack(fill=tk.X, padx=15, pady=(0, 4))
        
        def save():
            try:
                item_id = entries["ent_id"].get().strip()
                w = float(entries["ent_w"].get().replace(",", "."))
                h = float(entries["ent_h"].get().replace(",", "."))
                t = float(entries["ent_t"].get().replace(",", "."))
                cc = entries["ent_cc"].get().strip()
                cd = entries["ent_cd"].get().strip()
                q = int(entries["ent_q"].get())
                has_grain = var_grain.get()
                selected_type = combo_type.get()
                
                if not item_id or w <= 0 or h <= 0 or t <= 0 or not cc or q <= 0:
                    raise ValueError("I campi obbligatori non sono validi.")
            except ValueError:
                messagebox.showerror("Errore inserimento", "Dati non validi. Verifica le dimensioni, spessori e quantità.")
                return
                
            # Process stock_type and prefix ID if it's a residual
            if selected_type == "Residuo (♻️)":
                stock_type = "remnant"
                if not item_id.startswith("S_REC_"):
                    item_id = f"S_REC_{item_id}"
            else:
                stock_type = "whole_board"
                if item_id.startswith("S_REC_"):
                    item_id = item_id[6:]

            # Verifica ID duplicati
            if not is_edit or item_id != current_item["id"]:
                if any(b["id"] == item_id for b in barre):
                    messagebox.showerror("Errore ID", f"Una lastra con ID '{item_id}' è già presente in magazzino.")
                    return
            
            new_data = {
                "id": item_id,
                "width": w,
                "height": h,
                "thickness": t,
                "color_code": cc,
                "color_desc": cd,
                "has_grain": has_grain,
                "quantity": q,
                "stock_type": stock_type
            }
            
            if is_edit:
                barre[edit_index] = new_data
            else:
                barre.append(new_data)
                
            self.data_manager.set_barre(barre)
            self.reload_magazzino_tables()
            dialog.destroy()
            
        btn_text = "Salva Modifiche" if is_edit else "Salva in Magazzino"
        ttk.Button(dialog, text=btn_text, command=save).pack(fill=tk.X, padx=15, pady=10)

    def add_semi_dialog(self):
        self.show_semi_dialog(edit_index=None)

    def edit_semi_dialog(self, event=None):
        selected = self.tree_semi.selection()
        if not selected:
            if event is None:
                messagebox.showwarning("Seleziona elemento", "Seleziona un semilavorato dalla tabella per modificarlo.")
            return
        
        item_id = self.tree_semi.item(selected[0], "values")[0]
        semis = self.data_manager.get_semilavorati()
        item_idx = -1
        for idx, s in enumerate(semis):
            if s["id"] == item_id:
                item_idx = idx
                break
        
        if item_idx == -1:
            messagebox.showerror("Errore", "Elemento non trovato nel database.")
            return
            
        self.show_semi_dialog(edit_index=item_idx)

    def show_semi_dialog(self, edit_index=None):
        dialog = tk.Toplevel(self.root)
        is_edit = edit_index is not None
        dialog.title("Modifica Semilavorato" if is_edit else "Aggiungi Semilavorato")
        dialog.geometry("350x580")
        dialog.grab_set()
        
        semis = self.data_manager.get_semilavorati()
        current_item = semis[edit_index] if is_edit else None
        
        fields = [
            ("ID Pezzo (es. S2):", "ent_id", current_item["id"] if is_edit else ""),
            ("Larghezza (mm):", "ent_w", str(current_item["width"]) if is_edit else ""),
            ("Altezza (mm) ↕ (Senso Venatura):", "ent_h", str(current_item["height"]) if is_edit else ""),
            ("Spessore (mm):", "ent_t", str(current_item["thickness"]) if is_edit else ""),
            ("Cod. Colore (es. U708):", "ent_cc", current_item["color_code"] if is_edit else ""),
            ("Desc. Colore (es. Grigio):", "ent_cd", current_item["color_desc"] if is_edit else ""),
            ("Quantità:", "ent_q", str(current_item.get("quantity", 1)) if is_edit else "")
        ]
        
        entries = {}
        for idx, (label_text, var_name, default) in enumerate(fields):
            ttk.Label(dialog, text=label_text).pack(anchor=tk.W, padx=15, pady=(4, 1))
            entry = ttk.Entry(dialog)
            entry.insert(0, default)
            entry.pack(fill=tk.X, padx=15)
            entries[var_name] = entry
            
        # grain
        initial_grain = current_item.get("has_grain", False) if is_edit else False
        var_grain = tk.BooleanVar(value=initial_grain)
        chk = tk.Checkbutton(dialog, text="Ha venatura (Evita rotazioni in ottimizzazione)", variable=var_grain)
        chk.pack(anchor=tk.W, padx=15, pady=4)

        # type selector
        ttk.Label(dialog, text="Tipo Materiale:").pack(anchor=tk.W, padx=15, pady=(4, 1))
        combo_type = ttk.Combobox(dialog, values=["Barra (📦)", "Residuo (♻️)"], state="readonly")
        
        initial_type = "Barra (📦)"
        if is_edit:
            st = current_item.get("stock_type", "semilavorato_bar")
            if st == "remnant" or current_item["id"].startswith("S_REC_"):
                initial_type = "Residuo (♻️)"
        combo_type.set(initial_type)
        combo_type.pack(fill=tk.X, padx=15, pady=(0, 4))
        
        def save():
            try:
                item_id = entries["ent_id"].get().strip()
                w = float(entries["ent_w"].get().replace(",", "."))
                h = float(entries["ent_h"].get().replace(",", "."))
                t = float(entries["ent_t"].get().replace(",", "."))
                cc = entries["ent_cc"].get().strip()
                cd = entries["ent_cd"].get().strip()
                q = int(entries["ent_q"].get())
                has_grain = var_grain.get()
                selected_type = combo_type.get()
                
                if not item_id or w <= 0 or h <= 0 or t <= 0 or not cc or q <= 0:
                    raise ValueError("I campi obbligatori non sono validi.")
            except ValueError:
                messagebox.showerror("Errore inserimento", "Dati non validi. Verifica le dimensioni, spessori e quantità.")
                return
                
            # Process stock_type and prefix ID if it's a residual
            if selected_type == "Residuo (♻️)":
                stock_type = "remnant"
                if not item_id.startswith("S_REC_"):
                    item_id = f"S_REC_{item_id}"
            else:
                stock_type = "semilavorato_bar"
                if item_id.startswith("S_REC_"):
                    item_id = item_id[6:]

            if not is_edit or item_id != current_item["id"]:
                if any(s["id"] == item_id for s in semis):
                    messagebox.showerror("Errore ID", f"Un semilavorato con ID '{item_id}' è già presente in magazzino.")
                    return
            
            new_data = {
                "id": item_id,
                "width": w,
                "height": h,
                "thickness": t,
                "color_code": cc,
                "color_desc": cd,
                "has_grain": has_grain,
                "quantity": q,
                "stock_type": stock_type
            }
            
            if is_edit:
                semis[edit_index] = new_data
            else:
                semis.append(new_data)
                
            self.data_manager.set_semilavorati(semis)
            self.reload_magazzino_tables()
            dialog.destroy()
            
        btn_text = "Salva Modifiche" if is_edit else "Salva in Magazzino"
        ttk.Button(dialog, text=btn_text, command=save).pack(fill=tk.X, padx=15, pady=10)

    def add_piece_dialog(self):
        if getattr(self, "current_commessa_status", "Aperta") == "Chiusa":
            messagebox.showerror("Errore", "La commessa corrente è CHIUSA e non può essere modificata.")
            return
        self.show_piece_dialog(edit_index=None)

    def edit_piece_dialog(self, event=None):
        if getattr(self, "current_commessa_status", "Aperta") == "Chiusa":
            messagebox.showerror("Errore", "La commessa corrente è CHIUSA e non può essere modificata.")
            return
        selected = self.tree_pieces.selection()
        if not selected:
            if event is None:
                messagebox.showwarning("Seleziona pezzo", "Seleziona un pezzo dalla lista per modificarlo.")
            return
            
        vals = self.tree_pieces.item(selected[0], "values")
        item_idx = int(vals[0]) - 1
        
        if item_idx < 0 or item_idx >= len(self.current_order):
            messagebox.showerror("Errore", "Elemento non trovato nell'ordine.")
            return
            
        self.show_piece_dialog(edit_index=item_idx)

    def show_piece_dialog(self, edit_index=None):
        dialog = tk.Toplevel(self.root)
        is_edit = edit_index is not None
        dialog.title("Modifica Pezzo dell'Ordine" if is_edit else "Aggiungi Pezzo all'Ordine")
        dialog.geometry("350x460")
        dialog.grab_set()
        
        current_item = self.current_order[edit_index] if is_edit else None
        
        fields = [
            ("Descrizione Pezzo (es. Fianco DX):", "ent_desc", current_item["descrizione"] if is_edit else ""),
            ("Larghezza (mm):", "ent_w", str(current_item["width"]) if is_edit else ""),
            ("Altezza (mm) ↕ (Senso Venatura):", "ent_h", str(current_item["height"]) if is_edit else ""),
            ("Spessore (mm):", "ent_t", str(current_item["thickness"]) if is_edit else ""),
            ("Cod. Colore (es. U708):", "ent_cc", current_item["color_code"] if is_edit else ""),
            ("Desc. Colore (es. Grigio):", "ent_cd", current_item["color_desc"] if is_edit else ""),
            ("Quantità:", "ent_q", str(current_item.get("quantity", 1)) if is_edit else "")
        ]
        
        entries = {}
        for idx, (label_text, var_name, default) in enumerate(fields):
            ttk.Label(dialog, text=label_text).pack(anchor=tk.W, padx=15, pady=(5, 1))
            entry = ttk.Entry(dialog)
            entry.insert(0, default)
            entry.pack(fill=tk.X, padx=15)
            entries[var_name] = entry
            
        def save():
            try:
                desc = entries["ent_desc"].get().strip()
                w = float(entries["ent_w"].get().replace(",", "."))
                h = float(entries["ent_h"].get().replace(",", "."))
                t = float(entries["ent_t"].get().replace(",", "."))
                cc = entries["ent_cc"].get().strip()
                cd = entries["ent_cd"].get().strip()
                q = int(entries["ent_q"].get())
                
                if not desc or w <= 0 or h <= 0 or t <= 0 or not cc or q <= 0:
                    raise ValueError()
            except ValueError:
                messagebox.showerror("Errore inserimento", "Verifica che le dimensioni e la quantità siano valori validi.")
                return
                
            new_data = {
                "descrizione": desc,
                "width": w,
                "height": h,
                "thickness": t,
                "color_code": cc,
                "color_desc": cd,
                "quantity": q
            }
            
            if is_edit:
                self.current_order[edit_index] = new_data
            else:
                self.current_order.append(new_data)
                
            self.reload_order_table()
            dialog.destroy()
            
        btn_text = "Salva Modifiche" if is_edit else "Aggiungi all'Ordine"
        ttk.Button(dialog, text=btn_text, command=save).pack(fill=tk.X, padx=15, pady=15)

    def open_bulk_edit_dialog(self, source_type):
        if source_type == "pezzi" and getattr(self, "current_commessa_status", "Aperta") == "Chiusa":
            messagebox.showerror("Errore", "La commessa corrente è CHIUSA e non può essere modificata.")
            return

        # Rileva gli elementi selezionati
        if source_type == "barre":
            selected = self.tree_barre.selection()
            if not selected:
                messagebox.showwarning("Nessuna selezione", "Seleziona almeno un pannello da duplicare/modificare in serie.")
                return
            items = []
            all_db_items = self.data_manager.get_barre()
            for sel in selected:
                item_id = self.tree_barre.item(sel, "values")[0]
                for b in all_db_items:
                    if b["id"] == item_id:
                        items.append(copy.deepcopy(b))
                        break
        elif source_type == "semilavorati":
            selected = self.tree_semi.selection()
            if not selected:
                messagebox.showwarning("Nessuna selezione", "Seleziona almeno un semilavorato da duplicare/modificare in serie.")
                return
            items = []
            all_db_items = self.data_manager.get_semilavorati()
            for sel in selected:
                item_id = self.tree_semi.item(sel, "values")[0]
                for s in all_db_items:
                    if s["id"] == item_id:
                        items.append(copy.deepcopy(s))
                        break
        elif source_type == "pezzi":
            selected = self.tree_pieces.selection()
            if not selected:
                messagebox.showwarning("Nessuna selezione", "Seleziona almeno un pezzo da duplicare/modificare in serie.")
                return
            items = []
            for sel in selected:
                vals = self.tree_pieces.item(sel, "values")
                item_idx = int(vals[0]) - 1
                if 0 <= item_idx < len(self.current_order):
                    items.append(copy.deepcopy(self.current_order[item_idx]))
        else:
            return

        # Crea finestra di dialogo
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Duplicazione / Modifica in Serie - {source_type.capitalize()}")
        dialog.geometry("920x450")
        dialog.grab_set()

        # Canvas e Scrollbar per supportare molte righe
        main_frame = tk.Frame(dialog, bg="#f5f6fa")
        main_frame.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(main_frame, bg="#f5f6fa", highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#f5f6fa")

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        # Consenti all'area interna di allargarsi assieme al canvas
        def on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)
            
        canvas.bind("<Configure>", on_canvas_configure)
        canvas.configure(yscrollcommand=scrollbar.set)

        # Griglia intestazioni
        # Griglia intestazioni
        headers = []
        if source_type in ("barre", "semilavorati"):
            headers = [
                ("ID (Univoco)", 100),
                ("Larghezza (W mm)", 100),
                ("Altezza (H mm)", 100),
                ("Spessore (mm)", 90),
                ("Cod. Colore", 90),
                ("Desc. Colore", 180),
                ("Venatura (S/N)", 90),
                ("Tipo", 90),
                ("Quantità", 80)
            ]
        else: # pezzi
            headers = [
                ("Descrizione Pezzo", 180),
                ("Larghezza (W mm)", 100),
                ("Altezza (H mm)", 100),
                ("Spessore (mm)", 90),
                ("Cod. Colore", 90),
                ("Desc. Colore", 180),
                ("Quantità", 80)
            ]

        # Configura il ridimensionamento dinamico delle colonne
        for col_idx in range(len(headers)):
            scrollable_frame.grid_columnconfigure(col_idx, weight=1)

        # Disegna intestazioni
        for col_idx, (header_text, width) in enumerate(headers):
            lbl = tk.Label(scrollable_frame, text=header_text, font=("Segoe UI", 9, "bold"),
                           bg="#273c75", fg="white", bd=1, relief=tk.RIDGE)
            lbl.grid(row=0, column=col_idx, sticky="ew", padx=1, pady=1)

        # Disegna righe con valori modificabili
        row_entries = [] # lista di dizionari che collegano gli Entry della riga
        for row_idx, item in enumerate(items, start=1):
            row_widgets = {}
            
            if source_type in ("barre", "semilavorati"):
                # ID
                ent_id = ttk.Entry(scrollable_frame)
                ent_id.insert(0, item["id"])
                ent_id.grid(row=row_idx, column=0, padx=1, pady=1, sticky="ew")
                row_widgets["id"] = ent_id
                
                # W
                ent_w = ttk.Entry(scrollable_frame)
                ent_w.insert(0, str(item["width"]))
                ent_w.grid(row=row_idx, column=1, padx=1, pady=1, sticky="ew")
                row_widgets["width"] = ent_w
                
                # H
                ent_h = ttk.Entry(scrollable_frame)
                ent_h.insert(0, str(item["height"]))
                ent_h.grid(row=row_idx, column=2, padx=1, pady=1, sticky="ew")
                row_widgets["height"] = ent_h
                
                # T
                ent_t = ttk.Entry(scrollable_frame)
                ent_t.insert(0, str(item["thickness"]))
                ent_t.grid(row=row_idx, column=3, padx=1, pady=1, sticky="ew")
                row_widgets["thickness"] = ent_t
                
                # CC
                ent_cc = ttk.Entry(scrollable_frame)
                ent_cc.insert(0, item["color_code"])
                ent_cc.grid(row=row_idx, column=4, padx=1, pady=1, sticky="ew")
                row_widgets["color_code"] = ent_cc
                
                # CD
                ent_cd = ttk.Entry(scrollable_frame)
                ent_cd.insert(0, item["color_desc"])
                ent_cd.grid(row=row_idx, column=5, padx=1, pady=1, sticky="ew")
                row_widgets["color_desc"] = ent_cd
                
                # Has Grain
                cb_grain = ttk.Combobox(scrollable_frame, values=["Sì", "No"], state="readonly")
                cb_grain.set("Sì" if item.get("has_grain", False) else "No")
                cb_grain.grid(row=row_idx, column=6, padx=1, pady=1, sticky="ew")
                row_widgets["has_grain"] = cb_grain
                
                # Tipo
                cb_type = ttk.Combobox(scrollable_frame, state="readonly")
                if source_type == "barre":
                    cb_type["values"] = ["Pannello (🪵)", "Residuo (♻️)"]
                    st = item.get("stock_type", "whole_board")
                    if st == "remnant" or item["id"].startswith("S_REC_"):
                        cb_type.set("Residuo (♻️)")
                    else:
                        cb_type.set("Pannello (🪵)")
                else:
                    cb_type["values"] = ["Barra (📦)", "Residuo (♻️)"]
                    st = item.get("stock_type", "semilavorato_bar")
                    if st == "remnant" or item["id"].startswith("S_REC_"):
                        cb_type.set("Residuo (♻️)")
                    else:
                        cb_type.set("Barra (📦)")
                cb_type.grid(row=row_idx, column=7, padx=1, pady=1, sticky="ew")
                row_widgets["stock_type_widget"] = cb_type
                
                # Q
                ent_q = ttk.Entry(scrollable_frame)
                ent_q.insert(0, str(item.get("quantity", 1)))
                ent_q.grid(row=row_idx, column=8, padx=1, pady=1, sticky="ew")
                row_widgets["quantity"] = ent_q
                
            else: # pezzi
                # Descrizione
                ent_desc = ttk.Entry(scrollable_frame)
                ent_desc.insert(0, item["descrizione"])
                ent_desc.grid(row=row_idx, column=0, padx=1, pady=1, sticky="ew")
                row_widgets["descrizione"] = ent_desc
                
                # W
                ent_w = ttk.Entry(scrollable_frame)
                ent_w.insert(0, str(item["width"]))
                ent_w.grid(row=row_idx, column=1, padx=1, pady=1, sticky="ew")
                row_widgets["width"] = ent_w
                
                # H
                ent_h = ttk.Entry(scrollable_frame)
                ent_h.insert(0, str(item["height"]))
                ent_h.grid(row=row_idx, column=2, padx=1, pady=1, sticky="ew")
                row_widgets["height"] = ent_h
                
                # T
                ent_t = ttk.Entry(scrollable_frame)
                ent_t.insert(0, str(item["thickness"]))
                ent_t.grid(row=row_idx, column=3, padx=1, pady=1, sticky="ew")
                row_widgets["thickness"] = ent_t
                
                # CC
                ent_cc = ttk.Entry(scrollable_frame)
                ent_cc.insert(0, item["color_code"])
                ent_cc.grid(row=row_idx, column=4, padx=1, pady=1, sticky="ew")
                row_widgets["color_code"] = ent_cc
                
                # CD
                ent_cd = ttk.Entry(scrollable_frame)
                ent_cd.insert(0, item["color_desc"])
                ent_cd.grid(row=row_idx, column=5, padx=1, pady=1, sticky="ew")
                row_widgets["color_desc"] = ent_cd
                
                # Q
                ent_q = ttk.Entry(scrollable_frame)
                ent_q.insert(0, str(item.get("quantity", 1)))
                ent_q.grid(row=row_idx, column=6, padx=1, pady=1, sticky="ew")
                row_widgets["quantity"] = ent_q
                
            row_entries.append(row_widgets)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)


        # Frame per i pulsanti a fondo maschera
        btn_frame = tk.Frame(dialog, bg="#f5f6fa", pady=10)
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM)

        lbl_shortcut = tk.Label(btn_frame, text="Premi F5 per confermare e inserire", font=("Segoe UI", 9, "italic"), bg="#f5f6fa", fg="#7f8c8d")
        lbl_shortcut.pack(side=tk.LEFT, padx=20)

        def do_save():
            # Carica dati attuali per controlli di univocità
            self.data_manager.db = self.data_manager.load_db()
            existing_barre = self.data_manager.get_barre()
            existing_semis = self.data_manager.get_semilavorati()
            
            new_records = []
            
            # Per controllare univocità anche tra le righe nuove stesse
            used_ids_in_batch = set()
            
            for idx, r_widgets in enumerate(row_entries):
                try:
                    if source_type in ("barre", "semilavorati"):
                        item_id = r_widgets["id"].get().strip()
                        w = float(r_widgets["width"].get().replace(",", "."))
                        h = float(r_widgets["height"].get().replace(",", "."))
                        t = float(r_widgets["thickness"].get().replace(",", "."))
                        cc = r_widgets["color_code"].get().strip()
                        cd = r_widgets["color_desc"].get().strip()
                        has_grain = (r_widgets["has_grain"].get() == "Sì")
                        q = int(r_widgets["quantity"].get())
                        
                        if not item_id or w <= 0 or h <= 0 or t <= 0 or not cc or q <= 0:
                            raise ValueError("Campi obbligatori non validi.")
                        
                        if source_type == "semilavorati":
                            selected_type = r_widgets["stock_type_widget"].get()
                            if selected_type == "Residuo (♻️)":
                                stock_type = "remnant"
                                if not item_id.startswith("S_REC_"):
                                    item_id = f"S_REC_{item_id}"
                            else:
                                stock_type = "semilavorato_bar"
                                if item_id.startswith("S_REC_"):
                                    item_id = item_id[6:]
                        elif source_type == "barre":
                            selected_type = r_widgets["stock_type_widget"].get()
                            if selected_type == "Residuo (♻️)":
                                stock_type = "remnant"
                                if not item_id.startswith("S_REC_"):
                                    item_id = f"S_REC_{item_id}"
                            else:
                                stock_type = "whole_board"
                                if item_id.startswith("S_REC_"):
                                    item_id = item_id[6:]
                        else:
                            stock_type = "whole_board"

                        # Controllo univocità chiave
                        if item_id in used_ids_in_batch:
                            messagebox.showerror("Errore Duplicato", f"Riga {idx+1}: L'ID '{item_id}' è duplicato all'interno di questa stessa maschera.")
                            return
                        used_ids_in_batch.add(item_id)
                        
                        if source_type == "barre":
                            if any(b["id"] == item_id for b in existing_barre):
                                messagebox.showerror("Errore ID", f"Riga {idx+1}: L'ID '{item_id}' è già presente nel database (Pannelli Standard).")
                                return
                        else:
                            if any(s["id"] == item_id for s in existing_semis):
                                messagebox.showerror("Errore ID", f"Riga {idx+1}: L'ID '{item_id}' è già presente nel database (Semilavorati).")
                                return
                                
                        rec = {
                            "id": item_id,
                            "width": w,
                            "height": h,
                            "thickness": t,
                            "color_code": cc,
                            "color_desc": cd,
                            "has_grain": has_grain,
                            "quantity": q,
                            "stock_type": stock_type
                        }
                        new_records.append(rec)
                    else: # pezzi
                        desc = r_widgets["descrizione"].get().strip()
                        w = float(r_widgets["width"].get().replace(",", "."))
                        h = float(r_widgets["height"].get().replace(",", "."))
                        t = float(r_widgets["thickness"].get().replace(",", "."))
                        cc = r_widgets["color_code"].get().strip()
                        cd = r_widgets["color_desc"].get().strip()
                        q = int(r_widgets["quantity"].get())
                        
                        if not desc or w <= 0 or h <= 0 or t <= 0 or not cc or q <= 0:
                            raise ValueError()
                            
                        new_records.append({
                            "descrizione": desc,
                            "width": w,
                            "height": h,
                            "thickness": t,
                            "color_code": cc,
                            "color_desc": cd,
                            "quantity": q
                        })
                except ValueError:
                    messagebox.showerror("Dati non validi", f"Errore alla riga {idx+1}: verifica che le dimensioni e le quantità siano numeriche e maggiori di zero.")
                    return

            # Esegui l'inserimento effettivo
            if source_type == "barre":
                all_items = existing_barre + new_records
                self.data_manager.set_barre(all_items)
                self.reload_magazzino_tables()
            elif source_type == "semilavorati":
                all_items = existing_semis + new_records
                self.data_manager.set_semilavorati(all_items)
                self.reload_magazzino_tables()
            elif source_type == "pezzi":
                self.current_order.extend(new_records)
                self.reload_order_table()
                
            dialog.destroy()
            messagebox.showinfo("Successo", f"Inseriti con successo {len(new_records)} record.")

        # Associa il tasto F5 alla maschera
        dialog.bind("<F5>", lambda e: do_save())

        # Pulsante di salvataggio/conferma
        btn_save = ttk.Button(btn_frame, text="Inserisci Record (F5)", style="Accent.TButton", command=do_save)
        btn_save.pack(side=tk.RIGHT, padx=20)

        btn_cancel = ttk.Button(btn_frame, text="Annulla", command=dialog.destroy)
        btn_cancel.pack(side=tk.RIGHT)

    def _sort_treeview_column(self, tree, col, reverse):
        # Ottiene gli elementi correnti del treeview
        l = [(tree.set(k, col), k) for k in tree.get_children('')]
        
        # Ordina
        l.sort(key=lambda t: make_sort_key(t[0]), reverse=reverse)
        
        # Riposiziona
        for index, (val, k) in enumerate(l):
            tree.move(k, '', index)
            
        # Modifica il comando per il click successivo
        tree.heading(col, command=lambda _col=col: self._sort_treeview_column(tree, _col, not reverse))

    def get_color_grain_map(self):
        color_grain_map = {}
        self.data_manager.db = self.data_manager.load_db()
        for b in self.data_manager.get_barre():
            color_grain_map[b["color_code"]] = b.get("has_grain", False)
        return color_grain_map

    def on_heading_right_click(self, event, table_name):
        tree = event.widget
        region = tree.identify_region(event.x, event.y)
        if region != "heading":
            return
            
        col_id = tree.identify_column(event.x)
        try:
            col_idx = int(col_id.replace("#", "")) - 1
            col_name = tree["columns"][col_idx]
            heading_text = tree.heading(col_name, "text")
        except Exception:
            return
            
        if table_name == "barre":
            filters_dict = self.filters_barre
        elif table_name == "semilavorati":
            filters_dict = self.filters_semi
        elif table_name == "commesse":
            filters_dict = self.filters_commesse
        else:
            filters_dict = self.filters_pieces
            
        current_filter = filters_dict.get(col_name, "")
        val = simpledialog.askstring(
            "Filtra Colonna",
            f"Filtra la colonna '{heading_text}' per il valore:\n(lascia vuoto per rimuovere il filtro)",
            initialvalue=current_filter,
            parent=self.root
        )
        if val is None:
            return
            
        clean_val = val.strip().lower()
        if clean_val:
            filters_dict[col_name] = clean_val
        else:
            filters_dict.pop(col_name, None)
            
        if table_name in ["barre", "semilavorati"]:
            self.reload_magazzino_tables()
        elif table_name == "commesse":
            self.reload_commesse_table()
        else:
            self.reload_order_table()

    def toggle_pieces_green(self, event=None):
        selected = self.tree_pieces.selection()
        if not selected:
            return
            
        # Determina se c'è almeno un pezzo selezionato che NON è verde
        has_non_green = False
        for item in selected:
            vals = self.tree_pieces.item(item, "values")
            if vals:
                idx = int(vals[0]) - 1
                if 0 <= idx < len(self.current_order):
                    if not self.current_order[idx].get("is_green", False):
                        has_non_green = True
                        break
        
        # Se c'è almeno un pezzo non verde, rendili tutti verdi (accumulo).
        # Altrimenti (tutti già verdi), deselezionali tutti.
        target_state = True if has_non_green else False
        
        for item in selected:
            vals = self.tree_pieces.item(item, "values")
            if vals:
                idx = int(vals[0]) - 1
                if 0 <= idx < len(self.current_order):
                    self.current_order[idx]["is_green"] = target_state
                    
        self.reload_order_table()

    def select_all_pieces(self):
        if getattr(self, "current_commessa_status", "Aperta") == "Chiusa":
            return
        for p in self.current_order:
            p["is_green"] = True
        self.reload_order_table()
        children = self.tree_pieces.get_children()
        if children:
            self.tree_pieces.selection_set(children)

    def deselect_all_pieces(self):
        if getattr(self, "current_commessa_status", "Aperta") == "Chiusa":
            return
        for p in self.current_order:
            p["is_green"] = False
        self.reload_order_table()
        self.tree_pieces.selection_set("")

    def clear_filters_barre(self):
        self.filters_barre = {}
        self.reload_magazzino_tables()

    def clear_filters_semi(self):
        self.filters_semi = {}
        self.reload_magazzino_tables()

    def clear_filters_commesse(self):
        self.filters_commesse = {}
        for p in self.current_order:
            p["is_green"] = False
        self.reload_commesse_table()
        self.reload_order_table()

    def clear_filters_pieces(self):
        self.filters_pieces = {}
        self.reload_order_table()

    def ask_panel_grain_direction(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Direzione Venatura Pannelli")
        dialog.geometry("350x180")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)
        
        dialog.update_idletasks()
        pw = self.root.winfo_width()
        ph = self.root.winfo_height()
        px = self.root.winfo_rootx()
        py = self.root.winfo_rooty()
        dx = px + (pw - 350) // 2
        dy = py + (ph - 180) // 2
        dialog.geometry(f"+{dx}+{dy}")
        
        direction_var = tk.StringVar(value="verticale")
        
        lbl = ttk.Label(
            dialog, 
            text="La venatura per il calcolo sui pannelli deve essere\nconsiderata in verticale o orizzontale?", 
            justify=tk.CENTER,
            font=("Segoe UI", 10)
        )
        lbl.pack(pady=20)
        
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=5)
        
        def choose_vert():
            direction_var.set("verticale")
            dialog.destroy()
            
        def choose_horiz():
            direction_var.set("orizzontale")
            dialog.destroy()
            
        btn_vert = ttk.Button(btn_frame, text="↕ Verticale (Default)", style="Accent.TButton", command=choose_vert)
        btn_vert.pack(side=tk.LEFT, padx=10)
        
        btn_horiz = ttk.Button(btn_frame, text="↔ Orizzontale", command=choose_horiz)
        btn_horiz.pack(side=tk.LEFT, padx=10)
        
        self.root.wait_window(dialog)
        return direction_var.get()

    def show_db_settings_dialog(self):
        pwd = simpledialog.askstring("Accesso Riservato", "Inserisci la password per accedere alle impostazioni:", show="*")
        if pwd is None:
            return
        if pwd == "Rdf202764!":
            DbSettingsDialog(self.root, self.data_manager, self)
        else:
            messagebox.showerror("Accesso Negato", "Password errata! Accesso non consentito.")

class DbSettingsDialog(tk.Toplevel):
    def __init__(self, parent, data_manager, app):
        super().__init__(parent)
        self.app = app
        self.title("Configurazione Database")
        self.geometry("680x600")
        self.resizable(False, False)
        self.grab_set()
        
        self.data_manager = data_manager
        self.config = data_manager.load_config()
        
        self.bg_primary = "#f5f6fa"
        self.bg_card = "#ffffff"
        self.accent_color = "#273c75"
        self.accent_light = "#487eb0"
        self.text_color = "#2f3640"
        self.configure(bg=self.bg_primary)
        
        self.db_type_var = tk.StringVar(value=self.config.get("db_type", "local"))
        self.sql_type_var = tk.StringVar(value=self.config.get("sql_type", "MySQL"))
        
        # Frame Principale
        main_frame = ttk.Frame(self, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Titolo
        lbl_title = ttk.Label(main_frame, text="IMPOSTAZIONI DI SISTEMA", font=("Segoe UI", 12, "bold"), foreground=self.accent_color)
        lbl_title.pack(anchor=tk.W, pady=(0, 10))
        
        # Notebook (Linguette)
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 1. Tab Database
        tab_db = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab_db, text="Database")
        
        # 2. Tab Parametri Standard
        tab_params = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab_params, text="Parametri Standard")
        
        # 3. Tab Dati Cliente
        tab_client = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab_client, text="Dati Cliente")
        
        # 4. Tab Generazione Rilascio
        tab_build = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab_build, text="Generazione Rilascio")
        
        # Radio buttons per Tipo Db (nel tab_db)
        f_type = ttk.LabelFrame(tab_db, text="Tipo Database", padding=8)
        f_type.pack(fill=tk.X, pady=(0, 8))
        
        rb_local = ttk.Radiobutton(f_type, text="Monoutente (Locale JSON)", variable=self.db_type_var, value="local", command=self.toggle_fields)
        rb_local.pack(anchor=tk.W, pady=2)
        rb_sql = ttk.Radiobutton(f_type, text="Multiutente (Server SQL)", variable=self.db_type_var, value="sql", command=self.toggle_fields)
        rb_sql.pack(anchor=tk.W, pady=2)
        
        # Frame Configurazione SQL (nel tab_db)
        self.f_sql = ttk.LabelFrame(tab_db, text="Parametri SQL Server", padding=8)
        self.f_sql.pack(fill=tk.BOTH, expand=True, pady=(0, 8))
        
        # Tipo SQL (MySQL / SQL Server)
        ttk.Label(self.f_sql, text="Tipo Server SQL:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.cmb_sql_type = ttk.Combobox(self.f_sql, textvariable=self.sql_type_var, values=["MySQL", "SQL Server"], state="readonly", width=15)
        self.cmb_sql_type.grid(row=0, column=1, sticky=tk.W, pady=2, padx=5)
        
        # Host (IP)
        ttk.Label(self.f_sql, text="IP Server:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.ent_host = ttk.Entry(self.f_sql, width=20)
        self.ent_host.insert(0, self.config.get("sql_host", "127.0.0.1"))
        self.ent_host.grid(row=1, column=1, sticky=tk.W, pady=2, padx=5)
        
        # Port
        ttk.Label(self.f_sql, text="Porta:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.ent_port = ttk.Entry(self.f_sql, width=10)
        self.ent_port.insert(0, str(self.config.get("sql_port", 3306)))
        self.ent_port.grid(row=2, column=1, sticky=tk.W, pady=2, padx=5)
        
        # User
        ttk.Label(self.f_sql, text="Nome Utente:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.ent_user = ttk.Entry(self.f_sql, width=20)
        self.ent_user.insert(0, self.config.get("sql_user", ""))
        self.ent_user.grid(row=3, column=1, sticky=tk.W, pady=2, padx=5)
        
        # Password
        ttk.Label(self.f_sql, text="Password:").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.ent_pass = ttk.Entry(self.f_sql, show="*", width=20)
        self.ent_pass.insert(0, self.config.get("sql_password", ""))
        self.ent_pass.grid(row=4, column=1, sticky=tk.W, pady=2, padx=5)
        
        # Database Name
        ttk.Label(self.f_sql, text="Nome Database:").grid(row=5, column=0, sticky=tk.W, pady=2)
        self.ent_db = ttk.Entry(self.f_sql, width=20)
        self.ent_db.insert(0, self.config.get("sql_database", "cutmob"))
        self.ent_db.grid(row=5, column=1, sticky=tk.W, pady=2, padx=5)
        
        # Frame Attivazione Funzioni Importazione (nel tab_db)
        f_import = ttk.LabelFrame(tab_db, text="Funzioni di Importazione", padding=8)
        f_import.pack(fill=tk.X, pady=(4, 0))
        
        self.var_import_enabled = tk.BooleanVar(value=self.config.get("import_enabled", True))
        chk_import = tk.Checkbutton(f_import, text="Abilita importazione dati da file CSV", variable=self.var_import_enabled)
        chk_import.pack(anchor=tk.W, pady=2)
        
        # --- TAB PARAMETRI STANDARD ---
        ttk.Label(tab_params, text="Kerf di default (spessore lama mm):").grid(row=0, column=0, sticky=tk.W, pady=6)
        self.ent_def_kerf = ttk.Entry(tab_params, width=15)
        self.ent_def_kerf.insert(0, str(self.config.get("default_kerf", "5.0")))
        self.ent_def_kerf.grid(row=0, column=1, sticky=tk.W, pady=6, padx=10)
        
        ttk.Label(tab_params, text="Rifilo Orizzontale di default (mm):").grid(row=1, column=0, sticky=tk.W, pady=6)
        self.ent_def_rifilo_h = ttk.Entry(tab_params, width=15)
        self.ent_def_rifilo_h.insert(0, str(self.config.get("default_rifilo_h", "0")))
        self.ent_def_rifilo_h.grid(row=1, column=1, sticky=tk.W, pady=6, padx=10)
        
        ttk.Label(tab_params, text="Rifilo Verticale di default (mm):").grid(row=2, column=0, sticky=tk.W, pady=6)
        self.ent_def_rifilo_v = ttk.Entry(tab_params, width=15)
        self.ent_def_rifilo_v.insert(0, str(self.config.get("default_rifilo_v", "0")))
        self.ent_def_rifilo_v.grid(row=2, column=1, sticky=tk.W, pady=6, padx=10)
        
        ttk.Label(tab_params, text="Sfrido pezzi di default (mm):").grid(row=3, column=0, sticky=tk.W, pady=6)
        self.ent_def_sfrido = ttk.Entry(tab_params, width=15)
        self.ent_def_sfrido.insert(0, str(self.config.get("default_sfrido", "10")))
        self.ent_def_sfrido.grid(row=3, column=1, sticky=tk.W, pady=6, padx=10)
        
        ttk.Label(tab_params, text="Tipo Macchinario di default:").grid(row=4, column=0, sticky=tk.W, pady=6)
        self.cmb_def_macchina = ttk.Combobox(tab_params, values=["Sezionatrice", "Pantografo"], state="readonly", width=13)
        def_macch = self.config.get("default_macchina", "sezionatrice")
        if def_macch.lower() == "pantografo":
            self.cmb_def_macchina.set("Pantografo")
        else:
            self.cmb_def_macchina.set("Sezionatrice")
        self.cmb_def_macchina.grid(row=4, column=1, sticky=tk.W, pady=6, padx=10)
        
        ttk.Label(tab_params, text="Min. larghezza recupero di default (mm):").grid(row=5, column=0, sticky=tk.W, pady=6)
        self.ent_def_min_w = ttk.Entry(tab_params, width=15)
        self.ent_def_min_w.insert(0, str(self.config.get("default_min_w", "300")))
        self.ent_def_min_w.grid(row=5, column=1, sticky=tk.W, pady=6, padx=10)
        
        ttk.Label(tab_params, text="Min. altezza recupero di default (mm):").grid(row=6, column=0, sticky=tk.W, pady=6)
        self.ent_def_min_h = ttk.Entry(tab_params, width=15)
        self.ent_def_min_h.insert(0, str(self.config.get("default_min_h", "300")))
        self.ent_def_min_h.grid(row=6, column=1, sticky=tk.W, pady=6, padx=10)
        
        # --- TAB DATI CLIENTE ---
        ttk.Label(tab_client, text="Nome / Ragione Sociale:").grid(row=0, column=0, sticky=tk.W, pady=8)
        self.ent_client_name = ttk.Entry(tab_client, width=30)
        self.ent_client_name.insert(0, self.config.get("client_name", ""))
        self.ent_client_name.grid(row=0, column=1, sticky=tk.W, pady=8, padx=10)
        
        ttk.Label(tab_client, text="Codice Fiscale / Partita IVA:").grid(row=1, column=0, sticky=tk.W, pady=8)
        self.ent_client_cf_piva = ttk.Entry(tab_client, width=30)
        self.ent_client_cf_piva.insert(0, self.config.get("client_cf_piva", ""))
        self.ent_client_cf_piva.grid(row=1, column=1, sticky=tk.W, pady=8, padx=10)
        
        ttk.Label(tab_client, text="Indirizzo E-mail:").grid(row=2, column=0, sticky=tk.W, pady=8)
        self.ent_client_email = ttk.Entry(tab_client, width=30)
        self.ent_client_email.insert(0, self.config.get("client_email", ""))
        self.ent_client_email.grid(row=2, column=1, sticky=tk.W, pady=8, padx=10)
        
        # default stock selections (Uso Magazzino di Default)
        ttk.Label(tab_client, text="Uso Magazzino di Default:").grid(row=3, column=0, sticky=tk.W, pady=8)
        f_stock_def = ttk.Frame(tab_client)
        f_stock_def.grid(row=3, column=1, sticky=tk.W, pady=8, padx=10)
        
        self.var_def_residuo = tk.BooleanVar(value=self.config.get("default_use_residuo", True))
        self.var_def_barra = tk.BooleanVar(value=self.config.get("default_use_barra", True))
        self.var_def_pannello = tk.BooleanVar(value=self.config.get("default_use_pannello", True))
        
        chk_res = tk.Checkbutton(f_stock_def, text="Residuo (♻️)", variable=self.var_def_residuo)
        chk_res.pack(side=tk.LEFT, padx=3)
        chk_bar = tk.Checkbutton(f_stock_def, text="Barra (📁)", variable=self.var_def_barra)
        chk_bar.pack(side=tk.LEFT, padx=3)
        chk_pan = tk.Checkbutton(f_stock_def, text="Pannello (🪵)", variable=self.var_def_pannello)
        chk_pan.pack(side=tk.LEFT, padx=3)
        
        # Controllo Licenza
        ttk.Label(tab_client, text="Controllo Licenza:").grid(row=4, column=0, sticky=tk.W, pady=8)
        self.var_license_enabled = tk.BooleanVar(value=self.config.get("license_enabled", True))
        self.chk_license = tk.Checkbutton(
            tab_client, 
            text="Attiva Controllo Licenza (protetto da password)", 
            variable=self.var_license_enabled,
            state="disabled",
            disabledforeground="#7f8c8d",
            command=self.update_license_fields_state
        )
        self.chk_license.grid(row=4, column=1, sticky=tk.W, pady=8, padx=10)
        
        def unlock_settings_license(event):
            pwd = simpledialog.askstring("Sblocco di sicurezza", "Inserire la password di sblocco licenza:", show="*")
            if pwd == "Rdf20276498!":
                self.chk_license.configure(state="normal")
                messagebox.showinfo("Sblocco", "Controllo licenza sbloccato. Ora puoi modificare lo stato.")
            elif pwd is not None:
                messagebox.showerror("Errore", "Password non valida.")
                
        self.chk_license.bind("<Double-1>", unlock_settings_license)
        
        # Inizializza stato campi in base alla licenza
        if self.config.get("license_enabled", True):
            self.ent_client_name.configure(state="disabled")
            self.ent_client_cf_piva.configure(state="disabled")
            
        # Versione Software
        ttk.Label(tab_client, text="Versione Software:").grid(row=5, column=0, sticky=tk.W, pady=8)
        lbl_version_val = ttk.Label(tab_client, text=f"{self.app.APP_VERSION} (Attiva)", font=("Segoe UI", 10, "bold"))
        lbl_version_val.grid(row=5, column=1, sticky=tk.W, pady=8, padx=10)
        
        # Forza Aggiornamento
        btn_force_update = ttk.Button(tab_client, text="🔄 Verifica / Forza Aggiornamento", command=self.force_update_check)
        btn_force_update.grid(row=6, column=1, sticky=tk.W, pady=8, padx=10)
            
        # --- CONFIGURAZIONE TAB GENERAZIONE RILASCIO ---
        ttk.Label(tab_build, text="STRUMENTI DI RILASCIO", font=("Segoe UI", 11, "bold"), foreground=self.accent_color).pack(anchor=tk.W, pady=(0, 10))
        ttk.Label(tab_build, text="Genera i pacchetti di installazione/aggiornamento dell'applicazione per la distribuzione sul panel.", font=("Segoe UI", 9, "italic"), wraplength=440, justify=tk.LEFT).pack(anchor=tk.W, pady=(0, 15))
        
        # Campo versione da compilare
        f_version = ttk.Frame(tab_build)
        f_version.pack(fill=tk.X, pady=10)
        ttk.Label(f_version, text="Versione da rilasciare (es. 2.1.4):", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=(0, 10))
        self.ent_build_version = ttk.Entry(f_version, width=15)
        self.ent_build_version.insert(0, self.app.APP_VERSION)
        self.ent_build_version.pack(side=tk.LEFT)
        
        btn_build_win = ttk.Button(tab_build, text="💻 Genera Pacchetto Windows (.exe)", command=self.build_windows_installer)
        btn_build_win.pack(fill=tk.X, pady=8)
        
        btn_build_mac = ttk.Button(tab_build, text="🍎 Genera Pacchetto macOS (.dmg)", command=self.build_mac_installer)
        btn_build_mac.pack(fill=tk.X, pady=8)
        
        # Sezione Chiave di Attivazione
        ttk.Label(tab_build, text="CHIAVE DI ATTIVAZIONE ATTIVA", font=("Segoe UI", 10, "bold"), foreground=self.accent_color).pack(anchor=tk.W, pady=(20, 5))
        current_key = self.app.data_manager.load_license_key() or ""
        self.txt_license_key = tk.Text(tab_build, height=3, font=("Consolas", 9), wrap=tk.CHAR)
        self.txt_license_key.insert(tk.END, current_key)
        self.txt_license_key.pack(fill=tk.X, pady=5)
        
        btn_update_key = ttk.Button(tab_build, text="🔑 Salva / Aggiorna Chiave Licenza", command=self.update_license_key_from_settings)
        btn_update_key.pack(anchor=tk.E, pady=5)
        
        # Bottoni Azione (in main_frame, posizionati in fondo)
        f_buttons = ttk.Frame(main_frame)
        f_buttons.pack(fill=tk.X, side=tk.BOTTOM, pady=(5, 0))
        
        btn_cancel = ttk.Button(f_buttons, text="Annulla", command=self.destroy)
        btn_cancel.pack(side=tk.RIGHT, padx=5)
        
        btn_save = ttk.Button(f_buttons, text="Salva e Applica", command=self.save_settings)
        btn_save.pack(side=tk.RIGHT, padx=5)
        
        self.btn_test = ttk.Button(f_buttons, text="Test Connessione", command=self.test_connection)
        self.btn_test.pack(side=tk.LEFT, padx=5)
        
        self.toggle_fields()

    def toggle_fields(self):
        state = tk.NORMAL if self.db_type_var.get() == "sql" else tk.DISABLED
        for child in self.f_sql.winfo_children():
            try:
                child.configure(state=state)
            except Exception:
                pass
        if state == tk.DISABLED:
            self.btn_test.configure(state=tk.DISABLED)
        else:
            self.btn_test.configure(state=tk.NORMAL)

    def update_license_fields_state(self):
        if self.var_license_enabled.get():
            self.ent_client_name.configure(state="disabled")
            self.ent_client_cf_piva.configure(state="disabled")
        else:
            self.ent_client_name.configure(state="normal")
            self.ent_client_cf_piva.configure(state="normal")

    def test_connection(self):
        temp_config = {
            "db_type": "sql",
            "sql_type": self.sql_type_var.get(),
            "sql_host": self.ent_host.get(),
            "sql_port": int(self.ent_port.get() if self.ent_port.get().isdigit() else 3306),
            "sql_user": self.ent_user.get(),
            "sql_password": self.ent_pass.get(),
            "sql_database": self.ent_db.get()
        }
        
        from data_manager import DataManager
        test_dm = DataManager()
        test_dm.config = temp_config
        
        self.btn_test.configure(state=tk.DISABLED)
        self.update()
        
        try:
            conn = test_dm._get_sql_connection()
            conn.close()
            messagebox.showinfo("Connessione Riuscita", "Connessione al database SQL avvenuta con successo!")
        except Exception as e:
            messagebox.showerror("Errore di Connessione", f"Impossibile connettersi al database:\n{e}")
        finally:
            self.btn_test.configure(state=tk.NORMAL)

    def save_settings(self):
        db_type = self.db_type_var.get()
        
        # Convalida e leggi i parametri standard
        try:
            k = float(self.ent_def_kerf.get().replace(",", "."))
            rh = float(self.ent_def_rifilo_h.get().replace(",", "."))
            rv = float(self.ent_def_rifilo_v.get().replace(",", "."))
            sf = float(self.ent_def_sfrido.get().replace(",", "."))
            mw = float(self.ent_def_min_w.get().replace(",", "."))
            mh = float(self.ent_def_min_h.get().replace(",", "."))
            if k < 0 or rh < 0 or rv < 0 or sf < 0 or mw < 0 or mh < 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Errore Dati", "Verifica che i parametri standard siano numeri validi non negativi.")
            return

        new_config = {
            "db_type": db_type,
            "local_path": r"C:\CutMob\DbDati\database.json",
            "sql_type": self.cmb_sql_type.get() if db_type == "sql" else self.config.get("sql_type", "MySQL"),
            "sql_host": self.ent_host.get() if db_type == "sql" else self.config.get("sql_host", "127.0.0.1"),
            "sql_port": int(self.ent_port.get() if self.ent_port.get().isdigit() else 3306) if db_type == "sql" else self.config.get("sql_port", 3306),
            "sql_user": self.ent_user.get() if db_type == "sql" else self.config.get("sql_user", ""),
            "sql_password": self.ent_pass.get() if db_type == "sql" else self.config.get("sql_password", ""),
            "sql_database": self.ent_db.get() if db_type == "sql" else self.config.get("sql_database", "cutmob"),
            
            # Parametri standard
            "default_kerf": k,
            "default_rifilo_h": rh,
            "default_rifilo_v": rv,
            "default_sfrido": sf,
            "default_macchina": self.cmb_def_macchina.get().lower(),
            "show_cut_progression": self.config.get("show_cut_progression", True),
            "default_min_w": mw,
            "default_min_h": mh,
            
            # Dati cliente e funzioni importazione / uso magazzino
            "client_name": self.ent_client_name.get().strip(),
            "client_cf_piva": self.ent_client_cf_piva.get().strip(),
            "client_email": self.ent_client_email.get().strip(),
            "import_enabled": self.var_import_enabled.get(),
            "license_enabled": self.var_license_enabled.get(),
            
            "default_use_residuo": self.var_def_residuo.get(),
            "default_use_barra": self.var_def_barra.get(),
            "default_use_pannello": self.var_def_pannello.get()
        }
        
        if db_type == "sql":
            try:
                from data_manager import DataManager
                test_dm = DataManager()
                test_dm.config = new_config
                conn = test_dm._get_sql_connection()
                conn.close()
            except Exception as e:
                confirm = messagebox.askyesno("Errore Connessione", f"Il test di connessione è fallito con il seguente errore:\n{e}\n\nVuoi salvare comunque la configurazione?")
                if not confirm:
                    return

        success = self.data_manager.save_config(new_config)
        if success:
            self.data_manager.reinit_backend()
            # Sincronizza i campi della sidebar
            self.app.ent_kerf.delete(0, tk.END)
            self.app.ent_kerf.insert(0, str(k))
            
            self.app.ent_rifilo_h.delete(0, tk.END)
            self.app.ent_rifilo_h.insert(0, str(int(rh) if rh.is_integer() else rh))
            
            self.app.ent_rifilo_v.delete(0, tk.END)
            self.app.ent_rifilo_v.insert(0, str(int(rv) if rv.is_integer() else rv))
            
            self.app.ent_sfrido.delete(0, tk.END)
            self.app.ent_sfrido.insert(0, str(int(sf) if sf.is_integer() else sf))
            
            self.app.ent_min_w.delete(0, tk.END)
            self.app.ent_min_w.insert(0, str(int(mw) if mw.is_integer() else mw))
            
            self.app.ent_min_h.delete(0, tk.END)
            self.app.ent_min_h.insert(0, str(int(mh) if mh.is_integer() else mh))
            
            if self.cmb_def_macchina.get() == "Pantografo":
                self.app.cmb_macchina.set("Pantografo")
            else:
                self.app.cmb_macchina.set("Sezionatrice")
                
            self.app.update_client_display()
            self.app.update_import_features()
            
            messagebox.showinfo("Impostazioni Salvate", "La configurazione è stata salvata con successo. Il database è stato ricaricato.")
            self.destroy()
        else:
            messagebox.showerror("Errore", "Impossibile salvare il file di configurazione.")

    def build_windows_installer(self):
        import subprocess
        import os
        from tkinter import messagebox
        import threading
        
        target_version = self.ent_build_version.get().strip()
        if not target_version:
            messagebox.showerror("Errore", "Specificare una versione valida prima di compilare.")
            return

        if not messagebox.askyesno("Compilazione Windows", f"Vuoi impostare il programma alla versione {target_version} e avviare la compilazione del pacchetto di installazione Windows?\nQuesta operazione richiederà alcuni istanti."):
            return
            
        try:
            # Aggiorna versione nel codice sorgente di app.py prima di compilare
            app_py_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.py")
            if os.path.exists(app_py_path):
                with open(app_py_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                updated = False
                for i, line in enumerate(lines):
                    if "self.APP_VERSION =" in line:
                        lines[i] = f'        self.APP_VERSION = "{target_version}"\n'
                        updated = True
                        break
                if updated:
                    with open(app_py_path, "w", encoding="utf-8") as f:
                        f.writelines(lines)
            
            script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "build_installer.py")
            if not os.path.exists(script_path):
                messagebox.showerror("Errore", f"Script di compilazione non trovato: {script_path}")
                return
                
            messagebox.showinfo("Compilazione avviata", f"Compilazione della versione {target_version} avviata in background.\nRiceverai una notifica al completamento.")
            
            def run_build():
                res = subprocess.run(["python", script_path], capture_output=True, text=True)
                if res.returncode == 0:
                    messagebox.showinfo("Compilazione Completata", f"Compilazione Windows (v{target_version}) completata con successo!\nIl file Setup_CutMob_{target_version}.zip si trova nella cartella dist/\n\nLa cartella dist/ verrà aperta automaticamente.")
                    try:
                        os.startfile("dist")
                    except Exception:
                        try:
                            import subprocess
                            subprocess.Popen(["explorer", "dist"])
                        except Exception:
                            pass
                else:
                    messagebox.showerror("Errore Compilazione", f"Errore durante la compilazione:\n{res.stderr or res.stdout}")
                    
            threading.Thread(target=run_build, daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile avviare la compilazione: {e}")

    def build_mac_installer(self):
        import sys
        from tkinter import messagebox
        if sys.platform != "darwin":
            messagebox.showwarning("Compilazione macOS", "La compilazione del pacchetto macOS (.dmg) può essere eseguita esclusivamente da un computer Mac.")
            return
            
        messagebox.showinfo("Compilazione macOS", "La compilazione per macOS è disponibile eseguendo il programma da un sistema Apple Mac.")

    def force_update_check(self):
        import urllib.request
        import json
        import sys
        from tkinter import messagebox
        
        try:
            os_name = "mac" if sys.platform == "darwin" else "windows"
            piva = self.app.data_manager.config.get("client_cf_piva", "")
            ver = self.app.APP_VERSION
            url = f"https://panel.aiconsultingitalia.com/panel_cutmob/api.php?action=get_latest_version&prodotto=CutMob&os={os_name}&partita_iva={piva}&version={ver}"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                res_data = json.loads(response.read().decode('utf-8'))
                if res_data.get("status") == "success":
                    info = res_data.get("data")
                    latest_version = info.get("version", "2.0.0")
                    current_version = self.app.APP_VERSION
                    
                    def parse_ver(v):
                        try:
                            return [int(x) for x in v.strip('v').split('.')]
                        except Exception:
                            return [0, 0]
                            
                    self.app.latest_version_info = info
                    
                    if parse_ver(latest_version) > parse_ver(current_version):
                        msg = f"È disponibile una nuova versione: v{latest_version} (versione installata: v{current_version}).\nVuoi scaricare e installare l'aggiornamento ora?"
                        if messagebox.askyesno("Aggiornamento Disponibile", msg):
                            self.app.run_update_process()
                            self.destroy()
                    else:
                        msg = f"L'applicazione è già aggiornata alla versione più recente (v{current_version}).\n\nVuoi comunque forzare il download e la reinstallazione dell'ultimo pacchetto dal server?"
                        if messagebox.askyesno("Nessun Aggiornamento Necessario", msg):
                            self.app.run_update_process()
                            self.destroy()
                else:
                    messagebox.showerror("Errore", f"Risposta del server non valida: {res_data.get('message')}")
        except Exception as e:
            messagebox.showerror("Errore di connessione", f"Impossibile connettersi al server di aggiornamento:\n{e}")

    def update_license_key_from_settings(self):
        from license_manager import verifica_chiave_licenza
        from tkinter import messagebox
        
        new_key = self.txt_license_key.get("1.0", tk.END).strip()
        if not new_key:
            messagebox.showerror("Errore", "La chiave di licenza non può essere vuota.")
            return
            
        valida, err_msg, data = verifica_chiave_licenza(new_key)
        if valida:
            self.app.data_manager.save_license_key(new_key)
            
            # Aggiorna i dati del cliente nella configurazione
            config = self.app.data_manager.config
            config["client_name"] = data.get("ragione_sociale", "")
            config["client_cf_piva"] = data.get("partita_iva", "")
            config["license_enabled"] = True
            self.app.data_manager.save_config(config)
            
            self.app.update_client_display()
            
            # Aggiorna anche i campi di testo visibili in "Dati Cliente"
            self.ent_client_name.configure(state="normal")
            self.ent_client_name.delete(0, tk.END)
            self.ent_client_name.insert(0, data.get("ragione_sociale", ""))
            self.ent_client_name.configure(state="disabled")
            
            self.ent_client_cf_piva.configure(state="normal")
            self.ent_client_cf_piva.delete(0, tk.END)
            self.ent_client_cf_piva.insert(0, data.get("partita_iva", ""))
            self.ent_client_cf_piva.configure(state="disabled")
            
            messagebox.showinfo("Successo", f"Chiave di licenza salvata ed attivata con successo!\nCliente: {data.get('ragione_sociale')}\nScadenza: {data.get('data_fine')}")
        else:
            messagebox.showerror("Errore Licenza", f"La chiave inserita non è valida:\n{err_msg}")




class FabbisognoDialog(tk.Toplevel):
    def __init__(self, parent, report_data, global_sufficient):
        super().__init__(parent)
        self.title("Calcolo Fabbisogno Commessa")
        self.geometry("800x600")
        self.minsize(750, 500)
        self.grab_set()
        
        self.report_data = report_data
        self.global_sufficient = global_sufficient
        
        # Colori coerenti con il tema principale
        self.bg_primary = "#f5f6fa"
        self.bg_card = "#ffffff"
        self.accent_color = "#273c75"
        self.accent_light = "#487eb0"
        self.text_color = "#2f3640"
        self.configure(bg=self.bg_primary)
        
        # Imposta lo stile per la tabella del fabbisogno a 32px (spaziatura confortevole ma non eccessiva)
        # e per evitare di alterare globalmente la tabella principale
        self.style = ttk.Style(self)
        self.style.configure("Fabbisogno.Treeview", font=("Segoe UI", 10), rowheight=32)
        self.style.configure("Fabbisogno.Treeview.Heading", font=("Segoe UI", 10, "bold"), background="#dcdde1", relief="flat")
        
        self._create_widgets()
        
        # Gestione chiusura della finestra
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        self.destroy()

    def _create_widgets(self):
        # 1. Banner in alto
        banner_bg = "#2ecc71" if self.global_sufficient else "#e74c3c"
        banner_text = (
            "✔ MAGAZZINO SUFFICIENTE\nTutto il materiale necessario per la commessa è disponibile in magazzino!"
            if self.global_sufficient else
            "⚠ MATERIALE INSUFFICIENTE\nAlcuni materiali sono insufficienti o non producibili con lo stock attuale!"
        )
        
        banner_frame = tk.Frame(self, bg=banner_bg, pady=15)
        banner_frame.pack(fill=tk.X)
        
        lbl_banner = tk.Label(
            banner_frame, text=banner_text, fg="#ffffff", bg=banner_bg,
            font=("Segoe UI", 11, "bold"), justify=tk.CENTER
        )
        lbl_banner.pack(fill=tk.X)
        
        # 2. Main content container
        content_frame = ttk.Frame(self, padding=15)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # PanedWindow per dividere la tabella e la casella di testo
        paned = tk.PanedWindow(content_frame, orient=tk.VERTICAL, bg=self.bg_primary, bd=0, sashwidth=4)
        paned.pack(fill=tk.BOTH, expand=True)
        
        # 2a. Frame Superiore (Tabella)
        frame_top = ttk.Frame(paned)
        paned.add(frame_top, stretch="always")
        
        # Titolo "Analisi Fabbisogno per Materiale" in un banner spazioso a contrasto
        title_frame = tk.Frame(frame_top, bg=self.accent_color, pady=8, padx=10)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        lbl_table_title = tk.Label(
            title_frame, text="Analisi Fabbisogno per Materiale",
            font=("Segoe UI", 11, "bold"), fg="#ffffff", bg=self.accent_color, anchor=tk.W
        )
        lbl_table_title.pack(fill=tk.X)
        
        # Frame contenitore per la tabella + scrollbar (risolve problemi di geometry propagation)
        table_container = ttk.Frame(frame_top)
        table_container.pack(fill=tk.BOTH, expand=True)
        
        # 3. Tabella Riepilogo (Treeview)
        cols = ("material", "demands", "residui", "pannelli", "barre", "unplaced", "status")
        self.tree = ttk.Treeview(table_container, columns=cols, show="headings", height=5)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.tree.heading("material", text="Materiale")
        self.tree.heading("demands", text="Pezzi Ordine")
        self.tree.heading("residui", text="Pezzi da Residui")
        self.tree.heading("pannelli", text="Barre (Stock / Da Tagliare)")
        self.tree.heading("barre", text="Pannelli (Stock / Da Acquistare)")
        self.tree.heading("unplaced", text="Non Producibili")
        self.tree.heading("status", text="Stato")
        
        self.tree.column("material", width=260, anchor=tk.W)
        self.tree.column("demands", width=80, anchor=tk.CENTER)
        self.tree.column("residui", width=110, anchor=tk.CENTER)
        self.tree.column("pannelli", width=180, anchor=tk.CENTER)
        self.tree.column("barre", width=180, anchor=tk.CENTER)
        self.tree.column("unplaced", width=100, anchor=tk.CENTER)
        self.tree.column("status", width=90, anchor=tk.CENTER)
        
        # Stili righe
        self.tree.tag_configure("insufficient", background="#ffe8e8", foreground="#c23616")
        self.tree.tag_configure("sufficient", background="#eef9ef", foreground="#27ae60")
        
        for item in self.report_data:
            mat_str = f"{item['thickness']}mm - {item['color_code']} ({item['color_desc']})"
            
            # Pezzi da residui
            residui_str = f"{item.get('pieces_from_residui', 0)} (Disp. {item.get('avail_residui', 0)})"
            
            # Pannelli (Stock / Da Tagliare)
            pannelli_str = f"{item.get('pannelli_real_used', 0)} / {item.get('pannelli_virtual_needed', 0)}"
            
            # Barre (Stock / Da Acquistare)
            barre_str = f"{item.get('total_barre_real_used', 0)} / {item.get('total_barre_virtual_needed', 0)}"
            
            unplaced_str = str(item["unplaced_count"])
            status_str = item["status"]
            
            tag = "insufficient" if item["status"] == "INSUFFICIENTE" else "sufficient"
            
            self.tree.insert("", tk.END, values=(
                mat_str,
                item["total_demands"],
                residui_str,
                pannelli_str,
                barre_str,
                unplaced_str,
                status_str
            ), tags=(tag,))
            
        # Scrollbar tabella (a fianco del Treeview)
        sc = ttk.Scrollbar(table_container, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sc.set)
        sc.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 2b. Frame Inferiore (Dettagli)
        frame_bottom = ttk.Frame(paned)
        paned.add(frame_bottom, stretch="always")
        
        # 4. Area Dettaglio Testuale (Rapporto descrittivo)
        text_title_frame = tk.Frame(frame_bottom, bg=self.accent_color, pady=6, padx=10)
        text_title_frame.pack(fill=tk.X, pady=(5, 5))
        lbl_text_title = tk.Label(
            text_title_frame, text="Dettaglio e Suggerimenti",
            font=("Segoe UI", 10, "bold"), fg="#ffffff", bg=self.accent_color, anchor=tk.W
        )
        lbl_text_title.pack(fill=tk.X)
        
        text_container = ttk.Frame(frame_bottom)
        text_container.pack(fill=tk.BOTH, expand=True)
        
        self.txt_summary = tk.Text(
            text_container, font=("Consolas", 9), bg="#ffffff", fg="#2f3640",
            wrap=tk.WORD, borderwidth=1, relief="solid", height=6
        )
        self.txt_summary.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        sc_text = ttk.Scrollbar(text_container, orient=tk.VERTICAL, command=self.txt_summary.yview)
        self.txt_summary.configure(yscrollcommand=sc_text.set)
        sc_text.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Genera il testo descrittivo
        self.summary_text = self._generate_summary_text()
        self.txt_summary.insert(tk.END, self.summary_text)
        self.txt_summary.config(state=tk.DISABLED) # Sola lettura
        
        # 5. Pulsanti di azione in basso
        btn_frame = ttk.Frame(content_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(
            btn_frame, text="Copia negli Appunti",
            command=self.copy_to_clipboard
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            btn_frame, text="Salva su File",
            command=self.save_to_file
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            btn_frame, text="Chiudi", style="Accent.TButton",
            command=self.on_close
        ).pack(side=tk.RIGHT, padx=5)
        
    def _generate_summary_text(self):
        lines = []
        lines.append("=====================================================================")
        lines.append("                RAPPORTO DI FABBISOGNO COMMESSA                     ")
        lines.append("=====================================================================\n")
        
        has_any_shortage = False
        for item in self.report_data:
            mat_str = f"{item['thickness']}mm {item['color_desc']} ({item['color_code']})"
            lines.append(f"Materiale: {mat_str}")
            lines.append(f"  - Pezzi richiesti in commessa: {item['total_demands']}")
            lines.append(f"  - [♻️ RESIDUI]: Pezzi prodotti da residui: {item.get('pieces_from_residui', 0)} (Residui disponibili in stock: {item.get('avail_residui', 0)})")
            
            # Pannelli (ora Barre)
            pannelli_real = item.get('pannelli_real_used', 0)
            pannelli_virt = item.get('pannelli_virtual_needed', 0)
            avail_pan = item.get('avail_pannelli', 0)
            lines.append(f"  - [📁 BARRE]: Barre necessarie alla produzione: {pannelli_real + pannelli_virt} totali")
            lines.append(f"    * Barre usate da stock in magazzino: {pannelli_real} (Disponibili: {avail_pan})")
            lines.append(f"    * Barre aggiuntive da ritagliare dai pannelli standard: {pannelli_virt}")
            
            # Barre standard (ora Pannelli standard)
            barre_real_direct = item.get('barre_real_used_direct', 0)
            barre_real_panels = item.get('barre_real_used_for_panels', 0)
            barre_virt_direct = item.get('barre_virtual_needed_direct', 0)
            barre_virt_panels = item.get('barre_virtual_needed_for_panels', 0)
            avail_barre = item.get('avail_barre', 0)
            
            total_real_bars = barre_real_direct + barre_real_panels
            total_virt_bars = barre_virt_direct + barre_virt_panels
            
            lines.append(f"  - [🪵 PANNELLI STANDARD]: Pannelli standard totali necessari: {total_real_bars + total_virt_bars} totali")
            lines.append(f"    * Pannelli in stock utilizzati: {total_real_bars} (Disponibili: {avail_barre})")
            lines.append(f"      - per pezzi finiti direttamente: {barre_real_direct}")
            lines.append(f"      - per ritagliare le barre virtuali: {barre_real_panels}")
            lines.append(f"    * Pannelli aggiuntivi [DEFICIT] da acquistare: {total_virt_bars}")
            if total_virt_bars > 0:
                has_any_shortage = True
                extra_parts = [f"{qty}x {b_id}" for b_id, qty in item["extra_needed"].items()]
                lines.append(f"      [DEFICIT DETTAGLIATO]: {', '.join(extra_parts)}")
                
            if item["unplaced_count"] > 0:
                has_any_shortage = True
                lines.append(f"  - [ATTENZIONE] Pezzi non producibili: {item['unplaced_count']}")
                for up in item.get("unplaced_list", []):
                    reason = up.get("unproducible_reason", "Mancano pannelli standard di riferimento o configurazione")
                    lines.append(f"    * {up['descrizione']} ({int(up['width_orig'])}x{int(up['height_orig'])}): {reason}")
                
            if total_virt_bars == 0 and item["unplaced_count"] == 0:
                lines.append("  - [OK] Materiale sufficiente.")
            lines.append("")
            
        lines.append("---------------------------------------------------------------------")
        if not has_any_shortage:
            lines.append("ESITO COMPLESSIVO: ✔ COMMESSA COMPLETAMENTE PRODUCIBILE")
            lines.append("Il magazzino contiene tutto il materiale necessario.")
        else:
            lines.append("ESITO COMPLESSIVO: ⚠ INSUFFICIENTE / ACQUISTI O TAGLI NECESSARI")
            lines.append("Provvedere all'approvvigionamento o al ritaglio dei materiali indicati sopra prima di procedere.")
        lines.append("=====================================================================")
        
        return "\n".join(lines)
        
    def copy_to_clipboard(self):
        self.clipboard_clear()
        self.clipboard_append(self.summary_text)
        messagebox.showinfo("Copia Completata", "Il report del fabbisogno è stato copiato negli appunti.")
        
    def save_to_file(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("File di testo", "*.txt"), ("Tutti i file", "*.*")],
            title="Salva Report Fabbisogno"
        )
        if not filepath:
            return
            
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(self.summary_text)
            messagebox.showinfo("Report Salvato", f"Il report del fabbisogno è stato salvato con successo in:\n{filepath}")
        except Exception as e:
            messagebox.showerror("Errore di Salvataggio", f"Impossibile salvare il file:\n{e}")

class LoadingDialog(tk.Toplevel):
    def __init__(self, parent, message="Elaborazione in corso. Attendere prego..."):
        super().__init__(parent)
        self.title("CutMob - Elaborazione")
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        
        w = 360
        h = 140
        
        try:
            parent.update_idletasks()
            parent_w = parent.winfo_width()
            parent_h = parent.winfo_height()
            parent_x = parent.winfo_rootx()
            parent_y = parent.winfo_rooty()
            x = parent_x + (parent_w - w) // 2
            y = parent_y + (parent_h - h) // 2
        except Exception:
            x = (self.winfo_screenwidth() - w) // 2
            y = (self.winfo_screenheight() - h) // 2
            
        self.geometry(f"{w}x{h}+{x}+{y}")
        
        bg_card = "#ffffff"
        accent_color = "#273c75"
        text_color = "#2f3640"
        
        self.configure(bg=accent_color)
        
        inner_frame = tk.Frame(self, bg=bg_card, bd=0)
        inner_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        lbl_title = tk.Label(
            inner_frame, 
            text="Elaborazione in corso", 
            font=("Segoe UI", 12, "bold"), 
            fg=accent_color, 
            bg=bg_card
        )
        lbl_title.pack(pady=(20, 5))
        
        lbl_msg = tk.Label(
            inner_frame, 
            text=message, 
            font=("Segoe UI", 10), 
            fg=text_color, 
            bg=bg_card
        )
        lbl_msg.pack(pady=(0, 15))
        
        self.progress = ttk.Progressbar(inner_frame, mode="indeterminate", length=280)
        self.progress.pack(pady=(0, 15))
        self.progress.start(10)
        
        self.grab_set()
        self.focus_set()
        self.update()

    def destroy(self):
        try:
            self.progress.stop()
        except Exception:
            pass
        super().destroy()

def make_sort_key(val):
    if not val:
        return (0, "")
    val_clean = str(val).strip()
    import re
    # Estrae tutti i numeri nella stringa (es. per dimensioni tipo 2800 x 2070)
    numbers = re.findall(r'\d+(?:\.\d+)?', val_clean)
    if len(numbers) >= 2:
        try:
            return (2, [float(num) for num in numbers])
        except ValueError:
            pass
    elif len(numbers) == 1:
        try:
            return (1, float(numbers[0]))
        except ValueError:
            pass
    return (0, val_clean.lower())

if __name__ == "__main__":
    root = tk.Tk()
    app = CutMobApp(root)
    root.mainloop()
