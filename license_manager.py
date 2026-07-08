import hmac
import hashlib
import base64
import json
from datetime import datetime

SECRET_SALT = b"CutMobLicenseSecretSalt2026!"

def genera_chiave_licenza(ragione_sociale, partita_iva, data_inizio, data_fine):
    """
    Genera una stringa di licenza crittografata e firmata.
    """
    payload = {
        "ragione_sociale": ragione_sociale.strip(),
        "partita_iva": partita_iva.strip(),
        "data_inizio": data_inizio.strip(),
        "data_fine": data_fine.strip()
    }
    payload_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    signature = hmac.new(SECRET_SALT, payload_bytes, hashlib.sha256).hexdigest().encode("utf-8")
    
    combined = payload_bytes + b"|" + signature
    return base64.b64encode(combined).decode("utf-8")

def verifica_chiave_licenza(chiave_str, client_name=None, client_piva=None):
    """
    Verifica se la chiave di licenza è valida.
    Ritorna (is_valid, msg, payload_data)
    """
    if not chiave_str:
        return False, "Codice licenza vuoto.", None
        
    try:
        # Rimuove spazi bianchi o caratteri di a capo
        chiave_str = "".join(chiave_str.strip().split())
        decoded_bytes = base64.b64decode(chiave_str.encode("utf-8"))
        if b"|" not in decoded_bytes:
            return False, "Formato licenza non valido.", None
            
        payload_bytes, signature = decoded_bytes.rsplit(b"|", 1)
        
        # Verifica firma HMAC
        expected_signature = hmac.new(SECRET_SALT, payload_bytes, hashlib.sha256).hexdigest().encode("utf-8")
        if not hmac.compare_digest(signature, expected_signature):
            return False, "Chiave alterata o non valida.", None
            
        data = json.loads(payload_bytes.decode("utf-8"))
        
        # Verifica corrispondenza dati se forniti
        if client_name and data.get("ragione_sociale") != client_name:
            return False, f"La licenza appartiene a: {data.get('ragione_sociale')}.", data
        if client_piva and data.get("partita_iva") != client_piva:
            return False, f"La P.IVA non corrisponde alla licenza ({data.get('partita_iva')}).", data
            
        # Verifica date
        today = datetime.now().date()
        try:
            start_date = datetime.strptime(data.get("data_inizio"), "%Y-%m-%d").date()
            end_date = datetime.strptime(data.get("data_fine"), "%Y-%m-%d").date()
        except ValueError:
            return False, "Formato date nella licenza errato (atteso YYYY-MM-DD).", data
            
        if today < start_date:
            return False, f"La licenza non è ancora attiva (valida dal {data.get('data_inizio')}).", data
        if today > end_date:
            return False, f"La licenza è scaduta il {data.get('data_fine')}.", data
            
        return True, "Licenza attiva e valida.", data
    except Exception as e:
        return False, f"Errore durante la decodifica della chiave: {str(e)}", None
