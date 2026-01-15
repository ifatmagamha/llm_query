import time
from typing import Any, Dict, List
from neo4j import GraphDatabase, basic_auth
from .base import BaseConnector, DatabaseMetadata, ExecutionResult

class Neo4jConnector(BaseConnector):
    def __init__(self, uri: str = "bolt://localhost:7687", user: str = "neo4j", password: str = "password", **kwargs):
        super().__init__(uri, **kwargs)
        self.auth = (user, password)
        self.driver = None

    def connect(self):
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=self.auth)
            self.driver.verify_connectivity()
            self.connected = True
            print("Connected to Neo4j")
        except Exception as e:
            print(f"Failed to connect to Neo4j: {e}")
            self.connected = False
            raise e

    def get_metadata(self) -> DatabaseMetadata:
        if not self.connected:
            self.connect()
        
        summary = {"nodes": [], "relationships": []}
        try:
            with self.driver.session() as session:
                # Get labels
                result = session.run("CALL db.labels()")
                summary["nodes"] = [record["label"] for record in result]
                
                # Get relationship types
                result = session.run("CALL db.relationshipTypes()")
                summary["relationships"] = [record["relationshipType"] for record in result]
                
                # Could also do db.schema.visualization() but that returns a complex graph object
        except Exception as e:
            print(f"Error fetching Neo4j metadata: {e}")

        return DatabaseMetadata(
            db_type="neo4j",
            schema_summary=summary,
            version="unknown"
        )

    def execute(self, query: str, operation_type: str = "read") -> ExecutionResult:
        """
        Executes a Cypher query.
        """
        if not self.connected:
            self.connect()
            
        start_time = time.time()
        try:
            with self.driver.session() as session:
                # Run query
                if operation_type == "read":
                    result = session.run(query)
                else: 
                     # Write transaction if we were separating them rigidly, but 'run' handles both.
                     # The Policy layer should have blocked unsafe writes.
                     result = session.run(query)

                # Fetch all data
                data = [dict(record) for record in result]
                
                # Consume result to get stats
                consume_result = result.consume()
            
            duration = (time.time() - start_time) * 1000
            return ExecutionResult(
                status="success",
                payload=data,
                raw_response=consume_result.counters, # Stats about updates
                execution_time_ms=duration
            )

        except Exception as e:
            return ExecutionResult(
                status="error",
                payload=None,
                raw_response=None,
                error_message=str(e),
                execution_time_ms=(time.time() - start_time) * 1000
            )

    def close(self):
        if self.driver:
            self.driver.close()
