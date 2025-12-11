
import requests
import os
from dotenv import load_dotenv

load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN")
if not HF_TOKEN:
    print("Error: HF_TOKEN not found provided.")
    # Try looking in .env file directly
    try:
        # Check .env first
        if os.path.exists(".env"):
            with open(".env", "r") as f:
                for line in f:
                    if line.startswith("HF_TOKEN="):
                        HF_TOKEN = line.strip().split("=", 1)[1]
                        print("Found token in .env manually")
        
        # Check .env.cloud if not found
        if not HF_TOKEN and os.path.exists(".env.cloud"):
            print("Checking .env.cloud for token...")
            with open(".env.cloud", "r") as f:
                for line in f:
                    if line.startswith("HF_TOKEN="):
                        HF_TOKEN = line.strip().split("=", 1)[1]
                        print("Found token in .env.cloud manually")
    except Exception as e:
        print(f"Error reading env files: {e}")


if not HF_TOKEN:
    print("CRITICAL: HF_TOKEN missing")
    exit(1)

API_URL = "https://router.huggingface.co/hf-inference/models/microsoft/trocr-base-printed"
headers = {"Authorization": f"Bearer {HF_TOKEN}"}

# Use the uploaded image path provided in metadata
image_path = "C:/Users/gmadh/.gemini/antigravity/brain/ba516e40-7d2b-44d9-8c26-ffab9e48d01d/uploaded_image_1765452364080.png"

if not os.path.exists(image_path):
    print(f"Image not found at {image_path}")
    # Try creating a dummy image
    from PIL import Image, ImageDraw
    img = Image.new('RGB', (100, 30), color = (73, 109, 137))
    d = ImageDraw.Draw(img)
    d.text((10,10), "Hello World", fill=(255, 255, 0))
    img.save('temp_test_image.jpg')
    image_path = 'temp_test_image.jpg'
    print("Created temp_test_image.jpg")





from huggingface_hub import InferenceClient

test_model = "google/gemma-2-9b-it" 

print(f"\nVerifying with InferenceClient and model: {test_model}")
try:
    client = InferenceClient(token=HF_TOKEN)
    # Use chat_completion for Gemma
    messages = [{"role": "user", "content": "Hello"}]
    response = client.chat_completion(messages, model=test_model)
    print(f"Gemma passed! Client resolved URL automatically.")
    print(f"Response: {response.choices[0].message.content}")
except Exception as e:
    print(f"Gemma client test error: {e}")

# Now try OCR model with Client
ocr_models = [
    "microsoft/trocr-base-printed",
    "Salesforce/blip-image-captioning-large",
    "naver-clova-ix/donut-base-finetuned-cord-v2"
]

print(f"\nTesting OCR Models with Client...")
try:
    with open(image_path, "rb") as f:
        data = f.read()
    
    client = InferenceClient(token=HF_TOKEN)
    
    for model in ocr_models:
        print(f"\n--- Testing {model} ---")
        try:
            # image_to_text is the method for OCR
            response = client.image_to_text(data, model=model)
            print(f"SUCCESS with {model}!")
            print(response)
            break # Stop if one works
        except Exception as e:
            print(f"FAILED {model}: {e}")
            
except Exception as e:
    print(f"Setup Error: {e}")





