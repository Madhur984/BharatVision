# BharatVision Compliance API Documentation

## Overview
BharatVision provides a comprehensive Legal Metrology compliance validation API for e-commerce platforms. Validate product listings against Indian Legal Metrology (Packaged Commodities) Rules, 2011.

**Base URL**: `https://api.bharatvision.com/v1` (or `http://localhost:8001` for local development)

---

## Quick Start

### 1. Get API Key
Sign up at [bharatvision.com/signup](https://bharatvision.com/signup) to get your API key.

### 2. Make Your First Request

```bash
curl -X POST "http://localhost:8001/api/v1/validate/product" \
  -H "X-API-Key: demo_key_12345" \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "shopify",
    "generic_name": "Iodized Salt",
    "manufacturer_details": "ABC Foods Pvt Ltd, Mumbai, Maharashtra",
    "net_quantity": "1kg",
    "mrp": "₹40.00",
    "category": "Food"
  }'
```

---

## Authentication

All API requests require an API key in the header:

```
X-API-Key: your_api_key_here
```

---

## Endpoints

### 1. Validate Single Product

**POST** `/api/v1/validate/product`

Validate a single product for compliance.

**Request Body:**
```json
{
  "product_id": "PROD123",
  "platform": "amazon",
  "manufacturer_details": "ABC Foods Pvt Ltd, 123 Main St, Mumbai, Maharashtra 400001",
  "country_of_origin": "India",
  "generic_name": "Iodized Salt",
  "net_quantity": "1kg",
  "mrp": "₹40.00",
  "best_before_date": "12 months from manufacture",
  "date_of_manufacture": "01/2026",
  "unit_sale_price": "₹40/kg",
  "category": "Food",
  "image_url": "https://example.com/product.jpg"
}
```

**Response:**
```json
{
  "validation_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "overall_status": "COMPLIANT",
  "total_rules": 10,
  "violations_count": 0,
  "violations": [],
  "timestamp": "2026-01-20T22:30:00Z",
  "product_id": "PROD123"
}
```

---

### 2. Batch Validation

**POST** `/api/v1/validate/batch`

Validate multiple products at once.

**Request Body:**
```json
{
  "platform": "flipkart",
  "products": [
    {
      "product_id": "PROD123",
      "generic_name": "Salt",
      "net_quantity": "1kg",
      "mrp": "₹40"
    },
    {
      "product_id": "PROD124",
      "generic_name": "Sugar",
      "net_quantity": "500g",
      "mrp": "₹30"
    }
  ]
}
```

**Response:**
```json
{
  "batch_id": "batch_550e8400",
  "status": "processing",
  "total_products": 2,
  "message": "Batch validation started. Check status at /api/v1/validation/batch_550e8400"
}
```

---

### 3. Get Validation Result

**GET** `/api/v1/validation/{validation_id}`

Retrieve validation results by ID.

**Response:**
```json
{
  "validation_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "overall_status": "VIOLATION",
  "total_rules": 10,
  "violations_count": 2,
  "violations": [
    {
      "rule_id": "LM_RULE_01_MANUFACTURER_MISSING",
      "description": "Name and address of manufacturer/importer is mandatory.",
      "field": "manufacturer_details",
      "severity": "critical",
      "violated": true,
      "details": "Name and address of manufacturer/importer is mandatory but missing."
    }
  ],
  "timestamp": "2026-01-20T22:30:00Z"
}
```

---

### 4. API Usage Statistics

**GET** `/api/v1/stats`

Get your API usage statistics.

**Response:**
```json
{
  "account": "Demo Account",
  "tier": "free",
  "requests_used": 45,
  "requests_limit": 100,
  "requests_remaining": 55
}
```

---

### 5. Register Webhook

**POST** `/api/v1/webhooks/register`

Register a webhook to receive validation events.

**Request Body:**
```json
{
  "webhook_url": "https://yoursite.com/webhook",
  "events": ["validation.completed", "validation.failed"]
}
```

**Response:**
```json
{
  "webhook_id": "webhook_123",
  "url": "https://yoursite.com/webhook",
  "events": ["validation.completed", "validation.failed"],
  "status": "active"
}
```

---

## Supported Platforms

| Platform | Code | Status |
|----------|------|--------|
| Amazon India | `amazon` | ✅ Supported |
| Flipkart | `flipkart` | ✅ Supported |
| Meesho | `meesho` | ✅ Supported |
| JioMart | `jiomart` | ✅ Supported |
| Myntra | `myntra` | ✅ Supported |
| Shopify | `shopify` | ✅ Supported |
| WooCommerce | `woocommerce` | ✅ Supported |
| Magento | `magento` | ✅ Supported |
| BigCommerce | `bigcommerce` | ✅ Supported |
| Snapdeal | `snapdeal` | ✅ Supported |
| Paytm Mall | `paytm` | ✅ Supported |
| IndiaMART | `indiamart` | ✅ Supported |
| Udaan | `udaan` | ✅ Supported |

---

## Validation Rules

The API validates against 8 mandatory Legal Metrology fields:

1. **Manufacturer/Importer Details** - Name and address
2. **Country of Origin** - Required for imported products
3. **Generic Name** - Common name of commodity
4. **Net Quantity** - With standard unit (g, kg, ml, L, etc.)
5. **MRP** - Maximum Retail Price including all taxes
6. **Best Before Date** - For time-sensitive items
7. **Date of Manufacture/Import** - At least one required
8. **Unit Sale Price** - For food/beverage/grocery items

---

## Error Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Invalid API key |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error |

---

## Rate Limits

| Tier | Requests/Month | Rate |
|------|----------------|------|
| Free | 100 | 10/minute |
| Pro | 5,000 | 100/minute |
| Enterprise | Unlimited | Custom |

---

## Code Examples

### Python

```python
import requests

API_KEY = "your_api_key"
API_URL = "http://localhost:8001/api/v1/validate/product"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

data = {
    "platform": "amazon",
    "generic_name": "Iodized Salt",
    "manufacturer_details": "ABC Foods Pvt Ltd, Mumbai",
    "net_quantity": "1kg",
    "mrp": "₹40.00",
    "category": "Food"
}

response = requests.post(API_URL, json=data, headers=headers)
result = response.json()

print(f"Status: {result['overall_status']}")
print(f"Violations: {result['violations_count']}")
```

### JavaScript/Node.js

```javascript
const axios = require('axios');

const API_KEY = 'your_api_key';
const API_URL = 'http://localhost:8001/api/v1/validate/product';

const data = {
  platform: 'shopify',
  generic_name: 'Iodized Salt',
  manufacturer_details: 'ABC Foods Pvt Ltd, Mumbai',
  net_quantity: '1kg',
  mrp: '₹40.00',
  category: 'Food'
};

axios.post(API_URL, data, {
  headers: {
    'X-API-Key': API_KEY,
    'Content-Type': 'application/json'
  }
})
.then(response => {
  console.log('Status:', response.data.overall_status);
  console.log('Violations:', response.data.violations_count);
})
.catch(error => {
  console.error('Error:', error.response.data);
});
```

### PHP

```php
<?php
$api_key = 'your_api_key';
$api_url = 'http://localhost:8001/api/v1/validate/product';

$data = array(
    'platform' => 'woocommerce',
    'generic_name' => 'Iodized Salt',
    'manufacturer_details' => 'ABC Foods Pvt Ltd, Mumbai',
    'net_quantity' => '1kg',
    'mrp' => '₹40.00',
    'category' => 'Food'
);

$options = array(
    'http' => array(
        'header'  => "X-API-Key: $api_key\r\nContent-Type: application/json\r\n",
        'method'  => 'POST',
        'content' => json_encode($data)
    )
);

$context  = stream_context_create($options);
$result = file_get_contents($api_url, false, $context);
$response = json_decode($result);

echo "Status: " . $response->overall_status . "\n";
echo "Violations: " . $response->violations_count . "\n";
?>
```

---

## Webhook Events

When you register a webhook, you'll receive POST requests for the following events:

### validation.completed
```json
{
  "event": "validation.completed",
  "validation_id": "550e8400-e29b-41d4-a716-446655440000",
  "product_id": "PROD123",
  "overall_status": "COMPLIANT",
  "timestamp": "2026-01-20T22:30:00Z"
}
```

### validation.failed
```json
{
  "event": "validation.failed",
  "validation_id": "550e8400-e29b-41d4-a716-446655440000",
  "product_id": "PROD123",
  "error": "Processing error",
  "timestamp": "2026-01-20T22:30:00Z"
}
```

---

## Support

- **Documentation**: https://docs.bharatvision.com
- **Email**: support@bharatvision.com
- **GitHub**: https://github.com/Madhur984/BharatVision
- **Discord**: https://discord.gg/bharatvision

---

*Last Updated: January 20, 2026*
