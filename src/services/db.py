import os
import redis
from pymongo import MongoClient
from neo4j import GraphDatabase
import happybase
from dotenv import load_dotenv

load_dotenv()

class DatabaseManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        # MongoDB
        try:
            self.mongo_client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=2000)
            self.mongo_db = self.mongo_client.movie_db
            print("✅ MongoDB Connected")
        except Exception as e:
            print(f"❌ MongoDB Error: {e}")
            self.mongo_db = None

        # Neo4j
        try:
            self.neo4j_driver = GraphDatabase.driver(
                "bolt://localhost:7687", 
                auth=("neo4j", "password123")
            )
            print("✅ Neo4j Connected")
        except Exception as e:
            print(f"❌ Neo4j Error: {e}")
            self.neo4j_driver = None

        # Redis
        try:
            self.redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
            self.redis_client.ping()
            print("✅ Redis Connected")
        except Exception as e:
            print(f"❌ Redis Error: {e}")
            self.redis_client = None

        # HBase
        try:
            self.hbase_pool = happybase.ConnectionPool(size=3, host='localhost', port=9090)
            print("✅ HBase Connected")
        except Exception as e:
            print(f"❌ HBase Error: {e}")
            self.hbase_pool = None

    def get_mongo_db(self):
        return self.mongo_db

    def get_neo4j_driver(self):
        return self.neo4j_driver
    
    def get_redis_client(self):
        return self.redis_client

    def get_hbase_connection(self):
        if self.hbase_pool:
            return self.hbase_pool.connection()
        return None

# Global Instance
db_manager = DatabaseManager()
