
from openai import OpenAI
import os
import time
from dotenv import load_dotenv

load_dotenv()
deepseek_api_key = os.getenv("DEEPSEEK_API_KEY") # Assuming you have this set
deepseek_base_url = "https://api.deepseek.com"
client = OpenAI(api_key=deepseek_api_key, base_url=deepseek_base_url)
response = client.chat.completions.create(
            model="deepseek-chat",
            messages="how are you",
            stream=False
        )
print(response.text)