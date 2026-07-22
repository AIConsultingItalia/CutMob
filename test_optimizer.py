import os
import json
from data_manager import DataManager
from optimizer import CuttingOptimizer

def test_optimization():
    print("=== AVVIO TEST DI OTTIMIZZAZIONE CLASSICO ===")
    
    db_file = "test_database.json"
    if os.path.exists(db_file):
        os.remove(db_file)
        
    dm = DataManager(db_filename=db_file)
    
    barre = [
        {
            "id": "B1",
            "width": 2800.0,
            "height": 2070.0,
            "thickness": 18.0,
            "color_code": "U708",
            "color_desc": "Grigio",
            "has_grain": False
        }
    ]
    
    semilavorati = [
        {
            "id": "S1",
            "width": 2800.0,
            "height": 720.0,
            "thickness": 18.0,
            "color_code": "U708",
            "color_desc": "Grigio"
        }
    ]
    
    dm.set_barre(barre)
    dm.set_semilavorati(semilavorati)
    
    print("Database di test configurato correttamente.")
    
    demands = [
        {
            "descrizione": "Anta A",
            "width": 600.0,
            "height": 720.0,
            "thickness": 18.0,
            "color_code": "U708",
            "color_desc": "Grigio",
            "quantity": 3
        },
        {
            "descrizione": "Anta B",
            "width": 450.0,
            "height": 720.0,
            "thickness": 18.0,
            "color_code": "U708",
            "color_desc": "Grigio",
            "quantity": 2
        }
    ]
    
    stocks = dm.get_semilavorati() + dm.get_barre()
    
    opt = CuttingOptimizer(kerf=4.0)
    risultati = opt.optimize(stocks, demands, respect_grain=True)
    
    print("\nRisultati Ottimizzazione:")
    summary = risultati["summary_generale"]
    print(f"Area Lastre Totale: {summary['totale_area_lastre']} mm²")
    print(f"Area Pezzi Tagliati: {summary['totale_area_pezzi']} mm²")
    print(f"Area Scarto: {summary['totale_area_scarto']} mm²")
    print(f"Efficienza Media: {summary['efficienza_media']}%")
    
    for key, g in risultati["gruppi"].items():
        print(f"\nGruppo: {key}")
        print(f"Lastre usate: {len(g['used_boards'])}")
        print(f"Pezzi non piazzati: {len(g['unplaced_pieces'])}")
        
        for i, ub in enumerate(g["used_boards"]):
            print(f"  Lastra {i+1} (Tipo: {ub['board']['id']} - {ub['board']['width']}x{ub['board']['height']}):")
            print(f"    Efficienza lastra: {ub['efficiency']}%")
            print(f"    Pezzi posizionati:")
            for p in ub["placed_pieces"]:
                print(f"      - {p['descrizione']}: pos={p['x']},{p['y']} dim={p['w']}x{p['h']} (Ruotato: {p['rotated']})")
                
            for p in ub["placed_pieces"]:
                assert p['x'] + p['w'] <= ub['board']['width'], f"Pezzo {p['descrizione']} supera la larghezza della lastra!"
                assert p['y'] + p['h'] <= ub['board']['height'], f"Pezzo {p['descrizione']} supera l'altezza della lastra!"
                
        assert len(g['unplaced_pieces']) == 0, "Ci sono pezzi non piazzati, ma dovrebbero entrare tutti!"
        
    print("\n=== TEST CLASSICO COMPLETATO CON SUCCESSO! ===")
    
    if os.path.exists(db_file):
        os.remove(db_file)

def test_guillotine_and_semilavorati():
    print("\n=== AVVIO TEST FUNZIONALITA' AVANZATE (GUILLOTINE & SEMILAVORATI) ===")
    
    db_file = "test_adv_database.json"
    if os.path.exists(db_file):
        os.remove(db_file)
        
    dm = DataManager(db_filename=db_file)
    
    # 1. Configura barre standard grandi
    barre = [
        {
            "id": "B1",
            "width": 2000.0,
            "height": 1000.0,
            "thickness": 18.0,
            "color_code": "U708",
            "color_desc": "Grigio",
            "has_grain": False
        }
    ]
    dm.set_barre(barre)
    dm.set_semilavorati([])
    
    # Ordina pezzi che lasciano un grande spazio libero recuperabile
    # Ad esempio un pezzo da 1000 x 1000. 
    # Questo lascerà un rettangolo di 1000 x 1000 come scarto (che è > della dimensione min di recupero 300x300)
    demands = [
        {
            "descrizione": "Pannello Quadrato",
            "width": 1000.0,
            "height": 1000.0,
            "thickness": 18.0,
            "color_code": "U708",
            "color_desc": "Grigio",
            "quantity": 1
        }
    ]
    
    opt = CuttingOptimizer(kerf=4.0)
    
    # Esegui ottimizzazione con min_semilavorato 300x300
    risultati = opt.optimize(
        stocks=dm.get_barre(),
        demands=demands,
        respect_grain=True,
        min_semilavorato_width=300.0,
        min_semilavorato_height=300.0
    )
    
    # Verifica che ci sia un gruppo
    assert "18.0mm_U708" in risultati["gruppi"]
    gruppo = risultati["gruppi"]["18.0mm_U708"]
    
    assert len(gruppo["used_boards"]) == 1
    ub = gruppo["used_boards"][0]
    
    # Verifica che sia stato generato un semilavorato recuperabile di circa 996 x 1000 (considerando il kerf di 4)
    new_semis = ub.get("new_semilavorati", [])
    print(f"Nuovi semilavorati generati dal taglio: {new_semis}")
    assert len(new_semis) > 0, "Dovrebbe essere generato almeno un semilavorato di recupero!"
    
    # Verifica presenza dei tagli dell'algoritmo Guillotine
    assert "cuts" in ub, "La lastra usata deve contenere l'elenco dei tagli dell'algoritmo Guillotine!"
    print(f"Linee di taglio registrate: {ub['cuts']}")
    
    # 2. Testa la memorizzazione dei semilavorati (Consumo materiali)
    all_used = [ub]
    dm.consume_materials(all_used)
    
    # Verifica che la barra B1 sia stata consumata e che il suo residuo sia stato inserito in barre (Pannelli)
    barre_in_db = dm.get_barre()
    print(f"Pannelli registrati nel database dopo il consumo: {barre_in_db}")
    assert len(barre_in_db) == 1, "Il nuovo residuo del pannello B1 dovrebbe essere registrato in barre!"
    assert barre_in_db[0]["id"].startswith("S_REC_"), "Il residuo del pannello deve avere prefisso S_REC_!"
    
    # Verifica che il database dei semilavorati sia rimasto vuoto (perché B1 era originato da barre)
    semis_in_db = dm.get_semilavorati()
    assert len(semis_in_db) == 0, "Nessun residuo dovrebbe essere finito in semilavorati poichè il genitore B1 era un pannello!"
    
    # 3. Testa l'esportazione del report HTML
    report_file = "test_report.html"
    if os.path.exists(report_file):
        os.remove(report_file)
        
    success = dm.export_html_report(risultati, report_file)
    assert success
    assert os.path.exists(report_file), "Il file report HTML dovrebbe essere stato creato!"
    print("Report HTML generato con successo.")
    
    # Pulisci file temporanei
    if os.path.exists(db_file):
        os.remove(db_file)
    if os.path.exists(report_file):
        os.remove(report_file)
        
    print("\n=== TEST FUNZIONALITA' AVANZATE COMPLETATO CON SUCCESSO! ===")

def test_requirement_simulation():
    print("\n=== AVVIO TEST SIMULAZIONE FABBISOGNO ===")
    import copy
    
    # Grigio (18mm, U708) - 1x B1 (2000x1000) standard bar
    stocks = [
        {
            "id": "B1",
            "width": 2000.0,
            "height": 1000.0,
            "thickness": 18.0,
            "color_code": "U708",
            "color_desc": "Grigio",
            "has_grain": False,
            "quantity": 1
        }
    ]
    
    # Demands che richiedono 3x barre (totale 3 pezzi da 1000x1000)
    demands = [
        {
            "descrizione": "Pannello",
            "width": 1000.0,
            "height": 1000.0,
            "thickness": 18.0,
            "color_code": "U708",
            "color_desc": "Grigio",
            "quantity": 3
        }
    ]
    
    # Costruisci lo stock simulato (con 100 copie virtuali aggiuntive)
    simulated_stock = []
    # 1. Barre reali
    for b in stocks:
        qty = b.get("quantity", 1)
        for q in range(qty):
            item = copy.deepcopy(b)
            item["_source_type"] = "barre_real"
            simulated_stock.append(item)
            
    # 2. Barre virtuali
    for b in stocks:
        for q in range(100):
            item = copy.deepcopy(b)
            item["_source_type"] = "barre_virtual"
            simulated_stock.append(item)
            
    opt = CuttingOptimizer(kerf=4.0)
    risultati = opt.optimize(stocks=simulated_stock, demands=demands, respect_grain=True)
    
    # Analizza i risultati
    semis_used = 0
    barre_real_used = 0
    barre_virtual_used = 0
    
    for key, g in risultati["gruppi"].items():
        for ub in g["used_boards"]:
            src = ub["board"].get("_source_type")
            if src == "semi":
                semis_used += 1
            elif src == "barre_real":
                barre_real_used += 1
            elif src == "barre_virtual":
                barre_virtual_used += 1
                
    print(f"Barre reali usate: {barre_real_used} (attese: 1)")
    print(f"Barre virtuali usate (deficit): {barre_virtual_used} (attese: 2)")
    
    assert barre_real_used == 1, "Dovrebbe usare esattamente la barra reale disponibile!"
    assert barre_virtual_used == 2, "Dovrebbero servire 2 barre virtuali aggiuntive!"
    
    print("=== TEST SIMULAZIONE FABBISOGNO COMPLETATO CON SUCCESSO! ===")

def test_new_csv_format_and_duplicates():
    print("\n=== AVVIO TEST NUOVO FORMATO CSV E DUPLICATI ===")
    
    db_file = "test_csv_database.json"
    if os.path.exists(db_file):
        os.remove(db_file)
        
    dm = DataManager(db_filename=db_file)
    
    # 1. Creiamo un file CSV di test con il formato e i dati forniti dall'utente
    csv_content = """CodVariante;CodOpzione;NomeVariante;CodBarra;Tipologia;LarghezzaBarra_mm;AltezzaBarra_mm;SpessoreBarra_mm;Venatura;SfridoTaglio_mm
_FIN;01.A1.100;M. BIANCO;_FIN\\01.A1.100;MEL;2800;2070;22;Falso;0
_FIN;01.A1.101;M. OLIVA;_FIN\\01.A1.101;MEL;2800;2070;22;Falso;0
"""
    test_csv_path = "test_barre_new.csv"
    with open(test_csv_path, "w", encoding="utf-8") as f:
        f.write(csv_content)
        
    try:
        # Importa per la prima volta
        nuove_barre = dm.import_barre_csv(test_csv_path)
        assert len(nuove_barre) == 2
        
        # Verifica i campi mappati
        b1 = nuove_barre[0]
        assert b1["id"] == "_FIN\\01.A1.100"
        assert b1["width"] == 2800.0
        assert b1["height"] == 2070.0
        assert b1["thickness"] == 22.0
        assert b1["color_code"] == "_FIN\\01.A1.100"
        assert b1["color_desc"] == "M. BIANCO"
        assert b1["has_grain"] is False
        assert b1["quantity"] == 0
        
        # Imposta lo stock iniziale
        dm.set_barre(nuove_barre)
        
        # 2. Testiamo la logica dei duplicati (lato app)
        barre_in_db = dm.get_barre()
        assert len(barre_in_db) == 2
        
        # Prepariamo un secondo set di dati importati (ad esempio, re-importiamo lo stesso file)
        # ed una nuova barra.
        csv_content_with_new = """CodVariante;CodOpzione;NomeVariante;CodBarra;Tipologia;LarghezzaBarra_mm;AltezzaBarra_mm;SpessoreBarra_mm;Venatura;SfridoTaglio_mm
_FIN;01.A1.100;M. BIANCO;_FIN\\01.A1.100;MEL;2800;2070;22;Falso;0
_FIN;01.A1.102;M. NUOVA;_FIN\\01.A1.102;MEL;3000;2000;22;Vero;0
"""
        with open(test_csv_path, "w", encoding="utf-8") as f:
            f.write(csv_content_with_new)
            
        importate_2 = dm.import_barre_csv(test_csv_path)
        assert len(importate_2) == 2
        
        # Verifichiamo che la venatura 'Vero' sia impostata correttamente su True
        assert importate_2[1]["has_grain"] is True
        
        # Simuliamo la logica di deduplicazione presente in app.py
        chiavi_esistenti = {
            (b["id"], float(b["width"]), float(b["height"]), float(b["thickness"]))
            for b in barre_in_db
        }
        
        barre_da_aggiungere = []
        barre_gia_presenti_count = 0
        for nb in importate_2:
            nb_key = (nb["id"], float(nb["width"]), float(nb["height"]), float(nb["thickness"]))
            if nb_key not in chiavi_esistenti:
                barre_da_aggiungere.append(nb)
                chiavi_esistenti.add(nb_key)
            else:
                barre_gia_presenti_count += 1
                
        # Dovrebbe saltare il primo (BIANCO 2800x2070x22) e aggiungere solo il secondo (NUOVA 3000x2000x22)
        assert barre_gia_presenti_count == 1
        assert len(barre_da_aggiungere) == 1
        assert barre_da_aggiungere[0]["id"] == "_FIN\\01.A1.102"
        
        # Salva lo stock aggiornato
        dm.set_barre(barre_in_db + barre_da_aggiungere)
        assert len(dm.get_barre()) == 3
        
        print("=== TEST NUOVO FORMATO CSV E DUPLICATI COMPLETATO CON SUCCESSO! ===")
        
    finally:
        # Pulizia
        if os.path.exists(test_csv_path):
            os.remove(test_csv_path)
        if os.path.exists(db_file):
            os.remove(db_file)

def test_new_order_csv_format_and_alignment():
    print("\n=== AVVIO TEST NUOVO FORMATO CSV ORDINE E ALLINEAMENTO BARRE ===")
    
    db_file = "test_order_database.json"
    if os.path.exists(db_file):
        os.remove(db_file)
        
    dm = DataManager(db_filename=db_file)
    
    # 1. Creiamo un file CSV per le barre standard
    bar_csv_content = """CodVariante;CodOpzione;NomeVariante;CodBarra;Tipologia;LarghezzaBarra_mm;AltezzaBarra_mm;SpessoreBarra_mm;Venatura;SfridoTaglio_mm
_FIN;01.A3.114;M. CEMENTO GHIACCIO;_FIN\\01.A3.114;MEL;2800;2070;22;Falso;0
"""
    test_bar_csv = "test_barre_align.csv"
    with open(test_bar_csv, "w", encoding="utf-8") as f:
        f.write(bar_csv_content)
        
    # 2. Creiamo un file CSV per l'ordine
    order_csv_content = """COD_ART_COMP;DESCR;UM;SommaDiQUANT_DA_PROD;LUNGH_STDAG;LARG_STDAG;ALT_STDAG;FLAG_FUORI_MISURA;COL_NAME;COD_TAB;CodBarra;LACPVCIMP;RISPOSTE
000PT04908022A;ALLUNGO PER TAVOLO 49,5x80x22 MELAMINICO;NR;1;22;495;800;0;_FIN;01.A3.114;_FIN\\01.A3.114;MEL;M. CEMENTO GHIACCIO (LANDSCAPE)
"""
    test_order_csv = "test_order_align.csv"
    with open(test_order_csv, "w", encoding="utf-8") as f:
        f.write(order_csv_content)
        
    try:
        # Importiamo barre e ordini
        barre = dm.import_barre_csv(test_bar_csv)
        ordine = dm.import_csv(test_order_csv)
        
        # Verifichiamo correttezza del parsing delle barre
        assert len(barre) == 1
        b = barre[0]
        assert b["id"] == "_FIN\\01.A3.114"
        assert b["color_code"] == "_FIN\\01.A3.114"
        assert b["thickness"] == 22.0
        
        # Verifichiamo correttezza del parsing dell'ordine
        assert len(ordine) == 1
        o = ordine[0]
        assert o["descrizione"] == "ALLUNGO PER TAVOLO 49,5x80x22 MELAMINICO"
        assert o["thickness"] == 22.0
        assert o["width"] == 495.0
        assert o["height"] == 800.0
        assert o["quantity"] == 1
        assert o["color_code"] == "_FIN\\01.A3.114"
        assert o["color_desc"] == "M. CEMENTO GHIACCIO (LANDSCAPE)"
        
        # 3. Verifichiamo l'allineamento e l'ottimizzazione
        opt = CuttingOptimizer(kerf=4.0)
        # Impostiamo quantità = 1 per la barra a magazzino
        b["quantity"] = 1
        
        risultati = opt.optimize(stocks=[b], demands=ordine, respect_grain=True)
        
        # Verifichiamo che il gruppo sia stato creato e la domanda piazzata
        group_key = "22.0mm__FIN\\01.A3.114"
        assert group_key in risultati["gruppi"]
        
        gruppo = risultati["gruppi"][group_key]
        assert len(gruppo["used_boards"]) == 1
        assert len(gruppo["unplaced_pieces"]) == 0
        
        placed = gruppo["used_boards"][0]["placed_pieces"][0]
        assert placed["descrizione"] == "ALLUNGO PER TAVOLO 49,5x80x22 MELAMINICO"
        
        print("=== TEST NUOVO FORMATO CSV ORDINE E ALLINEAMENTO COMPLETATO CON SUCCESSO! ===")
        
    finally:
        # Pulisci file
        for p in [test_bar_csv, test_order_csv, db_file]:
            if os.path.exists(p):
                os.remove(p)

def test_pdf_export():
    print("\n=== AVVIO TEST ESPORTAZIONE REPORT PDF ===")
    
    db_file = "test_pdf_database.json"
    if os.path.exists(db_file):
        os.remove(db_file)
        
    dm = DataManager(db_filename=db_file)
    
    barre = [
        {
            "id": "B1",
            "width": 2800.0,
            "height": 2070.0,
            "thickness": 18.0,
            "color_code": "U708",
            "color_desc": "Grigio",
            "has_grain": False,
            "quantity": 1
        }
    ]
    dm.set_barre(barre)
    
    demands = [
        {
            "descrizione": "Anta A",
            "width": 600.0,
            "height": 720.0,
            "thickness": 18.0,
            "color_code": "U708",
            "color_desc": "Grigio",
            "quantity": 1
        }
    ]
    
    opt = CuttingOptimizer(kerf=4.0)
    risultati = opt.optimize(stocks=barre, demands=demands, respect_grain=True)
    
    # Crea percorso PDF di test
    test_pdf_path = f"test_export_report_{os.getpid()}.pdf"
    try:
        if os.path.exists(test_pdf_path):
            os.remove(test_pdf_path)
    except Exception:
        pass
        
    try:
        success = dm.export_pdf_report(risultati, test_pdf_path)
        assert success, "La generazione del PDF dovrebbe aver avuto successo!"
        assert os.path.exists(test_pdf_path), "Il file PDF esportato deve esistere su disco!"
        
        print("=== TEST ESPORTAZIONE REPORT PDF COMPLETATO CON SUCCESSO! ===")
        
    finally:
        # Pulisci file
        for p in [test_pdf_path, db_file]:
            try:
                if os.path.exists(p):
                    os.remove(p)
            except Exception:
                pass

def test_semilavorati_csv_import():
    print("\n=== AVVIO TEST IMPORTAZIONE CSV SEMILAVORATI CON NUOVO FORMATO ===")
    
    db_file = "test_semi_csv_database.json"
    if os.path.exists(db_file):
        os.remove(db_file)
        
    dm = DataManager(db_filename=db_file)
    
    # 1. Creiamo un file CSV di test per i semilavorati
    csv_content = """CodPannello;Altezza_mm;Larghezza_mm;Spessore_mm;Venatura;CodVariante;CodOpzione;CodBarra;NomeVariante;Note
1;1197;2800;22;Falso;_FIN;01.A1.100;_FIN\\01.A1.100;M. BIANCO;
1;1197;2800;22;Falso;_FIN;01.A1.100;_FIN\\01.A1.100;M. BIANCO;
1;1000;2000;22;Vero;_FIN;01.A1.101;_FIN\\01.A1.101;M. OLIVA;
"""
    test_csv_path = "test_semilavorati_new.csv"
    with open(test_csv_path, "w", encoding="utf-8") as f:
        f.write(csv_content)
        
    try:
        # Importa
        nuovi_semis = dm.import_semilavorati_csv(test_csv_path)
        
        # Dovrebbero esserci 2 semilavorati distinti dopo l'aggregazione (1 per BIANCO 2800x1197 con qty 2, 1 per OLIVA 2000x1000 con qty 1)
        assert len(nuovi_semis) == 2, f"Attesi 2 semilavorati, trovati {len(nuovi_semis)}"
        
        # Ordina per id/dim per facilitare i controlli
        nuovi_semis.sort(key=lambda s: s["width"])
        
        s_oliva = nuovi_semis[0]  # width = 1000
        s_bianco = nuovi_semis[1] # width = 1197
        
        # Verifica oliva (con venatura)
        assert s_oliva["width"] == 1000.0
        assert s_oliva["height"] == 2000.0
        assert s_oliva["thickness"] == 22.0
        assert s_oliva["color_code"] == "_FIN\\01.A1.101"
        assert s_oliva["color_desc"] == "M. OLIVA"
        assert s_oliva["has_grain"] is True
        assert s_oliva["quantity"] == 0
        assert s_oliva["id"] == "_FIN_01.A1.101_1000x2000"
        
        # Verifica bianco (aggregato con quantità 0)
        assert s_bianco["width"] == 1197.0
        assert s_bianco["height"] == 2800.0
        assert s_bianco["thickness"] == 22.0
        assert s_bianco["color_code"] == "_FIN\\01.A1.100"
        assert s_bianco["color_desc"] == "M. BIANCO"
        assert s_bianco["has_grain"] is False
        assert s_bianco["quantity"] == 0
        assert s_bianco["id"] == "_FIN_01.A1.100_1197x2800"
        
        # 2. Testiamo la logica di unione/sostituzione lato app (simulata)
        # Inizializziamo database con un semilavorato esistente
        esistente = {
            "id": "_FIN_01.A1.100_1197x2800",
            "width": 1197.0,
            "height": 2800.0,
            "thickness": 22.0,
            "color_code": "_FIN\\01.A1.100",
            "color_desc": "M. BIANCO",
            "has_grain": False,
            "quantity": 5
        }
        dm.set_semilavorati([esistente])
        
        # Simuliamo l'unione (scelta = Sì)
        semis_db = dm.get_semilavorati()
        semis_dict = {s["id"]: s for s in semis_db}
        for ns in nuovi_semis:
            if ns["id"] in semis_dict:
                semis_dict[ns["id"]]["quantity"] = semis_dict[ns["id"]].get("quantity", 1) + ns["quantity"]
            else:
                semis_dict[ns["id"]] = ns
                
        dm.set_semilavorati(list(semis_dict.values()))
        semis_finali = dm.get_semilavorati()
        
        assert len(semis_finali) == 2
        semis_finali.sort(key=lambda s: s["width"])
        
        # Il bianco deve avere quantità 5 + 0 = 5
        assert semis_finali[1]["id"] == "_FIN_01.A1.100_1197x2800"
        assert semis_finali[1]["quantity"] == 5
        
        print("=== TEST IMPORTAZIONE CSV SEMILAVORATI COMPLETATO CON SUCCESSO! ===")
        
    finally:
        for p in [test_csv_path, db_file]:
            if os.path.exists(p):
                os.remove(p)

def test_remnants_prioritization_and_exclusion():
    print("\n=== AVVIO TEST PRIORITIZZAZIONE E SELEZIONE CHECKBOX (S_REC_) ===")
    
    from app import CutMobApp
    import tkinter as tk
    import copy
    
    # Avviamo root tkinter fittizio (necessario per CutMobApp)
    root = tk.Tk()
    root.withdraw() # Nascondi la finestra
    
    app = CutMobApp(root)
    app.ent_sfrido.delete(0, tk.END)
    app.ent_sfrido.insert(0, "0")
    app.ent_kerf.delete(0, tk.END)
    app.ent_kerf.insert(0, "4.0")
    
    # Prepariamo semilavorati di test:
    # 1 residuo (S_REC_) e 1 pannello pre-tagliato (S_PANEL)
    test_semis = [
        {"id": "S_PANEL_1", "width": 1000.0, "height": 500.0, "thickness": 18.0, "color_code": "U708", "color_desc": "Grigio", "quantity": 1},
        {"id": "S_REC_1", "width": 800.0, "height": 400.0, "thickness": 18.0, "color_code": "U708", "color_desc": "Grigio", "quantity": 1}
    ]
    test_barre = [
        {"id": "B1", "width": 2800.0, "height": 2070.0, "thickness": 18.0, "color_code": "U708", "color_desc": "Grigio", "quantity": 1}
    ]
    
    import tkinter.messagebox as msgbox
    original_showinfo = msgbox.showinfo
    msgbox.showinfo = lambda title, message: None
    
    app.data_manager.get_semilavorati = lambda: test_semis
    app.data_manager.get_barre = lambda: test_barre
    
    # Mock dell'ottimizzatore
    captured_stocks = []
    def mock_optimize(stocks, demands, respect_grain, min_semilavorato_width, min_semilavorato_height, **kwargs):
        nonlocal captured_stocks
        captured_stocks = stocks
        return {"gruppi": {}, "summary_generale": {"efficienza_media": 0, "totale_area_lastre": 0, "totale_area_pezzi": 0, "totale_area_scarto": 0}}
        
    app.optimizer.optimize = mock_optimize
    app.current_order = [{"descrizione": "Pezzo", "width": 100.0, "height": 100.0, "thickness": 18.0, "color_code": "U708", "color_desc": "Grigio", "quantity": 1}]
    
    try:
        # Caso 1: Selezionati tutti e tre (Residuo, Pannello, Barra)
        app.var_stock_residuo.set(True)
        app.var_stock_pannello.set(True)
        app.var_stock_barra.set(True)
        
        captured_stocks = []
        app.run_optimization()
        
        assert len(captured_stocks) == 3
        # L'ordine deve essere: Residuo -> Pannello -> Barra
        assert captured_stocks[0]["id"] == "S_REC_1"
        assert captured_stocks[1]["id"] == "S_PANEL_1"
        assert captured_stocks[2]["id"] == "B1"
        
        # Caso 2: Solo Residuo selezionato
        app.var_stock_residuo.set(True)
        app.var_stock_pannello.set(False)
        app.var_stock_barra.set(False)
        
        captured_stocks = []
        app.run_optimization()
        
        assert len(captured_stocks) == 1
        assert captured_stocks[0]["id"] == "S_REC_1"
        
        # Caso 3: Solo Pannello e Barra selezionati
        app.var_stock_residuo.set(False)
        app.var_stock_pannello.set(True)
        app.var_stock_barra.set(True)
        
        captured_stocks = []
        app.run_optimization()
        
        assert len(captured_stocks) == 2
        assert captured_stocks[0]["id"] == "S_PANEL_1"
        assert captured_stocks[1]["id"] == "B1"
        
        print("=== TEST PRIORITIZZAZIONE E SELEZIONE CHECKBOX COMPLETATO CON SUCCESSO! ===")
    finally:
        msgbox.showinfo = original_showinfo
        root.destroy()

def test_panel_production():
    print("\n=== AVVIO TEST PRODUZIONE PANNELLI (Barre->Pannelli) ===")
    import tkinter as tk
    from tkinter import messagebox
    from app import CutMobApp
    import os
    import json
    
    root = tk.Tk()
    root.withdraw()
    
    app = CutMobApp(root)
    app.ent_sfrido.delete(0, tk.END)
    app.ent_sfrido.insert(0, "0")
    app.ent_kerf.delete(0, tk.END)
    app.ent_kerf.insert(0, "4.0")
    
    # Crea un database temporaneo controllato
    test_db = {
        "barre": [
            {
                "id": "B_PROD_1",
                "width": 2800.0,
                "height": 2070.0,
                "thickness": 18.0,
                "color_code": "TEST_COLOR",
                "color_desc": "Test Desc",
                "has_grain": False,
                "quantity": 2
            }
        ],
        "semilavorati": [
            {
                "id": "S_PROD_PANEL",
                "width": 1200.0,
                "height": 600.0,
                "thickness": 18.0,
                "color_code": "TEST_COLOR",
                "color_desc": "Test Desc",
                "has_grain": True,
                "quantity": 1
            }
        ],
        "ordine": []
    }
    
    # Sovrascrivi il db dell'applicazione
    original_db_path = app.data_manager.db_path
    app.data_manager.db_path = os.path.join(os.path.dirname(original_db_path), "test_db_prod.json")
    with open(app.data_manager.db_path, "w", encoding="utf-8") as f:
        json.dump(test_db, f, indent=4)
        
    app.reload_magazzino_tables()
    
    try:
        # Mock showinfo e askyesno
        original_showinfo = messagebox.showinfo
        original_askyesno = messagebox.askyesno
        messagebox.showinfo = lambda title, message: None
        messagebox.askyesno = lambda title, message: True
        
        # 1. Aggiungi pannello da produrre
        # Aggiungiamo 2 pannelli di dimensioni 1200x600 alla lista di produzione
        app.panel_production_list = [
            {
                "thickness": 18.0,
                "color_code": "TEST_COLOR",
                "color_desc": "Test Desc",
                "width": 1200.0,
                "height": 600.0,
                "quantity_to_produce": 2
            }
        ]
        
        # 2. Calcola fabbisogno
        app.calculate_prod_requirements()
        
        # Le barre usate devono essere 1 (dato che 2 pannelli 1200x600 c'entrano abbondantemente in una barra 2800x2070)
        assert app.optimization_results is not None
        assert "18.0mm_TEST_COLOR" in app.optimization_results["gruppi"]
        g_res = app.optimization_results["gruppi"]["18.0mm_TEST_COLOR"]
        assert len(g_res["used_boards"]) == 1
        
        # 3. Consuma materiali
        app.consume_prod_materials()
        
        # Controlla database aggiornato
        updated_db = app.data_manager.load_db()
        
        # La barra B_PROD_1 deve avere quantità 1 (era 2, decrementata di 1)
        barre_aggiornate = updated_db["barre"]
        assert len(barre_aggiornate) == 1
        assert barre_aggiornate[0]["quantity"] == 1
        
        # Il pannello S_PROD_PANEL deve avere quantità 3 (era 1, incrementata di 2)
        semis_aggiornati = updated_db["semilavorati"]
        assert len(semis_aggiornati) == 1
        assert semis_aggiornati[0]["quantity"] == 3
        
        print("=== TEST PRODUZIONE PANNELLI COMPLETATO CON SUCCESSO! ===")
    finally:
        messagebox.showinfo = original_showinfo
        messagebox.askyesno = original_askyesno
        if os.path.exists(app.data_manager.db_path):
            os.remove(app.data_manager.db_path)
        app.data_manager.db_path = original_db_path
        root.destroy()

def test_commesse_persistence():
    print("\n=== AVVIO TEST GESTIONE E PERSISTENZA COMMESSE ===")
    
    db_file = "test_commesse_database.json"
    dm = DataManager(db_file)
    
    try:
        # Pulisce DB
        dm.db = {"barre": [], "semilavorati": [], "commesse": []}
        dm.save_db()
        
        # 1. Salva nuova commessa
        pezzi = [
            {"descrizione": "Pezzo A", "width": 500.0, "height": 300.0, "thickness": 18.0, "color_code": "C1", "color_desc": "Bianco", "quantity": 2}
        ]
        commessa = dm.save_commessa(None, "Commessa Cucina", pezzi)
        
        assert commessa["id"] == 1
        assert commessa["nome"] == "Commessa Cucina"
        assert commessa["stato"] == "Aperta"
        assert len(commessa["pezzi"]) == 1
        
        # 2. Verifica che sia presente nell'elenco
        commesse = dm.get_commesse()
        assert len(commesse) == 1
        assert commesse[0]["nome"] == "Commessa Cucina"
        
        # 3. Aggiorna commessa esistente
        pezzi_aggiornati = pezzi + [
            {"descrizione": "Pezzo B", "width": 600.0, "height": 400.0, "thickness": 18.0, "color_code": "C1", "color_desc": "Bianco", "quantity": 1}
        ]
        commessa_aggiornata = dm.save_commessa(1, "Commessa Cucina V2", pezzi_aggiornati)
        
        assert commessa_aggiornata["id"] == 1
        assert commessa_aggiornata["nome"] == "Commessa Cucina V2"
        assert len(commessa_aggiornata["pezzi"]) == 2
        
        # 4. Chiudi commessa
        dm.close_commessa(1)
        commesse_dopo_chiusura = dm.get_commesse()
        assert commesse_dopo_chiusura[0]["stato"] == "Chiusa"
        
        # 5. Verifica che non sia modificabile
        try:
            dm.save_commessa(1, "Tentativo Modifica", pezzi)
            assert False, "Dovrebbe sollevare ValueError per commessa chiusa"
        except ValueError:
            pass # Successo, ha impedito la modifica
            
        # 6. Elimina commessa
        dm.delete_commessa(1)
        commesse_dopo_eliminazione = dm.get_commesse()
        assert len(commesse_dopo_eliminazione) == 0
        
        print("=== TEST GESTIONE E PERSISTENZA COMMESSE COMPLETATO CON SUCCESSO! ===")
    finally:
        if os.path.exists(dm.db_path):
            os.remove(dm.db_path)

def test_bar_height_alignment():
    print("\n=== AVVIO TEST ALLINEAMENTO ALTEZZA BARRE STANDARD ===")
    import tkinter as tk
    from tkinter import messagebox
    import app as app_mod
    from app import CutMobApp
    import os
    import json
    
    root = tk.Tk()
    root.withdraw()
    
    # Mock dei dialoghi per evitare il blocco della UI
    class MockDialog:
        def __init__(self, *args, **kwargs):
            pass
        def destroy(self):
            pass
            
    original_loading = app_mod.LoadingDialog
    original_fabbisogno = app_mod.FabbisognoDialog
    app_mod.LoadingDialog = MockDialog
    app_mod.FabbisognoDialog = MockDialog
    
    original_showinfo = messagebox.showinfo
    original_askyesno = messagebox.askyesno
    messagebox.showinfo = lambda title, message: None
    messagebox.askyesno = lambda title, message: True
    
    # 1. Configurazione database temporaneo
    # Abbiamo standard bar heights (semilavorati) in archivio per TEST_COLOR di 18mm: 397 e 717
    # Abbiamo standard board (barra) B1 di 2800x2070
    test_db = {
        "barre": [
            {
                "id": "B1",
                "width": 2800.0,
                "height": 2070.0,
                "thickness": 18.0,
                "color_code": "TEST_COLOR",
                "color_desc": "Test Desc",
                "has_grain": False,
                "quantity": 1
            }
        ],
        "semilavorati": [
            {
                "id": "BARRA_STD_397",
                "width": 2800.0,
                "height": 397.0,
                "thickness": 18.0,
                "color_code": "TEST_COLOR",
                "color_desc": "Test Desc",
                "has_grain": False,
                "quantity": 0  # Standard template
            },
            {
                "id": "BARRA_STD_717",
                "width": 2800.0,
                "height": 717.0,
                "thickness": 18.0,
                "color_code": "TEST_COLOR",
                "color_desc": "Test Desc",
                "has_grain": False,
                "quantity": 0  # Standard template
            }
        ],
        "commesse": []
    }
    
    app = CutMobApp(root)
    app.ent_sfrido.delete(0, tk.END)
    app.ent_sfrido.insert(0, "0")
    app.ent_kerf.delete(0, tk.END)
    app.ent_kerf.insert(0, "4.0")
    original_db_path = app.data_manager.db_path
    app.data_manager.db_path = os.path.join(os.path.dirname(original_db_path), "test_db_align.json")
    
    with open(app.data_manager.db_path, "w", encoding="utf-8") as f:
        json.dump(test_db, f, indent=4)
        
    app.reload_magazzino_tables()
    
    try:
        # Caso: use_barra = False, use_pannello = True (Usa magazzino Barre (📁) in UI abilitato, disabilita gli altri)
        # Ordiniamo un pezzo fuori misura di larghezza 394 (dovrebbe allinearsi alla barra standard 397)
        app.current_order = [
            {
                "descrizione": "Anta Fuori Misura",
                "width": 394.0,
                "height": 600.0,
                "thickness": 18.0,
                "color_code": "TEST_COLOR",
                "color_desc": "Test Desc",
                "quantity": 1
            }
        ]
        
        # Abilitiamo l'uso delle Barre (use_pannello) e disabilitiamo il resto per pulizia
        app.var_stock_residuo.set(False)
        app.var_stock_pannello.set(True)  # Barra (📁) in UI
        app.var_stock_barra.set(False)   # Pannello (🪵) in UI
        
        app.calculate_requirements()
        
        # Verifichiamo che la barra virtuale usata nel primo passaggio abbia altezza 397 (allineata) e non 394
        assert app.optimization_results is not None
        g_res = app.optimization_results["gruppi"]["18.0mm_TEST_COLOR"]
        
        used_boards = g_res["used_boards"]
        # Ci deve essere la barra virtuale prodotta o usata
        # E la sua altezza deve essere 397!
        virtual_pannelli = [ub for ub in used_boards if ub["board"].get("_source_type") == "pannello_virtual"]
        assert len(virtual_pannelli) > 0, "Dovrebbe esserci almeno una barra virtuale di primo passaggio!"
        
        for vp in virtual_pannelli:
            assert vp["board"]["height"] == 397.0, f"L'altezza della barra virtuale dovrebbe essere 397.0, trovata {vp['board']['height']}"
            
        print("=== TEST ALLINEAMENTO ALTEZZA BARRE STANDARD COMPLETATO CON SUCCESSO! ===")
        
    finally:
        # Ripristino dei mock e pulizia file
        app_mod.LoadingDialog = original_loading
        app_mod.FabbisognoDialog = original_fabbisogno
        messagebox.showinfo = original_showinfo
        messagebox.askyesno = original_askyesno
        if os.path.exists(app.data_manager.db_path):
            os.remove(app.data_manager.db_path)
        app.data_manager.db_path = original_db_path
        root.destroy()

def test_tall_pieces_routing_to_panels():
    """
    Test che verifica la corretta gestione delle altezze superiori alla massima altezza standard delle barre.
    - Gli elementi con altezza <= max_std_height devono essere allineati all'altezza standard successiva e tagliati da barre virtuali.
    - Gli elementi con altezza > max_std_height devono indurre l'attivazione automatica del pannello e venire tagliati da esso direttamente.
    """
    print("\n=== AVVIO TEST PASSAGGIO DI PEZZI ALTI AI PANNELLI ===")
    
    # 1. Configurazione mock app e database di test
    import tkinter as tk
    from tkinter import messagebox
    import app as app_mod
    from app import CutMobApp
    
    root = tk.Tk()
    root.withdraw()
    
    app = CutMobApp(root)
    app.ent_sfrido.delete(0, tk.END)
    app.ent_sfrido.insert(0, "0")
    app.ent_kerf.delete(0, tk.END)
    app.ent_kerf.insert(0, "4.0")
    original_db_path = app.data_manager.db_path
    
    test_db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_db_tall_routing.json")
    app.data_manager.db_path = test_db_path
    
    # Configuriamo il database di test con venatura attiva per impedire la rotazione
    test_db = {
        "barre": [
            {
                "id": "TEMPLATE_BARRA",
                "width": 2800.0,
                "height": 2070.0,
                "thickness": 22.0,
                "color_code": "TEST_COLOR",
                "color_desc": "TEST DESC",
                "has_grain": True,
                "quantity": 0
            }
        ],
        "semilavorati": [
            {
                "id": "SEMI_397",
                "width": 2800.0,
                "height": 397.0,
                "thickness": 22.0,
                "color_code": "TEST_COLOR",
                "color_desc": "TEST DESC",
                "has_grain": True,
                "quantity": 0
            },
            {
                "id": "SEMI_717",
                "width": 2800.0,
                "height": 717.0,
                "thickness": 22.0,
                "color_code": "TEST_COLOR",
                "color_desc": "TEST DESC",
                "has_grain": True,
                "quantity": 0
            }
        ],
        "commesse": []
    }
    
    with open(test_db_path, "w", encoding="utf-8") as f:
        json.dump(test_db, f, indent=4)
        
    app.data_manager.db = app.data_manager.load_db()
    
    # 2. Configurazione ordine (commessa) di test
    app.current_order = [
        {
            "descrizione": "Anta standard",
            "width": 394.0,
            "height": 500.0,
            "thickness": 22.0,
            "color_code": "TEST_COLOR",
            "color_desc": "TEST DESC",
            "quantity": 1
        },
        {
            "descrizione": "Fianco alto",
            "width": 1500.0,
            "height": 500.0,
            "thickness": 22.0,
            "color_code": "TEST_COLOR",
            "color_desc": "TEST DESC",
            "quantity": 1
        }
    ]
    
    # Selezioniamo solo Barra (📁) [use_pannello=True], escludiamo Pannello (🪵) [use_barra=False]
    app.var_stock_residuo.set(False)
    app.var_stock_pannello.set(True)  # Barra (📁)
    app.var_stock_barra.set(False)    # Pannello (🪵) - disattivato!
    
    # Mock dei dialoghi di output
    original_loading = app_mod.LoadingDialog
    original_fabbisogno = app_mod.FabbisognoDialog
    original_showinfo = messagebox.showinfo
    original_askyesno = messagebox.askyesno
    
    class MockLoading:
        def __init__(self, *args, **kwargs): pass
        def update_progress(self, *args): pass
        def destroy(self): pass
        
    app_mod.LoadingDialog = MockLoading
    messagebox.showinfo = lambda *args: None
    messagebox.askyesno = lambda *args: False
    
    fabbisogno_chiamato = False
    fabbisogno_data = None
    
    class MockFabbisogno:
        def __init__(self, *args, **kwargs):
            nonlocal fabbisogno_chiamato, fabbisogno_data
            fabbisogno_chiamato = True
            fabbisogno_data = args[1]
            
    app_mod.FabbisognoDialog = MockFabbisogno
    
    try:
        app.calculate_requirements()
        
        assert fabbisogno_chiamato is True
        
        assert len(fabbisogno_data) == 1
        group_rep = fabbisogno_data[0]
        
        # Può essere 0 o 1 a seconda se il pezzo piccolo è ottimizzato nello spazio residuo del pannello
        assert group_rep["pannelli_virtual_needed"] >= 0
        assert group_rep["unplaced_count"] == 0
        
        # Il pezzo da 1500 deve essere andato direttamente sul pannello (barra_virtual)
        assert group_rep["barre_virtual_needed_direct"] == 1
        
        print("=== TEST PASSAGGIO DI PEZZI ALTI AI PANNELLI COMPLETATO CON SUCCESSO! ===")
        
    finally:
        # Ripristino dei mock e pulizia file
        app_mod.LoadingDialog = original_loading
        app_mod.FabbisognoDialog = original_fabbisogno
        messagebox.showinfo = original_showinfo
        messagebox.askyesno = original_askyesno
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
        app.data_manager.db_path = original_db_path
        root.destroy()

def test_standard_bar_height_constraint():
    print("\n=== AVVIO TEST VINCOLO ALTEZZE STANDARD NELL'OTTIMIZZATORE ===")
    from optimizer import CuttingOptimizer
    import copy
    opt = CuttingOptimizer(kerf=4.0)
    
    # Abbiamo barre standard a magazzino di altezza 897 e 1197
    stocks = [
        {
            "id": "BAR_897",
            "width": 2800.0,
            "height": 897.0,
            "thickness": 22.0,
            "color_code": "WHITE",
            "color_desc": "White",
            "stock_type": "semilavorato_bar",
            "quantity": 1
        },
        {
            "id": "BAR_1197",
            "width": 2800.0,
            "height": 1197.0,
            "thickness": 22.0,
            "color_code": "WHITE",
            "color_desc": "White",
            "stock_type": "semilavorato_bar",
            "quantity": 1
        }
    ]
    
    # Chiediamo di posizionare un pezzo di larghezza 897
    demands = [
        {
            "descrizione": "Pezzo 897",
            "width": 897.0,
            "height": 600.0,
            "thickness": 22.0,
            "color_code": "WHITE",
            "color_desc": "White",
            "quantity": 1
        }
    ]
    
    # Altezze standard per il gruppo WHITE (che rappresentano le larghezze delle barre standard)
    group_std_heights = {
        "22.0mm_WHITE": [897.0, 1197.0]
    }
    
    # Se ottimizziamo con il vincolo sulle altezze standard:
    # Il pezzo 897 NON deve finire sulla barra 1197. Deve finire sulla barra 897.
    # Proviamo ad ottimizzare.
    res = opt.optimize(stocks, demands, respect_grain=True, group_std_heights=group_std_heights)
    
    g_res = res["gruppi"]["22.0mm_WHITE"]
    used_boards = g_res["used_boards"]
    
    assert len(used_boards) == 1, f"Dovrebbe essere usata una sola barra, usate {len(used_boards)}"
    used_board = used_boards[0]["board"]
    assert used_board["id"] == "BAR_897", f"Il pezzo 897 dovrebbe essere posizionato sulla barra BAR_897, posizionato su {used_board['id']}"
    
    # Caso 2: Un pezzo di larghezza 899 (fuori misura rispetto a 897, quindi deve andare sulla 1197)
    stocks_2 = copy.deepcopy(stocks)
    demands_2 = [
        {
            "descrizione": "Pezzo 899",
            "width": 899.0,
            "height": 600.0,
            "thickness": 22.0,
            "color_code": "WHITE",
            "color_desc": "White",
            "quantity": 1
        }
    ]
    res_2 = opt.optimize(stocks_2, demands_2, respect_grain=True, group_std_heights=group_std_heights)
    g_res_2 = res_2["gruppi"]["22.0mm_WHITE"]
    used_boards_2 = g_res_2["used_boards"]
    assert len(used_boards_2) == 1
    used_board_2 = used_boards_2[0]["board"]
    assert used_board_2["id"] == "BAR_1197", f"Il pezzo 899 dovrebbe essere posizionato sulla barra BAR_1197, posizionato su {used_board_2['id']}"
    print("=== TEST VINCOLO ALTEZZE STANDARD COMPLETATO CON SUCCESSO! ===")

def test_filtering_and_f3_optimization():
    """
    Test che verifica il filtraggio F2 delle tabelle e l'ottimizzazione F3
    su parte selezionata / filtrata delle commesse.
    """
    print("\n=== AVVIO TEST FILTRAGGIO F2 E OTTIMIZZAZIONE F3 ===")
    import tkinter as tk
    from tkinter import messagebox
    from app import CutMobApp
    
    root = tk.Tk()
    root.withdraw()
    
    app = CutMobApp(root)
    app.ent_sfrido.delete(0, tk.END)
    app.ent_sfrido.insert(0, "0")
    app.ent_kerf.delete(0, tk.END)
    app.ent_kerf.insert(0, "4.0")
    original_db_path = app.data_manager.db_path
    test_db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_db_filtering.json")
    app.data_manager.db_path = test_db_path
    
    with open(test_db_path, "w", encoding="utf-8") as f:
        json.dump({"barre": [], "semilavorati": [], "commesse": []}, f)
    app.data_manager.db = app.data_manager.load_db()
    
    # 1. Testiamo la struttura iniziale dei filtri di colonna
    assert app.filters_barre == {}
    assert app.filters_semi == {}
    assert app.filters_commesse == {}
    
    # Popoliamo il database con barre note
    test_barre = [
        {"id": "B_X", "width": 2800.0, "height": 2070.0, "thickness": 18.0, "color_code": "RED", "color_desc": "Rosso", "quantity": 10},
        {"id": "B_Y", "width": 2800.0, "height": 2070.0, "thickness": 18.0, "color_code": "BLUE", "color_desc": "Blu", "quantity": 10}
    ]
    app.data_manager.set_barre(test_barre)
    
    # Ricarica tabelle e verifica presenza di entrambe
    app.reload_magazzino_tables()
    assert len(app.tree_barre.get_children()) == 2
    
    # Applichiamo un filtro di colonna "color_desc" -> "ross"
    app.filters_barre["color_desc"] = "ross"
    app.reload_magazzino_tables()
    # Ora dovrebbe essere visibile solo B_X
    items = app.tree_barre.get_children()
    assert len(items) == 1
    vals = app.tree_barre.item(items[0], "values")
    assert vals[0] == "B_X"
    
    # Reset filtro
    app.filters_barre = {}
    app.reload_magazzino_tables()
    
    # 2. Testiamo la logica di F3 (righe verdi) su tree_pieces
    app.current_order = [
        {"descrizione": "Pezzo A", "width": 400.0, "height": 720.0, "thickness": 18.0, "color_code": "RED", "color_desc": "Rosso", "quantity": 1},
        {"descrizione": "Pezzo B", "width": 600.0, "height": 720.0, "thickness": 18.0, "color_code": "RED", "color_desc": "Rosso", "quantity": 1}
    ]
    app.reload_order_table()
    piece_items = app.tree_pieces.get_children()
    assert len(piece_items) == 2
    
    # Selezioniamo il primo pezzo e premiamo F3 (toggle green)
    app.tree_pieces.selection_set(piece_items[0])
    app.toggle_pieces_green()
    
    # Verifica che il primo pezzo sia contrassegnato come is_green=True
    assert app.current_order[0]["is_green"] is True
    assert app.current_order[1].get("is_green", False) is False
    
    # Ricarichiamo e verifichiamo che l'elemento visualizzato abbia il tag green_item
    app.reload_order_table()
    piece_items = app.tree_pieces.get_children()
    assert "green_item" in app.tree_pieces.item(piece_items[0], "tags")
    assert "green_item" not in app.tree_pieces.item(piece_items[1], "tags")
    
    # 3. Testiamo che l'ottimizzazione venga fatta esclusivamente sul pezzo verde
    # Mockiamo optimize dell'ottimizzatore per verificare cosa viene passato
    original_optimize = app.optimizer.optimize
    original_update_report = app.update_report_tab
    original_populate_groups = app.populate_groups_combobox
    
    passed_demands = []
    def mock_optimize(*args, **kwargs):
        nonlocal passed_demands
        passed_demands = kwargs.get("demands", [])
        return {"gruppi": {}, "summary_generale": {}}
        
    app.optimizer.optimize = mock_optimize
    app.update_report_tab = lambda *a, **k: None
    app.populate_groups_combobox = lambda *a, **k: None
    
    # Mockiamo messagebox showinfo / showwarning / askyesno
    original_showwarning = messagebox.showwarning
    original_showinfo = messagebox.showinfo
    original_askyesno = messagebox.askyesno
    
    messagebox.showwarning = lambda *a, **k: None
    messagebox.showinfo = lambda *a, **k: None
    messagebox.askyesno = lambda *a, **k: False
    
    try:
        app.run_optimization()
        # Dovrebbe aver passato all'ottimizzatore solo il pezzo contrassegnato in verde!
        assert len(passed_demands) == 1
        assert passed_demands[0]["descrizione"] == "Pezzo A"
        
            # Simula che nessun pezzo sia verde
        app.current_order[0]["is_green"] = False
        app.run_optimization()
        # Dovrebbe ottimizzare tutti i pezzi presenti (cioè 2)
        assert len(passed_demands) == 2
        
        # 4. Testiamo il filtraggio di colonna anche su tree_pieces
        assert app.filters_pieces == {}
        app.filters_pieces["desc"] = "pezzo b"
        app.reload_order_table()
        piece_items = app.tree_pieces.get_children()
        # Dovrebbe esserci solo Pezzo B
        assert len(piece_items) == 1
        vals = app.tree_pieces.item(piece_items[0], "values")
        assert vals[1] == "Pezzo B"
        
        # Annulla filtri pezzi
        app.clear_filters_pieces()
        assert app.filters_pieces == {}
        assert len(app.tree_pieces.get_children()) == 2
        
    finally:
        app.optimizer.optimize = original_optimize
        app.update_report_tab = original_update_report
        app.populate_groups_combobox = original_populate_groups
        messagebox.showwarning = original_showwarning
        messagebox.showinfo = original_showinfo
        messagebox.askyesno = original_askyesno
        app.data_manager.db_path = original_db_path
        try:
            if os.path.exists(test_db_path):
                os.remove(test_db_path)
        except Exception:
            pass
        
    print("=== TEST FILTRAGGIO TASTO DESTRO ED F3 COMPLETATO CON SUCCESSO! ===")

def test_commessa_delete_and_clear_filters():
    """
    Verifica che l'eliminazione della commessa aggiorni la lista a sinistra e l'intestazione,
    e che il clear filters di commesse azzeri sia i filtri che le selezioni F3 (is_green).
    """
    print("\n=== AVVIO TEST ELIMINAZIONE COMMESSA E RESET FILTRI/F3 ===")
    import tkinter as tk
    from tkinter import messagebox
    from app import CutMobApp
    
    root = tk.Tk()
    root.withdraw()
    
    app = CutMobApp(root)
    app.ent_sfrido.delete(0, tk.END)
    app.ent_sfrido.insert(0, "0")
    app.ent_kerf.delete(0, tk.END)
    app.ent_kerf.insert(0, "4.0")
    original_db_path = app.data_manager.db_path
    test_db_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_test_dir")
    os.makedirs(test_db_dir, exist_ok=True)
    test_db_path = os.path.join(test_db_dir, "database.json")
    app.data_manager.db_path = test_db_path
    
    # 1. Testiamo la quantita automatica a 100 sui pannelli standard (barre)
    # Creiamo un db temporaneo con una barra a quantità 1
    with open(test_db_path, "w", encoding="utf-8") as f:
        json.dump({
            "barre": [
                {"id": "B_TEST", "width": 2800.0, "height": 2070.0, "thickness": 18.0, "color_code": "RED", "color_desc": "Rosso", "quantity": 1}
            ],
            "semilavorati": [],
            "commesse": []
        }, f)
        
    # Carichiamo tramite DataManager e verifichiamo che la quantità sia ora 100!
    app.data_manager.db = app.data_manager.load_db()
    barre = app.data_manager.get_barre()
    assert len(barre) == 1
    assert barre[0]["quantity"] == 100
    
    # 2. Testiamo l'eliminazione commessa e reset intestazione
    # Salviamo una commessa
    c = app.data_manager.save_commessa(None, "Commessa da eliminare", [
        {"descrizione": "Pezzo Test", "width": 600.0, "height": 720.0, "thickness": 18.0, "color_code": "RED", "color_desc": "Rosso", "quantity": 1}
    ])
    
    # Carichiamo la commessa come attiva
    app.reload_commesse_table()
    commesse_items = app.tree_commesse.get_children()
    assert len(commesse_items) == 1
    
    app.tree_commesse.selection_set(commesse_items[0])
    app.on_commessa_select()
    
    assert app.current_commessa_id == c["id"]
    assert "Commessa da eliminare" in app.lbl_commessa_info.cget("text")
    
    # Mockiamo la conferma dell'eliminazione (confermata)
    original_askyesno = messagebox.askyesno
    original_showinfo = messagebox.showinfo
    messagebox.askyesno = lambda *a, **k: True
    messagebox.showinfo = lambda *a, **k: None
    
    try:
        app.delete_commessa_action()
        # Verifica che la commessa attiva sia resettata e l'intestazione sia azzerata
        assert app.current_commessa_id is None
        assert app.current_commessa_name == ""
        assert "Nuova Commessa" in app.lbl_commessa_info.cget("text")
        
        # Verifica che la commessa sia stata tolta dalla lista di sinistra
        commesse_items_after = app.tree_commesse.get_children()
        assert len(commesse_items_after) == 0
        
    finally:
        messagebox.askyesno = original_askyesno
        messagebox.showinfo = original_showinfo
        
    # 3. Testiamo che clear_filters_commesse tolga sia i filtri che le selezioni F3 (is_green)
    app.current_order = [
        {"descrizione": "P1", "width": 600.0, "height": 720.0, "thickness": 18.0, "color_code": "RED", "color_desc": "Rosso", "quantity": 1, "is_green": True}
    ]
    app.filters_commesse = {"nome": "test"}
    
    app.clear_filters_commesse()
    assert app.filters_commesse == {}
    assert app.current_order[0]["is_green"] is False
    
    # Ripristino db originale ed eliminazione db di test
    app.data_manager.db_path = original_db_path
    try:
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
        if os.path.exists(test_db_dir):
            os.rmdir(test_db_dir)
    except Exception:
        pass
        
    print("=== TEST ELIMINAZIONE COMMESSA E RESET FILTRI/F3 COMPLETATO CON SUCCESSO! ===")

def test_sfrido():
    print("\n=== AVVIO TEST PARAMETRO SFRIDO ===")
    opt = CuttingOptimizer(kerf=0.5)
    stocks = [
        {
            "id": "B1",
            "width": 1000.0,
            "height": 1000.0,
            "thickness": 18.0,
            "color_code": "U708",
            "color_desc": "Grigio",
            "stock_type": "whole_board"
        }
    ]
    demands = [
        {
            "descrizione": "Anta",
            "width": 480.0,
            "height": 480.0,
            "thickness": 18.0,
            "color_code": "U708",
            "color_desc": "Grigio",
            "quantity": 4
        }
    ]
    # Senza sfrido, 4 ante 480x480 con kerf 0.5 entrano perfettamente in 1000x1000.
    # Con sfrido = 10, le ante diventano 490x490.
    # 490 * 2 + 0.5 = 980.5 <= 1000, quindi dovrebbero entrare comunque tutti e 4!
    # Con sfrido = 25, le ante diventano 505x505. 505 * 2 + 0.5 = 1010.5 > 1000, quindi non entrano più 4!
    
    res1 = opt.optimize(stocks, demands, respect_grain=True, sfrido=10.0)
    g1 = res1["gruppi"]["18.0mm_U708"]
    assert len(g1["unplaced_pieces"]) == 0, "Dovrebbero entrare tutti con sfrido 10"
    placed = g1["used_boards"][0]["placed_pieces"]
    # Con lo sfrido sommato all'elemento, sia w che width_original devono valere 490
    assert placed[0]["width_original"] == 490.0
    assert placed[0]["w"] == 490.0
    
    res2 = opt.optimize(stocks, demands, respect_grain=True, sfrido=25.0)
    g2 = res2["gruppi"]["18.0mm_U708"]
    assert len(g2["unplaced_pieces"]) > 0, "Non dovrebbero entrare tutti con sfrido 25"
    print("=== TEST PARAMETRO SFRIDO COMPLETATO CON SUCCESSO! ===")

def test_rifilo():
    print("\n=== AVVIO TEST PARAMETRO RIFILO ===")
    opt = CuttingOptimizer(kerf=0.5)
    stocks = [
        {
            "id": "B1",
            "width": 1000.0,
            "height": 1000.0,
            "thickness": 18.0,
            "color_code": "U708",
            "color_desc": "Grigio",
            "stock_type": "whole_board"
        }
    ]
    demands_large = [
        {
            "descrizione": "Anta Grande",
            "width": 995.0,
            "height": 995.0,
            "thickness": 18.0,
            "color_code": "U708",
            "color_desc": "Grigio",
            "quantity": 1
        }
    ]
    demands_small = [
        {
            "descrizione": "Anta Piccola",
            "width": 970.0,
            "height": 970.0,
            "thickness": 18.0,
            "color_code": "U708",
            "color_desc": "Grigio",
            "quantity": 1
        }
    ]
    
    res1 = opt.optimize(stocks, demands_large, respect_grain=True, rifilo_verticale=10.0, rifilo_orizzontale=10.0, sfrido=0.0)
    g1 = res1["gruppi"]["18.0mm_U708"]
    assert len(g1["unplaced_pieces"]) == 1, "Pezzo grande non deve entrare a causa del rifilo"
    
    res2 = opt.optimize(stocks, demands_small, respect_grain=True, rifilo_verticale=10.0, rifilo_orizzontale=10.0, sfrido=0.0)
    g2 = res2["gruppi"]["18.0mm_U708"]
    assert len(g2["unplaced_pieces"]) == 0, "Pezzo piccolo deve entrare"
    placed = g2["used_boards"][0]["placed_pieces"][0]
    assert placed["x"] == 10.0
    assert placed["y"] == 10.0
    print("=== TEST PARAMETRO RIFILO COMPLETATO CON SUCCESSO! ===")

def test_nesting_pantografo():
    print("\n=== AVVIO TEST NESTING PANTOGRAFO ===")
    opt = CuttingOptimizer(kerf=0.5)
    stocks = [
        {
            "id": "B1",
            "width": 1000.0,
            "height": 1000.0,
            "thickness": 18.0,
            "color_code": "U708",
            "color_desc": "Grigio",
            "stock_type": "whole_board"
        }
    ]
    demands = [
        {
            "descrizione": "Pezzo A",
            "width": 400.0,
            "height": 200.0,
            "thickness": 18.0,
            "color_code": "U708",
            "color_desc": "Grigio",
            "quantity": 2
        },
        {
            "descrizione": "Pezzo B",
            "width": 200.0,
            "height": 400.0,
            "thickness": 18.0,
            "color_code": "U708",
            "color_desc": "Grigio",
            "quantity": 2
        }
    ]
    
    res = opt.optimize(stocks, demands, respect_grain=True, machine_type="pantografo", sfrido=0.0)
    g = res["gruppi"]["18.0mm_U708"]
    assert len(g["unplaced_pieces"]) == 0, "Tutti i pezzi devono essere piazzati con il nesting"
    used_board = g["used_boards"][0]
    assert len(used_board["placed_pieces"]) == 4, "Tutti i 4 pezzi devono essere posizionati sulla lastra"
    
    pieces = used_board["placed_pieces"]
    for i, p1 in enumerate(pieces):
        for j, p2 in enumerate(pieces):
            if i != j:
                overlap_x = p1["x"] < p2["x"] + p2["w"] and p1["x"] + p1["w"] > p2["x"]
                overlap_y = p1["y"] < p2["y"] + p2["h"] and p1["y"] + p1["h"] > p2["y"]
                assert not (overlap_x and overlap_y), f"Sovrapposizione rilevata tra pezzo {i} e pezzo {j}!"
                
    print("=== TEST NESTING PANTOGRAFO COMPLETATO CON SUCCESSO! ===")

def test_sfrido_only_on_panels():
    print("\n=== AVVIO TEST PARAMETRO SFRIDO SOLO SU PANNELLI ===")
    opt = CuttingOptimizer(kerf=0.5)
    
    # 1. Test su barra (semilavorato_bar) -> lo sfrido non deve essere applicato
    stocks_bar = [
        {
            "id": "S1",
            "width": 1000.0,
            "height": 500.0,
            "thickness": 18.0,
            "color_code": "U708",
            "color_desc": "Grigio",
            "stock_type": "semilavorato_bar"
        }
    ]
    demands = [
        {
            "descrizione": "Anta",
            "width": 500.0,
            "height": 1000.0,
            "thickness": 18.0,
            "color_code": "U708",
            "color_desc": "Grigio",
            "quantity": 1
        }
    ]
    
    res = opt.optimize(stocks_bar, demands, respect_grain=True, sfrido=10.0)
    g = res["gruppi"]["18.0mm_U708"]
    assert len(g["unplaced_pieces"]) == 0, "Il pezzo dovrebbe entrare nella barra perché lo sfrido non si applica sulle barre"
    placed = g["used_boards"][0]["placed_pieces"][0]
    assert placed["width_original"] == 500.0, "La misura finale non deve includere lo sfrido per le barre"
    
    # 2. Test su pannello (whole_board) -> lo sfrido deve essere applicato
    stocks_panel = [
        {
            "id": "B1",
            "width": 1000.0,
            "height": 500.0,
            "thickness": 18.0,
            "color_code": "U708",
            "color_desc": "Grigio",
            "stock_type": "whole_board"
        }
    ]
    res_panel = opt.optimize(stocks_panel, demands, respect_grain=True, sfrido=10.0)
    g_panel = res_panel["gruppi"]["18.0mm_U708"]
    assert len(g_panel["unplaced_pieces"]) == 1, "Il pezzo non deve entrare nel pannello perché lo sfrido lo rende 1010x510"
    
    print("=== TEST PARAMETRO SFRIDO SOLO SU PANNELLI COMPLETATO CON SUCCESSO! ===")

def test_remnants_orientation_and_matching():
    print("\n=== AVVIO TEST ORIENTAMENTO E CORRISPONDENZA RESIDUI ===")
    import tkinter as tk
    from app import CutMobApp
    import os
    import json
    
    root = tk.Tk()
    root.withdraw()
    
    app = CutMobApp(root)
    app.ent_sfrido.delete(0, tk.END)
    app.ent_sfrido.insert(0, "0")
    app.ent_kerf.delete(0, tk.END)
    app.ent_kerf.insert(0, "4.0")
    
    original_db_path = app.data_manager.db_path
    test_db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_db_remnants_orient.json")
    app.data_manager.db_path = test_db_path
    
    # 1. Prepariamo database di test con:
    # - barre standard: no
    # - semilavorati (template standard): altezza 717, lunghezza 2800 (nella DB memorizzato come width=717, height=2800)
    # - residuo: altezza 717, lunghezza 800. Ma memorizzato in DB come S_REC_H717_... con width=717, height=800
    # - residuo 2: altezza 717, lunghezza 500. Memorizzato in DB come S_REC_H717_... con width=717, height=500
    test_db = {
        "barre": [],
        "semilavorati": [
            {
                "id": "BARRA_STD_717",
                "width": 717.0,
                "height": 2800.0,
                "thickness": 18.0,
                "color_code": "TEST_COLOR",
                "color_desc": "Test Desc",
                "has_grain": True,
                "quantity": 0  # Template
            },
            {
                "id": "S_REC_H717_12345_0_0",
                "width": 717.0,
                "height": 800.0,
                "thickness": 18.0,
                "color_code": "TEST_COLOR",
                "color_desc": "Test Desc",
                "has_grain": True,
                "quantity": 1  # Residuo reale
            },
            {
                "id": "S_REC_H717_12345_0_1",
                "width": 717.0,
                "height": 500.0,
                "thickness": 18.0,
                "color_code": "TEST_COLOR",
                "color_desc": "Test Desc",
                "has_grain": True,
                "quantity": 1  # Residuo reale 2
            }
        ],
        "commesse": []
    }
    
    with open(test_db_path, "w", encoding="utf-8") as f:
        json.dump(test_db, f, indent=4)
        
    app.data_manager.db = app.data_manager.load_db()
    app.reload_magazzino_tables()
    
    # 2. Configura ordine (commessa) di test
    # Chiediamo un pezzo da 600 x 717 (dovrebbe finire sul residuo da 800)
    # E un pezzo da 450 x 717 (dovrebbe finire sul residuo da 500)
    app.current_order = [
        {
            "descrizione": "Pezzo Grande",
            "width": 600.0,
            "height": 717.0,
            "thickness": 18.0,
            "color_code": "TEST_COLOR",
            "color_desc": "Test Desc",
            "quantity": 1
        },
        {
            "descrizione": "Pezzo Piccolo",
            "width": 450.0,
            "height": 400.0,
            "thickness": 18.0,
            "color_code": "TEST_COLOR",
            "color_desc": "Test Desc",
            "quantity": 1
        }
    ]
    
    # Selezioniamo solo Residuo (use_residuo=True)
    app.var_stock_residuo.set(True)
    app.var_stock_pannello.set(False)
    app.var_stock_barra.set(False)
    
    # Mock dei dialoghi di output
    import app as app_mod
    from tkinter import messagebox
    original_loading = app_mod.LoadingDialog
    original_showinfo = messagebox.showinfo
    original_askyesno = messagebox.askyesno
    
    class MockLoading:
        def __init__(self, *args, **kwargs): pass
        def update_progress(self, *args): pass
        def destroy(self): pass
        
    app_mod.LoadingDialog = MockLoading
    messagebox.showinfo = lambda *args: None
    messagebox.askyesno = lambda *args: False
    
    try:
        # Avviamo ottimizzazione
        app.run_optimization()
        
        assert app.optimization_results is not None
        g_res = app.optimization_results["gruppi"]["18.0mm_TEST_COLOR"]
        
        used_boards = g_res["used_boards"]
        unplaced = g_res["unplaced_pieces"]
        
        # Devono essere posizionati entrambi i pezzi!
        assert len(unplaced) == 0, f"Ci sono {len(unplaced)} pezzi non piazzati!"
        assert len(used_boards) == 2, f"Dovrebbero essere usati 2 residui, usati {len(used_boards)}"
        
        # Verifica posizionamento corretto
        res_800 = next(ub for ub in used_boards if ub["board"]["id"] == "S_REC_H717_12345_0_0")
        res_500 = next(ub for ub in used_boards if ub["board"]["id"] == "S_REC_H717_12345_0_1")
        
        assert len(res_800["placed_pieces"]) == 1
        assert res_800["placed_pieces"][0]["descrizione"] == "Pezzo Grande"
        
        assert len(res_500["placed_pieces"]) == 1
        assert res_500["placed_pieces"][0]["descrizione"] == "Pezzo Piccolo"
        
        print("=== TEST ORIENTAMENTO E CORRISPONDENZA RESIDUI COMPLETATO CON SUCCESSO! ===")
    finally:
        app_mod.LoadingDialog = original_loading
        messagebox.showinfo = original_showinfo
        messagebox.askyesno = original_askyesno
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
        app.data_manager.db_path = original_db_path
        root.destroy()

def test_new_warehouse_selection_logic():
    print("\n=== AVVIO TEST NUOVE LOGICHE DI SELEZIONE MAGAZZINO E RESIDUI IDONEI ===")
    
    import tkinter as tk
    from tkinter import messagebox
    import app as app_mod
    from app import CutMobApp
    
    root = tk.Tk()
    root.withdraw()
    
    app = CutMobApp(root)
    original_db_path = app.data_manager.db_path
    test_db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_db_new_logic.json")
    app.data_manager.db_path = test_db_path
    
    test_db = {
        "barre": [
            {
                "id": "TEMPLATE_BARRA",
                "width": 2800.0,
                "height": 2070.0,
                "thickness": 18.0,
                "color_code": "TEST_COLOR",
                "color_desc": "TEST DESC",
                "has_grain": False,
                "quantity": 100
            }
        ],
        "semilavorati": [
            {
                "id": "S_REC_IDONEO",
                "width": 800.0,
                "height": 717.0,
                "thickness": 18.0,
                "color_code": "TEST_COLOR",
                "color_desc": "TEST DESC",
                "has_grain": False,
                "quantity": 1
            },
            {
                "id": "S_REC_NON_IDONEO",
                "width": 100.0,
                "height": 100.0,
                "thickness": 18.0,
                "color_code": "TEST_COLOR",
                "color_desc": "TEST DESC",
                "has_grain": False,
                "quantity": 1
            },
            {
                "id": "SEMI_717",
                "width": 2800.0,
                "height": 717.0,
                "thickness": 18.0,
                "color_code": "TEST_COLOR",
                "color_desc": "TEST DESC",
                "has_grain": False,
                "quantity": 2
            }
        ],
        "commesse": []
    }
    
    with open(test_db_path, "w", encoding="utf-8") as f:
        json.dump(test_db, f, indent=4)
        
    app.data_manager.db = app.data_manager.load_db()
    
    # Ordine con un pezzo normale e uno troppo grande
    app.current_order = [
        {
            "descrizione": "Anta idonea",
            "width": 600.0,
            "height": 717.0,
            "thickness": 18.0,
            "color_code": "TEST_COLOR",
            "color_desc": "TEST DESC",
            "quantity": 1
        },
        {
            "descrizione": "Anta gigante",
            "width": 1200.0,
            "height": 800.0,
            "thickness": 18.0,
            "color_code": "TEST_COLOR",
            "color_desc": "TEST DESC",
            "quantity": 1
        }
    ]
    
    # Mock dei dialoghi
    original_loading = app_mod.LoadingDialog
    original_fabbisogno = app_mod.FabbisognoDialog
    original_showinfo = messagebox.showinfo
    original_askyesno = messagebox.askyesno
    
    class MockLoading:
        def __init__(self, *args, **kwargs): pass
        def update_progress(self, *args): pass
        def destroy(self): pass
        
    app_mod.LoadingDialog = MockLoading
    messagebox.showinfo = lambda *args: None
    messagebox.askyesno = lambda *args: False
    
    fabbisogno_chiamato = False
    fabbisogno_data = None
    
    class MockFabbisogno:
        def __init__(self, parent, report_data, global_sufficient):
            nonlocal fabbisogno_chiamato, fabbisogno_data
            fabbisogno_chiamato = True
            fabbisogno_data = report_data
            
    app_mod.FabbisognoDialog = MockFabbisogno
    
    try:
        # Selezioniamo: Residuo=True, Barra=True, Pannello=False
        app.var_stock_residuo.set(True)
        app.var_stock_pannello.set(True)
        app.var_stock_barra.set(False)
        
        # Test 1: Filtraggio residui idonei
        group_std_heights = {"18.0mm_TEST_COLOR": [717.0]}
        respect_grain_dict = {"18.0mm_TEST_COLOR": False}
        suitable_remnants = app.get_suitable_residui(
            app.data_manager.get_semilavorati(),
            app.current_order,
            respect_grain_dict,
            group_std_heights
        )
        assert len(suitable_remnants) == 1
        assert suitable_remnants[0]["id"] == "S_REC_IDONEO"
        
        # Test 2: Calcolo Fabbisogni con attivazione automatica del pannello
        app.calculate_requirements()
        assert fabbisogno_chiamato is True
        
        group_rep = fabbisogno_data[0]
        assert group_rep["unplaced_count"] == 0
        assert group_rep["total_barre_real_used"] > 0 or group_rep["total_barre_virtual_needed"] > 0
        
        print("=== TEST NUOVE LOGICHE DI SELEZIONE MAGAZZINO E RESIDUI IDONEI COMPLETATO! ===")
    finally:
        app_mod.LoadingDialog = original_loading
        app_mod.FabbisognoDialog = original_fabbisogno
        messagebox.showinfo = original_showinfo
        messagebox.askyesno = original_askyesno
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
        app.data_manager.db_path = original_db_path
        root.destroy()

def test_settings_protection_and_tabs():
    print("\n=== AVVIO TEST PROTEZIONE PASSWORD E SCHEDE DI CONFIGURAZIONE ===")
    
    import tkinter as tk
    from tkinter import messagebox
    import app as app_mod
    from app import CutMobApp, DbSettingsDialog
    
    root = tk.Tk()
    root.withdraw()
    
    app = CutMobApp(root)
    original_db_path = app.data_manager.db_path
    test_db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_db_settings.json")
    app.data_manager.db_path = test_db_path
    
    # Mock dei dialoghi
    original_askstring = app_mod.simpledialog.askstring
    original_showinfo = messagebox.showinfo
    original_showerror = messagebox.showerror
    
    # Configura il test per password errata prima, poi corretta
    password_attempt = None
    def mock_askstring(title, prompt, **kwargs):
        return password_attempt
        
    app_mod.simpledialog.askstring = mock_askstring
    
    showerror_called = False
    def mock_showerror(title, message, **kwargs):
        nonlocal showerror_called
        showerror_called = True
        
    messagebox.showerror = mock_showerror
    messagebox.showinfo = lambda *args, **kwargs: None
    
    try:
        # 1. Test password errata
        password_attempt = "wrong_pwd"
        app.show_db_settings_dialog()
        assert showerror_called is True
        
        # 2. Test password corretta
        password_attempt = "Rdf202764!"
        showerror_called = False
        
        # Intercettiamo l'apertura del dialog per verificare i campi e salvarli
        opened_dialog = None
        original_init = DbSettingsDialog.__init__
        
        def mock_init(self, *args, **kwargs):
            nonlocal opened_dialog
            original_init(self, *args, **kwargs)
            opened_dialog = self
            
        DbSettingsDialog.__init__ = mock_init
        
        app.show_db_settings_dialog()
        assert opened_dialog is not None
        
        # Verifica la presenza delle linguette (Notebook)
        assert hasattr(opened_dialog, "notebook")
        assert len(opened_dialog.notebook.tabs()) == 4
        
        # Inserisci nuovi dati standard e cliente
        opened_dialog.ent_def_kerf.delete(0, tk.END)
        opened_dialog.ent_def_kerf.insert(0, "4.5")
        
        opened_dialog.ent_client_name.delete(0, tk.END)
        opened_dialog.ent_client_name.insert(0, "Mobili Rossi S.r.l.")
        
        # Salva le impostazioni
        opened_dialog.save_settings()
        
        # Verifica aggiornamento dinamico sul programma principale
        assert app.ent_kerf.get() == "4.5"
        assert app.lbl_client.cget("text") == "per Mobili Rossi S.r.l."
        assert "Mobili Rossi S.r.l." in app.root.title()
        
        print("=== TEST PROTEZIONE PASSWORD E SCHEDE DI CONFIGURAZIONE COMPLETATO CON SUCCESSO! ===")
    finally:
        app_mod.simpledialog.askstring = original_askstring
        messagebox.showinfo = original_showinfo
        messagebox.showerror = original_showerror
        DbSettingsDialog.__init__ = original_init
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
        app.data_manager.db_path = original_db_path
        root.destroy()

def test_grain_rotation_and_selection():
    print("\n=== AVVIO TEST LOGICHE ROTAZIONE E DIREZIONE VENATURA ===")
    from optimizer import CuttingOptimizer
    opt = CuttingOptimizer(kerf=0.5)
    
    # 1. Test su Barra: la venatura costringe la rotazione (altezza pezzo su larghezza barra)
    # Barra di larghezza 720 (H pezzo), altezza 2000. Pezzo di H 720, W 600.
    stocks_bar = [{
        "id": "BAR_1",
        "width": 720.0,
        "height": 2000.0,
        "thickness": 18.0,
        "color_code": "ROVERE",
        "color_desc": "Rovere",
        "stock_type": "semilavorato_bar",
        "has_grain": True
    }]
    demands = [{
        "descrizione": "Anta Rovere",
        "width": 600.0,
        "height": 720.0,
        "thickness": 18.0,
        "color_code": "ROVERE",
        "color_desc": "Rovere",
        "quantity": 1
    }]
    
    res_bar = opt.optimize(stocks_bar, demands, respect_grain=True)
    g_bar = res_bar["gruppi"]["18.0mm_ROVERE"]
    assert len(g_bar["unplaced_pieces"]) == 0, "L'anta Rovere deve essere posizionata sulla barra con venatura ignorata"

    # 2. Test su Pannello con direzione "orizzontale":
    stocks_panel = [{
        "id": "PAN_1",
        "width": 2000.0,
        "height": 720.0,
        "thickness": 18.0,
        "color_code": "ROVERE",
        "color_desc": "Rovere",
        "stock_type": "whole_board",
        "has_grain": True
    }]
    res_panel_horiz = opt.optimize(stocks_panel, demands, respect_grain=True, panel_grain_direction="orizzontale")
    g_panel_horiz = res_panel_horiz["gruppi"]["18.0mm_ROVERE"]
    assert len(g_panel_horiz["unplaced_pieces"]) == 0
    placed_panel = g_panel_horiz["used_boards"][0]["placed_pieces"][0]
    assert placed_panel["rotated"] is True, "Con venatura orizzontale sul pannello, il pezzo deve essere ruotato"

    res_panel_vert = opt.optimize(stocks_panel, demands, respect_grain=True, panel_grain_direction="verticale")
    g_panel_vert = res_panel_vert["gruppi"]["18.0mm_ROVERE"]
    assert len(g_panel_vert["unplaced_pieces"]) == 0
    placed_panel_vert = g_panel_vert["used_boards"][0]["placed_pieces"][0]
    assert placed_panel_vert["rotated"] is False, "Con venatura verticale sul pannello, il pezzo non deve essere ruotato"
    
    print("=== TEST LOGICHE ROTAZIONE E DIREZIONE VENATURA COMPLETATO CON SUCCESSO! ===")

def test_bar_cutting_logic_vs_for_reduced_width():
    print("\n=== AVVIO TEST TAGLIO ORIZZONTALE PRIMA DI RIFILO SU BARRA (1 ANTA) ===")
    opt = CuttingOptimizer(kerf=5.0)
    stocks = [
        {
            "id": "B_BAR_597",
            "width": 2800.0,
            "height": 597.0,
            "thickness": 18.0,
            "color_code": "U708",
            "color_desc": "Grigio",
            "stock_type": "semilavorato_bar"
        }
    ]
    demands = [
        {
            "descrizione": "Anta Ridotta 717x580",
            "width": 580.0,  # Larghezza
            "height": 717.0, # Altezza
            "thickness": 18.0,
            "color_code": "U708",
            "color_desc": "Grigio",
            "quantity": 1
        }
    ]
    res = opt.optimize(stocks, demands, respect_grain=True, group_std_heights={"18.0mm_U708": [597.0]})
    g = res["gruppi"]["18.0mm_U708"]
    
    assert len(g["unplaced_pieces"]) == 0
    ub = g["used_boards"][0]
    
    cuts = ub["cuts"]
    print("Tagli registrati (1 anta):", cuts)
    
    v_cuts = [c for c in cuts if c["type"] == "V"]
    h_cuts = [c for c in cuts if c["type"] == "H"]
    
    assert len(v_cuts) >= 1, "Manca il taglio verticale"
    assert len(h_cuts) >= 1, "Manca il taglio orizzontale"
    
    first_v_cut = sorted(v_cuts, key=lambda c: c["step"])[0]
    assert first_v_cut["x1"] == 717.0, f"Il taglio verticale dovrebbe essere a X=717, trovato {first_v_cut['x1']}"
    assert first_v_cut["y2"] == 597.0, f"Il taglio verticale dovrebbe tagliare l'intera altezza (597), trovato y2={first_v_cut['y2']}"
    
    first_h_cut = sorted(h_cuts, key=lambda c: c["step"])[0]
    assert first_h_cut["y1"] == 580.0, f"Il taglio orizzontale dovrebbe essere a Y=580, trovato {first_h_cut['y1']}"
    assert first_h_cut["x2"] == 717.0, f"Il taglio orizzontale dovrebbe limitarsi a X=717, trovato x2={first_h_cut['x2']}"
    
    new_semis = ub["new_semilavorati"]
    print("Nuovi semilavorati (1 anta):", new_semis)
    bar_remnant = next((s for s in new_semis if s["width"] == 2800 - 717 - 5), None)
    assert bar_remnant is not None, "Residuo barra principale non generato!"
    assert bar_remnant["height"] == 597.0, f"Il residuo della barra dovrebbe avere altezza 597.0, trovato {bar_remnant['height']}"

    print("=== AVVIO TEST TAGLIO ORIZZONTALE PRIMA DI RIFILO SU BARRA (3 ANTE) ===")
    demands_3 = [
        {
            "descrizione": "Anta Ridotta 717x580",
            "width": 580.0,  # Larghezza
            "height": 717.0, # Altezza
            "thickness": 18.0,
            "color_code": "U708",
            "color_desc": "Grigio",
            "quantity": 3
        }
    ]
    res_3 = opt.optimize(stocks, demands_3, respect_grain=True, group_std_heights={"18.0mm_U708": [597.0]})
    g_3 = res_3["gruppi"]["18.0mm_U708"]
    
    assert len(g_3["unplaced_pieces"]) == 0
    ub_3 = g_3["used_boards"][0]
    cuts_3 = ub_3["cuts"]
    print("Tagli registrati (3 ante):", cuts_3)
    
    # Dovremmo avere esattamente 4 tagli
    assert len(cuts_3) == 4, f"Ci dovrebbero essere esattamente 4 tagli, trovati {len(cuts_3)}"
    
    # 1. Taglio verticale per separare il blocco a X=2161 (level=1)
    cut1 = cuts_3[0]
    assert cut1["type"] == "V" and cut1["x1"] == 2161.0 and cut1["y2"] == 597.0 and cut1["level"] == 1, f"Taglio 1 errato: {cut1}"
    
    # 2. Taglio orizzontale continuo a Y=580 per lunghezza 2161 (level=2)
    cut2 = cuts_3[1]
    assert cut2["type"] == "H" and cut2["y1"] == 580.0 and cut2["x1"] == 0.0 and cut2["x2"] == 2161.0 and cut2["level"] == 2, f"Taglio 2 errato: {cut2}"
    
    # 3. Tagli verticali interni a X=717 e X=1439 (level=3)
    cut3 = cuts_3[2]
    assert cut3["type"] == "V" and cut3["x1"] == 717.0 and cut3["y2"] == 580.0 and cut3["level"] == 3, f"Taglio 3 errato: {cut3}"
    
    cut4 = cuts_3[3]
    assert cut4["type"] == "V" and cut4["x1"] == 1439.0 and cut4["y2"] == 580.0 and cut4["level"] == 3, f"Taglio 4 errato: {cut4}"
    
    # Verifichiamo che il residuo rimanga di altezza 597 e larghezza 2800 - 2161 - 5 = 634
    new_semis_3 = ub_3["new_semilavorati"]
    print("Nuovi semilavorati (3 ante):", new_semis_3)
    bar_remnant_3 = next((s for s in new_semis_3 if s["width"] == 634.0), None)
    assert bar_remnant_3 is not None, "Residuo barra principale per 3 ante non generato!"
    assert bar_remnant_3["height"] == 597.0, f"Il residuo dovrebbe avere altezza 597.0, trovato {bar_remnant_3['height']}"

    print("=== TEST TAGLIO ORIZZONTALE PRIMA DI RIFILO SU BARRA COMPLETATO CON SUCCESSO! ===")

if __name__ == "__main__":
    test_bar_cutting_logic_vs_for_reduced_width()
    test_grain_rotation_and_selection()
    test_settings_protection_and_tabs()
    test_new_warehouse_selection_logic()
    test_remnants_orientation_and_matching()
    test_sfrido_only_on_panels()
    test_sfrido()
    test_rifilo()
    test_nesting_pantografo()
    test_optimization()
    test_guillotine_and_semilavorati()
    test_requirement_simulation()
    test_new_csv_format_and_duplicates()
    test_new_order_csv_format_and_alignment()
    test_pdf_export()
    test_semilavorati_csv_import()
    test_remnants_prioritization_and_exclusion()
    test_panel_production()
    test_commesse_persistence()
    test_bar_height_alignment()
    test_tall_pieces_routing_to_panels()
    test_standard_bar_height_constraint()
    test_filtering_and_f3_optimization()
    test_commessa_delete_and_clear_filters()
