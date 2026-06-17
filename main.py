import pandas as pd
import os
import time
import json
import requests
from bs4 import BeautifulSoup
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

# Initialisation Firebase
if not firebase_admin._apps:
    service_account_info = json.loads(os.environ['FIREBASE_SERVICE_ACCOUNT'])
    cred = credentials.Certificate(service_account_info)
    firebase_admin.initialize_app(cred)
db = firestore.client()

def get_station_url(name):
    """Recherche l'URL de la station sur mbenzin.cz en utilisant le moteur de recherche du site"""
    try:
        search_url = f"https://www.mbenzin.cz/index.php?s={name.replace(' ', '+')}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(search_url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Le premier résultat est généralement le bon
        link = soup.select_one(".station-result a")
        if link:
            return "https://www.mbenzin.cz" + link['href']
    except:
        return None
    return None

def get_prices_from_url(url):
    """Extrait les prix une fois l'URL trouvée"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')

        diesel = soup.select_one(".price-diesel").text.strip().replace(',', '.')
        essence = soup.select_one(".price-natural95").text.strip().replace(',', '.')

        return {
            "prixDiesel": float(diesel),
            "prixEssence95": float(essence),
            "derniereModification": datetime.now().strftime("%d/%m/%Y")
        }
    except Exception as e:
        print(f"❌ Erreur extraction prix : {e}")
        return None

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(script_dir, 'stations.csv')
    df = pd.read_csv(csv_path)

    for _, row in df.iterrows():
        name = str(row['name']).strip()
        station_id = name.replace(" ", "_").lower()
        
        print(f"🔍 Recherche URL pour : {name}...")
        url = get_station_url(name)
        
        if url:
            print(f"✅ URL trouvée : {url}")
            data = get_prices_from_url(url)
            if data:
                db.collection('stations').document(station_id).set(data, merge=True)
                print(f"🚀 Mise à jour réussie pour {name}")
        else:
            print(f"⚠️ URL introuvable pour {name}")
        
        time.sleep(2) # Anti-blocage

if __name__ == "__main__":
    main()
