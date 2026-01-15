from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

@dataclass
class ExecutionResult:
    status: str  # "success" or "error"
    payload: Any  # The simplified data returned
    raw_response: Any  # Original DB cursor/response
    error_message: Optional[str] = None
    execution_time_ms: float = 0.0

@dataclass
class DatabaseMetadata:
    db_type: str
    schema_summary: Dict[str, Any]  # e.g. {"collections": ["movies"], "fields": ...}
    version: str = "unknown"

class BaseConnector(ABC):
    """
    Abstract Base Class for all NoSQL Connectors.
    Enforces a unified interface for the 'Polyglot Persistence' architecture.
    """

    def __init__(self, uri: str, **kwargs):
        self.uri = uri
        self.config = kwargs
        self.connected = False

    @abstractmethod
    def connect(self):
        """Establish connection to the database."""
        pass

    @abstractmethod
    def get_metadata(self) -> DatabaseMetadata:
        """Retrieve schema/structure information for RAG/Context."""
        pass

    @abstractmethod
    def execute(self, query: str, operation_type: str = "read") -> ExecutionResult:
        """
        Execute a query. 
        Args:
            query: The db-specific query string (JSON for Mongo, Cypher for Neo4j).
            operation_type: 'read' or 'write'. Should check checking policy before execution if possible.
        """
        pass

    @abstractmethod
    def close(self):
        """Close the connection."""
        pass
