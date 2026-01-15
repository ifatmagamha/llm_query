import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

class LLMService:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model_name = "models/gemini-2.0-flash"
        self.url = f"https://generativelanguage.googleapis.com/v1beta/{self.model_name}:generateContent?key={self.api_key}"
        
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model_name = "models/gemini-2.0-flash"
        self.url = f"https://generativelanguage.googleapis.com/v1beta/{self.model_name}:generateContent?key={self.api_key}"
        
        self.system_prompt = """
You are an expert NoSQL Engineer. You translate Natural Language to NoSQL Queries.
Your Goal: Return a STRICT JSON object (no markdown, no extra text) with the following structure:

{
  "sql_type": "READ" | "WRITE" | "DELETE",
  "mongo": {
    "query": { ...JSON filter... },
    "explanation": "Short explainer"
  },
  "neo4j": {
    "query": "MATCH ... RETURN ...",
    "explanation": "Short explainer"
  },
  "hbase": {
    "method": "scan" | "get" | "put" | "delete",
    "table": "movies",
    "params": { 
      "filter": "SingleColumnValueFilter(...)" or null,
      "row_key": "..." or null,
      "data": { ... } or null
    },
    "explanation": "Short explainer"
  },
  "redis": {
    "command": "GET key" | "SET key val",
    "explanation": "Short explainer"
  },
  "strategy": {
    "optimization": "Index suggestions...",
    "analysis": "Why this DB is good/bad..."
  }
}

Context for 'movies' DB:
- MongoDB: {title, year, genre, director, actors, rating}
- Neo4j: (:Movie {title})<-[:DIRECTED]-(:Director), (:Movie)<-[:ACTED_IN]-(:Actor)
- HBase: RowKey=movie_id. Cols: info:title, info:rating, credits:director
- Redis: Key=movie:{id}. Value=JSON string.

User Query: "{user_query}"
"""

    def generate_query(self, user_query):
        prompt = self.system_prompt.replace("{user_query}", user_query)
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        
        import time
        retries = 3
        for i in range(retries):
            try:
                res = requests.post(self.url, json=payload)
                if res.status_code == 200:
                    raw_text = res.json()['candidates'][0]['content']['parts'][0]['text']
                    return self._parse_json_response(raw_text)
                elif res.status_code == 429:
                    if i < retries - 1:
                        time.sleep(2 ** i)
                        continue
                    return {"error": "API Quota Exceeded."}
                else:
                    return {"error": f"API Error {res.status_code}"}
            except Exception as e:
                return {"error": str(e)}

    def _parse_json_response(self, raw_text):
        try:
            # Clean Markdown wrappers if present
            clean_text = raw_text.strip()
            if clean_text.startswith("```json"):
                clean_text = clean_text.split("```json")[1]
            if clean_text.endswith("```"):
                clean_text = clean_text.rsplit("```", 1)[0]
            clean_text = clean_text.strip()
            
            return json.loads(clean_text)
        except json.JSONDecodeError as e:
            return {"error": "JSON Parse Error", "raw": raw_text}
        except Exception as e:
            return {"error": f"Unknown Error: {e}", "raw": raw_text}

llm_service = LLMService()
