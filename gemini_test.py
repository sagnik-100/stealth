from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)

response = client.generate_content(
    model="gemini-1.5-flash",  # Use "gemini-1.5-flash" or "gemini-1.5-pro"
    contents="Explain how AI works in a few words",
)

print(response.text)
