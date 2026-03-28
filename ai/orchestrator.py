import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=api_key)

try:
    # API test to verify key and model access
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="Hi"
    )
    print("✅ API key works! Model responded:", response.text)
except Exception as e:
    print("❌ API key or model issue:", e)