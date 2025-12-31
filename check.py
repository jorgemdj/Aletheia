from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("API_KEY"))

print("Modelos disponíveis para você:")
for model in client.models.list():
    print(f" - {model.name}")