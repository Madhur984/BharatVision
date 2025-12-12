"""
ml_service.compliance

Configurable, rule-driven compliance scoring for Legal Metrology / E-commerce.

Design:
- Each rule has: key -> { weight, message, checker, enabled }
- Checker function signature: checker(parsed: dict) -> (bool_ok, optional_info_str)
- compute_compliance_score runs all enabled rules and sums penalty weights for failed rules.
- Rules are easy to add/remove at runtime via register_rule / enable_rule / disable_rule.
- load_rule_config(path) allows loading weight/enabled overrides from JSON (checker must be registered in code).

The default rules include the six required declarations:
  1. manufacturer (name +/- address)
  2. net quantity (with units)
  3. MRP inclusive of taxes
  4. consumer care details (phone/email/website)
  5. date of manufacture / import (or best-before/expiry)
  6. country of origin
"""

from __future__ import annotations
from typing import Dict, Any, Callable, Tuple, Optional, List
import re
import json
import os

# -------------------------
# Helpers / default checkers
# -------------------------

def _extract_raw_text(parsed: Dict[str, Any]) -> str:
    return (parsed.get("raw_text") or "") + " " + " ".join(
        filter(None, [
            parsed.get("product_name") or "",
            parsed.get("tagline") or "",
            " ".join(parsed.get("claims") or []) if parsed.get("claims") else ""
        ])
    )

def _looks_like_mrp(v: Optional[str]) -> bool:
    if not v:
        return False
    # Accept numbers with optional rupee symbol/INR and commas/decimals
    return bool(re.search(r'(\u20B9|rs\.?|inr)?\s*[\d]{1,3}(?:[\d,]*\d)?(?:\.\d+)?', v or "", re.I))

def _looks_like_net_qty(v: Optional[str]) -> bool:
    if not v:
        return False
    # units commonly used in India: g, kg, mg, ml, l, litre, nos (number), pcs
    return bool(re.search(r'\b\d+(\.\d+)?\s*(g|kg|mg|ml|l|litre|litres|ltr|nos|pcs|pieces|count|units)\b', (v or "").lower()))

def _has_name_and_address(packed: Optional[dict]) -> Tuple[bool, Optional[str]]:
    if not packed:
        return False, None
    name = packed.get("name")
    addr_lines = packed.get("address_lines")
    name_ok = bool(name and isinstance(name, str) and name.strip())
    addr_ok = bool(addr_lines and isinstance(addr_lines, (list, tuple)) and any(a and a.strip() for a in addr_lines))
    return (name_ok, ("address_present" if addr_ok else None))

def _dates_present(parsed: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    # Check for mfg_date, best_before, expiry in parsed fields or raw_text
    if parsed.get("mfg_date"):
        return True, "mfg_date_field"
    if parsed.get("best_before"):
        return True, "best_before_field"
    raw = (parsed.get("raw_text") or "")
    if re.search(r'\b(manufactured on|mfg\.|mfg date|manufactured|manufacturing date|date of manufacture|imported on|imported)\b', raw, re.I):
        return True, "raw_text_hint"
    if re.search(r'\b(expiry|expiry date|best before|use by|use-by)\b', raw, re.I):
        return True, "expiry_hint"
    return False, None

def _customer_care_present(parsed: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    cc = parsed.get("customer_care") or {}
    if not isinstance(cc, dict):
        return False, None
    if any(cc.get(k) for k in ("phone", "email", "website")):
        # return which contact type(s) found
        found = ",".join([k for k in ("phone","email","website") if cc.get(k)])
        return True, found
    # also try scanning raw_text for "customer care"
    raw = _extract_raw_text(parsed).lower()
    if "customer care" in raw or "customer service" in raw:
        return True, "raw_text_hint"
    return False, None

def _country_of_origin_present(parsed: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    # common labels: "made in <country>", "product of <country>", "origin: <country>"
    raw = _extract_raw_text(parsed).lower()
    m = re.search(r'\b(made in|product of|origin:|country of origin)\s+([A-Za-z ]{2,40})', raw)
    if m:
        return True, m.group(2).strip()
    # also look for explicit field (some parsers may capture it)
    coo = parsed.get("country_of_origin") or parsed.get("country")
    if coo and isinstance(coo, str) and coo.strip():
        return True, coo.strip()
    return False, None

# -------------------------
# Rule registration & config
# -------------------------

RuleChecker = Callable[[Dict[str, Any]], Tuple[bool, Optional[str]]]

# internal registry of rule metadata and checker functions
_RULES: Dict[str, Dict[str, Any]] = {}

def register_rule(
    key: str,
    weight: int,
    checker: RuleChecker,
    message: str,
    enabled: bool = True
) -> None:
    """
    Register or update a rule.
      key: unique rule id (string)
      weight: penalty points (int; higher = more severe)
      checker: function(parsed)->(ok:bool, info:str|None)
      message: failure message describing the required field
      enabled: whether rule is active
    """
    _RULES[key] = {
        "weight": int(weight),
        "checker": checker,
        "message": message,
        "enabled": bool(enabled),
    }

def enable_rule(key: str) -> None:
    if key in _RULES:
        _RULES[key]["enabled"] = True

def disable_rule(key: str) -> None:
    if key in _RULES:
        _RULES[key]["enabled"] = False

def get_rule(key: str) -> Optional[Dict[str, Any]]:
    return _RULES.get(key)

def list_rules() -> Dict[str, Dict[str, Any]]:
    # return shallow copy without functions to avoid repr issues if needed
    return {k: {**v, "checker": v["checker"]} for k, v in _RULES.items()}

def load_rule_config(path: str) -> None:
    """
    Load a small JSON file that can override rule weights and enable/disable them.
    Format:
      {
        "rules": {
           "manufacturer": {"weight": 30, "enabled": true},
           "mrp": {"weight": 50, "enabled": true}
        }
      }
    Note: this does NOT (and cannot) set a checker function; checkers remain those registered in code.
    """
    try:
        with open(path, "r", encoding="utf8") as fh:
            data = json.load(fh)
        rules_conf = data.get("rules", {})
        for key, meta in rules_conf.items():
            if key in _RULES:
                if "weight" in meta:
                    _RULES[key]["weight"] = int(meta["weight"])
                if "enabled" in meta:
                    _RULES[key]["enabled"] = bool(meta["enabled"])
    except Exception as e:
        raise RuntimeError(f"Failed to load rule config: {e}")

# -------------------------
# Default rules (six required)
# -------------------------

# 1. Manufacturer / packer / importer name (and optionally address)
def _checker_manufacturer(parsed: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    packed = parsed.get("packed_and_marketed_by")
    ok, info = _has_name_and_address(packed)
    return ok, info

register_rule(
    key="manufacturer",
    weight=25,
    checker=_checker_manufacturer,
    message="Name (and preferably address) of manufacturer/packer/importer must be present.",
    enabled=True,
)

# 2. Net quantity (standard units)
def _checker_net_quantity(parsed: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    # check gross_content / net quantity fields
    v = parsed.get("gross_content") or parsed.get("net_quantity") or parsed.get("gross") or parsed.get("net")
    if _looks_like_net_qty(v):
        return True, v
    # also inspect raw_text (sometimes captured differently)
    raw = _extract_raw_text(parsed)
    m = re.search(r'\b\d+(\.\d+)?\s*(g|kg|ml|l|litre|ltr|mg|nos|pcs|pieces)\b', raw.lower())
    if m:
        return True, m.group(0)
    return False, None

register_rule(
    key="net_quantity",
    weight=15,
    checker=_checker_net_quantity,
    message="Net quantity (weight/volume/number) in standard units must be present.",
    enabled=True,
)

# 3. Retail sale price / MRP inclusive of taxes
def _checker_mrp(parsed: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    v = parsed.get("mrp_incl_taxes") or parsed.get("mrp") or parsed.get("MRP")
    if _looks_like_mrp(v):
        return True, v
    # try raw text
    raw = _extract_raw_text(parsed)
    m = re.search(r'((\u20B9|rs\.?|inr)\s*)?[\d]{1,3}(?:[,0-9]*\d)?(?:\.\d+)?', raw, re.I)
    if m:
        return True, m.group(0)
    return False, None

register_rule(
    key="mrp",
    weight=25,
    checker=_checker_mrp,
    message="Retail sale price / MRP (inclusive of all taxes) must be declared.",
    enabled=True,
)

# 4. Consumer care details
def _checker_consumer_care(parsed: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    ok, info = _customer_care_present(parsed)
    return ok, info

register_rule(
    key="consumer_care",
    weight=5,
    checker=_checker_consumer_care,
    message="Consumer care details (phone/email/website) should be present for consumer grievance handling.",
    enabled=True,
)

# 5. Date of manufacture / import (or best-before/expiry)
def _checker_mfg_date(parsed: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    ok, info = _dates_present(parsed)
    return ok, info

register_rule(
    key="mfg_date",
    weight=15,
    checker=_checker_mfg_date,
    message="Manufacture date / import date or best-before/expiry information must be declared.",
    enabled=True,
)

# 6. Country of origin
def _checker_country_of_origin(parsed: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    ok, info = _country_of_origin_present(parsed)
    return ok, info

register_rule(
    key="country_of_origin",
    weight=15,
    checker=_checker_country_of_origin,
    message="Country of origin (Made in / Product of) should be declared.",
    enabled=True,
)

# -------------------------
# compute score & severity
# -------------------------

SEVERITY_BUCKETS = [
    (0, "very low"),
    (10, "low"),
    (30, "medium"),
    (60, "high"),
    (85, "very high"),
]  # threshold -> label (thresholds are inclusive lower bounds)

MAX_PENALTY = 100  # clamp score to 0..100

def _severity_from_score(score: int) -> str:
    # score is penalty points (higher worse)
    for threshold, label in reversed(SEVERITY_BUCKETS):
        if score >= threshold:
            return label
    return "very low"

def compute_compliance_score(parsed: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run all enabled rules against `parsed` (dict from parse_label) and compute penalties.

    Returns:
      {
        "total_score": int,   # 0..100 penalty points (higher = worse)
        "compliance_percentage": int,  # 0..100 (100 - total_score)
        "severity": str,
        "failed_rules": { key: { weight, message, info } },
        "passed_rules": { key: { weight, info } },
        "missing_fields": [keys...],
        "reasons": [human readable reasons...],
        "detail": { rules_meta ... }
      }
    """
    if not isinstance(parsed, dict):
        raise ValueError("parsed must be a dict (output of parse_label)")

    total_penalty = 0
    failed = {}
    passed = {}
    reasons = []

    for key, meta in _RULES.items():
        if not meta.get("enabled", True):
            continue
        weight = int(meta.get("weight", 0))
        checker = meta.get("checker")
        message = meta.get("message", "")
        try:
            ok, info = checker(parsed)
        except Exception as e:
            # if checker crashes, treat as failure but include exception info
            ok = False
            info = f"checker_error: {e}"

        if not ok:
            total_penalty += weight
            failed[key] = {"weight": weight, "message": message, "info": info}
            reasons.append(f"[{key}] {message}")
        else:
            passed[key] = {"weight": weight, "info": info}

    # clamp
    if total_penalty < 0:
        total_penalty = 0
    if total_penalty > MAX_PENALTY:
        total_penalty = MAX_PENALTY

    severity = _severity_from_score(total_penalty)

    # compliance percentage: 100 - total_penalty (clamped 0..100)
    compliance_pct = 100 - int(total_penalty)
    if compliance_pct < 0:
        compliance_pct = 0
    if compliance_pct > 100:
        compliance_pct = 100

    result = {
        "total_score": int(total_penalty),
        "compliance_percentage": int(compliance_pct),
        "severity": severity,
        "failed_rules": failed,
        "passed_rules": passed,
        "missing_fields": list(failed.keys()),
        "reasons": reasons,
        "detail": {
            # include small summary of which rules exist (weight + enabled)
            "rules_meta": {k: {"weight": v["weight"], "enabled": v["enabled"]} for k, v in _RULES.items()}
        }
    }
    return result

# -------------------------
# convenience merger & processor (same shape as prior implementation)
# -------------------------

def process_product_url(
    url: str,
    page_parsed: Optional[Dict[str, Any]] = None,
    ocr_parsed: Optional[Dict[str, Any]] = None,
    image_upload_res: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Merge parsed outputs (page preferred) and compute compliance payload.
    """
    merged = {}
    keys = [
        "product_name",
        "tagline",
        "claims",
        "best_before",
        "mrp_incl_taxes",
        "batch_no",
        "gross_content",
        "mfg_date",
        "packed_and_marketed_by",
        "customer_care",
        "storage_instructions",
        "allergen_information",
        "codes_and_misc",
        "raw_text",
    ]
    for k in keys:
        p = (page_parsed or {}).get(k) if page_parsed else None
        o = (ocr_parsed or {}).get(k) if ocr_parsed else None
        merged[k] = p if p else o

    # combine raw texts
    raw_texts = []
    if page_parsed and page_parsed.get("raw_text"):
        raw_texts.append(page_parsed.get("raw_text"))
    if ocr_parsed and ocr_parsed.get("raw_text"):
        raw_texts.append(ocr_parsed.get("raw_text"))
    merged["raw_text"] = "\n\n".join([t for t in raw_texts if t])

    compliance = compute_compliance_score(merged)
    payload = {
        "url": url,
        "image_upload": image_upload_res,
        "page_parsed": page_parsed,
        "ocr_parsed": ocr_parsed,
        "merged_parsed": merged,
        "compliance": compliance
    }
    return payload

# -------------------------
# Utility: allow easy adjustment for future
# -------------------------

def set_rule_weight(key: str, weight: int) -> None:
    if key in _RULES:
        _RULES[key]["weight"] = int(weight)

def remove_rule(key: str) -> None:
    if key in _RULES:
        del _RULES[key]

# -------------------------
# If desired: load overrides from env path at import time
# -------------------------
_RULE_CONFIG_PATH = os.getenv("COMPLIANCE_RULES_PATH")
if _RULE_CONFIG_PATH:
    try:
        load_rule_config(_RULE_CONFIG_PATH)
    except Exception:
        # do not crash import if config invalid
        pass