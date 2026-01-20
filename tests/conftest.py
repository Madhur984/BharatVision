# Test configuration and fixtures
import pytest
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def test_config():
    """Test configuration fixture"""
    return {
        "test_mode": True,
        "database_url": "sqlite:///./test.db",
        "api_base_url": "http://localhost:8000"
    }


@pytest.fixture(scope="session")
def sample_product_data():
    """Sample product data for testing"""
    return {
        "title": "Tata Salt 1kg",
        "brand": "Tata",
        "price": 25.00,
        "mrp": 30.00,
        "category": "Food & Beverages",
        "description": "Premium quality iodized salt"
    }


@pytest.fixture(scope="session")
def sample_image_path():
    """Path to sample test image"""
    return project_root / "tests" / "fixtures" / "sample_product.jpg"


@pytest.fixture(autouse=True)
def setup_test_env():
    """Setup test environment variables"""
    os.environ["TESTING"] = "true"
    os.environ["DATABASE_URL"] = "sqlite:///./test.db"
    yield
    # Cleanup
    if os.path.exists("test.db"):
        os.remove("test.db")
