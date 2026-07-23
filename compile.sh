#!/bin/bash

echo "=================================================="
echo "  CutMob - AVVIO COMPILAZIONE APPLICAZIONE (macOS)"
echo "=================================================="

# 1. Installa PyInstaller se non presente
if ! command -v pyinstaller &> /dev/null
then
    echo "PyInstaller non trovato. Installazione in corso..."
    pip3 install pyinstaller
    if [ $? -ne 0 ]; then
        echo "Errore durante l'installazione di PyInstaller!"
        exit 1
    fi
fi

# 2. Genera/Aggiorna logo.icns da app_icon.ico (o logo.png) per macOS
if [ -f "app_icon.ico" ]; then
    echo "Generazione di logo.icns da app_icon.ico..."
    python3 -c "from PIL import Image; img = Image.open('app_icon.ico'); img.seek(0); img.save('app_icon_base.png')" &>/dev/null
    SRC_IMG="app_icon_base.png"
elif [ -f "logo.png" ]; then
    SRC_IMG="logo.png"
fi

if [ -n "$SRC_IMG" ]; then
    mkdir -p logo.iconset
    sips -z 16 16 "$SRC_IMG" --out logo.iconset/icon_16x16.png &>/dev/null
    sips -z 32 32 "$SRC_IMG" --out logo.iconset/icon_16x16@2x.png &>/dev/null
    sips -z 32 32 "$SRC_IMG" --out logo.iconset/icon_32x32.png &>/dev/null
    sips -z 64 64 "$SRC_IMG" --out logo.iconset/icon_32x32@2x.png &>/dev/null
    sips -z 128 128 "$SRC_IMG" --out logo.iconset/icon_128x128.png &>/dev/null
    sips -z 256 256 "$SRC_IMG" --out logo.iconset/icon_128x128@2x.png &>/dev/null
    sips -z 256 256 "$SRC_IMG" --out logo.iconset/icon_256x256.png &>/dev/null
    sips -z 512 512 "$SRC_IMG" --out logo.iconset/icon_256x256@2x.png &>/dev/null
    sips -z 512 512 "$SRC_IMG" --out logo.iconset/icon_512x512.png &>/dev/null
    sips -z 1024 1024 "$SRC_IMG" --out logo.iconset/icon_512x512@2x.png &>/dev/null
    iconutil -c icns logo.iconset &>/dev/null
    rm -rf logo.iconset app_icon_base.png
fi

# 3. Avvia la compilazione
echo "Pulizia directory build/dist..."
rm -rf dist build
echo "Compilazione con PyInstaller..."
python3 -m PyInstaller --clean --noconfirm CutMob.spec
if [ $? -ne 0 ]; then
    echo "Errore nella compilazione dell'applicazione!"
    exit 1
fi

# 4. Crea la struttura di cartelle richiesta nella cartella Home (~/CutMob)
echo "Creazione struttura cartelle in ~/CutMob..."
BASE_DIR="$HOME/CutMob"
mkdir -p "$BASE_DIR"
mkdir -p "$BASE_DIR/DbDati"
mkdir -p "$BASE_DIR/Report"
mkdir -p "$BASE_DIR/Report/HTML"
mkdir -p "$BASE_DIR/Report/PDF"
mkdir -p "$BASE_DIR/Report/Pannelli"
mkdir -p "$BASE_DIR/Report/Barre"
mkdir -p "$BASE_DIR/Report/Elem_Cutmob"

# 5. Copia l'applicazione compilata nella cartella di destinazione e sul Desktop
echo "Copia dell'applicazione compilata in ~/CutMob e sul Desktop..."
DESKTOP_DIR="$HOME/Desktop"
if [ -d "dist/CutMob.app" ]; then
    rm -rf "$BASE_DIR/CutMob.app"
    cp -R dist/CutMob.app "$BASE_DIR/"
    echo "CutMob.app copiata con successo in ~/CutMob."
    rm -rf "$DESKTOP_DIR/CutMob.app"
    cp -R dist/CutMob.app "$DESKTOP_DIR/"
    echo "Icona di avvio CutMob.app creata sul Desktop!"
elif [ -d "dist/CutMob" ]; then
    rm -rf "$BASE_DIR/CutMob"
    cp -R dist/CutMob "$BASE_DIR/"
    echo "Applicazione cartella copiata con successo in ~/CutMob."
fi

# 5. Scelta gestione Database
echo ""
echo "=================================================="
echo "  GESTIONE DATABASE E CONFIGURAZIONE ($BASE_DIR/DbDati)"
echo "=================================================="
echo "  1] Inizializza con DB a zero (vuoto) e impostazioni di default"
echo "  2] Copia/Mantieni dati già esistenti (tabelle DB locali)"
echo "=================================================="
read -p "Scegli un'opzione [1 o 2]: " choice

if [ "$choice" = "1" ]; then
    echo "Inizializzazione database e configurazione vuoti..."
    python3 -c "import json, os; open(os.path.expanduser('~/CutMob/DbDati/database.json'), 'w', encoding='utf-8').write(json.dumps({'barre': [], 'semilavorati': [], 'commesse': []}, indent=4))"
    python3 -c "import json, os; open(os.path.expanduser('~/CutMob/DbDati/config.json'), 'w', encoding='utf-8').write(json.dumps({'db_type': 'local', 'local_path': os.path.expanduser('~/CutMob/DbDati/database.json'), 'sql_type': 'MySQL', 'sql_host': '127.0.0.1', 'sql_port': 3306, 'sql_user': '', 'sql_password': '', 'sql_database': 'cutmob', 'default_kerf': 5.0, 'default_rifilo_h': 0.0, 'default_rifilo_v': 0.0, 'default_sfrido': 10.0, 'default_macchina': 'sezionatrice', 'client_name': '', 'client_cf_piva': '', 'client_email': ''}, indent=4))"
    echo "Inizializzazione completata con successo."
else
    echo "Mantenimento dati esistenti in corso..."
    if [ ! -f "$BASE_DIR/DbDati/database.json" ]; then
        if [ -f "database.json" ]; then
            cp "database.json" "$BASE_DIR/DbDati/database.json"
            echo "Database di esempio database.json copiato come punto di partenza."
        fi
    else
        echo "database.json già presente in $BASE_DIR/DbDati. Mantenuto."
    fi
fi

echo "=================================================="
echo "  COMPILAZIONE E SETUP CARTELLE COMPLETATI!"
echo "  L'applicazione è pronta in $BASE_DIR/CutMob.app"
echo "  Puoi avviarla con: open $BASE_DIR/CutMob.app"
echo "=================================================="
