"""
ml_service.nlp

Transformer pipeline wrapper + fallback.

Exports:
  - nlp_pipeline(model_name: Optional[str] = None) -> object
      Initializes and returns a transformers pipeline (or a fallback object).
  - analyze_text_with_pipeline(text: str, top_k: int = 3) -> List[Dict[str, Any]]
      Runs the pipeline (or fallback) and returns a list of results like:
        [{"label":"POSITIVE","score":0.99}, ...]
"""

from __future__ import annotations
from typing import Optional, Any, List, Dict
import os
import logging
import threading
import re

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Environment-configurable model name
DEFAULT_MODEL = os.getenv(
    "ML_NLP_MODEL", "distilbert-base-uncased-finetuned-sst-2-english"
)

# Internal cached pipeline and lock for thread-safety
_PIPELINE_LOCK = threading.Lock()
_PIPELINE: Optional[Any] = None
_PIPELINE_MODEL_NAME: Optional[str] = None


def _simple_rule_fallback(text: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """
    Lightweight fallback classifier when transformers pipeline is unavailable.
    Returns labels 'POSITIVE'/'NEGATIVE' with crude heuristics and scores.
    This is intentionally naive but useful if model loading fails.
    """
    # heuristics: positive/negative word lists and numeric score based on counts
    positive_words = ["good", "great", "excellent", "best", "recommended", "love", "awesome", "healthy"]
    negative_words = ["bad", "poor", "banned", "illegal", "danger", "harmful", "allergic", "complaint", "complain"]
    text_low = (text or "").lower()

    pos_count = sum(1 for w in positive_words if w in text_low)
    neg_count = sum(1 for w in negative_words if w in text_low)

    # also penalize presence of words like 'no label', 'missing', 'not listed'
    missing_markers = ["missing", "not listed", "no label", "no mrp", "no expiry", "no batch", "no mfg"]
    missing_count = sum(1 for w in missing_markers if w in text_low)

    # compute a crude score
    score_raw = max(0, pos_count - neg_count - missing_count)
    # normalize into 0..1
    # base = pos_count + neg_count + 1 to avoid div by zero
    denom = float(pos_count + neg_count + 1)
    positive_score = max(0.0, min(1.0, (pos_count + 0.5) / denom))
    negative_score = max(0.0, min(1.0, (neg_count + 0.5) / denom))

    # return top_k ordered predictions
    preds = [
        {"label": "POSITIVE", "score": round(positive_score, 4)},
        {"label": "NEGATIVE", "score": round(negative_score, 4)},
    ]
    # order by score desc
    preds.sort(key=lambda x: x["score"], reverse=True)
    return preds[:max(1, top_k)]


def nlp_pipeline(model_name: Optional[str] = None) -> Any:
    """
    Initialize (or return cached) transformers pipeline for text-classification.
    - model_name: if None uses DEFAULT_MODEL, or value from env ML_NLP_MODEL.
    Returns the pipeline object or a fallback callable object with same interface.
    """
    global _PIPELINE, _PIPELINE_MODEL_NAME

    with _PIPELINE_LOCK:
        if _PIPELINE is not None:
            return _PIPELINE

        # determine model name
        chosen = model_name or os.getenv("ML_NLP_MODEL") or DEFAULT_MODEL
        try:
            from transformers import pipeline as transformers_pipeline
            # create a CPU pipeline by default. If GPU available and proper torch config, transformers will use it.
            pipe = transformers_pipeline("text-classification", model=chosen)
            _PIPELINE = pipe
            _PIPELINE_MODEL_NAME = chosen
            log.info("Loaded transformers pipeline model: %s", chosen)
            return _PIPELINE
        except Exception as e:
            log.warning("Could not initialize transformers pipeline (%s): %s", chosen, e)
            log.debug("transformers import/initialization traceback:", exc_info=True)
            # fallback: set _PIPELINE to a callable wrapper that uses _simple_rule_fallback
            def _fallback_callable(text: str, top_k: int = 3):
                return _simple_rule_fallback(text, top_k=top_k)
            _PIPELINE = _fallback_callable
            _PIPELINE_MODEL_NAME = "fallback/simple-rule"
            return _PIPELINE


def analyze_text_with_pipeline(text: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """
    Run the NLP pipeline or fallback on `text`.
    Returns a list of dicts: [{"label":"POSITIVE","score":0.99}, ...]
    """
    global _PIPELINE

    if not text:
        return []

    # lazy init pipeline if needed
    if _PIPELINE is None:
        nlp_pipeline()  # initializes _PIPELINE

    # If _PIPELINE is the fallback callable, it will return list of dicts
    try:
        # transformers pipeline accepts (text, top_k=...) returning list of dicts
        res = _PIPELINE(text, top_k=top_k) if callable(_PIPELINE) else _PIPELINE(text, top_k=top_k)
        # Normalize result to list[dict] with label & score
        normalized: List[Dict[str, Any]] = []
        if isinstance(res, list):
            for item in res[:top_k]:
                # item may already be {'label':..., 'score':...}
                if isinstance(item, dict) and 'label' in item and 'score' in item:
                    normalized.append({"label": str(item["label"]), "score": float(item["score"])})
                else:
                    # sometimes transformers returns tuples or other shapes; convert
                    try:
                        # attempt to coerce common shapes
                        label = item[0] if isinstance(item, (list, tuple)) and len(item) > 0 else str(item)
                        score = float(item[1]) if isinstance(item, (list, tuple)) and len(item) > 1 else 0.0
                        normalized.append({"label": str(label), "score": float(score)})
                    except Exception:
                        normalized.append({"label": str(item), "score": 0.0})
        else:
            # if pipeline returns a single dict or single label, coerce it
            try:
                if isinstance(res, dict) and 'label' in res and 'score' in res:
                    normalized = [{"label": res['label'], "score": float(res['score'])}]
                else:
                    normalized = [{"label": str(res), "score": 0.0}]
            except Exception:
                normalized = [{"label": str(res), "score": 0.0}]
        return normalized[:top_k]
    except Exception as e:
        log.exception("analyze_text_with_pipeline failed, using fallback: %s", e)
        return _simple_rule_fallback(text, top_k=top_k)
