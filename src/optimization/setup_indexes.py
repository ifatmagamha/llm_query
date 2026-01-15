from pymongo import MongoClient
from neo4j import GraphDatabase

def optimize_mongo(uri="mongodb://localhost:27017/"):
    print("Optimization: Applying MongoDB Indexes...")
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=2000)
        db = client.movie_db # MVP hardcoded
        
        # 1. Text Index for Search
        db.movies.create_index([("title", "text"), ("genre", "text")])
        
        # 2. Frequent Filter Indexes
        db.movies.create_index("year")
        db.movies.create_index("rating")
        db.movies.create_index("director")
        
        print("✅ MongoDB Indexes Created.")
    except Exception as e:
        print(f"⚠️ MongoDB Optimization Skipped: {e}")

def optimize_neo4j(uri="bolt://localhost:7687", auth=("neo4j", "password")):
    print("Optimization: Applying Neo4j Constraints...")
    try:
        driver = GraphDatabase.driver(uri, auth=auth)
        with driver.session() as session:
            # 1. ID Constraints
            session.run("CREATE CONSTRAINT FOR (m:Movie) REQUIRE m.id IS UNIQUE IF NOT EXISTS")
            session.run("CREATE CONSTRAINT FOR (p:Person) REQUIRE p.name IS UNIQUE IF NOT EXISTS")
            
            # 2. Search Indexes
            session.run("CREATE INDEX movie_title IF NOT EXISTS FOR (m:Movie) ON (m.title)")
            
        print("✅ Neo4j Indexes Created.")
    except Exception as e:
        print(f"⚠️ Neo4j Optimization Skipped: {e}")

if __name__ == "__main__":
    optimize_mongo()
    optimize_neo4j()
