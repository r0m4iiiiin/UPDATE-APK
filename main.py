import pandas as pd
import requests
from bs4 import BeautifulSoup
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

# Initialisation Firebase
if not firebase_admin._apps:
    firebase_admin.initialize_app()
db = firestore.client()

def get_prices_from_mbenzin(url):
    """Extrait les prix depuis la page mbenzin.cz"""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Sélecteurs basés sur la structure typique de mbenzin.cz
    # Vous devrez vérifier ces classes si le site a modifié son design
    prices = {}
    try:
        # Cherche les éléments contenant les prix (à adapter selon l'inspecteur HTML)
        # Exemple : .price-value
        price_elements = soup.find_all(class_="price") 
        # Logique simplifiée à ajuster selon le HTML réel du site
        prices['prixDiesel'] = float(soup.select_one(".diesel").text.replace(',', '.'))
        prices['prixEssence95'] = float(soup.select_one(".natural95").text.replace(',', '.'))
        prices['derniereModification'] = datetime.now().strftime("%d/%m/%Y")
    except Exception as e:
        print(f"Erreur lors du scraping de {url}: {e}")
        return None
    return prices

def process_stations_from_csv(csv_file):
    df = pd.read_csv(csv_file)
    
    for index, row in df.iterrows():
        station_id = str(row['id'])
        url = row['url']
        
        print(f"Traitement de : {station_id}...")
        new_data = get_prices_from_mbenzin(url)
        
        if new_data:
            db.collection('stations').document(station_id).update(new_data)
            print(f"✅ Mis à jour : {station_id}")

# Lancement
process_stations_from_csv('Feuille de calcul sans titre - Feuille 1.csv')
