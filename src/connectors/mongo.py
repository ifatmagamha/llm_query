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
            print(f"⚠️ Failed to connect to MongoDB: {e}")
            self.connected = False
            # Do not raise, allow graceful degradation

    def get_metadata(self) -> DatabaseMetadata:
        if not self.connected:
            try:
                self.connect()
            except:
                pass
        
        if not self.connected:
             return DatabaseMetadata(db_type="mongodb", schema_summary={"error": "Disconnected"}, version="N/A")

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
        """
        if not self.connected:
            try:
                self.connect()
            except:
                pass
        
        if not self.connected:
            return ExecutionResult(status="error", payload=None, raw_response=None, error_message="MongoDB is disconnected. Please start the server.")
            
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
            # Convert ObjectId to string for JSON serialization
            original_result_data = result_data # Store original for raw_response if needed
            sanitized_payload = []
            if isinstance(result_data, list):
                for doc in result_data:
                    # Create a copy to avoid modifying the original object in place if it's used elsewhere
                    # and to ensure _id is handled correctly if it's a BSON ObjectId
                    if isinstance(doc, dict):
                        new_doc = doc.copy()
                        if "_id" in new_doc:
                            new_doc["_id"] = str(new_doc["_id"])
                        sanitized_payload.append(new_doc)
                    else:
                        sanitized_payload.append(doc) # Append non-dict items as is
            elif isinstance(result_data, dict):
                sanitized_payload = result_data.copy()
                if "_id" in sanitized_payload:
                    sanitized_payload["_id"] = str(sanitized_payload["_id"])
            else:
                sanitized_payload = result_data

            return ExecutionResult(
                status="success", 
                payload=sanitized_payload,
                raw_response=original_result_data, 
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
