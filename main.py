import pandas as pd
import os
import requests
from bs4 import BeautifulSoup
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

# Initialisation Firebase sécurisée
if not firebase_admin._apps:
    firebase_admin.initialize_app()
db = firestore.client()

def get_prices_from_mbenzin(url):
    """Extrait les prix en s'adaptant à la structure du site"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # NOTE : Vérifiez bien ces classes CSS sur mbenzin.cz
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
    # 1. Gestion du chemin vers le CSV
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_filename = 'stations.csv'
    csv_path = os.path.join(script_dir, csv_filename)
    
    # 2. Debug (pour voir où il cherche)
    print(f"DEBUG: Chemin cherché -> {csv_path}")
    if not os.path.exists(csv_path):
        print(f"❌ Erreur : Le fichier {csv_filename} est introuvable !")
        print(f"DEBUG: Contenu du dossier : {os.listdir(script_dir)}")
        return

    # 3. Traitement
    df = pd.read_csv(csv_path)
    print(f"✅ Fichier chargé. Traitement de {len(df)} stations...")
    
    for _, row in df.iterrows():
        sid = str(row['id']).strip() # .strip() enlève les espaces invisibles
        url = row['url'].strip()
        
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
