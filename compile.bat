@echo off
echo ==================================================
echo   CutMob - AVVIO COMPILAZIONE APPLICAZIONE
echo ==================================================

:: 1. Installa PyInstaller se non presente
pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo Installazione di PyInstaller in corso...
    pip install pyinstaller
)

:: 2. Avvia la compilazione
echo Compilazione con PyInstaller...
python -m PyInstaller --clean CutMob.spec
if %errorlevel% neq 0 (
    echo Errore nella compilazione dell'eseguibile!
    pause
    exit /b %errorlevel%
)

:: 3. Crea la struttura di cartelle richiesta su C:\
echo Creazione struttura cartelle su C:\...
if not exist "C:\CutMob" mkdir "C:\CutMob"
if not exist "C:\CutMob\DbDati" mkdir "C:\CutMob\DbDati"
if not exist "C:\CutMob\Report" mkdir "C:\CutMob\Report"
if not exist "C:\CutMob\Report\HTML" mkdir "C:\CutMob\Report\HTML"
if not exist "C:\CutMob\Report\PDF" mkdir "C:\CutMob\Report\PDF"

:: 4. Copia i file compilati nella cartella di destinazione
echo Copia dell'applicazione compilata in C:\CutMob...
xcopy /s /y /i "dist\CutMob" "C:\CutMob"

:: 5. Scelta gestione Database
echo.
echo ==================================================
echo   GESTIONE DATABASE E CONFIGURAZIONE (C:\CutMob\DbDati)
echo ==================================================
echo   1] Inizializza con DB a zero (vuoto) e impostazioni aziendali di default
echo   2] Copia/Mantieni dati gia esistenti (tabelle DB locali e impostazioni attive)
echo ==================================================
set /p choice="Scegli un'opzione [1 o 2]: "

if "%choice%"=="1" (
    echo Inizializzazione database e configurazione vuoti...
    python -c "import json; open('C:\\CutMob\\DbDati\\database.json', 'w', encoding='utf-8').write(json.dumps({'barre': [], 'semilavorati': [], 'commesse': []}, indent=4))"
    python -c "import json; open('C:\\CutMob\\DbDati\\config.json', 'w', encoding='utf-8').write(json.dumps({'db_type': 'local', 'local_path': 'C:\\\\CutMob\\\\DbDati\\\\database.json', 'sql_type': 'MySQL', 'sql_host': '127.0.0.1', 'sql_port': 3306, 'sql_user': '', 'sql_password': '', 'sql_database': 'cutmob', 'default_kerf': 5.0, 'default_rifilo_h': 0.0, 'default_rifilo_v': 0.0, 'default_sfrido': 10.0, 'default_macchina': 'sezionatrice', 'client_name': '', 'client_cf_piva': '', 'client_email': ''}, indent=4))"
    echo Inizializzazione completata con successo.
) else (
    echo Mantenimento dati esistenti in corso...
    if not exist "C:\CutMob\DbDati\database.json" (
        if exist "database.json" (
            copy "database.json" "C:\CutMob\DbDati\database.json"
            echo Database di esempio database.json copiato come punto di partenza.
        )
    ) else (
        echo database.json gia presente in C:\CutMob\DbDati. Mantenuto.
    )
)

echo ==================================================
echo   COMPILAZIONE E SETUP CARTELLE COMPLETATI!
echo   L'applicazione e pronta all'uso in C:\CutMob\
echo ==================================================
pause
