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
    name = str(row['name']).strip()
    url = str(row.get('url', '')).strip()
    station_id = name.replace(" ", "_").lower()
    
    print(f"🔄 Traitement : {name}...", flush=True)
    
    try:
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Tentative 1 : Sélecteurs actuels
        el_diesel = soup.select_one(".price-diesel")
        el_essence = soup.select_one(".price-natural95")
        
        # Tentative 2 (Secours) : Si les classes ont changé, on cherche dans les balises génériques
        # Souvent les prix sont dans des éléments avec la classe 'price' ou 'value'
        if not el_diesel:
            el_diesel = soup.select_one("div[class*='diesel']") # Cherche un div contenant 'diesel'
        if not el_essence:
            el_essence = soup.select_one("div[class*='natural95']")

        if el_diesel and el_essence:
            diesel = el_diesel.text.strip().replace(',', '.')
            essence = el_essence.text.strip().replace(',', '.')
            
            # Nettoyage supplémentaire : garde seulement les chiffres et le point
            diesel = ''.join(c for c in diesel if c.isdigit() or c == '.')
            essence = ''.join(c for c in essence if c.isdigit() or c == '.')
            
            data = {
                "name": name,
                "prixDiesel": float(diesel),
                "prixEssence95": float(essence),
                "derniereModification": datetime.now().strftime("%d/%m/%Y %H:%M")
            }
            
            db.collection('stations').document(station_id).set(data, merge=True)
            print(f"✅ SUCCÈS | {name} | Diesel: {diesel} | Essence: {essence}", flush=True)
        else:
            # DEBUG CRUCIAL : On affiche une partie du HTML pour comprendre la structure
            print(f"❌ PRIX NON TROUVÉS pour {name}", flush=True)
            # Affiche les 300 premiers caractères du HTML pour inspecter les classes
            print(f"DEBUG HTML: {res.text[:300]}", flush=True) 
            
    except Exception as e:
        print(f"❌ ERREUR pour {name} : {e}", flush=True)

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(script_dir, 'station.csv')
    
    df = pd.read_csv(csv_path)
    df = df.dropna(subset=['name', 'url'])
    
    print(f"✅ Fichier chargé. {len(df)} stations à traiter.", flush=True)
    
    # On réduit max_workers à 2 pour éviter d'être bloqué par le site (anti-bot)
    with ThreadPoolExecutor(max_workers=2) as executor:
        executor.map(process_single_station, [row for _, row in df.iterrows()])
    
    print(f"🏁 Traitement terminé.", flush=True)

if __name__ == "__main__":
    main()
