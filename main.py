import pandas as pd
import requests
from bs4 import BeautifulSoup
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import os
def process_stations_from_csv():
    # Force le dossier de travail à être celui où se trouve le script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    csv_filename = 'stations.csv'
    
    # Debug profond
    print(f"DEBUG: Dossier actuel : {os.getcwd()}")
    print(f"DEBUG: Contenu du dossier : {os.listdir('.')}")
    
    if csv_filename not in os.listdir('.'):
        raise FileNotFoundError(f"Le fichier '{csv_filename}' est introuvable dans {os.getcwd()}")
        
    df = pd.read_csv(csv_filename)
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
        
        # Inspection de mbenzin.cz : les prix sont souvent dans des balises spécifiques.
        # Exemple de sélecteur basé sur la structure typique du site
        # Si le site change, il faudra mettre à jour ces chemins
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
    # Vérification du fichier CSV
    csv_filename = 'stations.csv' # Assurez-vous que votre fichier est renommé ainsi
    if not os.path.exists(csv_filename):
        print(f"❌ Erreur : Le fichier {csv_filename} est introuvable !")
        return

    df = pd.read_csv(csv_filename)
    
    for _, row in df.iterrows():
        sid = str(row['id'])
        url = row['url']
        
        print(f"🔍 Scraping : {sid}...")
        data = get_prices_from_mbenzin(url)
        
        if data:
            db.collection('stations').document(sid).update(data)
            print(f"✅ Mise à jour réussie pour {sid}")

if __name__ == "__main__":
    main()
