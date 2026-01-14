import streamlit as st
import requests
import json
import redis 
from pymongo import MongoClient
from neo4j import GraphDatabase
from streamlit_agraph import agraph, Node, Edge, Config
import os
from dotenv import load_dotenv
load_dotenv()

def draw_movie_graph(records):
    nodes = []
    edges = []
    node_ids = set()
    edge_ids = set()

    for record in records:
        for item in record.values():
            # CAS 1 : C'est un Nœud (Node)
            if hasattr(item, 'labels'): 
                n_id = item.element_id
                if n_id not in node_ids:
                    lbl = item.get('title') or item.get('name')
                    # Couleurs : Rouge=Film, Bleu=Acteur, Or=Réalisateur
                    color = "#FF4B4B" if "Movie" in item.labels else "#1C83E1"
                    if "Director" in item.labels: color = "#FFD700"
                    nodes.append(Node(id=n_id, label=lbl, color=color, size=20))
                    node_ids.add(n_id)
            
            # CAS 2 : C'est une Relation (Relationship)
            elif hasattr(item, 'start_node'): 
                e_id = item.element_id
                if e_id not in edge_ids:
                    edges.append(Edge(
                        source=item.start_node.element_id, 
                        target=item.end_node.element_id, 
                        label=item.type,
                        color="#3BCB96"
                    ))
                    edge_ids.add(e_id)

    if not nodes:
        st.warning("Aucune donnée visuelle trouvée.")
        return

    config = Config(width=800, height=600, directed=True, physics=True, hierarchical=False)
    return agraph(nodes=nodes, edges=edges, config=config)

# --- CONFIGURATION ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = "models/gemini-2.0-flash-001"
URL = f"https://generativelanguage.googleapis.com/v1beta/{MODEL_NAME}:generateContent?key={GEMINI_API_KEY}"

# --- CONNEXIONS BASES DE DONNÉES ---
try:
    # MongoDB
    mongo_client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=2000)
    db = mongo_client.movie_db
    
    # Neo4j
    neo4j_driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password123"))

    # Redis (NOUVEAU)
    # decode_responses=True permet de récupérer des chaînes de caractères plutôt que des bytes
    r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
except Exception as e:
    st.error(f"Erreur de connexion aux bases Docker : {e}")

# --- MÉTA-DONNÉES ---
SCHEMA_DESCRIPTION = """
Tu es un expert en bases de données NoSQL (MongoDB et Neo4j).
Voici le schéma exact de la base 'movie_db' (50 films) :

1. MONGODB (Collection: 'movies') - Format Document :
   - 'title' (String): Nom du film (ex: "Inception")
   - 'year' (Int): Année de sortie (ex: 2010)
   - 'genre' (String): Genre unique (Valeurs possibles: "Action", "Drama", "Sci-Fi", "Thriller", "Adventure")
   - 'director' (String): Nom complet du réalisateur
   - 'actors' (Array of Strings): Liste des acteurs
   - 'rating' (Float): Note sur 10

2. NEO4J - Format Graphe :
   - Nœuds : 
     * (:Movie {title, year, genre, rating})
     * (:Actor {name})
     * (:Director {name})
   - Relations :
     * (:Actor)-[:ACTED_IN]->(:Movie)
     * (:Director)-[:DIRECTED]->(:Movie)
    Pour Neo4j, si l'utilisateur veut voir un graphe ou des liens :
- Tu DOIS inclure la relation dans le RETURN.
- Exemple incorrect : MATCH (d)-[:DIRECTED]->(m) RETURN d, m
- Exemple CORRECT : MATCH (d:Director)-[r:DIRECTED]->(m:Movie) RETURN d, r, m
INSTRUCTION CRUCIALE : Pour Neo4j, tu dois toujours nommer et retourner la relation. Exemple : MATCH (a:Actor)-[r:ACTED_IN]->(m:Movie) RETURN a, r, m. Si tu ne mets pas 'r' dans le RETURN, le graphe sera vide.

RÈGLES CRUCIALES :
- Respecte la casse (ex: "Sci-Fi" et non "science-fiction").
- MongoDB : Retourne UNIQUEMENT l'objet JSON de filtre. Pas de 'db.movies.find()'.
- Neo4j : Utilise les noms de labels et types de relations définis ci-dessus.
"""

st.title("🎬 Multi-NoSQL Movie Query")

user_query = st.text_input("Posez une question sur les films :", "Quels films de Nolan ont une note > 8 ?")

# Initialisation du session_state
if 'mongo_q' not in st.session_state:
    st.session_state.mongo_q = None
    st.session_state.neo4j_q = None
    st.session_state.expla = None

if st.button("Générer les requêtes"):
    # --- LOGIQUE REDIS : VÉRIFICATION DU CACHE ---
    cache_key = f"query:{user_query.lower().strip()}"
    cached_data = None
    
    try:
        cached_data = r.get(cache_key)
    except:
        pass # Si redis n'est pas dispo, on continue sans cache

    if cached_data:
        # On récupère les données depuis Redis
        st.info("⚡ Récupéré depuis le cache Redis (Pas d'appel API)")
        data = json.loads(cached_data)
        st.session_state.mongo_q = data['mongo']
        st.session_state.neo4j_q = data['neo4j']
        st.session_state.expla = data['expla']
    else:
        # --- APPEL IA (Si pas de cache) ---
        prompt = f"""
{SCHEMA_DESCRIPTION}

Question de l'utilisateur : "{user_query}"

CONSIGNES TECHNIQUES STRICTES POUR MONGODB :
1. Produis UNIQUEMENT un objet JSON valide pour le premier argument de la fonction .find() de PyMongo.
2. INTERDICTION : Ne pas inclure de projection.
3. INTERDICTION : Ne pas inclure de fonctions comme 'db.collection.find()'.
4. FORMAT : Utilise le format JSON strict.

RETOUR ATTENDU :
---MONGO---
{{ "director": "Christopher Nolan", "rating": {{ "$gt": 8 }} }}
---NEO4J---
(Requête Cypher ici)
---EXPLICATION---
(Explication ici)
"""
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        
        with st.spinner("L'IA traduit votre question..."):
            res = requests.post(URL, json=payload)
            if res.status_code == 200:
                raw_text = res.json()['candidates'][0]['content']['parts'][0]['text']
                try:
                    # Extraction
                    m_raw = raw_text.split("---MONGO---")[1].split("---NEO4J---")[0].strip()
                    n_raw = raw_text.split("---NEO4J---")[1].split("---EXPLICATION---")[0].strip()
                    e_raw = raw_text.split("---EXPLICATION---")[1].strip()
                    
                    # Nettoyage
                    m_clean = m_raw.replace("```json", "").replace("```", "").replace("javascript", "").strip()
                    if "find(" in m_clean:
                        m_clean = m_clean.split("find(")[1].split(")")[0]
                    
                    n_clean = n_raw.replace("```cypher", "").replace("```", "").strip()

                    # Mise à jour du session_state
                    st.session_state.mongo_q = m_clean
                    st.session_state.neo4j_q = n_clean
                    st.session_state.expla = e_raw

                    # --- LOGIQUE REDIS : SAUVEGARDE DANS LE CACHE ---
                    res_to_cache = {
                        "mongo": m_clean,
                        "neo4j": n_clean,
                        "expla": e_raw
                    }
                    r.setex(cache_key, 3600, json.dumps(res_to_cache)) # Cache valide 1 heure

                except:
                    st.error("Erreur de lecture du format IA.")

# --- AFFICHAGE ET EXÉCUTION ---
if st.session_state.mongo_q:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🍃 MongoDB")
        st.code(st.session_state.mongo_q, language="json")
        if st.button("🚀 Run sur MongoDB"):
            try:
                raw_query = st.session_state.mongo_q.strip()
                clean_text = raw_query.replace("```json", "").replace("```", "").replace("javascript", "").strip()

                try:
                    parsed_data = json.loads(f"[{clean_text}]")
                except:
                    import ast
                    parsed_data = ast.literal_eval(f"[{clean_text}]")

                final_query = {}
                for d in parsed_data:
                    final_query.update(d)

                results = list(db.movies.find(final_query).limit(10))

                if results:
                    st.success(f"✅ {len(results)} résultats trouvés")
                    for r_doc in results:
                        # ON INCREMENTE ICI
                        if 'title' in r_doc:
                            r.zincrby("popularite", 1, r_doc['title'])
                        
                        r_doc.pop('_id', None)
                    st.table(results)
                else:
                    st.warning("Aucun film trouvé.")

            except Exception as e:
                st.error(f"Erreur de syntaxe : {e}")

    with col2:
        st.subheader("🕸️ Neo4j")
        st.code(st.session_state.neo4j_q, language="cypher")
        if st.button("🚀 Run sur Neo4j"):
            try:
                with neo4j_driver.session() as session:
                    res = session.run(st.session_state.neo4j_q)
                    data = [record.data() for record in res]
                    st.write(data if data else "Aucun noeud trouvé.")
            except Exception as e:
                st.error(f"Erreur Neo4j: {e}")
            
            try:
                with neo4j_driver.session() as session:
                    res = session.run(st.session_state.neo4j_q)
                    records = list(res) # On garde les données en mémoire
                    
                    if records:
                        st.success("Graphe généré :")
                        # Option A : Affichage visuel (Nouveau !)
                        draw_movie_graph(records)
                        
                        # Option B : Affichage texte (toujours utile)
                        with st.expander("Voir les données brutes"):
                            st.write([r.data() for r in records])
                    else:
                        st.warning("Aucun résultat pour cette requête.")
            except Exception as e:
                st.error(f"Erreur Neo4j: {e}")

    st.info(f"**Explication :** {st.session_state.expla}")

# --- ÉTAPE FINALE : DASHBOARD ANALYTICS (REDIS) ---
st.sidebar.header("📊 Statistiques Temps Réel")

# 1. Afficher l'état du cache
try:
    all_keys = r.keys("query:*")
    st.sidebar.metric("Requêtes en Cache", len(all_keys))
except:
    st.sidebar.error("Redis indisponible")

# 2. Afficher le Top 3 des films consultés
st.sidebar.subheader("🏆 Top 3 Films Consultés")
try:
    # On récupère les 3 meilleurs scores du 'Sorted Set' Redis
    top_movies = r.zrevrange("popularite", 0, 2, withscores=True)
    if top_movies:
        for i, (movie, score) in enumerate(top_movies, 1):
            st.sidebar.write(f"{i}. **{movie}** ({int(score)} vues)")
    else:
        st.sidebar.write("Aucune donnée pour le moment.")
except:
    pass

# 3. Bouton pour vider le cache (très utile pour la démo !)
if st.sidebar.button("🧹 Vider le Cache Redis"):
    for key in r.keys("query:*"):
        r.delete(key)
    st.sidebar.success("Cache vidé !")
    st.rerun()