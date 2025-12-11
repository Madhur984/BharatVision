from fastapi import APIRouter

router = APIRouter()

@router.get("/dashboard/stats")
def get_stats():
    return {
        "total_scans": 332,
        "compliance_rate": 92.5,
        "violations_flagged": 156,
        "devices_online": 8,
        "recent_scans": [
            {"product_id": "75521466", "brand": "Dharan", "category": "Foodgrains", "status": "Compliant"},
            {"product_id": "21562728", "brand": "Myatique", "category": "Personal Care", "status": "Violation"},
            {"product_id": "21564729", "brand": "Cataris", "category": "Food & Bev", "status": "Compliant"}
        ]
    }

@router.get("/search/products")
def search_products(q: str = ""):
    return {
        "total": 4,
        "results": [
            {"id": 1, "name": "Premium Tea Gold", "brand": "Dharan Tea Co", "category": "Beverages", "status": "Compliant", "score": 92},
            {"id": 2, "name": "Digestive Biscuits", "brand": "CatarisBrew", "category": "Snacks", "status": "Partial", "score": 75},
            {"id": 3, "name": "Honey Pure", "brand": "NatureLand", "category": "Food", "status": "Compliant", "score": 88},
            {"id": 4, "name": "Face Cream", "brand": "BeautyCare", "category": "Personal Care", "status": "Violation", "score": 42}
        ]
    }
