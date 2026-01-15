import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
model_name = "models/gemini-2.0-flash" 
url = f"https://generativelanguage.googleapis.com/v1beta/{model_name}:generateContent?key={api_key}"

payload = {
    "contents": [{
        "parts": [{"text": "Hello! Just checking if you work."}]
    }]
}

print(f"🚀 Testing generation with {model_name}...")
try:
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print("✅ Success!")
        print("Response:", response.json()['candidates'][0]['content']['parts'][0]['text'])
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"❌ Connection Error: {e}")
