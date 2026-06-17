import pandas as pd
import os
import requests
import json
import time  # <--- Import nécessaire
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

def get_prices_from_mbenzin(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Recherche sécurisée des éléments
        el_diesel = soup.select_one(".price-diesel")
        el_essence = soup.select_one(".price-natural95")

        # LOG DE DÉBOGAGE : Affiche ce qu'il voit dans le HTML
        if not el_diesel or not el_essence:
            print(f"DEBUG: Structure HTML inattendue sur {url}")
            print(f"DEBUG: Élément Diesel trouvé ? {el_diesel is not None}")
            print(f"DEBUG: Élément Essence trouvé ? {el_essence is not None}")
            return None

        # Extraction propre
        diesel = el_diesel.text.strip().replace(',', '.')
        essence = el_essence.text.strip().replace(',', '.')

        # Validation : vérifie si les valeurs sont bien des nombres
        return {
            "prixDiesel": float(diesel),
            "prixEssence95": float(essence),
            "derniereModification": datetime.now().strftime("%d/%m/%Y")
        }
    except Exception as e:
        print(f"❌ Erreur lors de l'extraction sur {url} : {e}")
        return None

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(script_dir, 'stations.csv')
    
    if not os.path.exists(csv_path):
        print(f"❌ Erreur : 'stations.csv' introuvable")
        return

    df = pd.read_csv(csv_path)
    print(f"✅ Fichier chargé. Traitement de {len(df)} stations...")
    
    for _, row in df.iterrows():
        # Utilisation de 'name' au lieu de 'id' car 'id' n'existe pas dans votre CSV
        # On crée un identifiant Firestore propre en remplaçant les espaces par des tirets
        name = str(row['name']).strip()
        station_id = name.replace(" ", "_").lower() 
        
        # Note : Dans votre CSV actuel, il n'y a pas d'URL ! 
        # Si vous n'avez pas d'URL, vous devez utiliser la logique de recherche par nom
        # Pour l'instant, je suppose que vous ajouterez une colonne 'url' ou chercherez par nom.
        url = row.get('url') 
        
        if not url:
            continue
            
        print(f"🔍 Scraping : {name}...")
        data = get_prices_from_mbenzin(url)
        
        if data:
            try:
                # On utilise .set(data, merge=True) pour créer ou mettre à jour
                db.collection('stations').document(station_id).set(data, merge=True)
                print(f"✅ Mise à jour réussie pour {name}")
            except Exception as e:
                print(f"❌ Erreur Firestore pour {name} : {e}")
        
        # PAUSE : Indispensable pour ne pas être bloqué par le site
        time.sleep(2) 

if __name__ == "__main__":
    main()
