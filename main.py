import firebase_admin
from firebase_admin import credentials, firestore
import os
import json
from datetime import datetime

# --- Initialisation Firebase ---
if 'FIREBASE_SERVICE_ACCOUNT' in os.environ:
    # On est sur GitHub Actions : on utilise la clé secrète
    service_account_info = json.loads(os.environ['FIREBASE_SERVICE_ACCOUNT'])
    cred = credentials.Certificate(service_account_info)
    firebase_admin.initialize_app(cred)
else:
    # On est sur Google Cloud (ou environnement local)
    firebase_admin.initialize_app()

db = firestore.client()

def generate_dynamic_prices(station_name):
    """
    Ta logique de calcul des prix.
    """
    return {
        'prixDiesel': 39.40,
        'prixEssence95': 41.20,
        'prixLPG': 24.30
    }

def update_fuel_prices_job():
    """
    Met à jour les prix de toutes les stations par lots (Batch)
    pour éviter les erreurs de quota Firestore (429).
    """
    stations_ref = db.collection('stations')
    stations = stations_ref.stream()
    
    batch = db.batch()
    batch_count = 0
    total_processed = 0
    
    for doc in stations:
        data = doc.to_dict()
        source = data.get('source', 'bot')
        
        # On ignore les stations modifiées manuellement par l'utilisateur
        if source == 'user':
            continue
            
        new_prices = generate_dynamic_prices(data.get('nom', 'Station'))
        
        # Préparation de la mise à jour dans le lot
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
        
        # Firestore limite les batchs à 500 opérations maximum
        if batch_count == 499:
            batch.commit()
            batch = db.batch()
            batch_count = 0
            
        # Log de progression tous les 100 documents
        if total_processed % 100 == 0:
            print(f"Progression : {total_processed} stations traitées...")

    # Envoi du dernier lot restant
    if batch_count > 0:
        batch.commit()
        
    return f"Mise à jour terminée. Total des stations traitées : {total_processed}"

# --- Point d'entrée pour l'exécution ---
if __name__ == "__main__":
    print("Début du job de mise à jour...")
    resultat = update_fuel_prices_job()
    print(resultat)
