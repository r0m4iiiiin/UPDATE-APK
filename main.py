import pandas as pd
import os
import requests
import json
from bs4 import BeautifulSoup
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

# 1. INITIALISATION FIREBASE CORRIGÉE POUR GITHUB ACTIONS
if not firebase_admin._apps:
    # On utilise la variable d'environnement définie dans vos secrets GitHub
    service_account_info = json.loads(os.environ['FIREBASE_SERVICE_ACCOUNT'])
    cred = credentials.Certificate(service_account_info)
    firebase_admin.initialize_app(cred)

db = firestore.client()

def get_prices_from_mbenzin(url):
    """Extrait les prix en s'adaptant à la structure du site"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # NOTE : Si ces sélecteurs ne fonctionnent pas, c'est que la classe CSS sur mbenzin a changé.
        # Utilisez l'inspecteur d'éléments (F12) sur le site pour vérifier les classes.
        diesel = soup.select_one(".price-diesel").text.strip().replace(',', '.')
        essence = soup.select_one(".price-natural95").text.strip().replace(',', '.')
        
        return {
            "prixDiesel": float(diesel),
            "prixEssence95": float(essence),
            "derniereModification": datetime.now().strftime("%d/%m/%Y")
        }
    except Exception as e:
        print(f"❌ Impossible d'extraire les données de {url} : {e}")
        return None

def main():
    # 2. CHEMIN ROBUSTE
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(script_dir, 'stations.csv')
    
    if not os.path.exists(csv_path):
        print(f"❌ Erreur : 'stations.csv' introuvable à {csv_path}")
        return

    df = pd.read_csv(csv_path)
    print(f"✅ Fichier chargé. Traitement de {len(df)} stations...")
    
    for _, row in df.iterrows():
        # Conversion sécurisée en string
        sid = str(row['id']).strip()
        url = str(row['url']).strip()
        
        print(f"🔍 Scraping : {sid}...")
        data = get_prices_from_mbenzin(url)
        
        if data:
            try:
                db.collection('stations').document(sid).update(data)
                print(f"✅ Mise à jour réussie pour {sid}")
            except Exception as e:
                print(f"❌ Erreur Firestore pour {sid} : {e}")

if __name__ == "__main__":
    main()
