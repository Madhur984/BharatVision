import requests
from bs4 import BeautifulSoup
from pathlib import Path
import re
import sys
from io import BytesIO
import json

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except Exception:
    YOLO_AVAILABLE = False

try:
    import pytesseract
    from PIL import Image
    TESSERACT_AVAILABLE = True
except Exception:
    TESSERACT_AVAILABLE = False

try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except Exception:
    TRANSFORMERS_AVAILABLE = False


def extract_image_urls(html):
    soup = BeautifulSoup(html, 'html.parser')
    urls = []
    for img in soup.find_all('img'):
        for attr in ('data-a-image-source', 'data-old-hires', 'data-src', 'data-a-dynamic-image', 'src'):
            val = img.get(attr)
            if not val:
                continue
            if attr == 'data-a-dynamic-image':
                try:
                    parsed = json.loads(val)
                    for k in parsed.keys():
                        if k and k not in urls:
                            urls.append(k)
                except Exception:
                    if val not in urls:
                        urls.append(val)
            else:
                if val not in urls:
                    urls.append(val)
    if not urls:
        found = re.findall(r'https?://[^\s"\']+\.(?:png|jpg|jpeg)', html)
        for u in found:
            if u not in urls:
                urls.append(u)
    return urls


def download_image(url):
    try:
        r = requests.get(url, timeout=15, headers={'User-Agent':'Mozilla/5.0'})
        if r.status_code == 200:
            return r.content
    except Exception as e:
        print('Download failed', url, e)
    return None


def run_yolo_on_bytes(model, img_bytes):
    out = {'boxes': [], 'ocr_texts': []}
    try:
        with open('tmp_run_img.jpg', 'wb') as f:
            f.write(img_bytes)
        results = model('tmp_run_img.jpg')
        for res in results:
            b = getattr(res, 'boxes', None)
            if b is None:
                continue
            try:
                xy = b.xyxy.cpu().numpy()
                for row in xy:
                    x1,y1,x2,y2 = [int(v) for v in row[:4]]
                    out['boxes'].append((x1,y1,x2,y2))
            except Exception:
                continue
        # OCR crops
        if out['boxes'] and TESSERACT_AVAILABLE:
            img = Image.open(BytesIO(img_bytes)).convert('RGB')
            for (x1,y1,x2,y2) in out['boxes']:
                try:
                    crop = img.crop((x1,y1,x2,y2))
                    txt = pytesseract.image_to_string(crop)
                    if txt:
                        out['ocr_texts'].append(txt)
                except Exception:
                    continue
    except Exception as e:
        print('YOLO error', e)
    return out


def run_llm_extract(text):
    # simple regex fallback
    def regex_extract(text):
        out = {}
        m = re.search(r'net\s*(?:weight|qty|quantity)[:\s]*([0-9]+\s*(?:g|kg|ml|l|mg))', text, flags=re.I)
        if m:
            out['net_quantity'] = m.group(1).strip()
        m2 = re.search(r'manufacturer[:\s]*([A-Za-z0-9\s,\-\.\&]+)', text, flags=re.I)
        if m2:
            out['manufacturer'] = m2.group(1).strip()
        return out

    if not text:
        return {}
    if not TRANSFORMERS_AVAILABLE:
        return regex_extract(text)
    try:
        import torch
        from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
        
        print("Loading Gemma 2 (9B) - this may take a while...")
        
        model_id = "google/gemma-2-9b-it"
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
        )
        
        tokenizer = AutoTokenizer.from_pretrained(model_id)
        model = AutoModelForCausalLM.from_pretrained(
            model_id, 
            quantization_config=bnb_config, 
            device_map="auto" # requires accelerate
        )
        
        chat = [
            { "role": "user", "content": f"""
You are a data extraction assistant.
Extract 'net_quantity' and 'manufacturer' from the text below.
Return ONLY a valid JSON object. No markdown formatting.
If a value is missing, use null.

Text:
{text[:3000]}
""" }
        ]
        
        prompt = tokenizer.apply_chat_template(chat, tokenize=False, add_generation_prompt=True)
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        
        outputs = model.generate(**inputs, max_new_tokens=256, do_sample=True, temperature=0.1)
        gen = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Strip prompt if included (Gemma usually returns full text or part of it depending on config, check)
        # Actually generate usually returns full text? No, standard generate returns what was generated appended to input?
        # AutoModelForCausalLM.generate returns input + output usually.
        # But we can decode only new tokens if we slice.
        # Let's just try to find the JSON in the output from the last turn.
        
        print('Gemma output raw:', gen[-500:]) # Log end of output
        
        # Try to find JSON object
        json_match = re.search(r'\{.*\}', gen, re.DOTALL)
        if json_match:
            try:
                parsed = json.loads(json_match.group(0))
                return parsed
            except:
                pass
                
        return regex_extract(gen)
        
    except Exception as e:
        print('LLM extraction failed:', e)
        return regex_extract(text)
    return regex_extract(text)


if __name__ == '__main__':
    url = sys.argv[1] if len(sys.argv) > 1 else 'https://www.amazon.in/TATA-Product-Essential-Nutrition-Superfood/dp/B01JCFDX4S/'
    print('Fetching', url)
    r = requests.get(url, headers={'User-Agent':'Mozilla/5.0'}, timeout=20)
    html = r.text if r.status_code == 200 else ''
    imgs = extract_image_urls(html)
    print('Found', len(imgs), 'images (showing up to 5)')
    for im in imgs[:5]:
        print('-', im)

    # prepare texts
    titlesoup = BeautifulSoup(html, 'html.parser')
    page_text = titlesoup.get_text(separator='\n', strip=True)[:2000]
    collected_ocr = []

    if imgs and YOLO_AVAILABLE:
        model = YOLO('best.pt') if Path('best.pt').exists() else YOLO('yolov8n.pt')
        for im in imgs[:5]:
            b = download_image(im)
            if not b:
                continue
            res = run_yolo_on_bytes(model, b)
            if res.get('ocr_texts'):
                collected_ocr.extend(res.get('ocr_texts'))
    else:
        # fallback: run pytesseract on first image if no YOLO
        if imgs and TESSERACT_AVAILABLE:
            b = download_image(imgs[0])
            if b:
                try:
                    img = Image.open(BytesIO(b)).convert('RGB')
                    txt = pytesseract.image_to_string(img)
                    if txt:
                        collected_ocr.append(txt)
                except Exception as e:
                    print('Tesseract failed on image:', e)

    combined = '\n'.join([page_text, '\n'.join(collected_ocr)])
    print('\n--- OCR snippet (first 800 chars) ---\n')
    print('\n'.join(collected_ocr)[:800])

    print('\n--- Running LLM (Gemma 2) extraction ---\n')
    fields = run_llm_extract(combined)
    print('Extracted fields:', fields)

    # Quick compliance call could be added, but we'll stop here.
