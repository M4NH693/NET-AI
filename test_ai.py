from google import genai
import os 
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("API_KEY"))

with open("test.png", "rb") as f:
    image_bytes = f.read()

image = types.Part.from_bytes(data=image_bytes, mime_type="image/png")

res = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=["mô tả hình ảnh này", image]
)

print(res.text)