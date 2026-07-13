import os
import sys
import zipfile
import subprocess
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk

INSTALL_DIR = r"C:\CutMob"
DB_DIR = os.path.join(INSTALL_DIR, "DbDati")
LICENSE_PATH = os.path.join(DB_DIR, "licenza.key")
CONFIG_PATH = os.path.join(DB_DIR, "config.json")
DATABASE_PATH = os.path.join(DB_DIR, "database.json")

def merge_configs(existing_path, default_config):
    import json
    import base64
    key = b"CutMobSecurityKey2026!"
    try:
        with open(existing_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
        try:
            obfuscated_bytes = base64.b64decode(content)
            decrypted = bytearray()
            for i in range(len(obfuscated_bytes)):
                decrypted.append(obfuscated_bytes[i] ^ key[i % len(key)])
            user_config = json.loads(decrypted.decode("utf-8"))
        except Exception:
            user_config = json.loads(content)
    except Exception:
        user_config = {}

    updated = False
    for k, v in default_config.items():
        if k not in user_config:
            user_config[k] = v
            updated = True
            
    if updated or not os.path.exists(existing_path):
        data_bytes = json.dumps(user_config, indent=4).encode("utf-8")
        obfuscated = bytearray()
        for i in range(len(data_bytes)):
            obfuscated.append(data_bytes[i] ^ key[i % len(key)])
        obfuscated_str = base64.b64encode(obfuscated).decode("utf-8")
        with open(existing_path, "w", encoding="utf-8") as f:
            f.write(obfuscated_str)

def merge_databases(existing_path, default_db):
    import json
    try:
        with open(existing_path, "r", encoding="utf-8") as f:
            user_db = json.load(f)
    except Exception:
        user_db = {}
        
    updated = False
    for k, v in default_db.items():
        if k not in user_db:
            user_db[k] = v
            updated = True
            
    if updated:
        with open(existing_path, "w", encoding="utf-8") as f:
            json.dump(user_db, f, indent=4)

class InstallerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Setup - CutMob")
        self.root.geometry("500x380")
        self.root.resizable(False, False)
        self.root.configure(bg="#f5f6fa")
        
        # Stile di design
        self.primary_color = "#273c75"
        self.text_color = "#2f3640"
        
        # Verifica se è presente la licenza
        self.is_update = os.path.exists(LICENSE_PATH)
        
        self.setup_ui()
        
    def setup_ui(self):
        # Header
        header_frame = tk.Frame(self.root, bg=self.primary_color, height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        lbl_title = tk.Label(header_frame, text="Installazione / Aggiornamento CutMob", 
                             font=("Segoe UI", 14, "bold"), fg="white", bg=self.primary_color)
        lbl_title.pack(side=tk.LEFT, padx=20, pady=20)
        
        # Main content area
        content_frame = tk.Frame(self.root, bg="#f5f6fa", padx=30, pady=25)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Stato rilevato
        if self.is_update:
            status_text = "Rilevata installazione precedente attiva."
            description = (
                "È stata trovata una licenza valida in C:\\CutMob.\n\n"
                "Procedendo, l'installer aggiornerà l'applicazione all'ultima versione "
                "mantenendo intatti tutti i dati esistenti:\n"
                "• I database delle commesse e materiali\n"
                "• La configurazione e i parametri macchina\n"
                "• La chiave di licenza attiva"
            )
            btn_text = "Aggiorna CutMob"
        else:
            status_text = "Nessuna installazione precedente trovata."
            description = (
                "Verrà configurata una nuova installazione di CutMob sul computer.\n\n"
                "Il programma verrà installato nella cartella predefinita:\n"
                "• C:\\CutMob\n\n"
                "Al termine dell'installazione, l'applicazione verrà avviata "
                "e ti verrà richiesto di inserire la chiave di licenza per l'attivazione."
            )
            btn_text = "Installa CutMob"
            
        lbl_status = tk.Label(content_frame, text=status_text, font=("Segoe UI", 11, "bold"), 
                             fg=self.primary_color if self.is_update else "#2f3640", bg="#f5f6fa")
        lbl_status.pack(anchor=tk.W, pady=(0, 10))
        
        lbl_desc = tk.Label(content_frame, text=description, font=("Segoe UI", 10), 
                            fg=self.text_color, bg="#f5f6fa", justify=tk.LEFT, wraplength=440)
        lbl_desc.pack(anchor=tk.W, pady=(0, 20))
        
        # Barra di progresso
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(content_frame, variable=self.progress_var, maximum=100)
        
        self.lbl_progress_status = tk.Label(content_frame, text="", font=("Segoe UI", 9, "italic"),
                                            fg="#7f8c8d", bg="#f5f6fa")
        
        # Area pulsanti
        btn_frame = tk.Frame(content_frame, bg="#f5f6fa")
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))
        
        btn_cancel = tk.Button(btn_frame, text="Annulla", font=("Segoe UI", 10), 
                              command=self.root.destroy, width=12, bg="#dcdde1", fg="#2f3640",
                              relief=tk.FLAT, bd=0)
        btn_cancel.pack(side=tk.RIGHT, padx=(10, 0))
        
        self.btn_action = tk.Button(btn_frame, text=btn_text, font=("Segoe UI", 10, "bold"), 
                                   command=self.start_install, width=18, bg="#44bd32", fg="white",
                                   relief=tk.FLAT, bd=0)
        self.btn_action.pack(side=tk.RIGHT)
        
    def start_install(self):
        self.btn_action.config(state=tk.DISABLED)
        self.progress_bar.pack(fill=tk.X, pady=(0, 5))
        self.lbl_progress_status.pack(anchor=tk.W)
        self.root.update()
        
        try:
            # Trova la risorsa zip incorporata (PyInstaller estrae in sys._MEIPASS)
            base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
            zip_name = "cutmob_dist.zip"
            zip_path = os.path.join(base_path, zip_name)
            
            if not os.path.exists(zip_path):
                # Caso di fallback se testato come script
                zip_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist", zip_name)
                if not os.path.exists(zip_path):
                    raise FileNotFoundError(f"Archivio di installazione non trovato ({zip_name}).")
            
            # Crea cartelle base
            self.lbl_progress_status.config(text="Preparazione cartelle...")
            self.progress_var.set(10)
            self.root.update()
            
            os.makedirs(INSTALL_DIR, exist_ok=True)
            os.makedirs(DB_DIR, exist_ok=True)
            os.makedirs(os.path.join(INSTALL_DIR, "Report", "HTML"), exist_ok=True)
            os.makedirs(os.path.join(INSTALL_DIR, "Report", "PDF"), exist_ok=True)
            
            self.lbl_progress_status.config(text="Estrazione file...")
            self.progress_var.set(30)
            self.root.update()
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                total_files = len(file_list)
                
                for i, member in enumerate(file_list):
                    # Costruisci il percorso di destinazione
                    # Rimuoviamo il prefisso 'CutMob/' se presente per estrarre direttamente
                    parts = member.split('/', 1)
                    if len(parts) > 1 and parts[1]:
                        rel_path = parts[1]
                    else:
                        if parts[0] == 'CutMob':
                            continue
                        rel_path = member
                        
                    target_path = os.path.join(INSTALL_DIR, rel_path)
                    
                    # Evita sovrascrittura di file dati sensibili se già esistenti
                    if self.is_update:
                        normalized_target = target_path.lower()
                        if normalized_target.endswith("database.json") or \
                           normalized_target.endswith("config.json") or \
                           normalized_target.endswith("licenza.key"):
                            if os.path.exists(target_path):
                                continue # Mantieni file esistente
                                
                    # Se è una directory, creala
                    if member.endswith('/'):
                        os.makedirs(target_path, exist_ok=True)
                    else:
                        os.makedirs(os.path.dirname(target_path), exist_ok=True)
                        with open(target_path, "wb") as f_out:
                            f_out.write(zip_ref.read(member))
                            
                    # Aggiorna progresso (da 30% a 90%)
                    prog = 30 + int((i / total_files) * 60)
                    self.progress_var.set(prog)
                    if i % 10 == 0:
                        self.root.update()
                        
            # Configurazione iniziale e allineamento (sia per nuove installazioni che per aggiornamenti)
            self.lbl_progress_status.config(text="Configurazione dei dati...")
            self.root.update()
            
            default_db = {"barre": [], "semilavorati": [], "commesse": []}
            default_config = {
                "db_type": "local",
                "local_path": DATABASE_PATH,
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
                "client_name": "",
                "client_cf_piva": "",
                "client_email": "",
                "license_enabled": True
            }
            
            # Esegui il merge/creazione del database
            merge_databases(DATABASE_PATH, default_db)
            
            # Esegui il merge/creazione della configurazione
            merge_configs(CONFIG_PATH, default_config)
                        
            self.progress_var.set(100)
            self.lbl_progress_status.config(text="Completato!")
            self.root.update()
            
            # Messaggio di successo
            msg_succ = "Aggiornamento completato con successo!" if self.is_update else "Installazione completata con successo!"
            messagebox.showinfo("Successo", msg_succ)
            
            # Avvia l'applicazione
            exe_path = os.path.join(INSTALL_DIR, "CutMob.exe")
            if os.path.exists(exe_path):
                subprocess.Popen([exe_path], cwd=INSTALL_DIR)
                
            self.root.destroy()
            
        except Exception as e:
            messagebox.showerror("Errore di installazione", f"Si è verificato un errore durante l'operazione:\n{str(e)}")
            self.btn_action.config(state=tk.NORMAL)
            self.lbl_progress_status.config(text="Errore.")
            self.progress_var.set(0)

if __name__ == "__main__":
    root = tk.Tk()
    app = InstallerApp(root)
    root.mainloop()
