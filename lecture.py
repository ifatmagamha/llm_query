import json
import os
from pymongo import MongoClient
import redis

# Use absolute path for data loading
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, 'data', 'data.json')

# Chargement des données
try:
    with open(DATA_FILE, 'r') as f:
        movies = json.load(f)
    print(f"✅ Data loaded: {len(movies)} movies found.")
except FileNotFoundError:
    print(f"❌ Error: Data file not found at {DATA_FILE}")
    exit(1)

# 1. Import vers MongoDB (Document)
try:
    mongo_client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=2000)
    db = mongo_client.movie_db
    # Idempotency: Drop collection first
    db.movies.drop()
    db.movies.insert_many(movies)
    print("✅ MongoDB : 50 films importés (Collection dropped & recreated).")
except Exception as e:
    print(f"❌ MongoDB Error: {e}")

# 2. Import vers Neo4j (Graphe) - Version Enrichie
try:
    from neo4j import GraphDatabase
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password123"))
    driver.verify_connectivity()
    
    with driver.session() as session:
        # Nettoyer la base pour éviter les doublons (Idempotency)
        session.run("MATCH (n) DETACH DELETE n")
        
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
            director=m['director'],
            actors=m['actors'])
    print("✅ Neo4j : Films, Acteurs et Directeurs importés avec succès.")
except ImportError:
    print("⚠️ Neo4j Driver not installed (pip install neo4j).")
except Exception as e:
    print(f"❌ Neo4j Error: {e}")

# 3. Import vers Redis (Clé-Valeur)
try:
    r = redis.Redis(host='localhost', port=6379, db=0)
    # Check connection
    r.ping()
    pipe = r.pipeline()
    for m in movies:
        pipe.set(f"movie:{m['id']}:views", 0)
    pipe.execute()
    print("✅ Redis : Compteurs de vues initialisés.")
except Exception as e:
    print(f"❌ Redis Error: {e}")

# 4. Import vers HBase (Column Family)
try:
    import happybase
    connection = happybase.Connection('localhost', port=9090)
    connection.open()
    # Check if table exists, create if not
    if b'movies' in connection.tables():
        print("   Found existing 'movies' table. analyzing state...")
        try:
            if connection.is_table_enabled('movies'):
                print("   Table is enabled. Disabling...")
                connection.disable_table('movies')
            else:
                 print("   Table is already disabled (or enabling).")
        except Exception as e:
             print(f"   Note: State transition error ({e}), attempting to delete anyway...")
             
        try:
            connection.delete_table('movies')
            print("   Table deleted.")
        except Exception as e:
            print(f"   Warning: Could not delete table: {e}")

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
    connection.close()
    print("✅ HBase : Import terminé.")
except ImportError:
    print("⚠️ happybase module not installed.")
except Exception as e:
    print(f"⚠️ HBase Indisponible (Docker container running?): {e}")
