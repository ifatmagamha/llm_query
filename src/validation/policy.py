from typing import List
import re

class SafetyException(Exception):
    pass

class PolicyValidator:
    """
    Enforces the 'Safe-by-Default' policy.
    Block writes unless explicitly allowed.
    """
    
    def __init__(self, allow_writes: bool = False):
        self.allow_writes = allow_writes
        
        # Regex patterns for dangerous keywords in raw queries
        self.DANGEROUS_PATTERNS = {
            "mongo": [r"insert", r"update", r"delete", r"drop", r"remove", r"write"],
            "redis": [r"SET", r"DEL", r"FLUSH", r"HMSET", r"LPOP"],
            "neo4j": [r"CREATE", r"DELETE", r"SET", r"MERGE", r"DETACH", r"DROP"],
            "sql": [r"INSERT", r"UPDATE", r"DELETE", r"DROP", r"ALTER"],
            "hbase": [r"put", r"delete", r"drop"],
            "sparql": [r"INSERT", r"DELETE", r"CLEAR", r"DROP"]
        }

    def check_ir_safety(self, ir_intent: str):
        """
        Check safety based on the structured Intermediate Representation intent.
        """
        safe_intents = ["FIND", "AGGREGATE", "TRAVERSAL", "SCAN"]
        # "MUTATION" or "WRITE" would be unsafe
        
        if ir_intent.upper() not in safe_intents:
            if not self.allow_writes:
                raise SafetyException(f"Safety Policy Violation: Intent '{ir_intent}' requires Write permissions.")
        
        return True

    def check_raw_safety(self, query: str, db_type: str):
        """
        Fallback check for raw query strings.
        """
        if self.allow_writes:
            return True
            
        patterns = self.DANGEROUS_PATTERNS.get(db_type, [])
        for pat in patterns:
            # Case insensitive check
            if re.search(pat, query, re.IGNORECASE):
                # Basic check, might have false positives (e.g. searching for a movie titled "The Delete")
                # But for a research prototype, better safe than sorry.
                # In a real system, we'd use a parser, not regex.
                raise SafetyException(f"Safety Policy Violation: Query contains forbidden keyword '{pat}'")
        
        return True
