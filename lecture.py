import json
from pymongo import MongoClient
from neo4j import GraphDatabase
import redis

# Chargement des données
<<<<<<< HEAD
with open('data.json', 'r') as f:
=======
with open('data/data.json', 'r') as f:
>>>>>>> iter2
    movies = json.load(f)

# 1. Import vers MongoDB (Document)
mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client.movie_db
db.movies.insert_many(movies)
print("✅ MongoDB : 50 films importés.")

# 2. Import vers Neo4j (Graphe) - Version Enrichie
driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password123"))
with driver.session() as session:
    # Optionnel : Nettoyer la base avant de ré-importer pour éviter les doublons
    # session.run("MATCH (n) DETACH DELETE n") 

    for m in movies:
        session.run("""
            // 1. Créer ou mettre à jour le film
            MERGE (mov:Movie {id: $id})
            SET mov.title = $title, 
                mov.year = $year, 
                mov.genre = $genre, 
                mov.rating = $rating
            
            // 2. Gérer le Réalisateur (Nouveau)
            WITH mov
            MERGE (dir:Director {name: $director})
            MERGE (dir)-[:DIRECTED]->(mov)
            
            // 3. Gérer les Acteurs
            WITH mov
            UNWIND $actors AS actor_name
            MERGE (act:Actor {name: actor_name})
            MERGE (act)-[:ACTED_IN]->(mov)
        """, 
        id=m['id'], 
        title=m['title'], 
        year=m['year'], 
        genre=m['genre'], 
        rating=m['rating'], 
        director=m['director'], # Ajout du champ director
        actors=m['actors'])

print("✅ Neo4j : Films, Acteurs et Directeurs importés avec succès.")
# 3. Import vers Redis (Clé-Valeur)
r = redis.Redis(host='localhost', port=6379, db=0)
<<<<<<< HEAD
for m in movies:
    # On stocke les vues (initialisées à 0) pour chaque film
    r.set(f"movie:{m['id']}:views", 0)
print("✅ Redis : Compteurs de vues initialisés.")
=======
try:
    for m in movies:
        r.set(f"movie:{m['id']}:views", 0)
    print("✅ Redis : Compteurs de vues initialisés.")
except Exception as e:
    print(f"❌ Redis Error: {e}")

# 4. Import vers HBase (Column Family)
try:
    import happybase
    connection = happybase.Connection('localhost', port=9090)
    connection.open()
    # Check if table exists, create if not
    if b'movies' not in connection.tables():
        connection.create_table(
            'movies',
            {'info': dict(), 'credits': dict()}
        )
    table = connection.table('movies')
    
    batch = table.batch()
    for m in movies:
        row_key = str(m['id']).encode('utf-8')
        batch.put(row_key, {
            b'info:title': m['title'].encode('utf-8'),
            b'info:year': str(m['year']).encode('utf-8'),
            b'info:genre': m['genre'].encode('utf-8'),
            b'credits:director': m['director'].encode('utf-8'),
            # Join actors list to string
            b'credits:actors': ",".join(m['actors']).encode('utf-8')
        })
    batch.send()
    print("✅ HBase : Import terminé.")
except Exception as e:
    print(f"⚠️ HBase Indisponible (Docker container running?): {e}")
>>>>>>> iter2
