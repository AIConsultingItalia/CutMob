import sys
sys.path.append("c:/GitHub/Siti/CutMob")
from data_manager import DataManager
import os

# 1. Crea un file CSV di test
test_csv_path = "c:/GitHub/Siti/CutMob/scratch/test_mq.csv"
os.makedirs(os.path.dirname(test_csv_path), exist_ok=True)

csv_content = """Descrizione;Larghezza;Altezza;Spessore;Codice Colore;Descrizione Colore;SommaDiQuant_DA_PROD;UM
Pannello A;600;720;18;U708;Grigio;0,7856;MQ
Pannello B;450;720;18;U708;Grigio;1,5000;ML
Pannello C;1000;500;18;W1000;Bianco;4;PZ
"""

with open(test_csv_path, "w", encoding="utf-8") as f:
    f.write(csv_content)

print("File CSV di test creato.")

# 2. Inizializza DataManager e importa
dm = DataManager()
pezzi = dm.import_csv(test_csv_path)

print("\n--- RISULTATO IMPORTAZIONE ---")
for idx, p in enumerate(pezzi):
    print(f"Pezzo {idx+1}: {p['descrizione']}")
    print(f"  Dimensioni: {p['height']} x {p['width']} x {p['thickness']} mm")
    print(f"  Quantità: {p['quantity']}")
    print(f"  Qt Origine: {p['qt_origine']}")
    
    # Formatta come in app.py
    qty_val = p['quantity']
    qt_orig = p['qt_origine']
    if qt_orig is not None:
        qty_display = f"{qty_val} ({str(qt_orig).replace('.', ',')})"
    else:
        qty_display = str(qty_val)
    print(f"  Visualizzazione qty: {qty_display}")

# Pulisce file di test
if os.path.exists(test_csv_path):
    os.remove(test_csv_path)
