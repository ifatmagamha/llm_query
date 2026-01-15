import hashlib
import json
import time

class SemanticCache:
    """
    Simple In-Memory LRU Cache for NLQ results.
    Keys are hashed NLQ + DB_TYPE.
    """
    def __init__(self, capacity: int = 100):
        self.capacity = capacity
        self.cache = {}
        self.order = []

    def _get_key(self, nlq: str, db_type: str) -> str:
        # Simple normalization
        normalized = nlq.lower().strip()
        raw = f"{db_type}:{normalized}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def get(self, nlq: str, db_type: str):
        key = self._get_key(nlq, db_type)
        if key in self.cache:
            # Move to end (recently used)
            self.order.remove(key)
            self.order.append(key)
            print(f"⚡ Cache Hit for '{nlq}'")
            return self.cache[key]
        return None

    def set(self, nlq: str, db_type: str, result: dict):
        key = self._get_key(nlq, db_type)
        if key in self.cache:
            self.order.remove(key)
        
        self.cache[key] = result
        self.order.append(key)
        
        if len(self.order) > self.capacity:
            oldest = self.order.pop(0)
            del self.cache[oldest]
