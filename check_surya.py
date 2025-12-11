
try:
    import surya
    print(f"Surya file: {surya.__file__}")
except Exception as e:
    print(f"Surya import error: {e}")

try:
    from surya.recognition import RecognitionPredictor
    print("SUCCESS: from surya.recognition import RecognitionPredictor")
except ImportError:
    print("FAIL: RecognitionPredictor")

try:
    from surya.ocr import run_ocr
    print("SUCCESS: from surya.ocr import run_ocr")
except ImportError:
    print("FAIL: run_ocr")
