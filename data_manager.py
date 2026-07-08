import os
import json
import csv

class DataManager:
    def __init__(self, db_filename="database.json"):
        self.config = self.load_config()
        self.db_type = self.config.get("db_type", "local")
        self.reinit_backend(db_filename)

    def _obfuscate(self, data_str):
        key = b"CutMobSecurityKey2026!"
        data_bytes = data_str.encode("utf-8")
        obfuscated = bytearray()
        for i in range(len(data_bytes)):
            obfuscated.append(data_bytes[i] ^ key[i % len(key)])
        import base64
        return base64.b64encode(obfuscated).decode("utf-8")

    def _deobfuscate(self, base64_str):
        key = b"CutMobSecurityKey2026!"
        import base64
        try:
            obfuscated = base64.b64decode(base64_str.encode("utf-8"))
            deobfuscated = bytearray()
            for i in range(len(obfuscated)):
                deobfuscated.append(obfuscated[i] ^ key[i % len(key)])
            return deobfuscated.decode("utf-8")
        except Exception:
            raise ValueError("Configurazione corrotta o non decifrabile.")

    def load_config(self):
        config_dir = r"C:\CutMob\DbDati"
        os.makedirs(config_dir, exist_ok=True)
        config_path = os.path.join(config_dir, "config.json")
        default_config = {
            "db_type": "local",
            "local_path": r"C:\CutMob\DbDati\database.json",
            "sql_type": "MySQL",
            "sql_host": "127.0.0.1",
            "sql_port": 3306,
            "sql_user": "",
            "sql_password": "",
            "sql_database": "cutmob",
            "default_kerf": 5.0,
            "default_rifilo_h": 0.0,
            "default_rifilo_v": 0.0,
            "default_sfrido": 10.0,
            "default_macchina": "sezionatrice",
            "show_cut_progression": True,
            "default_min_w": 300.0,
            "default_min_h": 300.0,
            "client_name": "",
            "client_cf_piva": "",
            "client_email": "",
            "license_enabled": True
        }
        if not os.path.exists(config_path):
            self.save_config(default_config)
            return default_config
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
            if not content:
                return default_config
            if content.startswith("{"):
                config = json.loads(content)
            else:
                config = json.loads(self._deobfuscate(content))
            for k, v in default_config.items():
                if k not in config:
                    config[k] = v
            return config
        except Exception:
            return default_config

    def save_config(self, config):
        self.config = config
        config_dir = r"C:\CutMob\DbDati"
        os.makedirs(config_dir, exist_ok=True)
        config_path = os.path.join(config_dir, "config.json")
        try:
            data_str = json.dumps(config, indent=4)
            obfuscated_str = self._obfuscate(data_str)
            with open(config_path, "w", encoding="utf-8") as f:
                f.write(obfuscated_str)
            return True
        except Exception:
            return False

    def load_license_key(self):
        lic_path = r"C:\CutMob\DbDati\licenza.key"
        if not os.path.exists(lic_path):
            return ""
        try:
            with open(lic_path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception:
            return ""

    def save_license_key(self, key_str):
        lic_dir = r"C:\CutMob\DbDati"
        os.makedirs(lic_dir, exist_ok=True)
        lic_path = os.path.join(lic_dir, "licenza.key")
        try:
            with open(lic_path, "w", encoding="utf-8") as f:
                f.write(key_str.strip())
            return True
        except Exception:
            return False

    def reinit_backend(self, db_filename="database.json"):
        self.db_type = self.config.get("db_type", "local")
        if self.db_type == "local":
            if db_filename != "database.json":
                if os.path.isabs(db_filename):
                    self.db_path = db_filename
                else:
                    self.db_path = os.path.join(r"C:\CutMob\DbDati", db_filename)
            else:
                self.db_path = r"C:\CutMob\DbDati\database.json"
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        else:
            self.db_path = None
            try:
                self._initialize_sql_tables()
            except Exception as e:
                print(f"Errore inizializzazione tabelle SQL: {e}")
        self.db = self.load_db()

    def _get_sql_connection(self):
        c = self.config
        sql_type = c.get("sql_type", "MySQL")
        host = c.get("sql_host", "127.0.0.1")
        port = int(c.get("sql_port", 3306))
        user = c.get("sql_user", "")
        password = c.get("sql_password", "")
        db_name = c.get("sql_database", "cutmob")

        if sql_type == "MySQL":
            try:
                import pymysql
                conn = pymysql.connect(
                    host=host,
                    port=port,
                    user=user,
                    password=password,
                    database=db_name,
                    charset="utf8mb4"
                )
                return conn
            except ImportError:
                pass
            try:
                import mysql.connector
                conn = mysql.connector.connect(
                    host=host,
                    port=port,
                    user=user,
                    password=password,
                    database=db_name
                )
                return conn
            except ImportError:
                raise ImportError("Driver MySQL non trovato. Eseguire: pip install pymysql")
        elif sql_type == "SQL Server":
            try:
                import pyodbc
                conn_str = f"DRIVER={{SQL Server}};SERVER={host};DATABASE={db_name};UID={user};PWD={password}"
                conn = pyodbc.connect(conn_str)
                return conn
            except ImportError:
                pass
            try:
                import pymssql
                conn = pymssql.connect(
                    server=host,
                    user=user,
                    password=password,
                    database=db_name
                )
                return conn
            except ImportError:
                raise ImportError("Driver SQL Server non trovato. Eseguire: pip install pyodbc")
        else:
            raise ValueError(f"Tipo SQL non supportato: {sql_type}")

    def _execute_query(self, cursor, query, params=()):
        sql_type = self.config.get("sql_type", "MySQL")
        if sql_type != "MySQL":
            query = query.replace("%s", "?")
        cursor.execute(query, params)

    def _initialize_sql_tables(self):
        conn = self._get_sql_connection()
        try:
            cursor = conn.cursor()
            sql_type = self.config.get("sql_type", "MySQL")
            
            if sql_type == "MySQL":
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS barre (
                        id VARCHAR(150) PRIMARY KEY,
                        width DOUBLE PRECISION,
                        height DOUBLE PRECISION,
                        thickness DOUBLE PRECISION,
                        color_code VARCHAR(50),
                        color_desc VARCHAR(150),
                        stock_type VARCHAR(50),
                        quantity INT
                    )
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS semilavorati (
                        id VARCHAR(150) PRIMARY KEY,
                        width DOUBLE PRECISION,
                        height DOUBLE PRECISION,
                        thickness DOUBLE PRECISION,
                        color_code VARCHAR(50),
                        color_desc VARCHAR(150),
                        stock_type VARCHAR(50),
                        quantity INT
                    )
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS commesse (
                        id INT PRIMARY KEY,
                        nome VARCHAR(200),
                        stato VARCHAR(50),
                        data_creazione VARCHAR(50),
                        pezzi TEXT
                    )
                """)
            else:
                cursor.execute("""
                    IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'barre')
                    CREATE TABLE barre (
                        id VARCHAR(150) PRIMARY KEY,
                        width FLOAT,
                        height FLOAT,
                        thickness FLOAT,
                        color_code VARCHAR(50),
                        color_desc VARCHAR(150),
                        stock_type VARCHAR(50),
                        quantity INT
                    )
                """)
                cursor.execute("""
                    IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'semilavorati')
                    CREATE TABLE semilavorati (
                        id VARCHAR(150) PRIMARY KEY,
                        width FLOAT,
                        height FLOAT,
                        thickness FLOAT,
                        color_code VARCHAR(50),
                        color_desc VARCHAR(150),
                        stock_type VARCHAR(50),
                        quantity INT
                    )
                """)
                cursor.execute("""
                    IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'commesse')
                    CREATE TABLE commesse (
                        id INT PRIMARY KEY,
                        nome VARCHAR(200),
                        stato VARCHAR(50),
                        data_creazione VARCHAR(50),
                        pezzi NVARCHAR(MAX)
                    )
                """)
            conn.commit()
        finally:
            conn.close()

    def _load_db_sql(self):
        default_structure = {
            "barre": [],
            "semilavorati": [],
            "commesse": []
        }
        conn = None
        try:
            conn = self._get_sql_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT id, width, height, thickness, color_code, color_desc, stock_type, quantity FROM barre")
            for row in cursor.fetchall():
                default_structure["barre"].append({
                    "id": row[0],
                    "width": float(row[1]),
                    "height": float(row[2]),
                    "thickness": float(row[3]),
                    "color_code": row[4],
                    "color_desc": row[5],
                    "stock_type": row[6],
                    "quantity": int(row[7])
                })
                
            cursor.execute("SELECT id, width, height, thickness, color_code, color_desc, stock_type, quantity FROM semilavorati")
            for row in cursor.fetchall():
                default_structure["semilavorati"].append({
                    "id": row[0],
                    "width": float(row[1]),
                    "height": float(row[2]),
                    "thickness": float(row[3]),
                    "color_code": row[4],
                    "color_desc": row[5],
                    "stock_type": row[6],
                    "quantity": int(row[7])
                })
                
            cursor.execute("SELECT id, nome, stato, data_creazione, pezzi FROM commesse")
            for row in cursor.fetchall():
                try:
                    pezzi = json.loads(row[4])
                except Exception:
                    pezzi = []
                default_structure["commesse"].append({
                    "id": int(row[0]),
                    "nome": row[1],
                    "stato": row[2],
                    "data_creazione": row[3],
                    "pezzi": pezzi
                })
                
            return default_structure
        except Exception as e:
            print(f"Errore caricamento database da SQL: {e}")
            return default_structure
        finally:
            if conn:
                conn.close()

    def _save_db_sql(self):
        conn = None
        try:
            conn = self._get_sql_connection()
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM barre")
            for b in self.db.get("barre", []):
                query = "INSERT INTO barre (id, width, height, thickness, color_code, color_desc, stock_type, quantity) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
                self._execute_query(cursor, query, (
                    b["id"], float(b["width"]), float(b["height"]), float(b["thickness"]),
                    b["color_code"], b["color_desc"], b["stock_type"], int(b["quantity"])
                ))
                
            cursor.execute("DELETE FROM semilavorati")
            for s in self.db.get("semilavorati", []):
                query = "INSERT INTO semilavorati (id, width, height, thickness, color_code, color_desc, stock_type, quantity) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
                self._execute_query(cursor, query, (
                    s["id"], float(s["width"]), float(s["height"]), float(s["thickness"]),
                    s["color_code"], s["color_desc"], s["stock_type"], int(s["quantity"])
                ))
                
            cursor.execute("DELETE FROM commesse")
            for c in self.db.get("commesse", []):
                pezzi_str = json.dumps(c.get("pezzi", []), ensure_ascii=False)
                query = "INSERT INTO commesse (id, nome, stato, data_creazione, pezzi) VALUES (%s, %s, %s, %s, %s)"
                self._execute_query(cursor, query, (
                    int(c["id"]), c["nome"], c["stato"], c["data_creazione"], pezzi_str
                ))
                
            conn.commit()
            return True
        except Exception as e:
            print(f"Errore salvataggio database su SQL: {e}")
            if conn:
                try:
                    conn.rollback()
                except Exception:
                    pass
            return False
        finally:
            if conn:
                conn.close()

    def load_db(self):
        if self.db_type != "local":
            data = self._load_db_sql()
            # Forza la quantità a 100 per le barre standard
            modified = False
            for b in data.get("barre", []):
                if b.get("quantity") != 100:
                    b["quantity"] = 100
                    modified = True
            if modified:
                self.db = data
                self._save_db_sql()
            return data

        default_structure = {
            "barre": [],
            "semilavorati": [],
            "commesse": []
        }
        if not os.path.exists(self.db_path):
            return default_structure
        try:
            with open(self.db_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for key in default_structure:
                    if key not in data:
                        data[key] = default_structure[key]
                
                # Imposta la quantità di tutti i pannelli standard a 100 (solo se è il database reale)
                if os.path.basename(self.db_path) == "database.json":
                    modified = False
                    for b in data.get("barre", []):
                        if b.get("quantity") != 100:
                            b["quantity"] = 100
                            modified = True
                    
                    self.db = data
                    if modified:
                        self.save_db()
                    
                return data
        except Exception:
            return default_structure

    def save_db(self):
        if self.db_type != "local":
            return self._save_db_sql()
        try:
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump(self.db, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Errore nel salvataggio del database: {e}")
            return False

    def get_barre(self):
        self.db = self.load_db()
        return self.db.get("barre", [])

    def set_barre(self, barre_list):
        self.db["barre"] = barre_list
        self.save_db()

    def get_semilavorati(self):
        self.db = self.load_db()
        return self.db.get("semilavorati", [])

    def set_semilavorati(self, semi_list):
        self.db["semilavorati"] = semi_list
        self.save_db()

    def import_csv(self, filepath):
        """
        Legge un file CSV e mappa le colonne in modo flessibile per estrarre la lista pezzi.
        Ritorna una lista di dizionari con chiavi normalizzate:
        'descrizione', 'width', 'height', 'thickness', 'color_code', 'color_desc', 'quantity'
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Il file {filepath} non esiste.")

        delimiter = ','
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                sample = f.read(2048)
                commas = sample.count(',')
                semicolons = sample.count(';')
                if semicolons > commas:
                    delimiter = ';'
        except Exception:
            pass

        pezzi = []
        try:
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f, delimiter=delimiter)
                headers = [h.strip().lower() for h in next(reader)]
                
                col_map = self._detect_columns(headers)
                
                for row_idx, row in enumerate(reader):
                    if not row or len(row) < max(col_map.values(), default=0) + 1:
                        continue
                    
                    try:
                        width_val = self._parse_float(row[col_map['width']]) if 'width' in col_map else 0.0
                        height_val = self._parse_float(row[col_map['height']]) if 'height' in col_map else 0.0
                        thick_val = self._parse_float(row[col_map['thickness']]) if 'thickness' in col_map else 0.0
                        qty_val = int(self._parse_float(row[col_map['quantity']])) if 'quantity' in col_map else 1
                        
                        desc_val = row[col_map['descrizione']].strip() if 'descrizione' in col_map else f"Pezzo {row_idx + 1}"
                        color_code_val = "N/D"
                        # 1. Se nel CSV c'è la colonna 'codbarra' (CodBarra), la usiamo preferibilmente
                        if 'color_code' in col_map and headers[col_map['color_code']] == 'codbarra':
                            color_code_val = row[col_map['color_code']].strip()
                        else:
                            # 2. Altrimenti cerchiamo se sono presenti colonne separate per variante (es. COL_NAME) e opzione (es. COD_TAB)
                            col_variant = -1
                            for syn in ['col_name', 'codvariante', 'cod_variante', 'variante']:
                                if syn in headers:
                                    col_variant = headers.index(syn)
                                    break
                            col_option = -1
                            for syn in ['cod_tab', 'codopzione', 'codice colore', 'codicecolore', 'codice_colore', 'codice', 'color_code', 'code', 'codice barra']:
                                if syn in headers:
                                    col_option = headers.index(syn)
                                    break
                                    
                            if col_variant != -1 and col_option != -1:
                                var_part = row[col_variant].strip()
                                opt_part = row[col_option].strip()
                                if var_part and opt_part:
                                    var_clean = var_part.rstrip("\\/")
                                    opt_clean = opt_part.lstrip("\\/")
                                    color_code_val = f"{var_clean}\\{opt_clean}"
                                else:
                                    color_code_val = opt_part if opt_part else var_part
                            elif 'color_code' in col_map:
                                color_code_val = row[col_map['color_code']].strip()
                        
                        color_desc_val = row[col_map['color_desc']].strip() if 'color_desc' in col_map else "N/D"

                        if color_desc_val == "N/D" and 'color' in col_map:
                            color_desc_val = row[col_map['color']].strip()

                        pezzi.append({
                            "descrizione": desc_val,
                            "width": width_val,
                            "height": height_val,
                            "thickness": thick_val,
                            "color_code": color_code_val,
                            "color_desc": color_desc_val,
                            "quantity": qty_val
                        })
                    except (ValueError, IndexError) as ve:
                        print(f"Errore alla riga {row_idx + 2}: {ve}. Riga saltata.")
                        continue
        except Exception as e:
            raise ValueError(f"Impossibile leggere il file CSV: {e}")

        return pezzi

    def _detect_columns(self, headers):
        synonyms = {
            'width': ['larghezza', 'lunghezza', 'width', 'length', 'l', 'w', 'lungh', 'largh', 'larg_stdag'],
            'height': ['altezza', 'height', 'h', 'alt', 'alt_stdag'],
            'thickness': ['spessore', 'thickness', 't', 'sp', 'spess', 'lungh_stdag'],
            'quantity': ['quantità', 'quantita', 'qta', 'quantity', 'qty', 'quantita\'', 'n', 'pezzi', 'pezzo', 'sommadiquant_da_prod'],
            'descrizione': ['descrizione', 'desc', 'description', 'nome', 'articolo', 'pezzo_desc', 'descr'],
            'color_code': ['codbarra', 'codice colore', 'codicecolore', 'codice_colore', 'codice', 'color code', 'color_code', 'code', 'codice barra'],
            'color_desc': ['descrizione colore', 'descrizionecolore', 'descrizione_colore', 'colore descrizione', 'color desc', 'color_desc', 'risposte'],
            'color': ['colore', 'color', 'finitura']
        }
        
        mapping = {}
        for key, syn_list in synonyms.items():
            for syn in syn_list:
                if syn in headers:
                    mapping[key] = headers.index(syn)
                    break
        
        if 'width' not in mapping and len(headers) > 0:
            mapping['width'] = 0
        if 'height' not in mapping and len(headers) > 1:
            mapping['height'] = 1
        if 'quantity' not in mapping and len(headers) > 2:
            mapping['quantity'] = len(headers) - 1 if len(headers) > 2 else 2
            
        return mapping

    def _parse_float(self, value):
        clean_val = value.strip().replace(',', '.')
        if not clean_val:
            return 0.0
        return float(clean_val)

    def consume_materials(self, used_boards):
        """
        Consuma le lastre usate dal magazzino decrementando le quantità
        e aggiunge i nuovi semilavorati generati dal recupero.
        """
        import time
        barre = self.get_barre()
        semilavorati = self.get_semilavorati()
        
        # Conta quante volte ciascun ID di lastra è stato utilizzato
        used_ids_count = {}
        for ub in used_boards:
            b_id = ub["board"].get("id")
            if b_id:
                used_ids_count[b_id] = used_ids_count.get(b_id, 0) + 1
        
        # Decrementa quantità o rimuove barre
        nuove_barre = []
        for b in barre:
            b_id = b.get("id")
            if b_id in used_ids_count:
                current_qty = int(b.get("quantity", 1))
                new_qty = current_qty - used_ids_count[b_id]
                if new_qty > 0:
                    b["quantity"] = new_qty
                    nuove_barre.append(b)
            else:
                if "quantity" not in b:
                    b["quantity"] = 1
                nuove_barre.append(b)
                
        # Decrementa quantità o rimuove semilavorati
        nuovi_semi = []
        for s in semilavorati:
            s_id = s.get("id")
            if s_id in used_ids_count:
                current_qty = int(s.get("quantity", 1))
                new_qty = current_qty - used_ids_count[s_id]
                if new_qty > 0:
                    s["quantity"] = new_qty
                    nuovi_semi.append(s)
            else:
                if "quantity" not in s:
                    s["quantity"] = 1
                nuovi_semi.append(s)
        
        # Aggiunge i nuovi semilavorati generati (con quantità = 1)
        for ub_idx, ub in enumerate(used_boards):
            new_semis = ub.get("new_semilavorati", [])
            for idx, ns in enumerate(new_semis):
                # Se il pannello genitore era una barra (semilavorato_bar) o residuo di barra,
                # salviamo l'altezza standard originaria nell'ID e orientiamo le dimensioni
                # con width = altezza standard e height = lunghezza.
                is_bar = ub["board"].get("stock_type") in ["semilavorato_bar", "remnant"]
                if is_bar:
                    std_h = ns["height"]
                    length = ns["width"]
                    unique_id = f"S_REC_H{int(std_h)}_{int(time.time())}_{ub_idx}_{idx}"
                    nuovi_semi.append({
                        "id": unique_id,
                        "width": std_h,
                        "height": length,
                        "thickness": ns["thickness"],
                        "color_code": ns["color_code"],
                        "color_desc": ns["color_desc"],
                        "quantity": 1
                    })
                else:
                    unique_id = f"S_REC_{int(time.time())}_{ub_idx}_{idx}"
                    nuovi_semi.append({
                        "id": unique_id,
                        "width": min(ns["width"], ns["height"]),
                        "height": max(ns["width"], ns["height"]),
                        "thickness": ns["thickness"],
                        "color_code": ns["color_code"],
                        "color_desc": ns["color_desc"],
                        "quantity": 1
                    })
                
        self.set_barre(nuove_barre)
        self.set_semilavorati(nuovi_semi)
        return True

    def export_html_report(self, risultati, filepath):
        """
        Genera un report HTML premium con grafici di taglio vettoriali SVG incorporati.
        """
        import time
        summary = risultati["summary_generale"]
        
        def _are_layouts_identical(l1, l2):
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

        def _group_layouts(layout_list):
            grouped = []
            for lay in layout_list:
                found = False
                for gb in grouped:
                    if _are_layouts_identical(gb["layout"], lay):
                        gb["qty"] += 1
                        found = True
                        break
                if not found:
                    grouped.append({
                        "layout": copy.deepcopy(lay),
                        "qty": 1
                    })
            return grouped
        
        client_name = self.config.get("client_name", "")
        client_html = ""
        if client_name:
            client_html = f'<p style="font-size: 16px; margin: 5px 0 0 0; color: #273c75; font-weight: bold;">per {client_name}</p>'
            
        html = []
        html.append("""<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <title>Report di Taglio</title>
    <style>
        body { font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif; color: #2c3e50; background-color: #f5f6fa; margin: 0; padding: 30px; }
        .container { max-width: 1000px; margin: 0 auto; background: #ffffff; padding: 40px; border-radius: 12px; box-shadow: 0 8px 24px rgba(0,0,0,0.06); }
        .header { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #f1f2f6; padding-bottom: 20px; margin-bottom: 30px; }
        .title h1 { margin: 0; color: #273c75; font-size: 28px; }
        .title p { margin: 5px 0 0 0; color: #7f8c8d; font-size: 14px; }
        .summary-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 40px; }
        .summary-card { background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #487eb0; }
        .summary-card.efficiency { border-left-color: #44bd32; }
        .summary-card.waste { border-left-color: #e84118; }
        .card-value { font-size: 24px; font-weight: bold; color: #2c3e50; margin-top: 5px; }
        .card-label { font-size: 11px; text-transform: uppercase; color: #95a5a6; font-weight: bold; letter-spacing: 0.5px; }
        .group-section { margin-bottom: 50px; }
        .group-header { background: #273c75; color: #ffffff; padding: 12px 20px; border-radius: 6px; font-size: 18px; font-weight: bold; margin-bottom: 20px; }
        .board-container { background: #fafafa; border: 1px solid #e1e2e6; border-radius: 8px; padding: 20px; margin-bottom: 30px; }
        .board-meta { display: flex; justify-content: space-between; margin-bottom: 15px; font-size: 14px; font-weight: bold; color: #34495e; }
        .svg-wrapper { background: #ffffff; border: 1px solid #eaeaea; border-radius: 6px; padding: 10px; margin-top: 10px; display: flex; justify-content: center; align-items: center; }
        .svg-wrapper svg { max-width: 100%; max-height: 480px; width: auto; height: auto; display: block; }
        table { width: 100%; border-collapse: collapse; margin: 15px 0; }
        th, td { padding: 10px 12px; text-align: left; border-bottom: 1px solid #eef0f3; font-size: 14px; }
        th { background: #f1f2f6; color: #2c3e50; font-weight: bold; }
        .badge { display: inline-block; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; color: #fff; }
        .badge.rotated { background: #e1b12c; }
        .badge.standard { background: #487eb0; }
        .badge.recupero { background: #2ecc71; }
        .print-page-break { display: none; }
        @media print {
            body { background: #ffffff; padding: 0; margin: 0; }
            .container { box-shadow: none; padding: 0; max-width: 100%; width: 100%; }
            .board-container { page-break-before: always; break-before: page; border: 1px solid #ccc; margin-bottom: 15px; padding: 10px; }
            .print-page-break { display: block; page-break-after: always; break-after: page; }
            .svg-wrapper { padding: 5px; margin-top: 5px; }
            .svg-wrapper svg { max-height: 80vh !important; max-width: 100% !important; width: auto !important; height: auto !important; }
            table { margin: 8px 0; }
            th, td { padding: 4px 8px; font-size: 11px; }
            h5 { margin: 10px 0 3px 0 !important; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="title">
                <h1>Report di Taglio</h1>
                """ + client_html + """
                <p>Generato il: """ + time.strftime("%d/%m/%Y %H:%M:%S") + """</p>
            </div>
        </div>
        
        <div class="summary-grid">
            <div class="summary-card">
                <div class="card-label">Area Barre Usate</div>
                <div class="card-value">""" + f"{summary['totale_area_lastre'] / 1e6:.2f} m²" + """</div>
            </div>
            <div class="summary-card efficiency">
                <div class="card-label">Efficienza Media</div>
                <div class="card-value">""" + f"{summary['efficienza_media']}%" + """</div>
            </div>
            <div class="summary-card">
                <div class="card-label">Area Pezzi Tagliati</div>
                <div class="card-value">""" + f"{summary['totale_area_pezzi'] / 1e6:.2f} m²" + """</div>
            </div>
            <div class="summary-card waste">
                <div class="card-label">Area Scarto</div>
                <div class="card-value">""" + f"{summary['totale_area_scarto'] / 1e6:.2f} m²" + """</div>
            </div>
        </div>
""")

        # Scorrere i gruppi di materiali
        for gk, g in risultati.get("gruppi", {}).items():
            parts = gk.split("_", 1)
            thickness_str = parts[0] if parts else gk
            color_code_str = parts[1] if len(parts) > 1 else "N/D"
            color_desc = "N/D"
            if g.get("used_boards"):
                color_desc = g["used_boards"][0]["board"].get("color_desc", "N/D")
            elif g.get("unplaced_pieces"):
                color_desc = g["unplaced_pieces"][0].get("color_desc", "N/D")
                
            html.append(f"""
        <div class="group-section">
            <div class="group-header">Materiale: Spessore {thickness_str} | Codice Colore: {color_code_str} - {color_desc} (Efficienza: {g['summary']['efficiency']}%)</div>
            
            <h3>Riepilogo Gruppo</h3>
            <table>
                <tr>
                    <th>Barre Usate</th>
                    <td>{g['summary']['total_boards_used']}</td>
                    <th>Efficienza</th>
                    <td>{g['summary']['efficiency']}%</td>
                </tr>
                <tr>
                    <th>Area Totale Barre</th>
                    <td>{g['summary']['total_board_area'] / 1e6:.2f} m²</td>
                    <th>Area Pezzi</th>
                    <td>{g['summary']['used_area'] / 1e6:.2f} m²</td>
                </tr>
                <tr>
                    <th>Area Scarto</th>
                    <td>{g['summary']['waste_area'] / 1e6:.2f} m²</td>
                    <th>Pezzi non piazzati</th>
                    <td>{len(g['unplaced_pieces'])}</td>
                </tr>
            </table>
""")

            if g['unplaced_pieces']:
                html.append("""
            <h4 style="color:#e84118;">Pezzi NON Piazzati</h4>
            <table>
                <thead>
                    <tr>
                        <th>Descrizione</th>
                        <th>Larghezza</th>
                        <th>Altezza</th>
                        <th>Spessore</th>
                        <th>Colore</th>
                    </tr>
                </thead>
                <tbody>
""")
                for up in g['unplaced_pieces']:
                    html.append(f"""
                    <tr>
                        <td>{up['descrizione']}</td>
                        <td>{up['width']} mm</td>
                        <td>{up['height']} mm</td>
                        <td>{up['thickness']} mm</td>
                        <td>{up['color_desc']} ({up['color_code']})</td>
                    </tr>
""")
                html.append("""
                </tbody>
            </table>
""")

            # Schemi delle singole lastre raggruppate
            grouped_boards = _group_layouts(g.get("used_boards", []))
            for b_idx, gb in enumerate(grouped_boards):
                ub = gb["layout"]
                qty = gb["qty"]
                board = ub["board"]
                bw = board["width"]
                bh = board["height"]
                efficiency = ub["efficiency"]
                
                # SVG del layout
                svg_content = self._generate_layout_svg(ub)
                
                # Rileva se la barra è virtuale/mancante
                is_virtual = (board.get("_source_type") == "barre_virtual") or (board.get("id") == "BARRA_VIRTUALE_DUMMY") or ("virtual" in str(board.get("id")).lower())
                board_style = "border: 2px solid #e84118; background: #fff5f5;" if is_virtual else ""
                virtual_badge = ' <span class="badge" style="background:#e84118;">MANCANTE - DA ACQUISTARE</span>' if is_virtual else ""
                
                qty_badge = f' <span class="badge" style="background:#273c75; font-size: 13px; padding: 4px 10px; margin-left: 5px;">X {qty} LASTR{"E" if qty > 1 else "A"} IDENTICH{"E" if qty > 1 else "A"}</span>' if qty > 1 else ""
                
                html.append(f"""
            <div class="board-container" style="{board_style}">
                <div class="board-meta">
                    <span>Layout {b_idx + 1}: {board.get('id', 'N/D')} - {board.get('color_desc', 'N/D')} ({int(bh)} x {int(bw)} x {board.get('thickness', '')} mm){qty_badge}{virtual_badge}</span>
                    <span style="color: #44bd32;">Efficienza: {efficiency}%</span>
                </div>
                <div>
                    <strong>Pezzi posizionati:</strong> {len(ub['placed_pieces'])} | 
                    <strong>Semilavorati recuperati:</strong> {len(ub.get('new_semilavorati', []))}
                </div>
                <div class="svg-wrapper">
                    {svg_content}
                </div>
                <div class="print-page-break"></div>
                
                <h5 style="margin: 15px 0 5px 0;">Elenco Tagli</h5>
                <table>
                    <thead>
                        <tr>
                            <th>Pezzo</th>
                            <th>X (mm)</th>
                            <th>Y (mm)</th>
                            <th>W (mm)</th>
                            <th>H (mm)</th>
                            <th>Stato</th>
                        </tr>
                    </thead>
                    <tbody>
""")
                for p in ub['placed_pieces']:
                    status_badge = '<span class="badge rotated">Ruotato</span>' if p.get('rotated') else '<span class="badge standard">Standard</span>'
                    html.append(f"""
                        <tr>
                            <td>{p['descrizione']}</td>
                            <td>{int(p['x'])}</td>
                            <td>{int(p['y'])}</td>
                            <td>{int(p['w'])}</td>
                            <td>{int(p['h'])}</td>
                            <td>{status_badge}</td>
                        </tr>
""")
                
                for s in ub.get('new_semilavorati', []):
                    html.append(f"""
                        <tr>
                            <td style="color:#2ecc71; font-style:italic;">Recupero Semilavorato</td>
                            <td>{int(s.get('x', 0))}</td>
                            <td>{int(s.get('y', 0))}</td>
                            <td>{int(s.get('width'))}</td>
                            <td>{int(s.get('height'))}</td>
                            <td><span class="badge recupero">Semilavorato</span></td>
                        </tr>
""")
                    
                html.append("""
                    </tbody>
                </table>
""")
                
                # Sequenza Tagli per l'operatore
                cuts = ub.get("cuts", [])
                if cuts:
                    html.append("""
                <h5 style="margin: 20px 0 5px 0; color: #e84118;">Sequenza Tagli Sezionatrice</h5>
                <table>
                    <thead>
                        <tr>
                            <th>Step</th>
                            <th>Tipo Taglio</th>
                            <th>Quota Taglio</th>
                            <th>Lunghezza</th>
                            <th>Coordinata Inizio/Fine</th>
                        </tr>
                    </thead>
                    <tbody>
""")
                    sorted_cuts = sorted(cuts, key=lambda c: c.get("step", 0))
                    for c in sorted_cuts:
                        tipo = "Orizzontale (guide Y)" if c["type"] == "H" else "Verticale (guide X)"
                        quota = int(c["y1"]) if c["type"] == "H" else int(c["x1"])
                        lunghezza = int(abs(c["x2"] - c["x1"])) if c["type"] == "H" else int(abs(c["y2"] - c["y1"]))
                        coord = f"da X={int(c['x1'])} a X={int(c['x2'])}" if c["type"] == "H" else f"da Y={int(c['y1'])} a Y={int(c['y2'])}"
                        html.append(f"""
                        <tr>
                            <td><strong>{c.get('step', '')}</strong></td>
                            <td>{tipo}</td>
                            <td><strong>{quota} mm</strong></td>
                            <td>{lunghezza} mm</td>
                            <td>{coord}</td>
                        </tr>
""")
                    html.append("""
                    </tbody>
                </table>
""")
                
                html.append("""
            </div>
""")

            html.append("""
        </div>
""")

        html.append("""
    </div>
</body>
</html>
""")
        
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("\n".join(html))
            return True
        except Exception as e:
            print(f"Errore nella scrittura del report HTML: {e}")
            return False
            
    def _generate_layout_svg(self, ub):
        import copy
        ub = copy.deepcopy(ub)
        board = ub["board"]
        
        is_bar = (board.get("stock_type") == "semilavorato_bar") or \
                 (board.get("stock_type") == "remnant" and min(board["width"], board["height"]) < 1300.0)
                 
        if is_bar and board["width"] > board["height"]:
            bw, bh = board["width"], board["height"]
            board["width"] = bh
            board["height"] = bw
            
            for p in ub["placed_pieces"]:
                px, py, pw, ph = p["x"], p["y"], p["w"], p["h"]
                p["x"] = py
                p["y"] = px
                p["w"] = ph
                p["h"] = pw
                if "width_original" in p and "height_original" in p:
                    p["width_original"], p["height_original"] = p["height_original"], p["width_original"]
                
            for c in ub.get("cuts", []):
                cx1, cy1, cx2, cy2 = c["x1"], c["y1"], c["x2"], c["y2"]
                c["x1"] = cy1
                c["y1"] = cx1
                c["x2"] = cy2
                c["y2"] = cx2
                c["type"] = "V" if c["type"] == "H" else "H"
                
            for s in ub.get("new_semilavorati", []):
                sx, sy, sw, sh = s.get("x", 0), s.get("y", 0), s["width"], s["height"]
                s["x"] = sy
                s["y"] = sx
                s["width"] = sh
                s["height"] = sw

        bw = board["width"]
        bh = board["height"]
        pieces = ub["placed_pieces"]
        cuts = ub.get("cuts", [])
        new_semis = ub.get("new_semilavorati", [])
        
        is_virtual = (board.get("_source_type") == "barre_virtual") or (board.get("id") == "BARRA_VIRTUALE_DUMMY") or ("virtual" in str(board.get("id")).lower())
        panel_color = "#fce4e4" if is_virtual else "#dcdde1"
        border_color = "#e84118" if is_virtual else "#7f8c8d"
        border_width = 3 if is_virtual else 2

        # Calcolo font size proporzionato alla dimensione massima del pannello
        # Questo assicura che il testo scali in modo perfettamente leggibile anche quando la barra/pannello viene riscaldata su schermo/A4
        base_size = max(14.0, max(bw, bh) * 0.027)
        desc_font_size = int(base_size * 1.25)
        dim_font_size = int(base_size * 0.9)
        
        svg_parts = []
        svg_parts.append(f'<svg viewBox="0 0 {bw} {bh}" width="{bw}" height="{bh}" style="max-width: 100%; height: auto; border: 1px solid #dcdde1; background-color: #f5f6fa;" xmlns="http://www.w3.org/2000/svg">')
        
        # 1. Pannello di sfondo (scarto)
        svg_parts.append(f'  <rect x="0" y="0" width="{bw}" height="{bh}" fill="{panel_color}" stroke="{border_color}" stroke-width="{border_width}" />')
        
        # 2. Semilavorati recuperabili
        for s in new_semis:
            if "x" in s and "y" in s:
                sx, sy, sw, sh = s["x"], s["y"], s["width"], s["height"]
                svg_parts.append(f'  <rect x="{sx}" y="{sy}" width="{sw}" height="{sh}" fill="#badc58" stroke="#6ab04c" stroke-width="1.5" stroke-dasharray="6,4" />')
                s_min_dim = min(sw, sh)
                s_font_size = min(desc_font_size, int(s_min_dim * 0.22))
                s_font_size = max(11, s_font_size)
                if sh > s_font_size * 1.5 and sw > s_font_size * 3:
                    svg_parts.append(f'  <text x="{sx + sw/2}" y="{sy + sh/2}" font-family="Segoe UI, sans-serif" font-size="{s_font_size}" fill="#2c3e50" font-style="italic" text-anchor="middle" dominant-baseline="middle">Recupero {int(sw)}x{int(sh)}</text>')
                elif sh > s_font_size * 1.2 and sw > s_font_size * 2:
                    svg_parts.append(f'  <text x="{sx + sw/2}" y="{sy + sh/2}" font-family="Segoe UI, sans-serif" font-size="{s_font_size}" fill="#2c3e50" font-style="italic" text-anchor="middle" dominant-baseline="middle">{int(sw)}x{int(sh)}</text>')
        
        # 3. Pezzi posizionati
        for p in pieces:
            px, py, pw, ph = p["x"], p["y"], p["w"], p["h"]
            is_rotated = p.get("rotated", False)
            bg = "#e1b12c" if is_rotated else "#487eb0"
            border = "#44bd32" if is_rotated else "#273c75"
            svg_parts.append(f'  <rect x="{px}" y="{py}" width="{pw}" height="{ph}" fill="{bg}" stroke="{border}" stroke-width="1.5" />')
            
            desc = p.get("descrizione", "Pezzo")
            
            piece_min_dim = min(pw, ph)
            p_desc_size = min(desc_font_size, int(piece_min_dim * 0.22))
            p_desc_size = max(11, p_desc_size)
            
            p_dim_size = min(dim_font_size, int(piece_min_dim * 0.18))
            p_dim_size = max(9, p_dim_size)
            
            # Descrizione al centro
            if ph > p_desc_size * 1.5 and pw > p_desc_size * 2:
                svg_parts.append(f'  <text x="{px + pw/2}" y="{py + ph/2}" font-family="Segoe UI, sans-serif" font-weight="bold" font-size="{p_desc_size}" fill="#ffffff" text-anchor="middle" dominant-baseline="middle">{desc}</text>')
            
            # Larghezza in basso
            if pw > p_dim_size * 2 and ph > p_dim_size * 2.2:
                svg_parts.append(f'  <text x="{px + pw/2}" y="{py + ph - p_dim_size * 1.8}" font-family="Segoe UI, sans-serif" font-size="{p_dim_size}" fill="#ffffff" text-anchor="middle" dominant-baseline="middle">{int(pw)}</text>')
                
            # Altezza a sinistra (ruotata)
            if ph > p_dim_size * 2 and pw > p_dim_size * 2.2:
                hx = px + p_dim_size * 1.8
                hy = py + ph/2
                svg_parts.append(f'  <text x="{hx}" y="{hy}" transform="rotate(-90, {hx}, {hy})" font-family="Segoe UI, sans-serif" font-size="{p_dim_size}" fill="#ffffff" text-anchor="middle" dominant-baseline="middle">{int(ph)}</text>')

        # 4. Linee di taglio
        show_progression = self.config.get("show_cut_progression", True)
        if cuts:
            for c in cuts:
                svg_parts.append(f'  <line x1="{c["x1"]}" y1="{c["y1"]}" x2="{c["x2"]}" y2="{c["y2"]}" stroke="#e84118" stroke-width="2.5" stroke-dasharray="8,6" />')
                step_num = c.get("step")
                if show_progression and step_num is not None:
                    mid_x = (c["x1"] + c["x2"]) / 2
                    mid_y = (c["y1"] + c["y2"]) / 2
                    circle_r = max(10.0, max(bw, bh) * 0.008)
                    font_sz = max(8.0, max(bw, bh) * 0.0065)
                    svg_parts.append(f'  <circle cx="{mid_x}" cy="{mid_y}" r="{circle_r}" fill="#ffffff" stroke="#e84118" stroke-width="2" />')
                    svg_parts.append(f'  <text x="{mid_x}" y="{mid_y}" font-family="Segoe UI, sans-serif" font-size="{font_sz}" font-weight="bold" fill="#e84118" text-anchor="middle" dominant-baseline="central">{step_num}</text>')
        else:
            # Fallback ripiani
            shelves = ub.get("shelves", [])
            for idx, shelf in enumerate(shelves):
                if idx < len(shelves) - 1:
                    cut_y = shelf["y"] + shelf["height"]
                    svg_parts.append(f'  <line x1="0" y1="{cut_y}" x2="{bw}" y2="{cut_y}" stroke="#e84118" stroke-width="2.5" stroke-dasharray="8,6" />')
                
                shelf_pieces = [p for p in pieces if abs(p["y"] - shelf["y"]) < 1e-2]
                shelf_pieces.sort(key=lambda p: p["x"])
                for p_idx, p in enumerate(shelf_pieces):
                    if p_idx < len(shelf_pieces) - 1:
                        cut_x = p["x"] + p["w"]
                        svg_parts.append(f'  <line x1="{cut_x}" y1="{shelf["y"]}" x2="{cut_x}" y2="{shelf["y"] + shelf["height"]}" stroke="#e84118" stroke-width="2.5" stroke-dasharray="8,6" />')

        svg_parts.append('</svg>')
        return "\n".join(svg_parts)

    def import_barre_csv(self, filepath):
        """
        Legge un file CSV e mappa le colonne per importare le barre in magazzino.
        Ritorna una lista di dizionari con chiavi normalizzate.
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Il file {filepath} non esiste.")

        delimiter = ','
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                sample = f.read(2048)
                commas = sample.count(',')
                semicolons = sample.count(';')
                if semicolons > commas:
                    delimiter = ';'
        except Exception:
            pass

        barre = []
        try:
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f, delimiter=delimiter)
                headers = [h.strip().lower() for h in next(reader)]
                
                # Mappatura colonne
                synonyms = {
                    'id': ['id', 'id lastra', 'id_lastra', 'codice lastra', 'codicelastra', 'id_barra', 'id barra', 'codbarra', 'codice barra'],
                    'width': ['larghezza', 'lunghezza', 'width', 'length', 'l', 'w', 'lungh', 'largh', 'larghezzabarra_mm', 'larghezza barra'],
                    'height': ['altezza', 'height', 'h', 'alt', 'altezzabarra_mm', 'altezza barra'],
                    'thickness': ['spessore', 'thickness', 't', 'sp', 'spess', 'spessorebarra_mm', 'spessore barra'],
                    'quantity': ['quantità', 'quantita', 'qta', 'quantity', 'qty', 'quantita\'', 'n', 'pezzi', 'pezzo'],
                    'color_code': ['codbarra', 'codice colore', 'codicecolore', 'codice_colore', 'codice', 'color code', 'color_code', 'code', 'codopzione'],
                    'color_desc': ['descrizione colore', 'descrizionecolore', 'descrizione_colore', 'colore descrizione', 'color desc', 'color_desc', 'nomevariante'],
                    'color': ['colore', 'color', 'finitura'],
                    'has_grain': ['venatura', 'grain', 'has_grain', 'has grain', 'venato', 'senso venatura']
                }
                
                col_map = {}
                for key, syn_list in synonyms.items():
                    for syn in syn_list:
                        if syn in headers:
                            col_map[key] = headers.index(syn)
                            break
                
                # Fallback se mancano colonne fondamentali
                if 'width' not in col_map and len(headers) > 1: col_map['width'] = 1
                if 'height' not in col_map and len(headers) > 2: col_map['height'] = 2
                
                for row_idx, row in enumerate(reader):
                    if not row or len(row) < max(col_map.values(), default=0) + 1:
                        continue
                    
                    try:
                        id_val = row[col_map['id']].strip() if 'id' in col_map else f"B_CSV_{row_idx + 1}"
                        width_val = self._parse_float(row[col_map['width']]) if 'width' in col_map else 0.0
                        height_val = self._parse_float(row[col_map['height']]) if 'height' in col_map else 0.0
                        thick_val = self._parse_float(row[col_map['thickness']]) if 'thickness' in col_map else 0.0
                        qty_val = int(self._parse_float(row[col_map['quantity']])) if 'quantity' in col_map else 0
                        
                        color_code_val = "N/D"
                        if 'codbarra' in headers:
                            color_code_val = row[headers.index('codbarra')].strip()
                        elif 'color_code' in col_map:
                            color_code_val = row[col_map['color_code']].strip()
                            
                        color_desc_val = row[col_map['color_desc']].strip() if 'color_desc' in col_map else "N/D"
                        if color_desc_val == "N/D" and 'color' in col_map:
                            color_desc_val = row[col_map['color']].strip()
                            
                        # Venatura
                        grain_val = False
                        if 'has_grain' in col_map:
                            val_str = row[col_map['has_grain']].strip().lower()
                            if val_str in ['si', 'sì', 'yes', 'true', '1', 'v', 'vero']:
                                grain_val = True
                                
                        barre.append({
                            "id": id_val,
                            "width": width_val,
                            "height": height_val,
                            "thickness": thick_val,
                            "color_code": color_code_val,
                            "color_desc": color_desc_val,
                            "has_grain": grain_val,
                            "quantity": qty_val
                        })
                    except (ValueError, IndexError) as ve:
                        print(f"Errore alla riga {row_idx + 2}: {ve}. Riga saltata.")
                        continue
        except Exception as e:
            raise ValueError(f"Impossibile leggere il file CSV: {e}")

        return barre

    def import_semilavorati_csv(self, filepath):
        """
        Legge un file CSV e mappa le colonne per importare i semilavorati in magazzino.
        Ritorna una lista di dizionari con chiavi normalizzate.
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Il file {filepath} non esiste.")

        delimiter = ','
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                sample = f.read(2048)
                commas = sample.count(',')
                semicolons = sample.count(';')
                if semicolons > commas:
                    delimiter = ';'
        except Exception:
            pass

        semis = []
        try:
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f, delimiter=delimiter)
                headers = [h.strip().lower() for h in next(reader)]
                
                # Mappatura colonne
                synonyms = {
                    'id': ['id', 'id pezzo', 'id_pezzo', 'codice pezzo', 'codicepezzo', 'id_semi', 'id semilavorato', 'codbarra', 'codice barra', 'codice_barra'],
                    'width': ['larghezza', 'lunghezza', 'width', 'length', 'l', 'w', 'lungh', 'largh', 'larghezza_mm', 'larghezza barra', 'larghezzabarra_mm'],
                    'height': ['altezza', 'height', 'h', 'alt', 'altezza_mm', 'altezza barra', 'altezzabarra_mm'],
                    'thickness': ['spessore', 'thickness', 't', 'sp', 'spess', 'spessore_mm', 'spessore barra', 'spessorebarra_mm'],
                    'quantity': ['quantità', 'quantita', 'qta', 'quantity', 'qty', 'quantita\''],
                    'color_code': ['codbarra', 'codice colore', 'codicecolore', 'codice_colore', 'codice', 'color code', 'color_code', 'code', 'codopzione'],
                    'color_desc': ['descrizione colore', 'descrizionecolore', 'descrizione_colore', 'colore descrizione', 'color desc', 'color_desc', 'nomevariante'],
                    'color': ['colore', 'color', 'finitura'],
                    'has_grain': ['venatura', 'grain', 'has_grain', 'has grain', 'venato', 'senso venatura']
                }
                
                col_map = {}
                for key, syn_list in synonyms.items():
                    for syn in syn_list:
                        if syn in headers:
                            col_map[key] = headers.index(syn)
                            break
                
                if 'width' not in col_map and len(headers) > 1: col_map['width'] = 1
                if 'height' not in col_map and len(headers) > 2: col_map['height'] = 2
                
                # Dizionario temporaneo per raggruppare i pezzi identici
                aggregated = {}
                
                for row_idx, row in enumerate(reader):
                    if not row or len(row) < max(col_map.values(), default=0) + 1:
                        continue
                    
                    try:
                        width_val = self._parse_float(row[col_map['width']]) if 'width' in col_map else 0.0
                        height_val = self._parse_float(row[col_map['height']]) if 'height' in col_map else 0.0
                        
                        db_width = min(width_val, height_val)
                        db_height = max(width_val, height_val)
                        thick_val = self._parse_float(row[col_map['thickness']]) if 'thickness' in col_map else 0.0
                        qty_val = int(self._parse_float(row[col_map['quantity']])) if 'quantity' in col_map else 0
                        
                        color_code_val = row[col_map['color_code']].strip() if 'color_code' in col_map else "N/D"
                        color_desc_val = row[col_map['color_desc']].strip() if 'color_desc' in col_map else "N/D"
                        if color_desc_val == "N/D" and 'color' in col_map:
                            color_desc_val = row[col_map['color']].strip()
                            
                        # Venatura
                        grain_val = False
                        if 'has_grain' in col_map:
                            val_str = row[col_map['has_grain']].strip().lower()
                            if val_str in ['si', 'sì', 'yes', 'true', '1', 'v', 'vero']:
                                grain_val = True
                                
                        # Calcola o leggi ID
                        has_explicit_id = 'id' in col_map and headers[col_map['id']] not in ['codbarra', 'codice barra', 'codice_barra']
                        if has_explicit_id:
                            id_val = row[col_map['id']].strip()
                        else:
                            # Se non c'è ID esplicito o se è mappato solo sul codice a barre,
                            # costruiamo un ID univoco descrittivo basato su materiale e dimensioni
                            base_id = row[col_map['id']].strip() if 'id' in col_map else color_code_val
                            if not base_id or base_id == "N/D":
                                base_id = "S_CSV"
                            clean_base = base_id.replace("\\", "_").replace("/", "_")
                            id_val = f"{clean_base}_{int(db_width)}x{int(db_height)}"
                            
                        # Se è un pannello semilavorato (non un residuo S_REC_), impostiamo la quantità a 0
                        if not id_val.startswith("S_REC_"):
                            qty_val = 0
                            
                        # Usiamo come chiave di raggruppamento per sommare le quantità di pezzi identici
                        key = (id_val, db_width, db_height, thick_val, color_code_val, color_desc_val, grain_val)
                        if key in aggregated:
                            aggregated[key]['quantity'] += qty_val
                        else:
                            aggregated[key] = {
                                "id": id_val,
                                "width": db_width,
                                "height": db_height,
                                "thickness": thick_val,
                                "color_code": color_code_val,
                                "color_desc": color_desc_val,
                                "has_grain": grain_val,
                                "quantity": qty_val
                            }
                    except (ValueError, IndexError) as ve:
                        print(f"Errore alla riga {row_idx + 2}: {ve}. Riga saltata.")
                        continue
                
                semis = list(aggregated.values())
        except Exception as e:
            raise ValueError(f"Impossibile leggere il file CSV: {e}")

        return semis

    def export_pdf_report(self, risultati, filepath):
        """
        Esporta il report di taglio in formato PDF utilizando Google Chrome in modalità headless.
        Genera temporaneamente un report HTML e lo converte in PDF.
        """
        import subprocess
        
        # Converte filepath in percorso assoluto per evitare problemi di risoluzione percorsi in Chrome
        abs_filepath = os.path.abspath(filepath)
        temp_html = abs_filepath.replace(".pdf", "_temp.html")
        success = self.export_html_report(risultati, temp_html)
        if not success:
            return False
            
        try:
            # 2. Individua l'eseguibile di Google Chrome su Windows
            chrome_paths = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                os.path.join(os.environ.get("LOCALAPPDATA", ""), r"Google\Chrome\Application\chrome.exe")
            ]
            
            chrome_bin = None
            for path in chrome_paths:
                if os.path.exists(path):
                    chrome_bin = path
                    break
                    
            if not chrome_bin:
                # Se non trovato in percorsi standard, prova come comando generico 'chrome'
                chrome_bin = "chrome"
                
            args = [
                chrome_bin,
                "--headless",
                "--disable-gpu",
                "--no-pdf-header-footer",
                f"--print-to-pdf={abs_filepath}",
                temp_html
            ]
            
            # Esegue il processo in background in modo sincrono con timeout
            result = subprocess.run(args, capture_output=True, text=True, timeout=20)
            
            # Rimuove il file HTML temporaneo
            if os.path.exists(temp_html):
                os.remove(temp_html)
                
            return os.path.exists(abs_filepath)
            
        except Exception as e:
            print(f"Errore nella generazione del report PDF con Chrome Headless: {e}")
            if os.path.exists(temp_html):
                try:
                    os.remove(temp_html)
                except Exception:
                    pass
            return False

    def get_commesse(self):
        """Ritorna l'elenco delle commesse salvate."""
        self.db = self.load_db()
        return self.db.get("commesse", [])

    def save_commessa(self, commessa_id, nome, pezzi, stato="Aperta"):
        """
        Salva o aggiorna una commessa nel database.
        Se commessa_id è None, genera un nuovo ID auto-incrementale.
        Ritorna la commessa salvata.
        """
        if self.db_type == "sql":
            import datetime
            conn = self._get_sql_connection()
            try:
                cursor = conn.cursor()
                if commessa_id is None:
                    cursor.execute("SELECT MAX(id) FROM commesse")
                    val = cursor.fetchone()[0]
                    commessa_id = (int(val) + 1) if val is not None else 1
                
                query_check = "SELECT id, data_creazione, stato FROM commesse WHERE id = %s"
                self._execute_query(cursor, query_check, (commessa_id,))
                row = cursor.fetchone()
                
                pezzi_str = json.dumps(pezzi, ensure_ascii=False)
                if row:
                    data_creazione = row[1]
                    exist_stato = row[2]
                    if exist_stato == "Chiusa":
                        raise ValueError("Non è possibile modificare una commessa chiusa.")
                    query_upd = "UPDATE commesse SET nome = %s, pezzi = %s, stato = %s WHERE id = %s"
                    self._execute_query(cursor, query_upd, (nome, pezzi_str, stato, commessa_id))
                else:
                    data_creazione = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
                    query_ins = "INSERT INTO commesse (id, nome, stato, data_creazione, pezzi) VALUES (%s, %s, %s, %s, %s)"
                    self._execute_query(cursor, query_ins, (commessa_id, nome, stato, data_creazione, pezzi_str))
                conn.commit()
                
                return {
                    "id": commessa_id,
                    "nome": nome,
                    "stato": stato,
                    "data_creazione": data_creazione,
                    "pezzi": pezzi
                }
            finally:
                conn.close()

        self.db = self.load_db()
        commesse = self.get_commesse()
        
        if commessa_id is None:
            # Genera nuovo ID automatico
            ids = [c["id"] for c in commesse if isinstance(c["id"], int)]
            commessa_id = max(ids, default=0) + 1
            import datetime
            data_creazione = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
            new_commessa = {
                "id": commessa_id,
                "nome": nome,
                "stato": stato,
                "data_creazione": data_creazione,
                "pezzi": pezzi
            }
            commesse.append(new_commessa)
        else:
            # Trova la commessa esistente
            found = False
            for c in commesse:
                if c["id"] == commessa_id:
                    if c.get("stato", "Aperta") == "Chiusa":
                        raise ValueError("Non è possibile modificare una commessa chiusa.")
                    c["nome"] = nome
                    c["pezzi"] = pezzi
                    c["stato"] = stato
                    found = True
                    new_commessa = c
                    break
            if not found:
                import datetime
                data_creazione = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
                new_commessa = {
                    "id": commessa_id,
                    "nome": nome,
                    "stato": stato,
                    "data_creazione": data_creazione,
                    "pezzi": pezzi
                }
                commesse.append(new_commessa)
        
        self.db["commesse"] = commesse
        self.save_db()
        return new_commessa

    def delete_commessa(self, commessa_id):
        """Elimina una commessa dal database."""
        if self.db_type == "sql":
            conn = self._get_sql_connection()
            try:
                cursor = conn.cursor()
                query = "DELETE FROM commesse WHERE id = %s"
                self._execute_query(cursor, query, (commessa_id,))
                conn.commit()
            finally:
                conn.close()
            return

        self.db = self.load_db()
        commesse = self.get_commesse()
        commesse = [c for c in commesse if c["id"] != commessa_id]
        self.db["commesse"] = commesse
        self.save_db()

    def close_commessa(self, commessa_id):
        """Chiude una commessa (la segna come Chiusa)."""
        if self.db_type == "sql":
            conn = self._get_sql_connection()
            try:
                cursor = conn.cursor()
                query = "UPDATE commesse SET stato = 'Chiusa' WHERE id = %s"
                self._execute_query(cursor, query, (commessa_id,))
                conn.commit()
            finally:
                conn.close()
            return

        self.db = self.load_db()
        commesse = self.get_commesse()
        for c in commesse:
            if c["id"] == commessa_id:
                c["stato"] = "Chiusa"
                break
        self.db["commesse"] = commesse
        self.save_db()

