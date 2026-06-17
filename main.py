"""
EXEMPLE DE CONFIGURATION & STRUCTURE FIREBASE
 
Ce fichier montre:
1. Comment structurer vos données Firebase
2. Comment configurer le script
3. Exemples de documents
"""
 
# =============================================================================
# 1. STRUCTURE D'UNE STATION DANS FIRESTORE
# =============================================================================
 
# Collection: "stations"
# Exemple de document avec tous les champs:
 
{
  # Champs REQUIS
  "lat": 49.8175,              # Latitude (float)
  "lon": 18.2891,              # Longitude (float)
  "nom": "EuroOil Ostrava",    # Nom de la station (string)
  
  # Champs optionnels mais recommandés
  "city": "Ostrava",           # Nom de la ville (string) - Auto-détecté si absent
  "adresse": "Vítkovická 38",  # Adresse complète (string)
  
  # Prix actuels
  "prixDiesel": 36.50,         # Prix du diesel en CZK/litre (float)
  "prixEssence95": 39.50,      # Prix essence 95 en CZK/litre (float)
  "prixLPG": 22.90,            # Prix LPG en CZK/litre (float)
  
  # Métadonnées
  "source": "bot",             # "bot" ou "user" - bot = auto-update, user = ignore
  "derniereModification": "16/06/2026",  # Date dernière update (string DD/MM/YYYY)
  "nombreMisesAJour": 42,      # Compteur updates optionnel (int)
  
  # Optionnel: réseau/marque
  "reseau": "EuroOil",         # Shell, OMV, MOL, Orlen, etc.
  "typeCarburant": ["Essence95", "Diesel", "LPG"],  # Types disponibles
}
 
 
# =============================================================================
# 2. CRÉER UNE STATION DE TEST
# =============================================================================
 
# Avec Firestore CLI:
firebase firestore:set stations/test_ostrava {
  "nom": "Test Station Ostrava",
  "lat": 49.8175,
  "lon": 18.2891,
  "city": "Ostrava",
  "source": "bot",
  "prixDiesel": 39.00,
  "prixEssence95": 41.00,
  "prixLPG": 23.00,
  "derniereModification": "16/06/2026"
}
 
 
# =============================================================================
# 3. BULK IMPORT (Script Python)
# =============================================================================
 
import firebase_admin
from firebase_admin import credentials, firestore
import json
 
# Initialiser Firebase
firebase_admin.initialize_app()
db = firestore.client()
 
# Liste de stations à importer
stations_data = [
    {
        "nom": "EuroOil Vítkovická",
        "lat": 49.8350,
        "lon": 18.2920,
        "city": "Ostrava",
        "prixDiesel": 36.50,
        "prixEssence95": 39.50,
        "prixLPG": 22.90,
        "source": "bot"
    },
    {
        "nom": "Orlen Ruská",
        "lat": 49.8200,
        "lon": 18.3050,
        "city": "Ostrava",
        "prixDiesel": 34.90,
        "prixEssence95": 36.90,
        "prixLPG": 21.50,
        "source": "bot"
    },
    # ... plus de stations
]
 
# Importer
batch = db.batch()
for i, station_data in enumerate(stations_data):
    doc_ref = db.collection('stations').document(f'station_{i}')
    batch.set(doc_ref, station_data)
 
batch.commit()
print(f"✅ {len(stations_data)} stations importées!")
 
 
# =============================================================================
# 4. EXPORTER LES STATIONS ACTUELLES (Backup)
# =============================================================================
 
import json
 
firebase_admin.initialize_app()
db = firestore.client()
 
stations = db.collection('stations').stream()
 
data = []
for doc in stations:
    station = doc.to_dict()
    station['id'] = doc.id
    data.append(station)
 
# Sauvegarder en JSON
with open('stations_backup.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
 
print(f"✅ {len(data)} stations exportées dans stations_backup.json")
 
 
# =============================================================================
# 5. VILLES SUPPORTÉES (Exemples)
# =============================================================================
 
# Les villes doivent correspondre à celles de mbenzin.cz:
 
SUPPORTED_CITIES = [
    # Moravie-Silésie (où vous êtes)
    "Ostrava",
    "Havířov",
    "Karviná",
    "Bruntál",
    "Frýdek-Místek",
    "Nový Jičín",
    
    # Autres régions
    "Praha",
    "Brno",
    "Plzeň",
    "Liberec",
    "Olomouc",
    "České Budějovice",
    "Jihava",
    "Ústí nad Labem",
    "Mladá Boleslav",
    "Tábor",
    "Česká Lípa",
    "Chrudim",
    "Havlíčkův Brod",
    "Cheb",
    "Kladno",
    "Most",
    "Ústí nad Orlicí",
    "Kutná Hora",
    "Šumperk",
    "Prostějov",
]
 
 
# =============================================================================
# 6. AUTOMATISER AVEC GOOGLE CLOUD SCHEDULER
# =============================================================================
 
# Créer une Cloud Function pour scraper quotidiennement:
 
# 1. Déployer le script en Cloud Function
gcloud functions deploy update_fuel_prices \
    --runtime python39 \
    --trigger-topic fuel-prices-update \
    --entry-point update_fuel_prices_job \
    --set-env-vars FIREBASE_SERVICE_ACCOUNT=$FIREBASE_SERVICE_ACCOUNT
 
# 2. Créer un Cloud Scheduler job
gcloud scheduler jobs create pubsub update-fuel-prices \
    --schedule="0 8 * * *" \
    --topic=fuel-prices-update \
    --message-body='{}' \
    --location=europe-west1
 
# Cela exécutera le script à 8h du matin chaque jour
 
 
# =============================================================================
# 7. VÉRIFIER LES MISES À JOUR
# =============================================================================
 
# Query Firestore pour voir les stations mises à jour récemment:
 
firebase firestore:query \
    "stations" \
    --field-filter "source==bot" \
    --field-filter "derniereModification=16/06/2026" \
    --order-by "derniereModification DESC"
 
# Ou en Python:
from datetime import datetime, timedelta
 
db = firestore.client()
 
yesterday = (datetime.now() - timedelta(days=1)).strftime("%d/%m/%Y")
 
stations = db.collection('stations')\
    .where('source', '==', 'bot')\
    .where('derniereModification', '>=', yesterday)\
    .stream()
 
count = 0
for doc in stations:
    data = doc.to_dict()
    print(f"{data['nom']}: D={data.get('prixDiesel')} E={data.get('prixEssence95')}")
    count += 1
 
print(f"\n✅ {count} stations mises à jour hier")
 
 
# =============================================================================
# 8. STATISTIQUES PRIX PAR VILLE
# =============================================================================
 
from statistics import mean, median
 
db = firestore.client()
 
cities = {}
 
stations = db.collection('stations').where('source', '==', 'bot').stream()
 
for doc in stations:
    data = doc.to_dict()
    city = data.get('city', 'Unknown')
    
    if city not in cities:
        cities[city] = []
    
    cities[city].append({
        'diesel': data.get('prixDiesel', 0),
        'essence': data.get('prixEssence95', 0),
        'lpg': data.get('prixLPG', 0)
    })
 
# Afficher les statistiques
print("\n" + "="*60)
print("STATISTIQUES PRIX PAR VILLE")
print("="*60)
 
for city in sorted(cities.keys()):
    prices = cities[city]
    
    diesels = [p['diesel'] for p in prices if p['diesel'] > 0]
    essences = [p['essence'] for p in prices if p['essence'] > 0]
    lpgs = [p['lpg'] for p in prices if p['lpg'] > 0]
    
    if diesels:
        print(f"\n{city} ({len(prices)} stations)")
        print(f"  Diesel:   {min(diesels):.2f} - {max(diesels):.2f} (moy: {mean(diesels):.2f})")
        if essences:
            print(f"  Essence:  {min(essences):.2f} - {max(essences):.2f} (moy: {mean(essences):.2f})")
        if lpgs:
            print(f"  LPG:      {min(lpgs):.2f} - {max(lpgs):.2f} (moy: {mean(lpgs):.2f})")
 
 
# =============================================================================
# 9. ARCHIVER LES ANCIENNES MISES À JOUR
# =============================================================================
 
# Garder l'historique dans une sous-collection (optionnel)
 
from datetime import datetime
 
def archive_prices(station_id, prices, date=None):
    """Archive les prix dans price_history/{date}"""
    
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
    
    db = firestore.client()
    
    doc_ref = db.collection('stations')\
        .document(station_id)\
        .collection('price_history')\
        .document(date)
    
    doc_ref.set({
        'prixDiesel': prices['prixDiesel'],
        'prixEssence95': prices['prixEssence95'],
        'prixLPG': prices.get('prixLPG', 0),
        'timestamp': datetime.now()
    })
 
 
# =============================================================================
# 10. RESTAURER DEPUIS BACKUP
# =============================================================================
 
import json
from datetime import datetime
 
def restore_from_backup(backup_file):
    """Restaure les stations depuis un fichier JSON"""
    
    with open(backup_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    db = firestore.client()
    batch = db.batch()
    
    for i, station in enumerate(data):
        # Restaure les données sauf l'ID
        station_data = {k: v for k, v in station.items() if k != 'id'}
        station_data['restoredAt'] = datetime.now().isoformat()
        
        doc_ref = db.collection('stations').document(station.get('id', f'station_{i}'))
        batch.set(doc_ref, station_data)
    
    batch.commit()
    print(f"✅ {len(data)} stations restaurées!")
 
# Utiliser:
# restore_from_backup('stations_backup.json')
 
 
print("✨ Configuration Firebase prête!")
 
