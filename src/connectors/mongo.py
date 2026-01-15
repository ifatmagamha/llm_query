import json
import time
from typing import Any, Dict
from pymongo import MongoClient
from .base import BaseConnector, DatabaseMetadata, ExecutionResult

class MongoConnector(BaseConnector):
    def __init__(self, uri: str = "mongodb://localhost:27017/", db_name: str = "movie_db", **kwargs):
        super().__init__(uri, **kwargs)
        self.db_name = db_name
        self.client = None
        self.db = None

    def connect(self):
        try:
            self.client = MongoClient(self.uri, serverSelectionTimeoutMS=2000)
            self.client.server_info() # Trigger connection check
            self.db = self.client[self.db_name]
            self.connected = True
            print(f"Connected to MongoDB: {self.db_name}")
        except Exception as e:
            print(f"Failed to connect to MongoDB: {e}")
            self.connected = False
            raise e

    def get_metadata(self) -> DatabaseMetadata:
        if not self.connected:
            self.connect()
        
        summary = {"collections": {}}
        try:
            collections = self.db.list_collection_names()
            for col in collections:
                # Simple heuristic: Field inference from first document
                one_doc = self.db[col].find_one()
                fields = list(one_doc.keys()) if one_doc else []
                summary["collections"][col] = {"fields": fields, "sample": str(one_doc)}
        except Exception as e:
            print(f"Error fetching metadata: {e}")
        
        return DatabaseMetadata(
            db_type="mongodb",
            schema_summary=summary,
            version="unknown"
        )

    def execute(self, query: str, operation_type: str = "read") -> ExecutionResult:
        """
        Executes a Mongo query.
        For MVP, query is expected to be a JSON string with:
        {
            "collection": "movies",
            "operation": "find" | "aggregate" | "insert_one" ...
            "args": { ... }
        }
        """
        if not self.connected:
            self.connect()
            
        start_time = time.time()
        try:
            # Parse the "Query" which is actually a JSON command instruction
            command = json.loads(query)
            col_name = command.get("collection")
            op = command.get("operation")
            args = command.get("args", {})

            if not col_name or not op:
                raise ValueError("Query must specify 'collection' and 'operation'")

            collection = self.db[col_name]
            
            # Simple dispatch (Safe-mode should catch writes before this, but basic logic here)
            result_data = None
            raw_cursor = None

            if op == "find":
                # args might contain 'filter', 'projection', 'limit'
                filter_ = args.get("filter", {})
                proj = args.get("projection")
                limit = args.get("limit", 10)
                
                cursor = collection.find(filter_, proj).limit(limit)
                result_data = list(cursor)
                raw_cursor = "Cursor consumed"
            
            elif op == "aggregate":
                pipeline = args.get("pipeline", [])
                cursor = collection.aggregate(pipeline)
                result_data = list(cursor)
                
            elif op == "count_documents":
                 filter_ = args.get("filter", {})
                 result_data = collection.count_documents(filter_)

            else:
                # MVP Safety fall-through
                if operation_type != "write":
                    return ExecutionResult(status="error", payload=None, raw_response=None, error_message=f"Operation '{op}' not allowed in read-only mode")
                
                # If write permitted (this is a research prototype, so we implement rudimentary write)
                if op == "insert_one":
                    res = collection.insert_one(args.get("document"))
                    result_data = str(res.inserted_id)
                else:
                    raise NotImplementedError(f"Mongo Operation {op} not implemented in connector")

            duration = (time.time() - start_time) * 1000
            return ExecutionResult(
                status="success",
                payload=result_data,
                raw_response=raw_cursor,
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
        if self.client:
            self.client.close()
