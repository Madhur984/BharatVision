
import os
from openai import OpenAI
import re
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

def run_llm_extract_api(text: str) -> Dict[str, Any]:
    """Run google/-2-9b-it via HuggingFace API to extract structured fields.
    Returns a dict with extracted fields. Falls back to simple regex if API not available.
    """
    if not text:
        return {}
    
    # Simple regex fallback
    def regex_extract(text):
        out = {}
        m = re.search(r'net\s*(?:weight|qty|quantity)[:\s]*([0-9]+\s*(?:g|kg|ml|l|mg))', text, flags=re.I)
        if m:
            out['net_quantity'] = m.group(1).strip()
        m2 = re.search(r'manufacturer[:\s]*([A-Za-z0-9\s,\-\.\&]+)', text, flags=re.I)
        if m2:
            out['manufacturer'] = m2.group(1).strip()
        return out

    # Try HuggingFace API approach
    try:
        hf_token = os.environ.get("HF_TOKEN")
        if not hf_token:
            logger.debug("HF_TOKEN not set, using regex extraction")
            return regex_extract(text)
        
        client = OpenAI(
            base_url="https://router.huggingface.co/v1",
            api_key=hf_token,
        )
        
        # Truncate text to avoid token limits
        truncated = re.sub(r"\s+", " ", text).strip()[:1500]
        
        completion = client.chat.completions.create(
            model="google/-2-9b-it",
            messages=[
                {
                    "role": "user",
                    "content": f"""Extract 'net_quantity' and 'manufacturer' from this product text.
Return ONLY a JSON object with these fields. Use null if not found.

Text: {truncated}

JSON:"""
                }
            ],
            temperature=0.1,
            max_tokens=150
        )
        
        response_text = completion.choices[0].message.content.strip()
        logger.debug(f"LLM response: {response_text[:200]}")
        
        # Parse JSON response
        json_match = re.search(r'\{[^}]+\}', response_text)
        if json_match:
            result = json.loads(json_match.group(0))
            logger.info(f"LLM extracted: {result}")
            return result
        else:
            logger.warning("Could not parse LLM response as JSON")
            return regex_extract(text)
            
    except Exception as e:
        logger.debug(f"API-based NLP extraction failed: {e}")
        return regex_extract(text)
