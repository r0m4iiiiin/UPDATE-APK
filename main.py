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
    lat = str(row['lat'])
    lon = str(row['lon'])
    name = str(row['name']).strip()
    station_id = name.replace(" ", "_").lower()
    
    # URL de recherche par coordonnées sur mbenzin.cz
    # Le site utilise souvent des paramètres de recherche cartographique
    search_url = f"https://www.mbenzin.cz/index.php?lat={lat}&lon={lon}"
    
    try:
        # On utilise une session pour garder les cookies et simuler un vrai navigateur
        session = requests.Session()
        session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
        
        # 1. On cherche la station via les coordonnées
        response = session.get(search_url, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # On cherche le lien vers la station (le premier résultat de la recherche)
        link = soup.select_one(".station-result a")
        if not link:
            print(f"⚠️ Aucune station trouvée pour {name} aux coordonnées {lat}, {lon}", flush=True)
            return

        station_url = "https://www.mbenzin.cz" + link['href']
        
        # 2. On récupère les prix sur cette page précise
        res = session.get(station_url, timeout=15)
        soup_price = BeautifulSoup(res.text, 'html.parser')
        
        # IMPORTANT : Inspectez ces classes dans votre navigateur sur une page de station
        # Si vous voyez toujours 'PRIX NON TROUVÉS', c'est que ces classes sont les mauvaises.
        diesel = soup_price.select_one(".price-diesel")
        essence = soup_price.select_one(".price-natural95")
        
        if diesel and essence:
            data = {
                "name": name,
                "prixDiesel": float(diesel.text.replace(',', '.')),
                "prixEssence95": float(essence.text.replace(',', '.')),
                "derniereModification": datetime.now().strftime("%d/%m/%Y %H:%M")
            }
            db.collection('stations').document(station_id).set(data, merge=True)
            print(f"✅ SUCCÈS | {name} | Diesel: {diesel.text} | Essence: {essence.text}", flush=True)
        else:
            print(f"❌ PRIX INTROUVABLES sur {station_url}", flush=True)
            
    except Exception as e:
        print(f"❌ ERREUR pour {name} : {e}", flush=True)
