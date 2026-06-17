import pandas as pd
import os
import json
import requests
from bs4 import BeautifulSoup
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# Initialisation Firebase
if not firebase_admin._apps:
    service_account_info = json.loads(os.environ['FIREBASE_SERVICE_ACCOUNT'])
    cred = credentials.Certificate(service_account_info)
    firebase_admin.initialize_app(cred)
db = firestore.client()

def process_single_station(row):
    """Extrait les prix et met à jour Firebase avec logs détaillés"""
    name = str(row['name']).strip()
    url = str(row.get('url', '')).strip()
    station_id = name.replace(" ", "_").lower()
    
    # Log de début de traitement
    print(f"🔄 Traitement : {name}...", flush=True)
    
    if not url or url == 'nan':
        print(f"⚠️ URL invalide pour {name}", flush=True)
        return

    try:
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        el_diesel = soup.select_one(".price-diesel")
        el_essence = soup.select_one(".price-natural95")
        
        if el_diesel and el_essence:
            diesel = el_diesel.text.strip().replace(',', '.')
            essence = el_essence.text.strip().replace(',', '.')
            
            data = {
                "name": name,
                "prixDiesel": float(diesel),
                "prixEssence95": float(essence),
                "derniereModification": datetime.now().strftime("%d/%m/%Y %H:%M")
            }
            
            db.collection('stations').document(station_id).set(data, merge=True)
            print(f"✅ SUCCÈS | {name} | Diesel: {diesel} | Essence: {essence}", flush=True)
        else:
            print(f"❌ PRIX NON TROUVÉS | {name} (Vérifiez le sélecteur CSS)", flush=True)
            
    except Exception as e:
        print(f"❌ ERREUR pour {name} : {e}", flush=True)

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(script_dir, 'station.csv')
    
    if not os.path.exists(csv_path):
        print(f"❌ Fichier 'station.csv' introuvable dans {script_dir}", flush=True)
        return

    df = pd.read_csv(csv_path)
    # Nettoyage
    df = df.dropna(subset=['name', 'url'])
    
    print(f"✅ Fichier chargé. {len(df)} stations prêtes à être traitées.", flush=True)
    
    # Utilisation du Pool d'exécution
    with ThreadPoolExecutor(max_workers=5) as executor:
        executor.map(process_single_station, [row for _, row in df.iterrows()])
    
    print(f"🏁 Traitement terminé.", flush=True)

if __name__ == "__main__":
    main()
