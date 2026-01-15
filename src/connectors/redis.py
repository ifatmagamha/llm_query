import time
from typing import Any, Dict, List
import redis
from .base import BaseConnector, DatabaseMetadata, ExecutionResult

class RedisConnector(BaseConnector):
    def __init__(self, uri: str = "redis://localhost:6379", **kwargs):
        # Handle simple host/port dict if needed, but uri is standard
        super().__init__(uri, **kwargs)
        self.client = None

    def connect(self):
        try:
            self.client = redis.Redis.from_url(self.uri, decode_responses=True)
            self.client.ping()
            self.connected = True
            print("Connected to Redis")
        except Exception as e:
            print(f"Failed to connect to Redis: {e}")
            self.connected = False
            raise e

    def get_metadata(self) -> DatabaseMetadata:
        if not self.connected:
            self.connect()
        
        # Redis has no schema. We scan for patterns.
        # Research approach: Sample random keys to guess schema.
        summary = {"key_patterns": [], "sample_keys": []}
        try:
            # Scan first 100 keys
            cursor, keys = self.client.scan(count=100)
            summary["sample_keys"] = keys
            
            # Simple pattern inference (e.g., "avg_rating" from "movie:1:avg_rating")
            patterns = set()
            for k in keys:
                parts = k.split(":")
                if len(parts) > 1:
                    # Abstract the ID part (numeric)
                    pattern = ":".join(["{id}" if p.isdigit() else p for p in parts])
                    patterns.add(pattern)
            summary["key_patterns"] = list(patterns)

        except Exception as e:
            print(f"Error fetching Redis metadata: {e}")

        return DatabaseMetadata(
            db_type="redis",
            schema_summary=summary,
            version="unknown"
        )

    def execute(self, query: str, operation_type: str = "read") -> ExecutionResult:
        """
        Executes a Redis command.
        Query is expected to be a space-separated string e.g. "GET movie:1" or "HGETALL movie:1:info"
        """
        if not self.connected:
            self.connect()
            
        start_time = time.time()
        try:
            # Very basic parsing. In a real shell we'd handle quotes.
            parts = query.split()
            if not parts:
                raise ValueError("Empty query")
            
            cmd = parts[0].upper()
            args = parts[1:]

            result = self.client.execute_command(cmd, *args)
            
            duration = (time.time() - start_time) * 1000
            return ExecutionResult(
                status="success",
                payload=result,
                raw_response=None,
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
