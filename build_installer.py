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
        
    # 2. Creazione dell'archivio intermedio dist/cutmob_dist.zip per l'installer
    zip_dist_target = os.path.join("dist", "cutmob_dist.zip")
    if os.path.exists(zip_dist_target):
        os.remove(zip_dist_target)
        
    print(f"\n=== 2. IMPACCHETTAMENTO APPLICAZIONE ({zip_dist_target}) ===")
    with zipfile.ZipFile(zip_dist_target, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(dist_dir):
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, os.path.dirname(dist_dir))
                zipf.write(file_path, rel_path)

    # 3. Compilazione dell'Installer monolitico Setup_CutMob.exe (con icona)
    print("\n=== 3. COMPILAZIONE INSTALLER ESEGUIBILE (Setup_CutMob.exe) ===")
    cmd_compile_setup = ["python", "-m", "PyInstaller", "--clean", "--noconfirm", "Setup_CutMob.spec"]
    print(f"Esecuzione: {' '.join(cmd_compile_setup)}")
    res_setup = subprocess.run(cmd_compile_setup)
    if res_setup.returncode != 0:
        print("Errore nella compilazione dell'installer Setup_CutMob.exe.")
        return

    # 4. Creazione dell'Archivio Zip Finale di Distribuzione (Setup_CutMob.zip contenente Setup_CutMob.exe)
    print("\n=== 4. CREAZIONE ARCHIVIO ZIP FINALE (Setup_CutMob.zip) ===")
    exe_target = os.path.join("dist", "Setup_CutMob.exe")
    zip_path = os.path.join("dist", "Setup_CutMob.zip")
    if os.path.exists(zip_path):
        os.remove(zip_path)

    if os.path.exists(exe_target):
        print(f"Inserimento di Setup_CutMob.exe all'interno di {zip_path}...")
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(exe_target, arcname="Setup_CutMob.exe")
        print(f"Archivio {zip_path} creato con successo!")

    # 5. Copia versionata dei file generati per la distribuzione
    versioned_zip = os.path.join("dist", f"Setup_CutMob_{version}.zip")
    versioned_exe = os.path.join("dist", f"Setup_CutMob_{version}.exe")
    
    if os.path.exists(zip_path):
        shutil.copy2(zip_path, versioned_zip)
    if os.path.exists(exe_target):
        shutil.copy2(exe_target, versioned_exe)

    print("\n=======================================================")
    print(" GENERAZIONE COMPLETATA CON SUCCESSO!")
    print(" File pronti per la distribuzione:")
    print(f" - Zip distribuibile (contiene Setup_CutMob.exe): {zip_path}")
    print(f" - Exe eseguibile diretto: {exe_target}")
    print("=======================================================")

if __name__ == "__main__":
    main()
