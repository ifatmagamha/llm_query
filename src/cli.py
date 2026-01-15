import argparse
import sys
import json
import os

# Add project root to path
sys.path.append(os.getcwd())

from src.connectors.mongo import MongoConnector
from src.connectors.redis import RedisConnector
from src.connectors.neo4j import Neo4jConnector
from src.connectors.rdf import RdfConnector
from src.connectors.hbase import HBaseConnector
from src.llm.provider import LLMProvider
from src.rag.store import SimpleRAGStore
from src.pipeline.smart import SmartPipeline

def get_connector(db_type: str):
    if db_type == "mongo":
        return MongoConnector()
    elif db_type == "redis":
        return RedisConnector()
    elif db_type == "neo4j":
        return Neo4jConnector()
    elif db_type == "rdf":
        return RdfConnector()
    elif db_type == "hbase":
        return HBaseConnector()
    else:
        raise ValueError(f"Unknown db_type: {db_type}")

def main():
    parser = argparse.ArgumentParser(description="NoSQL NLQ Research Prototype CLI")
    parser.add_argument("--db", required=True, choices=["mongo", "redis", "neo4j", "rdf", "hbase"], help="Target Database")
    parser.add_argument("--query", required=True, help="Natural Language Query")
    parser.add_argument("--unsafe", action="store_true", help="Allow write operations")
    parser.add_argument("--details", action="store_true", help="Show execution trace/IR")
    
    args = parser.parse_args()
    
    print(f"--- Initializing System for {args.db.upper()} ---")
    
    try:
        # 1. Setup Components
        connector = get_connector(args.db)
        llm = LLMProvider()
        rag = SimpleRAGStore()
        
        pipeline = SmartPipeline(connector, llm, rag)
        pipeline.set_safety(args.unsafe)
        
        # 2. Run
        print(f"Query: {args.query}")
        result = pipeline.run(args.query)
        
        # 3. Output
        if result["success"]:
            print("\n✅ Execution Success!")
            print("Result Payload:")
            print(json.dumps(result["final_result"], indent=2, default=str))
        else:
            print("\n❌ Execution Failed.")
            print(f"Error: {result.get('error')}")

        if args.details:
            print("\n--- Execution Details ---")
            for i, step in enumerate(result["steps"]):
                print(f"\nStep {i+1} (Attempt {step['attempt']}):")
                if "parsed_ir" in step:
                    print(f"  Intent: {step['parsed_ir'].get('intent')}")
                if "execution" in step:
                    print(f"  Exec Status: {step['execution'].status}")
                    if step['execution'].error_message:
                        print(f"  Error: {step['execution'].error_message}")

    except Exception as e:
        print(f"\nExample Usage: python src/cli.py --db mongo --query 'Find movies directed by Nolan'")
        print(f"Critial Error: {e}")

if __name__ == "__main__":
    main()
