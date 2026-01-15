import time
from typing import Any, Dict, List
try:
    import happybase
except ImportError:
    happybase = None

from .base import BaseConnector, DatabaseMetadata, ExecutionResult

class HBaseConnector(BaseConnector):
    def __init__(self, host: str = "localhost", port: int = 9090, **kwargs):
        super().__init__(f"{host}:{port}", **kwargs)
        self.host = host
        self.port = port
        self.connection = None

    def connect(self):
        if not happybase:
            raise ImportError("happybase library not installed. Cannot connect to HBase.")
        
        try:
            self.connection = happybase.Connection(self.host, port=self.port)
            self.connection.open()
            self.connected = True
            print(f"Connected to HBase at {self.host}:{self.port}")
        except Exception as e:
            print(f"Failed to connect to HBase: {e}")
            self.connected = False
            raise e

    def get_metadata(self) -> DatabaseMetadata:
        if not self.connected:
            self.connect()
        
        summary = {"tables": {}}
        try:
            tables = self.connection.tables()
            for t_name_bytes in tables:
                t_name = t_name_bytes.decode('utf-8')
                # Get column families
                table = self.connection.table(t_name)
                # families is a dict
                families = table.families() 
                # {b'info': {'max_versions': 3, ...}}
                summary["tables"][t_name] = {
                    "families": [f.decode('utf-8') if isinstance(f, bytes) else f for f in families.keys()]
                }
        except Exception as e:
            print(f"Error fetching HBase metadata: {e}")

        return DatabaseMetadata(
            db_type="hbase",
            schema_summary=summary,
            version="happybase"
        )

    def execute(self, query: str, operation_type: str = "read") -> ExecutionResult:
        """
        Executes an HBase operation.
        Query Format (JSON):
        {
            "table": "movies",
            "operation": "scan" | "get" | "put",
            "args": { ... }
        }
        """
        if not self.connected:
            self.connect()
            
        start_time = time.time()
        try:
            import json
            cmd = json.loads(query)
            t_name = cmd.get("table")
            op = cmd.get("operation")
            args = cmd.get("args", {})
            
            table = self.connection.table(t_name)
            result_data = None
            
            if op == "scan":
                # args: limit, filter? Happybase scan is simple
                # Scan returns generator (key, data_dict)
                limit = args.get("limit", 10)
                gen = table.scan(limit=limit) 
                # Convert bytes to strings for display
                data = []
                for key, val_dict in gen:
                    row = {"row_key": key.decode('utf-8')}
                    for col, val in val_dict.items():
                         row[col.decode('utf-8')] = val.decode('utf-8')
                    data.append(row)
                result_data = data
                
            elif op == "get":
                row_key = args.get("row_key")
                if not row_key:
                    raise ValueError("get require row_key")
                val_dict = table.row(row_key.encode('utf-8'))
                # Decode
                row = {"row_key": row_key}
                for col, val in val_dict.items():
                        row[col.decode('utf-8')] = val.decode('utf-8')
                result_data = row
                
            elif op == "put":
                if operation_type != "write":
                     raise PermissionError("Write not allowed")
                row_key = args.get("row_key")
                data = args.get("data", {}) # {"cf:col": "val"}
                # Encode data
                batch_data = {k.encode('utf-8'): v.encode('utf-8') for k, v in data.items()}
                table.put(row_key.encode('utf-8'), batch_data)
                result_data = "Success"
                
            else:
                 raise NotImplementedError(f"HBase Op {op} unknown")

            duration = (time.time() - start_time) * 1000
            return ExecutionResult(
                status="success",
                payload=result_data,
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
        if self.connection:
            self.connection.close()
