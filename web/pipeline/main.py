import subprocess
import tempfile
import os

def _ocr_with_surya(pil_image: Image.Image) -> Optional[str]:
    """
    Runs Surya OCR by calling the external script surya_ocr_main.py.
    Avoids direct heavy import loading inside Streamlit environment.
    """

    try:
        # Save crop temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            pil_image.save(tmp.name)
            temp_path = tmp.name

        # Call external script through subprocess
        proc = subprocess.run(
            ["python", "surya_ocr_main.py", temp_path],
            capture_output=True,
            text=True,
            timeout=120,
        )

        if os.path.exists(temp_path):
            os.remove(temp_path)

        text = proc.stdout.strip()
        return text if text else None

    except Exception as e:
        logger.warning(f"Surya subprocess failed: {e}")
        return None
