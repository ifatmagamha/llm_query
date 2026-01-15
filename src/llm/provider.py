import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

class LLMProvider:
    def __init__(self, model_name: str = "models/gemini-2.0-flash"):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment")
        self.model_name = model_name
        self.url = f"https://generativelanguage.googleapis.com/v1beta/{model_name}:generateContent?key={self.api_key}"

    def generate(self, prompt: str, system_instruction: str = None) -> str:
        """
        Call Gemini API.
        """
        # Gemini 1.5/2.0 supports system instructions but via different payload sometimes.
        # For simplicity in 2.0 Flash via REST:
        final_prompt = prompt
        if system_instruction:
            final_prompt = f"System Instruction: {system_instruction}\n\nUser Query: {prompt}"

        payload = {
            "contents": [{
                "parts": [{"text": final_prompt}]
            }]
        }
        
        try:
            response = requests.post(self.url, json=payload, timeout=30)
            if response.status_code == 200:
                data = response.json()
                try:
                    return data['candidates'][0]['content']['parts'][0]['text']
                except (KeyError, IndexError):
                    return "Error: Empty response from LLM"
            else:
                return f"Error: API {response.status_code} - {response.text}"
        except Exception as e:
            return f"Error: Request failed - {e}"
