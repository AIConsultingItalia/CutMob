import os
import sys
import zipfile
import shutil
import subprocess
import re

def get_version():
    try:
        with open("app.py", "r", encoding="utf-8") as f:
            for line in f:
                if "self.APP_VERSION =" in line:
                    m = re.search(r'self\.APP_VERSION\s*=\s*"([^"]+)"', line)
                    if m:
                        return m.group(1)
    except Exception as e:
        print(f"Errore nel recupero della versione: {e}")
    return "unknown"

def main():
    version = get_version()
    print(f"Versione rilevata nel codice: {version}")

    print("\n=== 1. COMPILAZIONE APPLICAZIONE PRINCIPALE (CutMob) ===")
    if not os.path.exists("CutMob.spec"):
        print("Errore: CutMob.spec non trovato.")
        return
        
    # Rimuovi la directory dist/CutMob se esiste per evitare cache obsolete
    dist_dir = os.path.join("dist", "CutMob")
    if os.path.exists(dist_dir):
        print(f"Pulizia cartella di output: {dist_dir}")
        shutil.rmtree(dist_dir, ignore_errors=True)

    cmd_compile_app = ["python", "-m", "PyInstaller", "--clean", "--noconfirm", "CutMob.spec"]
    print(f"Esecuzione: {' '.join(cmd_compile_app)}")
    res = subprocess.run(cmd_compile_app)
    if res.returncode != 0:
        print("Errore nella compilazione di CutMob.")
        return
        
    print("\n=== 2. CREAZIONE ARCHIVIO ZIP PER LA DISTRIBUZIONE ===")
    if not os.path.exists(dist_dir):
        print(f"Errore: la cartella compilata {dist_dir} non esiste.")
        return
        
    zip_path = os.path.join("dist", "Setup_CutMob.zip")
    if os.path.exists(zip_path):
        os.remove(zip_path)
        
    print(f"Creazione di {zip_path} a partire da {dist_dir}...")
    
    # Comprimiamo il contenuto della cartella dist/CutMob
    # in modo che estraendo lo zip venga creata la cartella "CutMob"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(dist_dir):
            for file in files:
                file_path = os.path.join(root, file)
                # Calcola il percorso relativo interno allo zip (in modo che contenga la cartella radice CutMob/)
                rel_path = os.path.relpath(file_path, os.path.dirname(dist_dir))
                zipf.write(file_path, rel_path)
                
    print("Archivio zip generico creato con successo.")
    
    # Crea la copia con il numero di versione nel nome
    versioned_zip_path = os.path.join("dist", f"Setup_CutMob_{version}.zip")
    try:
        shutil.copy2(zip_path, versioned_zip_path)
        print(f"Copia del file creata con successo: {versioned_zip_path}")
    except Exception as e:
        print(f"Errore nella creazione della copia con versione: {e}")
        
    print("\n=======================================================")
    print(" GENERAZIONE COMPLETATA!")
    print(f" Il file Setup_CutMob_{version}.zip è disponibile in: dist/Setup_CutMob_{version}.zip")
    print("=======================================================")

if __name__ == "__main__":
    main()
