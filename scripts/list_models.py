import os
import google.generativeai as genai
from dotenv import load_dotenv

# Try to find .env file
env_path = os.path.join(os.getcwd(), 'api', '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)
    api_key = os.getenv('GOOGLE_API_KEY')
else:
    # Try alternate location
    api_key = os.getenv('GOOGLE_API_KEY')

if not api_key:
    print("API Key not found.")
    exit(1)

genai.configure(api_key=api_key)

print("Listing models...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"Name: {m.name}, Display Name: {m.display_name}")
except Exception as e:
    print(f"Error: {e}")
