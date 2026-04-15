import os
import google.generativeai as genai
from dotenv import load_dotenv

print("--- FINNET MODEL SCANNER ---")

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("❌ GOOGLE_API_KEY not found in .env")
    exit()

# Configure the raw Google SDK
genai.configure(api_key=api_key)

print("✅ Connected to Google AI Studio. Scanning available models...\n")

available_models = []
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"🟢 Found Model: {m.name}")
            available_models.append(m.name)
            
    if not available_models:
        print("❌ Your API key has ZERO text-generation models unlocked.")
    else:
        print("\nTHE FIX: Copy one of the green model names above (e.g., 'models/gemini-1.5-flash')")
        print("and paste it EXACTLY like that into mcs_engine.py and root_diagnostic.py.")
        
except Exception as e:
    print(f"❌ SCAN FAILED: {e}")
