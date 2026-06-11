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

    """

    Cette fonction est appelée par le Cloud Scheduler.

    Elle parcourt toutes les stations et met à jour les prix.

    """

    stations_ref = db.collection('stations')

    stations = stations_ref.stream()



    for doc in stations:

        data = doc.to_dict()

        

        # Vérification : On ne met à jour que si ce n'est pas une modif manuelle récente

        # (Logique de sécurité pour éviter d'écraser un utilisateur)

        source = data.get('source', 'bot')

        if source == 'user':

            # Optionnel : Vérifier si la modif date de plus de 24h

            continue 



        # Ton algorithme de calcul

        new_prices = generate_dynamic_prices(data.get('nom', 'Station'))

        

        # Mise à jour dans Firestore

        stations_ref.document(doc.id).update({

            'prixDiesel': new_prices['prixDiesel'],

            'prixEssence95': new_prices['prixEssence95'],

            'prixLPG': new_prices['prixLPG'],

            'derniereModification': datetime.now().strftime("%d/%m/%Y"),

            'source': 'bot'

        })

    

    return "Mise à jour terminée."



def generate_dynamic_prices(station_name):

    # (Garde ici ta logique de calcul existante)

    # ...

    return {

        'prixDiesel': 39.40, # Exemple

        'prixEssence95': 41.20,

        'prixLPG': 24.30

    } 


