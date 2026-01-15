import json
import re
from typing import List, Dict

class SimpleRAGStore:
    def __init__(self, data_path: str = "data/examples.json"):
        self.data_path = data_path
        self.examples = []
        self._load_data()

    def _load_data(self):
        try:
            with open(self.data_path, 'r') as f:
                self.examples = json.load(f)
        except Exception as e:
            print(f"Warning: Could not load RAG data from {self.data_path}: {e}")
            self.examples = []

    def _tokenize(self, text: str) -> set:
        # Simple word tokenization, lowercased
        return set(re.findall(r'\w+', text.lower()))

    def _jaccard_similarity(self, query_tokens: set, doc_tokens: set) -> float:
        intersection = len(query_tokens.intersection(doc_tokens))
        union = len(query_tokens.union(doc_tokens))
        return intersection / union if union > 0 else 0.0

    def retrieve(self, nlq: str, db_type: str, k: int = 3) -> List[Dict]:
        """
        Retrieve K most similar examples for the given DB type.
        """
        # Filter by db_type first
        candidates = [ex for ex in self.examples if ex["db_type"] == db_type]
        
        query_tokens = self._tokenize(nlq)
        
        scored_candidates = []
        for ex in candidates:
            doc_tokens = self._tokenize(ex["nlq"])
            score = self._jaccard_similarity(query_tokens, doc_tokens)
            scored_candidates.append((score, ex))
        
        # Sort by score descending
        scored_candidates.sort(key=lambda x: x[0], reverse=True)
        
        return [item[1] for item in scored_candidates[:k]]
