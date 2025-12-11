
import os
import surya
import sys

print(f"Surya package path: {surya.__file__}")
base_dir = os.path.dirname(surya.__file__)

items = ['ocr', 'recognition', 'detection']

for item in items:
    path = os.path.join(base_dir, item)
    if os.path.exists(path):
        print(f"Found: {path}")
        if os.path.isdir(path):
            print(f"  Type: Directory")
            print(f"  Contents: {os.listdir(path)}")
        elif os.path.isfile(path):
            print(f"  Type: File")
    else:
        # Check for .py
        path_py = path + ".py"
        if os.path.exists(path_py):
            print(f"Found: {path_py} (Python File)")
        else:
            print(f"Not Found: {item}")

print("\nTrying imports:")
try:
    from surya.ocr import run_ocr
    print("SUCCESS: run_ocr")
except ImportError as e:
    print(f"FAIL run_ocr: {e}")

try:
    from surya.recognition import RecognitionPredictor
    print("SUCCESS: RecognitionPredictor")
except ImportError as e:
    print(f"FAIL RecognitionPredictor: {e}")
