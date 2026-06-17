import pandas as pd
import os
import time
import json
import requests
from bs4 import BeautifulSoup
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor # Pour accélérer

# Initialisation Firebase
if not firebase_admin._apps:
    service_account_info = json.loads(os.environ['FIREBASE_SERVICE_ACCOUNT'])
    cred = credentials.Certificate(service_account_info)
    firebase_admin.initialize_app(cred)
db = firestore.client()

def process_single_station(row):
    """Fonction traitant une seule station"""
    name = str(row['name']).strip()
    station_id = name.replace(" ", "_").lower()
    
    # 1. Recherche URL
    search_url = f"https://www.mbenzin.cz/index.php?s={name.replace(' ', '+')}"
    try:
        response = requests.get(search_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        link = soup.select_one(".station-result a")
        
        if not link:
            print(f"⚠️ URL introuvable pour {name}", flush=True)
            return

        url = "https://www.mbenzin.cz" + link['href']
        
        # 2. Extraction prix
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
        soup_price = BeautifulSoup(res.text, 'html.parser')
        
        diesel = soup_price.select_one(".price-diesel").text.strip().replace(',', '.')
        essence = soup_price.select_one(".price-natural95").text.strip().replace(',', '.')
        
        data = {
            "prixDiesel": float(diesel),
            "prixEssence95": float(essence),
            "derniereModification": datetime.now().strftime("%d/%m/%Y %H:%M")
        }
        
        # 3. Mise à jour Firestore avec détails
        db.collection('stations').document(station_id).set(data, merge=True)
        print(f"🚀 {name} | Diesel: {diesel}€ | Essence: {essence}€", flush=True)
        
    except Exception as e:
        print(f"❌ Erreur {name} : {e}", flush=True)

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    df = pd.read_csv(os.path.join(script_dir, 'stations.csv'))
    
    print(f"✅ Démarrage du traitement de {len(df)} stations...", flush=True)
    
    # Utilisation d'un ThreadPoolExecutor pour traiter 5 stations en parallèle
    # Cela multiplie la vitesse par 5 sans trop surcharger le site
    with ThreadPoolExecutor(max_workers=5) as executor:
        executor.map(process_single_station, [row for _, row in df.iterrows()])

if __name__ == "__main__":
    main()
