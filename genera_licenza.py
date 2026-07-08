import sys
import os

try:
    from license_manager import genera_chiave_licenza
except ImportError:
    print("Errore: impossibile caricare il modulo license_manager.")
    sys.exit(1)

def main():
    print("=========================================")
    print("   GENERATORE CHIAVI DI LICENZA CUTMOB   ")
    print("=========================================")
    
    try:
        ragione_sociale = input("Inserisci Ragione Sociale: ").strip()
        partita_iva = input("Inserisci Partita IVA / Codice Fiscale: ").strip()
        data_inizio = input("Data inizio validità (YYYY-MM-DD) [invio per oggi]: ").strip()
        
        if not data_inizio:
            from datetime import datetime
            data_inizio = datetime.now().strftime("%Y-%m-%d")
            
        data_fine = input("Data fine validità (YYYY-MM-DD): ").strip()
        
        if not ragione_sociale or not data_fine:
            print("Errore: Ragione Sociale e Data Fine sono campi obbligatori!")
            return
            
        chiave = genera_chiave_licenza(ragione_sociale, partita_iva, data_inizio, data_fine)
        print("\n=========================================")
        print(" CHIAVE DI LICENZA GENERATA CON SUCCESSO ")
        print("=========================================\n")
        print(chiave)
        print("\n=========================================")
        print("\nCopia e invia il codice sopra riportato al cliente.")
    except KeyboardInterrupt:
        print("\nOperazione annullata.")
    except Exception as e:
        print(f"Errore durante la generazione: {e}")
        
    input("\nPremi Invio per uscire...")

if __name__ == "__main__":
    main()
