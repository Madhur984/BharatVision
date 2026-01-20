"""
BharatVision Python SDK

Official Python SDK for BharatVision Compliance API
"""

import requests
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import json


@dataclass
class ValidationResult:
    """Validation result data class"""
    validation_id: str
    status: str
    overall_status: str
    total_rules: int
    violations_count: int
    violations: List[Dict[str, Any]]
    timestamp: str
    product_id: Optional[str] = None


class BharatVisionClient:
    """
    BharatVision API Client
    
    Usage:
        client = BharatVisionClient(api_key="your_api_key")
        result = client.validate_product(
            platform="amazon",
            generic_name="Iodized Salt",
            net_quantity="1kg",
            mrp="₹40.00"
        )
        print(result.overall_status)
    """
    
    def __init__(self, api_key: str, base_url: str = "http://localhost:8001"):
        """
        Initialize BharatVision client
        
        Args:
            api_key: Your API key
            base_url: API base URL (default: http://localhost:8001)
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'X-API-Key': api_key,
            'Content-Type': 'application/json'
        })
    
    def validate_product(
        self,
        platform: str,
        product_id: Optional[str] = None,
        manufacturer_details: Optional[str] = None,
        country_of_origin: Optional[str] = None,
        generic_name: Optional[str] = None,
        net_quantity: Optional[str] = None,
        mrp: Optional[str] = None,
        best_before_date: Optional[str] = None,
        date_of_manufacture: Optional[str] = None,
        unit_sale_price: Optional[str] = None,
        category: Optional[str] = None,
        image_url: Optional[str] = None
    ) -> ValidationResult:
        """
        Validate a single product
        
        Args:
            platform: E-commerce platform (amazon, flipkart, shopify, etc.)
            product_id: Your product ID
            manufacturer_details: Manufacturer name and address
            country_of_origin: Country of origin
            generic_name: Generic/common name of product
            net_quantity: Net quantity with unit (e.g., 500g, 1L)
            mrp: Maximum Retail Price
            best_before_date: Best before/expiry date
            date_of_manufacture: Manufacturing date
            unit_sale_price: Unit sale price
            category: Product category
            image_url: Product image URL for OCR
        
        Returns:
            ValidationResult object
        """
        data = {
            "platform": platform,
            "product_id": product_id,
            "manufacturer_details": manufacturer_details,
            "country_of_origin": country_of_origin,
            "generic_name": generic_name,
            "net_quantity": net_quantity,
            "mrp": mrp,
            "best_before_date": best_before_date,
            "date_of_manufacture": date_of_manufacture,
            "unit_sale_price": unit_sale_price,
            "category": category,
            "image_url": image_url
        }
        
        # Remove None values
        data = {k: v for k, v in data.items() if v is not None}
        
        response = self.session.post(
            f"{self.base_url}/api/v1/validate/product",
            json=data
        )
        response.raise_for_status()
        
        result_data = response.json()
        return ValidationResult(**result_data)
    
    def validate_batch(
        self,
        platform: str,
        products: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Validate multiple products in batch
        
        Args:
            platform: E-commerce platform
            products: List of product dictionaries
        
        Returns:
            Batch validation response with batch_id
        """
        data = {
            "platform": platform,
            "products": products
        }
        
        response = self.session.post(
            f"{self.base_url}/api/v1/validate/batch",
            json=data
        )
        response.raise_for_status()
        
        return response.json()
    
    def get_validation_result(self, validation_id: str) -> Dict[str, Any]:
        """
        Get validation result by ID
        
        Args:
            validation_id: Validation or batch ID
        
        Returns:
            Validation result dictionary
        """
        response = self.session.get(
            f"{self.base_url}/api/v1/validation/{validation_id}"
        )
        response.raise_for_status()
        
        return response.json()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get API usage statistics
        
        Returns:
            Usage statistics dictionary
        """
        response = self.session.get(
            f"{self.base_url}/api/v1/stats"
        )
        response.raise_for_status()
        
        return response.json()
    
    def register_webhook(
        self,
        webhook_url: str,
        events: List[str]
    ) -> Dict[str, Any]:
        """
        Register a webhook for validation events
        
        Args:
            webhook_url: Your webhook URL
            events: List of events to subscribe to
                   (validation.completed, validation.failed, batch.completed)
        
        Returns:
            Webhook registration response
        """
        data = {
            "webhook_url": webhook_url,
            "events": events
        }
        
        response = self.session.post(
            f"{self.base_url}/api/v1/webhooks/register",
            json=data
        )
        response.raise_for_status()
        
        return response.json()


# Example usage
if __name__ == "__main__":
    # Initialize client
    client = BharatVisionClient(api_key="demo_key_12345")
    
    # Validate single product
    result = client.validate_product(
        platform="amazon",
        product_id="PROD123",
        generic_name="Iodized Salt",
        manufacturer_details="ABC Foods Pvt Ltd, Mumbai, Maharashtra",
        net_quantity="1kg",
        mrp="₹40.00",
        category="Food",
        date_of_manufacture="01/2026"
    )
    
    print(f"Validation ID: {result.validation_id}")
    print(f"Overall Status: {result.overall_status}")
    print(f"Violations: {result.violations_count}/{result.total_rules}")
    
    if result.violations:
        print("\nViolations found:")
        for violation in result.violations:
            print(f"  - {violation['description']}")
    
    # Get usage stats
    stats = client.get_stats()
    print(f"\nAPI Usage: {stats['requests_used']}/{stats['requests_limit']}")
