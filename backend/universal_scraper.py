"""
Universal E-Commerce Scraper
Auto-detects platform and scrapes ANY e-commerce product link
"""

import re
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)

class UniversalScraper:
    """
    Universal scraper that works with ANY e-commerce platform
    Auto-detects platform from URL and applies appropriate strategy
    """
    
    # Platform detection patterns
    PLATFORM_PATTERNS = {
        'amazon': [
            r'amazon\.(in|com|co\.uk|de|fr|jp|ca|com\.au)',
            r'amzn\.',
        ],
        'flipkart': [
            r'flipkart\.com',
            r'fkrt\.it',
        ],
        'myntra': [
            r'myntra\.com',
        ],
        'meesho': [
            r'meesho\.com',
            r'meesho\.io',
        ],
        'ajio': [
            r'ajio\.com',
        ],
        'nykaa': [
            r'nykaa\.com',
        ],
        'snapdeal': [
            r'snapdeal\.com',
        ],
        'shopclues': [
            r'shopclues\.com',
        ],
        'paytmmall': [
            r'paytmmall\.com',
        ],
        'tatacliq': [
            r'tatacliq\.com',
        ],
        'jiomart': [
            r'jiomart\.com',
        ],
        'bigbasket': [
            r'bigbasket\.com',
        ],
        'grofers': [
            r'grofers\.com',
            r'blinkit\.com',
        ],
        'swiggy': [
            r'swiggy\.com',
        ],
        'zomato': [
            r'zomato\.com',
        ],
    }
    
    @classmethod
    def detect_platform(cls, url: str) -> Tuple[str, float]:
        """
        Auto-detect e-commerce platform from URL
        
        Args:
            url: Product URL
            
        Returns:
            Tuple of (platform_name, confidence_score)
        """
        url_lower = url.lower()
        
        for platform, patterns in cls.PLATFORM_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, url_lower):
                    confidence = 1.0 if pattern == patterns[0] else 0.9
                    logger.info(f"✅ Detected platform: {platform} (confidence: {confidence})")
                    return platform, confidence
        
        # Unknown platform - use generic scraper
        logger.warning(f"⚠️ Unknown platform for URL: {url[:100]}")
        return 'generic', 0.5
    
    @classmethod
    def get_platform_config(cls, platform: str) -> Dict:
        """
        Get scraping configuration for platform
        
        Args:
            platform: Platform name
            
        Returns:
            Configuration dictionary
        """
        configs = {
            'amazon': {
                'timeout': 15,
                'rate_limit': 2.0,
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'headers': {
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                },
                'selectors': {
                    'title': '#productTitle',
                    'price': '.a-price-whole',
                    'image': '#landingImage',
                }
            },
            'flipkart': {
                'timeout': 30,  # Flipkart needs longer timeout
                'rate_limit': 2.0,
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'headers': {
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Referer': 'https://www.flipkart.com/',
                    'Origin': 'https://www.flipkart.com',
                },
                'selectors': {
                    'title': '.B_NuCI',
                    'price': '._30jeq3',
                    'image': '._396cs4',
                }
            },
            'myntra': {
                'timeout': 20,
                'rate_limit': 2.0,
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'headers': {
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Referer': 'https://www.myntra.com/',
                },
                'selectors': {
                    'title': '.pdp-title',
                    'price': '.pdp-price',
                    'image': '.image-grid-image',
                }
            },
            'generic': {
                'timeout': 25,
                'rate_limit': 2.0,
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'headers': {
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                },
                'selectors': {}
            }
        }
        
        # Return platform config or generic fallback
        return configs.get(platform, configs['generic'])
    
    @classmethod
    def is_valid_product_url(cls, url: str) -> bool:
        """
        Check if URL is a valid product URL
        
        Args:
            url: URL to check
            
        Returns:
            True if valid product URL
        """
        try:
            parsed = urlparse(url)
            
            # Must have scheme and netloc
            if not parsed.scheme or not parsed.netloc:
                return False
            
            # Must be http or https
            if parsed.scheme not in ['http', 'https']:
                return False
            
            # Must have path (not just homepage)
            if not parsed.path or parsed.path == '/':
                return False
            
            # Common product URL patterns
            product_patterns = [
                r'/p/',  # Flipkart, Myntra
                r'/dp/',  # Amazon
                r'/product/',  # Generic
                r'/item/',  # Generic
                r'/pd/',  # Generic
            ]
            
            for pattern in product_patterns:
                if re.search(pattern, url, re.IGNORECASE):
                    return True
            
            # If URL has product-like path, accept it
            if len(parsed.path.split('/')) >= 3:
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"URL validation error: {e}")
            return False


# Example usage
if __name__ == "__main__":
    scraper = UniversalScraper()
    
    # Test URLs
    test_urls = [
        "https://www.amazon.in/dp/B0ABCD1234",
        "https://www.flipkart.com/product/p/xyz123",
        "https://www.myntra.com/tshirts/brand/12345",
        "https://www.meesho.com/product/abc",
        "https://www.ajio.com/item/xyz",
    ]
    
    for url in test_urls:
        platform, confidence = scraper.detect_platform(url)
        is_valid = scraper.is_valid_product_url(url)
        config = scraper.get_platform_config(platform)
        
        print(f"\nURL: {url}")
        print(f"Platform: {platform} (confidence: {confidence})")
        print(f"Valid: {is_valid}")
        print(f"Timeout: {config['timeout']}s")
