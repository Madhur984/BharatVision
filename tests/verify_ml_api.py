import requests
import sys
import os

API_URL = os.environ.get("ML_API_URL", "http://localhost:8000")

def test_health():
    print(f"Testing Health Endpoint at {API_URL}/health ...")
    try:
        r = requests.get(f"{API_URL}/health")
        if r.status_code == 200:
            print("✅ Health Check Passed!")
            print(r.json())
            return True
        else:
            print(f"❌ Health Check Failed: {r.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Could not connect to {API_URL}. Is the service running?")
        print("Run 'docker-compose up' first.")
        return False

def test_extraction():
    print(f"\nTesting Extraction Endpoint at {API_URL}/extract ...")
    # specific test image needed
    image_path = "test_image.jpg" 
    
    # Create a dummy image if not exists
    if not os.path.exists(image_path):
        from PIL import Image
        img = Image.new('RGB', (100, 30), color = (73, 109, 137))
        img.save(image_path)
        print("Created dummy test_image.jpg")

    with open(image_path, "rb") as f:
        files = {"file": ("test_image.jpg", f, "image/jpeg")}
        try:
            r = requests.post(f"{API_URL}/extract", files=files)
            if r.status_code == 200:
                print("✅ Extraction Passed!")
                print("Response keys:", r.json().keys())
                return True
            else:
                print(f"❌ Extraction Failed: {r.status_code}")
                print(r.text)
                return False
        except Exception as e:
            print(f"❌ Request Error: {e}")
            return False

if __name__ == "__main__":
    print("=== ML API Verification ===")
    if test_health():
        test_extraction()
    else:
        sys.exit(1)
