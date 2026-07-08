import os
import sys
import zipfile
import shutil
import subprocess

def main():
    print("=== 1. COMPILAZIONE APPLICAZIONE PRINCIPALE (CutMob) ===")
    # Assicurati di compilare CutMob.spec
    if not os.path.exists("CutMob.spec"):
        print("Errore: CutMob.spec non trovato.")
        return
        
    # Rimuovi la directory dist/CutMob se esiste per evitare errori di PyInstaller
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
        
    print("\n=== 2. CREAZIONE ARCHIVIO ZIP DEI FILE COMPILATI ===")
    dist_dir = os.path.join("dist", "CutMob")
    if not os.path.exists(dist_dir):
        print(f"Errore: la cartella compilata {dist_dir} non esiste.")
        return
        
    zip_path = os.path.join("dist", "cutmob_dist.zip")
    if os.path.exists(zip_path):
        os.remove(zip_path)
        
    print(f"Creazione di {zip_path} a partire da {dist_dir}...")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(dist_dir):
            for file in files:
                file_path = os.path.join(root, file)
                # Calcola il percorso relativo interno allo zip (es. CutMob/app.exe)
                rel_path = os.path.relpath(file_path, os.path.dirname(dist_dir))
                zipf.write(file_path, rel_path)
                
    print("Archivio zip creato con successo.")
    
    print("\n=== 3. COMPILAZIONE SETUP_CUTMOB.EXE ===")
    if not os.path.exists("installer.py"):
        print("Errore: installer.py non trovato.")
        return
        
    # Compila installer.py includendo cutmob_dist.zip come risorsa
    cmd_compile_installer = [
        "python", "-m", "PyInstaller",
        "--clean",
        "--noconfirm",
        "--onefile",
        "--noconsole",
        "--add-data", "dist/cutmob_dist.zip;.",
        "--name", "Setup_CutMob",
        "installer.py"
    ]
    print(f"Esecuzione: {' '.join(cmd_compile_installer)}")
    res = subprocess.run(cmd_compile_installer)
    if res.returncode != 0:
        print("Errore nella compilazione dell'installer.")
        return
        
    print("\n=== 4. PULIZIA FILE TEMPORANEI ===")
    if os.path.exists(zip_path):
        os.remove(zip_path)
        print("Rimosso archivio zip temporaneo.")
        
    print("\n=======================================================")
    print(" GENERAZIONE COMPLETATA!")
    print(" Il file Setup_CutMob.exe è disponibile in: dist/Setup_CutMob.exe")
    print("=======================================================")

if __name__ == "__main__":
    main()
