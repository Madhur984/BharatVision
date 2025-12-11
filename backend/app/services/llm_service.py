import json
import logging
import time
from typing import Dict, Any, Optional
from huggingface_hub import InferenceClient
from huggingface_hub.utils import HfHubHTTPError
from backend.app.core.config import settings

logger = logging.getLogger("bharatvision.llm")

class LLMService:
    """
    Professional LLM Service Wrapper for Hugging Face Inference API.
    Handles authentication, retries, and strict JSON parsing.
    """
    
    def __init__(self):
        if not settings.HF_TOKEN:
            logger.warning("HF_TOKEN is missing. LLM features will fail.")
        self.client = InferenceClient(token=settings.HF_TOKEN)
        self.model = settings.LLM_MODEL

    def predict(self, prompt: str, max_tokens: int = 500, temperature: float = 0.1) -> str:
        """
        Generate raw text response from LLM.
        """
        for attempt in range(3):
            try:
                response = self.client.text_generation(
                    prompt,
                    model=self.model,
                    max_new_tokens=max_tokens,
                    temperature=temperature,
                    do_sample=True,
                    return_full_text=False
                )
                return response.strip()
            except HfHubHTTPError as e:
                if e.response.status_code == 429: # Rate limit
                    wait = (attempt + 1) * 2
                    logger.warning(f"Rate limited. Waiting {wait}s...")
                    time.sleep(wait)
                    continue
                logger.error(f"LLM API Error: {e}")
                raise e
            except Exception as e:
                logger.error(f"LLM Unexpected Error: {e}")
                raise e
        return ""

    def generate_json(self, prompt: str) -> Dict[str, Any]:
        """
        Generate and parse JSON response from LLM.
        Ensures the output is valid JSON.
        """
        # Enforce JSON in prompt if not present (system prompt injection could happen here)
        secure_prompt = f"{prompt}\n\nIMPORTANT: Return ONLY valid JSON."
        
        raw_text = self.predict(secure_prompt)
        return self._extract_json(raw_text)

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """
         Robustly extract JSON from text (handles markdown code blocks).
        """
        try:
            # Try direct parse
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        # Try finding code blocks
        try:
            if "```json" in text:
                block = text.split("```json")[1].split("```")[0]
                return json.loads(block.strip())
            if "```" in text:
                block = text.split("```")[1].split("```")[0]
                return json.loads(block.strip())
        except Exception:
            pass
            
        # Try finding first { and last }
        try:
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1:
                return json.loads(text[start:end+1])
        except Exception:
            pass
            
        logger.error(f"Failed to extract JSON from LLM response: {text[:100]}...")
        return {}

llm_service = LLMService()
