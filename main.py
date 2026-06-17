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
    """Extrait les prix et met à jour Firebase"""
    name = str(row['name']).strip()
    url = str(row.get('url', '')).strip()
    station_id = name.replace(" ", "_").lower()
    
    if not url or url == 'nan':
        return # Ignore les lignes sans URL

    try:
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=8)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Extraction sécurisée
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
            print(f"🚀 {name} | Diesel: {diesel}€ | Essence: {essence}€", flush=True)
            
    except Exception as e:
        print(f"❌ Erreur {name} : {e}", flush=True)

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # J'ai mis 'station.csv' ici, assurez-vous que le fichier s'appelle bien comme ça sur GitHub
    csv_path = os.path.join(script_dir, 'station.csv')
    
    if not os.path.exists(csv_path):
        print(f"❌ Fichier 'station.csv' introuvable ! Vérifiez le nom dans GitHub.")
        return

    df = pd.read_csv(csv_path)
    # Nettoyage : supprime les lignes où le nom ou l'url est vide
    df = df.dropna(subset=['name', 'url'])
    
    print(f"✅ Fichier chargé. Traitement de {len(df)} stations...", flush=True)
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        executor.map(process_single_station, [row for _, row in df.iterrows()])

if __name__ == "__main__":
    main()
