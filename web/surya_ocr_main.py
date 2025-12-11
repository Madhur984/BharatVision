import sys
import torch
from PIL import Image
from surya.ocr import run_ocr
from surya.model.detection import model as det_model
from surya.model.recognition.model import load_model as load_rec_model
from surya.model.recognition.processor import load_processor as load_rec_processor

# Load models once globally
det_processor = det_model.load_processor()
detection_model = det_model.load_model()

rec_model = load_rec_model()
rec_processor = load_rec_processor()

def surya_ocr_on_path(image_path: str) -> str:
    img = Image.open(image_path).convert("RGB")
    langs = ["en", "hi"]

    predictions = run_ocr(
        [img],
        [langs],
        detection_model,
        det_processor,
        rec_model,
        rec_processor,
    )

    if not predictions:
        return ""

    page_preds = predictions[0]  # list of dicts
    lines = [p.get("text", "") for p in page_preds if p.get("text")]
    return "\n".join(lines).strip()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("")
        sys.exit(0)

    image_path = sys.argv[1]
    output = surya_ocr_on_path(image_path)

    # print ONLY text to stdout (Streamlit will capture this)
    print(output)
