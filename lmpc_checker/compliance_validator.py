"""
ComplianceValidator - Simplified

Rule engine for Legal Metrology packaging checks.
Validates ONLY the 6 mandatory fields as per Legal Metrology (Packaged Commodities) Rules, 2011:

1. Name and address of manufacturer/importer
2. Country of origin (if imported)
3. Common, generic name of the commodity
4. Net quantity in standard unit
5. MRP including all taxes
6. Best before/use by date (for time-sensitive commodities)
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

    def _rule_manufacturer_or_importer_missing(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        """Rule 1: Name and address of manufacturer/importer"""
        manu = self._get(data, "manufacturer_details")
        impr = self._get(data, "importer_details")
        
        if self._is_none_or_empty(manu) and self._is_none_or_empty(impr):
            return True, "Name and address of manufacturer/importer is mandatory but missing."
        
        # Check if details are sufficient (at least 10 characters)
        details = manu or impr
        if len(details) < 10:
            return True, f"Manufacturer/importer details too brief: '{details}'. Should include full name and address."
        
        return False, ""

    def _rule_country_origin_missing(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        """Rule 2: Country of origin (if imported)"""
        origin = self._get(data, "country_of_origin")
        
        # Check if product is imported
        importer = self._get(data, "importer_details")
        is_imported = not self._is_none_or_empty(importer)
        
        if is_imported and self._is_none_or_empty(origin):
            return True, "Country of origin is mandatory for imported products but is missing."
        
        # If country is provided, validate it's reasonable
        if not self._is_none_or_empty(origin) and len(origin) < 3:
            return True, f"Invalid country of origin: '{origin}'."
        
        return False, ""

    def _rule_generic_name_missing(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        """Rule 3: Common, generic name of the commodity"""
        generic_name = self._get(data, "generic_name")
        
        if self._is_none_or_empty(generic_name):
            return True, "Common/generic name of the commodity is mandatory but missing."
        
        if len(generic_name) < 2:
            return True, f"Generic name too short: '{generic_name}'."
        
        return False, ""

    def _rule_net_qty_missing(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        """Rule 4: Net quantity in standard unit"""
        qty = self._get(data, "net_quantity")
        
        if self._is_none_or_empty(qty):
            return True, "Net quantity is mandatory but missing."
        
        return False, ""

    def _rule_net_qty_unit(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        """Rule 4 (validation): Net quantity must have valid unit"""
        qty = self._get(data, "net_quantity")
        
        if self._is_none_or_empty(qty):
            return False, ""  # handled by missing rule
        
        # Valid units: g, kg, ml, l, cm, m, units, pieces
        valid_units = ["g", "kg", "ml", "l", "liter", "litre", "cm", "m", "unit", "units", "pc", "pcs", "piece", "pieces"]
        
        # Parse number + unit
        match = re.search(r"(\d+(\.\d+)?)\s*([a-zA-Z]+)", qty)
        if not match:
            return True, f"Could not parse quantity and unit from '{qty}'. Must include number and unit (e.g., '500g', '1L')."
        
        unit = match.group(3).lower()
        if unit not in valid_units:
            return True, f"Unit '{unit}' is not a valid standard unit. Use: g, kg, ml, L, cm, m, units, pieces."
        
        return False, ""

    def _rule_mrp_missing(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        """Rule 5: MRP including all taxes"""
        mrp = self._get(data, "mrp")
        
        if self._is_none_or_empty(mrp):
            return True, "MRP (Maximum Retail Price) including all taxes is mandatory but missing."
        
        return False, ""

    def _rule_mrp_format(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        """Rule 5 (validation): MRP format validation"""
        mrp = self._get(data, "mrp")
        
        if self._is_none_or_empty(mrp):
            return False, ""  # handled by missing rule
        
        # Check for standard format (₹50.00, Rs 50, or plain number)
        pattern = r"(₹|rs\.?\s*)?(\d+(\.\d{1,2})?)"
        
        if re.search(pattern, mrp, flags=re.IGNORECASE):
            return False, ""
        
        # Try to extract just numbers
        clean_mrp = re.sub(r"[^\d.]", "", mrp)
        try:
            val = float(clean_mrp)
            if val > 0:
                return False, ""
        except ValueError:
            pass
        
        return True, f"MRP format invalid: '{mrp}'. Expected format: ₹XX.XX or Rs. XX"

    def _rule_best_before_missing(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        """Rule 6: Best before/use by date (for time-sensitive commodities)"""
        best_before = self._get(data, "best_before_date")
        expiry = self._get(data, "expiry_date")
        
        # Check if this is a time-sensitive commodity
        category = (self._get(data, "category") or "").lower()
        is_time_sensitive = any(k in category for k in ["food", "beverage", "snack", "cosmetic", "medicine", "drug"])
        
        if is_time_sensitive:
            if self._is_none_or_empty(best_before) and self._is_none_or_empty(expiry):
                return True, f"Best before/use by date is mandatory for '{category}' items but is missing."
        
        return False, ""

    def _rule_date_of_manufacture_missing(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        """Rule 7: Date of manufacture or import"""
        mfg_date = self._get(data, "date_of_manufacture")
        imp_date = self._get(data, "date_of_import")
        
        if self._is_none_or_empty(mfg_date) and self._is_none_or_empty(imp_date):
            return True, "Date of manufacture or import is mandatory but missing."
        
        return False, ""

    def _rule_unit_sale_price_missing(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        """Rule 8: Unit sale price (for packaged commodities)"""
        unit_price = self._get(data, "unit_sale_price")
        
        # Check if this requires unit sale price
        category = (self._get(data, "category") or "").lower()
        requires_unit_price = any(k in category for k in ["food", "beverage", "grocery", "snack"])
        
        if requires_unit_price and self._is_none_or_empty(unit_price):
            return True, f"Unit sale price is mandatory for '{category}' items but is missing."
        
        return False, ""

    # ---------- build rule list ----------

    def _build_rules(self) -> None:
        """
        Build the 8 MANDATORY Legal Metrology rules as per Packaged Commodities Rules, 2011:
        1. Manufacturer/Importer Name and Address
        2. Country of Origin (if imported)
        3. Generic Name of Commodity
        4. Net Quantity in Standard Unit
        5. MRP including all taxes
        6. Best Before Date (for time-sensitive items)
        7. Date of Manufacture or Import
        8. Unit Sale Price (for packaged commodities)
        """
        self.rules = [
            Rule(
                "LM_RULE_01_MANUFACTURER_MISSING",
                "Name and address of manufacturer/importer is mandatory.",
                "manufacturer_details",
                "critical",
                self._rule_manufacturer_or_importer_missing,
            ),
            Rule(
                "LM_RULE_02_COUNTRY_ORIGIN",
                "Country of origin is mandatory for imported products.",
                "country_of_origin",
                "critical",
                self._rule_country_origin_missing,
            ),
            Rule(
                "LM_RULE_03_GENERIC_NAME",
                "Common, generic name of the commodity is mandatory.",
                "generic_name",
                "critical",
                self._rule_generic_name_missing,
            ),
            Rule(
                "LM_RULE_04_NET_QTY_MISSING",
                "Net quantity in standard unit is mandatory.",
                "net_quantity",
                "critical",
                self._rule_net_qty_missing,
            ),
            Rule(
                "LM_RULE_04_NET_QTY_UNIT",
                "Net quantity must be in valid standard unit (g, kg, ml, L, etc.).",
                "net_quantity",
                "high",
                self._rule_net_qty_unit,
            ),
            Rule(
                "LM_RULE_05_MRP_MISSING",
                "MRP (Maximum Retail Price) including all taxes is mandatory.",
                "mrp",
                "critical",
                self._rule_mrp_missing,
            ),
            Rule(
                "LM_RULE_05_MRP_FORMAT",
                "MRP format should be valid (₹XX.XX or Rs. XX).",
                "mrp",
                "high",
                self._rule_mrp_format,
            ),
            Rule(
                "LM_RULE_06_BEST_BEFORE",
                "Best before/use by date is mandatory for time-sensitive commodities.",
                "best_before_date",
                "critical",
                self._rule_best_before_missing,
            ),
            Rule(
                "LM_RULE_07_DATE_OF_MFG_IMPORT",
                "Date of manufacture or import is mandatory.",
                "date_of_manufacture",
                "critical",
                self._rule_date_of_manufacture_missing,
            ),
            Rule(
                "LM_RULE_08_UNIT_SALE_PRICE",
                "Unit sale price is mandatory for packaged commodities.",
                "unit_sale_price",
                "critical",
                self._rule_unit_sale_price_missing,
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


# Helper function for backward compatibility
def validate_compliance_score(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate compliance and return results"""
    validator = ComplianceValidator()
    return validator.validate(data)
