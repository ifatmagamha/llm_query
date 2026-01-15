import time
from typing import Any, Dict
import rdflib
from .base import BaseConnector, DatabaseMetadata, ExecutionResult

class RdfConnector(BaseConnector):
    def __init__(self, uri: str = "memory", **kwargs):
        """
        uri: 'memory' for in-memory graph, or a URL to a SPARQL endpoint (feature todo).
        """
        super().__init__(uri, **kwargs)
        self.graph = None

    def connect(self):
        try:
            self.graph = rdflib.Graph()
            # In a real app, we'd load data here or connect to a remote store.
            # For this prototype, we'll initialize with some dummy movie data 
            # so queries return something.
            self._load_sample_data()
            self.connected = True
            print("Connected to RDF Graph (In-Memory)")
        except Exception as e:
            print(f"Failed to connect to RDF: {e}")
            self.connected = False
            raise e
    
    def _load_sample_data(self):
        # Define some prefixes
        EX = rdflib.Namespace("http://example.org/movies/")
        self.graph.bind("ex", EX)
        
        # Add basic data (Inception) mimicking the other DBs
        movie = EX.Inception
        self.graph.add((movie, rdflib.RDF.type, EX.Movie))
        self.graph.add((movie, EX.title, rdflib.Literal("Inception")))
        self.graph.add((movie, EX.director, EX.ChristopherNolan))
        self.graph.add((EX.ChristopherNolan, rdflib.RDF.type, EX.Director))

    def get_metadata(self) -> DatabaseMetadata:
        if not self.connected:
            self.connect()
        
        summary = {"predicates": [], "types": []}
        try:
            # query distinct predicates
            q = "SELECT DISTINCT ?p WHERE { ?s ?p ?o }"
            res = self.graph.query(q)
            summary["predicates"] = [str(r.p) for r in res]
            
            # query distinct types
            q2 = "SELECT DISTINCT ?t WHERE { ?s a ?t }"
            res2 = self.graph.query(q2)
            summary["types"] = [str(r.t) for r in res2]
            
        except Exception as e:
            print(f"Error fetching RDF metadata: {e}")

        return DatabaseMetadata(
            db_type="rdf_sparql",
            schema_summary=summary,
            version="rdflib-memory"
        )

    def execute(self, query: str, operation_type: str = "read") -> ExecutionResult:
        """
        Executes a SPARQL query.
        """
        if not self.connected:
            self.connect()
            
        start_time = time.time()
        try:
            # rdflib query returns a Result object
            res = self.graph.query(query)
            
            # Convert to list of dicts for JSON serialization
            # res.bindings is a list of dicts of RDFlib terms
            data = []
            for row in res:
                # row is a resultRow, can be accessed by variable name
                # or we can iterate.
                # simpler: serialize to a standard format?
                # let's try to make a list of dicts from keys
                row_dict = {}
                # row.asdict() might happen if we iterate bindings?
                # rdflib Result is iterable.
                # let's map vars
                for var in res.vars:
                    val = row[var]
                    row_dict[str(var)] = str(val) # Convert URIs/Literals to strings
                data.append(row_dict)
                
            duration = (time.time() - start_time) * 1000
            return ExecutionResult(
                status="success",
                payload=data,
                raw_response="SPARQL Result",
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
        self.graph = None
