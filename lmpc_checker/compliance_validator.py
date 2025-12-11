"""
ComplianceValidator

Rule engine for Legal Metrology packaging checks.
Given structured_data (dict of extracted fields), it returns:

{
    "overall_status": "COMPLIANT" or "VIOLATION",
    "total_rules": int,
    "violations_count": int,
    "rule_results": [
        {
            "rule_id": str,
            "description": str,
            "field": str,
            "severity": str,
            "violated": bool,
            "details": str,
        }, ...
    ],
}

You plug this into your OCR+LLM pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List, Tuple, Optional
import re


@dataclass
class Rule:
    rule_id: str
    description: str
    field: str
    severity: str  # "critical" | "high" | "medium" | "low"
    func: Callable[[Dict[str, Any]], Tuple[bool, str]]
    # func returns (violated: bool, details: str)


class ComplianceValidator:
    def __init__(self) -> None:
        self.rules: List[Rule] = []
        self._build_rules()

    # ---------- helpers to get values safely ----------

    @staticmethod
    def _get(d: Dict[str, Any], key: str) -> Optional[str]:
        v = d.get(key)
        if v is None:
            return None
        if isinstance(v, str):
            v = v.strip()
        return v

    @staticmethod
    def _is_none_or_empty(value: Any) -> bool:
        if value is None:
            return True
        if isinstance(value, str) and value.strip() == "":
            return True
        return False

    # ---------- field specific validators ----------

    def _rule_mrp_missing(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        mrp = self._get(data, "mrp")
        if self._is_none_or_empty(mrp):
            return True, "No MRP detected in structured data."
        return False, ""

    def _rule_mrp_format(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        mrp = self._get(data, "mrp")
        if self._is_none_or_empty(mrp):
            # Missing is handled by another rule
            return False, ""
        # Accept typical forms like "₹50.00", "Rs 50", "MRP ₹ 50", etc.
        pattern = r"(₹|rs\.?\s*)(\d+(\.\d{1,2})?)"
        if re.search(pattern, mrp, flags=re.IGNORECASE):
            return False, ""
        return True, f"MRP format looks invalid: '{mrp}'. Expected something like '₹50.00' or 'Rs. 50'."

    def _rule_net_qty_missing(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        qty = self._get(data, "net_quantity")
        if self._is_none_or_empty(qty):
            return True, "Net Quantity is missing."
        return False, ""

    def _rule_net_qty_unit(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        qty = self._get(data, "net_quantity")
        if self._is_none_or_empty(qty):
            return False, ""  # handled by missing rule
        valid_units = ["g", "kg", "ml", "l", "cm", "m", "unit", "units", "pc", "pcs"]
        # very simple parsing: look for number + unit
        match = re.search(r"(\d+(\.\d+)?)\s*([a-zA-Z]+)", qty)
        if not match:
            return True, f"Could not parse quantity and unit from '{qty}'."
        unit = match.group(3).lower()
        if unit not in valid_units:
            return True, f"Unit '{unit}' is not a valid Legal Metrology unit."
        return False, ""

    def _rule_country_origin_missing(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        origin = self._get(data, "country_of_origin")
        if self._is_none_or_empty(origin):
            return True, "Country of Origin is missing."
        return False, ""

    def _rule_mfg_or_import_missing(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        mfg_date = self._get(data, "date_of_manufacture")
        imp_date = self._get(data, "date_of_import")
        if self._is_none_or_empty(mfg_date) and self._is_none_or_empty(imp_date):
            return True, "Both Manufacturing Date and Import Date are missing (at least one is required)."
        return False, ""

    def _rule_future_dates(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        today = datetime.now().date()
        problems = []

        for key in ["date_of_manufacture", "date_of_import", "best_before_date", "expiry_date"]:
            raw = self._get(data, key)
            if self._is_none_or_empty(raw):
                continue
            # extremely tolerant date parsing using simple heuristics
            parsed = self._parse_date_loose(raw)
            if parsed is None:
                continue
            if parsed.date() > today:
                problems.append(f"{key} ({raw}) is in the future")

        if problems:
            return True, "; ".join(problems)
        return False, ""

    @staticmethod
    def _parse_date_loose(text: str) -> Optional[datetime]:
        text = text.strip()
        # Try common patterns; you can extend this as needed.
        formats = [
            "%d-%m-%Y",
            "%d/%m/%Y",
            "%d.%m.%Y",
            "%d %b %Y",
            "%b %Y",
            "%B %Y",
            "%m-%Y",
            "%m/%Y",
        ]
        for f in formats:
            try:
                return datetime.strptime(text, f)
            except Exception:
                continue
        return None

    def _rule_manufacturer_or_importer_missing(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        manu = self._get(data, "manufacturer_details")
        impr = self._get(data, "importer_details")
        if self._is_none_or_empty(manu) and self._is_none_or_empty(impr):
            return True, "Manufacturer / Importer details are missing (at least one required)."
        return False, ""

    def _rule_consumer_care_missing(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        care = self._get(data, "customer_care_details")
        if self._is_none_or_empty(care):
            return True, "Consumer / Customer care details are missing."
        return False, ""

    def _rule_consumer_care_format(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        care = self._get(data, "customer_care_details")
        if self._is_none_or_empty(care):
            return False, ""  # handled by missing rule
        email_re = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
        phone_re = r"\+?\d[\d\-\s]{6,}"
        if re.search(email_re, care) or re.search(phone_re, care):
            return False, ""
        return True, "Customer care details do not contain a valid email or phone number."

    def _rule_best_before_required_missing(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        category = (self._get(data, "category") or "").lower()
        best_before = self._get(data, "best_before_date")
        # simple assumption: foods and cosmetics must have best-before / expiry
        needs = any(k in category for k in ["food", "beverage", "snack", "cosmetic"])
        if needs and self._is_none_or_empty(best_before):
            return True, f"Best-before / expiry date is required for category '{category}' but missing."
        return False, ""

    def _rule_unit_sale_price_required(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        category = (self._get(data, "category") or "").lower()
        usp = self._get(data, "unit_sale_price")
        needs = any(k in category for k in ["food", "beverage", "grocery"])
        if needs and self._is_none_or_empty(usp):
            return True, f"Unit Sale Price is required for '{category}' items but missing."
        return False, ""

    # ---------- build rule list ----------

    def _build_rules(self) -> None:
        self.rules = [
            Rule(
                "LM_RULE_01_MRP_MISSING",
                "MRP is a mandatory declaration and is missing.",
                "mrp",
                "critical",
                self._rule_mrp_missing,
            ),
            Rule(
                "LM_RULE_02_MRP_FORMAT",
                "MRP format looks invalid or not in standard ₹ / Rs form.",
                "mrp",
                "high",
                self._rule_mrp_format,
            ),
            Rule(
                "LM_RULE_03_NET_QTY_MISSING",
                "Net Quantity is a mandatory declaration and is missing.",
                "net_quantity",
                "critical",
                self._rule_net_qty_missing,
            ),
            Rule(
                "LM_RULE_04_NET_QTY_UNIT_INVALID",
                "Net Quantity unit is not a valid Legal Metrology unit.",
                "net_quantity",
                "high",
                self._rule_net_qty_unit,
            ),
            Rule(
                "LM_RULE_05_COUNTRY_ORIGIN_MISSING",
                "Country of Origin is a mandatory declaration and is missing.",
                "country_of_origin",
                "critical",
                self._rule_country_origin_missing,
            ),
            Rule(
                "LM_RULE_06_MFG_OR_IMPORT_MISSING",
                "At least one of Manufacturing Date or Import Date must be declared.",
                "date_of_manufacture",
                "critical",
                self._rule_mfg_or_import_missing,
            ),
            Rule(
                "LM_RULE_07_FUTURE_DATES",
                "Manufacturing / Import / Best-Before / Expiry dates must not be in the future.",
                "date_fields",
                "high",
                self._rule_future_dates,
            ),
            Rule(
                "LM_RULE_08_MANUFACTURER_IMPORTER_MISSING",
                "Manufacturer or Importer details must be present.",
                "manufacturer_details",
                "critical",
                self._rule_manufacturer_or_importer_missing,
            ),
            Rule(
                "LM_RULE_09_CUSTOMER_CARE_MISSING",
                "Consumer care details are required (address / email / phone).",
                "customer_care_details",
                "critical",
                self._rule_consumer_care_missing,
            ),
            Rule(
                "LM_RULE_10_CUSTOMER_CARE_FORMAT",
                "Consumer care details should contain a valid email or phone number.",
                "customer_care_details",
                "medium",
                self._rule_consumer_care_format,
            ),
            Rule(
                "LM_RULE_11_BEST_BEFORE_REQUIRED",
                "Best-before / expiry date must be printed for certain categories (e.g., Food, Beverages, Cosmetics).",
                "best_before_date",
                "high",
                self._rule_best_before_required_missing,
            ),
            Rule(
                "LM_RULE_12_UNIT_SALE_PRICE_REQUIRED",
                "Unit Sale Price is required for certain grocery / food products.",
                "unit_sale_price",
                "medium",
                self._rule_unit_sale_price_required,
            ),
        ]

    # ---------- public API ----------

    def validate(self, structured_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run all rules on structured_data.
        Returns a dict with overall status and per-rule results.
        """
        rule_results: List[Dict[str, Any]] = []
        violations_count = 0

        for rule in self.rules:
            violated, details = rule.func(structured_data)
            if violated:
                violations_count += 1

            rule_results.append(
                {
                    "rule_id": rule.rule_id,
                    "description": rule.description,
                    "field": rule.field,
                    "severity": rule.severity,
                    "violated": bool(violated),
                    "details": details or "",
                }
            )

        overall_status = "VIOLATION" if violations_count > 0 else "COMPLIANT"

        return {
            "overall_status": overall_status,
            "total_rules": len(self.rules),
            "violations_count": violations_count,
            "rule_results": rule_results,
        }
