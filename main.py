import firebase_admin
from firebase_admin import credentials, firestore
import random
import os
import json
from datetime import datetime
# --- MODIFICATION ICI ---
# Initialisation du client Firebase sécurisée
if 'FIREBASE_SERVICE_ACCOUNT' in os.environ:
    # On est sur GitHub Actions : on utilise la clé secrète
    service_account_info = json.loads(os.environ['FIREBASE_SERVICE_ACCOUNT'])
    cred = credentials.Certificate(service_account_info)
    firebase_admin.initialize_app(cred)
else:
    # On est sur Google Cloud (ou environnement local) : on utilise l'initialisation par défaut
    firebase_admin.initialize_app()
db = firestore.client()
# -------------------------
# Reste de ton code...
def update_fuel_prices_job(request=None):
    stations_ref = db.collection('stations')
    stations = stations_ref.stream()
    for doc in stations:
        data = doc.to_dict()
        source = data.get('source', 'bot')
        if source == 'user':
            continue 
        new_prices = generate_dynamic_prices(data.get('nom', 'Station'))
        stations_ref.document(doc.id).update({
            'prixDiesel': new_prices['prixDiesel'],
            'prixEssence95': new_prices['prixEssence95'],
            'prixLPG': new_prices['prixLPG'],
            'derniereModification': datetime.now().strftime("%d/%m/%Y"),
            'source': 'bot'
        })
        # Ce print doit être aligné avec stations_ref (4 espaces de retrait par rapport au for)
        print(f"Mise à jour de {data.get('nom', 'Station')} effectuée.")
    # Ce return doit être aligné avec le "for" (au même niveau que le début de la boucle)
    return "Mise à jour terminée."
def generate_dynamic_prices(station_name):
    # ... ta logique actuelle ...
    return {
        'prixDiesel': 39.40,
        'prixEssence95': 41.20,
        'prixLPG': 24.30
    }
# --- AJOUTE CES LIGNES TOUT EN BAS ---
if __name__ == "__main__":
    resultat = update_fuel_prices_job()
    print(resultat) 
