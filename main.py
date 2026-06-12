import firebase_admin
from firebase_admin import credentials, firestore
import os
import json
import time
from datetime import datetime
from google.api_core import exceptions

# --- Initialisation Firebase ---
if 'FIREBASE_SERVICE_ACCOUNT' in os.environ:
    service_account_info = json.loads(os.environ['FIREBASE_SERVICE_ACCOUNT'])
    cred = credentials.Certificate(service_account_info)
    firebase_admin.initialize_app(cred)
else:
    firebase_admin.initialize_app()

db = firestore.client()

def generate_dynamic_prices(station_name):
    """Logique de calcul des prix."""
    return {
        'prixDiesel': 39.40,
        'prixEssence95': 41.20,
        'prixLPG': 24.30
    }

def update_fuel_prices_job():
    """
    Met à jour les prix de toutes les stations par lots (Batch)
    avec gestion des pauses pour éviter l'erreur 429.
    """
    stations_ref = db.collection('stations')
    # On récupère tous les documents
    stations = stations_ref.stream()
    
    batch = db.batch()
    batch_count = 0
    total_processed = 0
    
    print("Début du traitement des 2800 stations...")
    
    for doc in stations:
        data = doc.to_dict()
        source = data.get('source', 'bot')
        
        # Ignorer les stations modifiées manuellement
        if source == 'user':
            continue
            
        new_prices = generate_dynamic_prices(data.get('nom', 'Station'))
        
        doc_ref = stations_ref.document(doc.id)
        batch.update(doc_ref, {
            'prixDiesel': new_prices['prixDiesel'],
            'prixEssence95': new_prices['prixEssence95'],
            'prixLPG': new_prices['prixLPG'],
            'derniereModification': datetime.now().strftime("%d/%m/%Y"),
            'source': 'bot'
        })
        
        batch_count += 1
        total_processed += 1
        
        # Firestore limite les batchs à 500 opérations
        if batch_count == 499:
            try:
                batch.commit()
                print(f"Batch de 500 envoyé. Total traité : {total_processed}. Pause de sécurité...")
                time.sleep(2)  # Pause pour éviter de saturer l'API (429)
                batch = db.batch()
                batch_count = 0
            except exceptions.ResourceExhausted:
                print("Quota atteint, pause longue de 10 secondes...")
                time.sleep(10)
                batch.commit()
                batch = db.batch()
                batch_count = 0
            
    # Envoi du dernier lot restant
    if batch_count > 0:
        batch.commit()
        
    return f"Mise à jour terminée avec succès. Total des stations traitées : {total_processed}"

if __name__ == "__main__":
    try:
        print("Initialisation du job...")
        resultat = update_fuel_prices_job()
        print(resultat)
    except Exception as e:
        print(f"Une erreur critique est survenue : {e}")
