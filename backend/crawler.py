"""
Web Crawling APIs for Major E-commerce Platforms
Automated data acquisition for Legal Metrology compliance checking
Enhanced with full page extraction, OCR on images, and proper compliance validation
"""

import requests
import subprocess
import tempfile
import json
import time
import logging
import numpy as np
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from urllib.parse import urljoin, urlparse, parse_qs
from datetime import datetime
import re
from bs4 import BeautifulSoup
import pandas as pd
from pathlib import Path
from io import BytesIO
import hashlib
import traceback
# Transformers removed - using compliance validator only
TRANSFORMERS_AVAILABLE = False

# Selenium removed: force requests + BeautifulSoup scraping only
SELENIUM_AVAILABLE = False
WEBDRIVER_MANAGER_AVAILABLE = False
logger_temp = logging.getLogger(__name__)
logger_temp.info("Selenium disabled: using requests + BeautifulSoup for scraping")

# Try PIL for image processing
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# Try pytesseract for OCR
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

logger = logging.getLogger(__name__)

# Import OCR Integrator
try:
    from backend.ocr_integration import get_ocr_integrator
    OCR_INTEGRATION_AVAILABLE = True
except ImportError:
    OCR_INTEGRATION_AVAILABLE = False
    get_ocr_integrator = None

# Import OCR Integrator
try:
    from backend.ocr_integration import get_ocr_integrator
    OCR_INTEGRATION_AVAILABLE = True
except ImportError:
    OCR_INTEGRATION_AVAILABLE = False
    get_ocr_integrator = None

# Import compliance validator
COMPLIANCE_AVAILABLE = False
try:
    import sys
    import pathlib
    project_root = pathlib.Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from lmpc_checker.compliance_validator import ComplianceValidator
    from lmpc_checker.mandatory_validator import get_validator as get_mandatory_validator
    COMPLIANCE_AVAILABLE = True
    logger.info("ComplianceValidator loaded successfully")
except ImportError as e:
    logger.warning(f"ComplianceValidator not available: {e}")
    ComplianceValidator = None
    get_mandatory_validator = None

# Import data refiner for field extraction
try:
    from data_refiner.refiner import DataRefiner
    REFINER_AVAILABLE = True
except ImportError:
    REFINER_AVAILABLE = False
    DataRefiner = None

# Import Database Manager
try:
    from backend.db import DatabaseManager
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False
    DatabaseManager = None

# Import API-based LLM extraction
try:
    from backend.llm_api import run_llm_extract_api
    LLM_API_AVAILABLE = True
except ImportError:
    LLM_API_AVAILABLE = False
    run_llm_extract_api = None

@dataclass
class ProductData:
    """Structured product data from e-commerce platforms"""
    
    # Basic product info
    title: str
    brand: Optional[str] = None
    price: Optional[float] = None
    mrp: Optional[float] = None
    description: Optional[str] = None
    
    # Legal Metrology fields
    net_quantity: Optional[str] = None
    manufacturer: Optional[str] = None
    manufacturer_details: Optional[str] = None
    importer_details: Optional[str] = None
    country_of_origin: Optional[str] = None
    mfg_date: Optional[str] = None
    date_of_manufacture: Optional[str] = None
    expiry_date: Optional[str] = None
    best_before_date: Optional[str] = None
    customer_care_details: Optional[str] = None
    ingredients: Optional[str] = None
    
    # Extended Details (Refined Crawler)
    features: List[str] = None          # Bullet points
    specs: Dict[str, str] = None        # Technical specifications table
    legal_disclaimer: Optional[str] = None
    aplus_content: Optional[str] = None # Rich HTML content
    
    # E-commerce metadata
    platform: Optional[str] = None
    seller: Optional[str] = None
    product_url: Optional[str] = None
    image_urls: List[str] = None
    local_image_paths: List[str] = None # NEW: Paths to downloaded images
    category: Optional[str] = None
    rating: Optional[float] = None
    reviews_count: Optional[int] = None
    
    # OCR extracted text
    ocr_text: Optional[str] = None
    full_page_text: Optional[str] = None
    
    # Compliance metadata
    extracted_at: Optional[str] = None
    compliance_score: Optional[float] = None
    compliance_status: Optional[str] = None  # COMPLIANT, NON_COMPLIANT, PARTIAL
    issues_found: List[str] = None
    validation_result: Optional[Dict[str, Any]] = None
    compliance_details: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.image_urls is None:
            self.image_urls = []
        if self.issues_found is None:
            self.issues_found = []
        if self.features is None:
            self.features = []
        if self.specs is None:
            self.specs = {}


def run_tesseract_on_image(image_url: str) -> str:
    """Download image and run Tesseract OCR on it"""
    if not PIL_AVAILABLE or not TESSERACT_AVAILABLE:
        return ""
    
    try:
        # Download image
        response = requests.get(image_url, timeout=15, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'
        })
        if response.status_code != 200:
            return ""
        
        # Open with PIL
        img = Image.open(BytesIO(response.content))
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Resize for better OCR if too small
        w, h = img.size
        if max(w, h) < 800:
            scale = 800 / max(w, h)
            img = img.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)
        
        # Run Tesseract with optimized config
        custom_config = r'--oem 3 --psm 6 -c preserve_interword_spaces=1'
        text = pytesseract.image_to_string(img, config=custom_config)
        
        return text.strip() if text else ""
    except Exception as e:
        logger.debug(f"OCR failed for {image_url}: {e}")
        return ""

class EcommerceCrawler:
    """Comprehensive web crawler for major Indian e-commerce platforms"""
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        platform: str = "amazon",
        product_extractor: Any = None,
        image_extractor: Any = None,
        logger=None,
        use_surya: bool = False,
        yolo_model_path: Optional[str] = None,
    ):
        """Initialize the e-commerce crawler with platform configurations"""
        # Core attributes
        self.base_url = base_url or "https://www.amazon.in"
        self.platform = platform or "amazon"
        self.product_extractor = product_extractor or (lambda *args, **kwargs: None)
        self.image_extractor = image_extractor
        # Defensive logger assignment
        if logger is not None and hasattr(logger, "warning"):
            self.logger = logger
        else:
            self.logger = logging.getLogger(__name__)

        # Compliance validator
        self.compliance_validator = None
        self.compliance_rules: List[Any] = []
        if COMPLIANCE_AVAILABLE and ComplianceValidator:
            try:
                self.compliance_validator = ComplianceValidator()
                if hasattr(self.compliance_validator, "rules"):
                    self.compliance_rules = self.compliance_validator.rules
                safe_logger = getattr(self, 'logger', logging.getLogger(__name__))
                safe_logger.info("ComplianceValidator initialized")
            except Exception as e:
                safe_logger = getattr(self, 'logger', logging.getLogger(__name__))
                safe_logger.warning(f"ComplianceValidator init failed: {e}")

        # Data refiner
        self.data_refiner = None
        if REFINER_AVAILABLE and DataRefiner:
            try:
                self.data_refiner = DataRefiner()
                safe_logger = getattr(self, 'logger', logging.getLogger(__name__))
                safe_logger.info("DataRefiner initialized")
            except Exception as e:
                safe_logger = getattr(self, 'logger', logging.getLogger(__name__))
                safe_logger.warning(f"DataRefiner init failed: {e}")
        
        # Platform configurations
        self.platforms = {
            'amazon': {
                'name': 'Amazon India',
                'base_url': 'https://www.amazon.in',
                'search_url': 'https://www.amazon.in/s?k={query}&ref=nb_sb_noss',
                'rate_limit': 2.0,  # seconds between requests
                'headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Cache-Control': 'max-age=0'
                }
            },
            'flipkart': {
                'name': 'Flipkart',
                'base_url': 'https://www.flipkart.com',
                'search_url': 'https://www.flipkart.com/search?q={query}',
                'rate_limit': 3.0,  # Increased from 2.0 to 3.0 seconds
                'headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-User': '?1',
                    'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                    'Sec-Ch-Ua-Mobile': '?0',
                    'Sec-Ch-Ua-Platform': '"Windows"',
                    'Cache-Control': 'max-age=0',
                    'DNT': '1'
                }
            },
            'myntra': {
                'name': 'Myntra',
                'base_url': 'https://www.myntra.com',
                'search_url': 'https://www.myntra.com/search?q={query}',
                'rate_limit': 2.0,
                'headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive',
                    'Referer': 'https://www.myntra.com/'
                }
            },
            'meesho': {
                'name': 'Meesho',
                'base_url': 'https://www.meesho.com',
                'search_url': 'https://www.meesho.com/search?q={query}',
                'rate_limit': 2.0,
                'timeout': 15,
                'headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9'
                }
            },
            'ajio': {
                'name': 'Ajio',
                'base_url': 'https://www.ajio.com',
                'search_url': 'https://www.ajio.com/search/?text={query}',
                'rate_limit': 2.0,
                'timeout': 15,
                'headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9'
                }
            },
            'nykaa': {
                'name': 'Nykaa',
                'base_url': 'https://www.nykaa.com',
                'search_url': 'https://www.nykaa.com/search/result/?q={query}',
                'rate_limit': 2.0,
                'timeout': 15,
                'headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9'
                }
            },
            'snapdeal': {
                'name': 'Snapdeal',
                'base_url': 'https://www.snapdeal.com',
                'search_url': 'https://www.snapdeal.com/search?keyword={query}',
                'rate_limit': 2.0,
                'timeout': 15,
                'headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9'
                }
            },
            'shopclues': {
                'name': 'ShopClues',
                'base_url': 'https://www.shopclues.com',
                'search_url': 'https://www.shopclues.com/search?q={query}',
                'rate_limit': 2.0,
                'timeout': 15,
                'headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9'
                }
            },
            'paytmmall': {
                'name': 'Paytm Mall',
                'base_url': 'https://www.paytmmall.com',
                'search_url': 'https://www.paytmmall.com/shop/search?q={query}',
                'rate_limit': 2.0,
                'timeout': 15,
                'headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9'
                }
            },
            'tatacliq': {
                'name': 'Tata CLiQ',
                'base_url': 'https://www.tatacliq.com',
                'search_url': 'https://www.tatacliq.com/search/?searchText={query}',
                'rate_limit': 2.0,
                'timeout': 15,
                'headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9'
                }
            },
            'jiomart': {
                'name': 'JioMart',
                'base_url': 'https://www.jiomart.com',
                'search_url': 'https://www.jiomart.com/search/{query}',
                'rate_limit': 2.0,
                'timeout': 15,
                'headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9'
                }
            },
            'generic': {
                'name': 'Generic',
                'base_url': '',
                'search_url': '',
                'rate_limit': 2.0,
                'timeout': 15,
                'headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9'
                }
            }
        }

        # If base_url not provided, infer from platform
        if self.base_url is None and self.platform in self.platforms:
            self.base_url = self.platforms[self.platform]['base_url']

        # HTTP session + rate limiting
        self.session = requests.Session()
        self.last_request_time: Dict[str, float] = {}

        # Lazy model holders and OCR flags
        self._yolo_model = None
        self._llm_model = None
        self.use_surya = False
        # default to repository best.pt if exists
        try:
            self.yolo_model_path = str(Path(__file__).resolve().parent.parent / 'best.pt')
        except Exception:
            self.yolo_model_path = 'best.pt'

        # OCR / detection defaults
        self.use_surya = use_surya
        self.yolo_model_path = yolo_model_path or str(Path(__file__).resolve().parent.parent / 'best.pt')
        self._yolo_model = None
        self._llm_model = None

        # Chrome driver options for Selenium (for JavaScript-heavy sites)
        if SELENIUM_AVAILABLE:
            self.chrome_options = Options()
            self.chrome_options.add_argument('--headless')
            self.chrome_options.add_argument('--no-sandbox')
            self.chrome_options.add_argument('--disable-dev-shm-usage')
            self.chrome_options.add_argument('--disable-gpu')
            self.chrome_options.add_argument('--window-size=1920,1080')
        else:
            self.chrome_options = None
        
        safe_logger = getattr(self, 'logger', logging.getLogger(__name__))
        safe_logger.info("EcommerceCrawler initialized with support for Amazon, Flipkart, and Myntra")
        safe_logger.info(f"Compliance checking: {'Enabled' if self.compliance_rules else 'Disabled'}")
        safe_logger.info(f"Compliance checking: {'Enabled' if self.compliance_rules else 'Disabled'}")
        safe_logger.info(f"Image extraction: {'Enabled' if self.image_extractor else 'Disabled'}")
        
        # Initialize OCR Integrator
        self.ocr_integrator = None
        if OCR_INTEGRATION_AVAILABLE and get_ocr_integrator:
            try:
                self.ocr_integrator = get_ocr_integrator()
                safe_logger.info("OCR Integrator initialized via factory")
            except Exception as e:
                safe_logger.warning(f"Failed to init OCR Integrator: {e}")
    
    def _respect_rate_limit(self, platform: str):
        """Respect rate limiting for the platform"""
        if platform in self.last_request_time:
            elapsed = time.time() - self.last_request_time[platform]
            rate_limit = self.platforms[platform]['rate_limit']
            if elapsed < rate_limit:
                sleep_time = rate_limit - elapsed
                logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
        
        self.last_request_time[platform] = time.time()
    
    def _make_request(self, url: str, platform: str, use_selenium: bool = False) -> Optional[str]:
        """Make HTTP request with proper headers and rate limiting.

        Selenium is intentionally disabled; this method uses `requests` + BeautifulSoup only.
        The `use_selenium` flag is accepted for compatibility but ignored.
        """
        try:
            self._respect_rate_limit(platform)

            headers = self.platforms[platform]['headers'].copy()
            
            # Enhanced headers for Flipkart with session cookies
            if platform == 'flipkart':
                headers.update({
                    'Referer': 'https://www.flipkart.com/',
                    'Origin': 'https://www.flipkart.com',
                })
                # Add session cookies if available
                if not hasattr(self, '_flipkart_cookies'):
                    # Initialize session by visiting homepage first
                    try:
                        homepage_response = self.session.get(
                            'https://www.flipkart.com',
                            headers=headers,
                            timeout=10
                        )
                        self._flipkart_cookies = self.session.cookies
                        logger.info("✅ Flipkart session initialized")
                    except:
                        self._flipkart_cookies = None
            else:
                # Add anti-bot headers for other platforms
                headers.update({
                    'Referer': self.platforms[platform]['base_url'],
                    'DNT': '1',
                    'X-Requested-With': 'XMLHttpRequest',
                })

            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # Much longer timeout for Flipkart (45s vs 15s)
                    timeout = 45 if platform == 'flipkart' else 15
                    response = self.session.get(url, headers=headers, timeout=timeout, allow_redirects=True)
                    if response.status_code == 200:
                        return response.text

                    # If blocked (403), try rotating a simple header set and retry
                    if response.status_code == 403:
                        if attempt < max_retries - 1:
                            wait_time = (attempt + 1) * 2
                            logger.warning(f"Got 403 Forbidden on attempt {attempt + 1}, retrying in {wait_time}s with modified headers...")
                            # modify headers slightly for next attempt
                            headers['User-Agent'] = headers.get('User-Agent', '') + ' Mozilla/5.0'
                            time.sleep(wait_time)
                            continue
                        else:
                            logger.warning(f"Got 403 Forbidden after {max_retries} attempts for {url}")
                            return None

                    if response.status_code in [429, 503, 502, 504, 500]:
                        if attempt < max_retries - 1:
                            wait_time = (attempt + 1) * 2
                            logger.warning(f"Status {response.status_code}, retrying in {wait_time}s...")
                            time.sleep(wait_time)
                            continue

                    try:
                        response.raise_for_status()
                    except requests.exceptions.HTTPError as he:
                        # If we get 403 Forbidden, try Playwright fallback
                        if response.status_code == 403:
                            logger.warning(f"HTTP 403 Forbidden for {url}, trying Playwright fallback...")
                            return self._make_request_playwright(url)
                        logger.warning(f"HTTP error {response.status_code} for {url}: {he}")
                        return None

                except requests.exceptions.Timeout:
                    if attempt < max_retries - 1:
                        wait_time = 2 ** (attempt + 1)  # Exponential: 2s, 4s, 8s
                        logger.warning(f"Timeout on attempt {attempt + 1}/{max_retries}, retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"Timeout after {max_retries} attempts for {url}, trying Playwright fallback...")
                        return self._make_request_playwright(url)
                except requests.exceptions.ConnectionError:
                    if attempt < max_retries - 1:
                        logger.warning(f"Connection error on attempt {attempt + 1}/{max_retries}, retrying...")
                        time.sleep(2)
                        continue
                    else:
                        logger.error(f"Connection error after {max_retries} attempts for {url}")
                        return None

            return None

        except requests.exceptions.RequestException as e:
            logger.warning(f"Request failed for {url}: {type(e).__name__}: {e}")
            return None
        except Exception as e:
            logger.error(f"Request error for {url}: {e}")
            return None
    
    def _make_request_playwright(self, url: str) -> Optional[str]:
        """
        Fallback scraping using Playwright when regular requests fail.
        Uses a real browser to bypass anti-bot protection.
        Works for Meesho, Flipkart, and any JavaScript-heavy site.
        """
        try:
            # Check if playwright is available
            try:
                from playwright.sync_api import sync_playwright
            except ImportError:
                logger.warning("Playwright not installed. Install with: pip install playwright && playwright install chromium")
                return None
            
            logger.info(f"🎭 Using Playwright fallback for {url}")
            
            with sync_playwright() as p:
                # Launch browser
                browser = p.chromium.launch(
                    headless=True,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-dev-shm-usage',
                        '--no-sandbox',
                        '--disable-setuid-sandbox'
                    ]
                )
                
                # Create context with realistic settings
                context = browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    locale='en-IN',
                    timezone_id='Asia/Kolkata'
                )
                
                page = context.new_page()
                
                try:
                    # Navigate with timeout
                    page.goto(url, wait_until='networkidle', timeout=30000)
                    
                    # Wait for content to load
                    page.wait_for_timeout(2000)
                    
                    # Get HTML content
                    html = page.content()
                    
                    logger.info(f"✅ Playwright successfully fetched {len(html)} bytes")
                    return html
                    
                finally:
                    browser.close()
                    
        except Exception as e:
            logger.error(f"Playwright fallback failed for {url}: {e}")
            return None
    
    def extract_product_from_url_simple(self, url: str) -> Optional[ProductData]:
        """
        UNIVERSAL EXTRACTION METHOD - Works for ANY e-commerce website!
        Uses generic patterns instead of platform-specific logic.
        This is simpler, more maintainable, and more reliable.
        """
        logger.info(f"🌐 Universal extraction from: {url}")
        
        # Fetch HTML (with auto Playwright fallback)
        html = self._make_request(url, 'generic', use_selenium=False)
        if not html:
            logger.info("HTTP failed, trying Playwright...")
            html = self._make_request_playwright(url)
        
        if not html:
            logger.error("Failed to fetch page")
            return None
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Initialize product
        product = ProductData()
        product.product_url = url
        product.extracted_at = time.strftime("%Y-%m-%d %H:%M:%S")
        
        # Extract title (try multiple selectors)
        title = None
        for selector in ['h1', 'title', '[class*="title"]', '[class*="product-name"]']:
            try:
                elem = soup.select_one(selector)
                if elem:
                    title = elem.get_text(strip=True)
                    if len(title) > 5:
                        break
            except:
                continue
        product.title = title or "Unknown Product"
        
        # Extract all visible text
        for tag in soup(['script', 'style', 'noscript', 'header', 'footer', 'nav']):
            tag.decompose()
        page_text = soup.get_text(separator="\n", strip=True)
        product.full_page_text = page_text
        
        # Extract images
        images = set()
        for img in soup.find_all("img"):
            src = img.get("src") or img.get("data-src") or img.get("data-lazy-src")
            if src:
                if not src.startswith("http"):
                    src = urljoin(url, src)
                if any(ext in src.lower() for ext in ["jpg", "jpeg", "png", "webp"]):
                    images.add(src)
        product.image_urls = list(images)[:15]
        logger.info(f"Found {len(product.image_urls)} images")
        
        # Run OCR on images
        if product.image_urls and TESSERACT_AVAILABLE and PIL_AVAILABLE:
            ocr_texts = []
            for img_url in product.image_urls[:5]:  # Limit to 5 images
                try:
                    r = self.session.get(img_url, timeout=10)
                    if r.status_code == 200:
                        img = Image.open(BytesIO(r.content)).convert("RGB")
                        text = pytesseract.image_to_string(img)
                        if len(text.strip()) > 10:
                            ocr_texts.append(text)
                except:
                    continue
            product.ocr_text = "\n---\n".join(ocr_texts)
        
        # Combine all text
        combined_text = "\n".join([
            product.title or "",
            page_text or "",
            product.ocr_text or ""
        ])
        
        # Extract fields using regex patterns
        patterns = {
            "price": r"₹\s*([\d,]+(?:\.\d{2})?)",
            "mrp": r"(?:MRP|M\.R\.P\.|Maximum Retail Price)[^\d₹]*₹?\s*([\d,]+)",
            "net_quantity": r"(?:Net|Net Qty|Net Weight|Quantity)[^\d]*(\d+\s*(?:g|kg|ml|l|gm|gms|ltr))",
            "manufacturer": r"(?:Manufactured by|Mfg by|Manufacturer|Marketed by)[^\n:]*[:\-]?\s*([^\n]{10,100})",
            "importer": r"(?:Imported by|Importer)[^\n:]*[:\-]?\s*([^\n]{10,100})",
            "country_of_origin": r"(?:Country of Origin|Made in|Origin)\s*[:\-]?\s*(\w+)",
            "customer_care": r"(?:Customer Care|Helpline|Contact|Customer Support)[^\n]{0,50}",
            "mfg_date": r"(?:Mfg|Manufactured|Manufacturing Date)[^\n]{0,30}",
            "expiry_date": r"(?:Best Before|Expiry|Exp|Use By)[^\n]{0,30}",
        }
        
        extracted_fields = {}
        for key, pattern in patterns.items():
            m = re.search(pattern, combined_text, re.IGNORECASE)
            if m:
                value = m.group(1).strip() if m.lastindex else m.group(0).strip()
                extracted_fields[key] = value[:200]
                setattr(product, key, value[:200])
        
        logger.info(f"Extracted fields: {list(extracted_fields.keys())}")
        
        # Compliance validation
        if self.compliance_validator:
            try:
                result = self.compliance_validator.validate(extracted_fields)
                product.compliance_status = result.get("overall_status", "UNKNOWN")
                product.compliance_score = result.get("score", 0)
                product.compliance_details = result
                
                product.issues_found = []
                for r in result.get("rule_results", []):
                    if r.get("violated"):
                        product.issues_found.append(r.get("description", r.get("rule_id")))
                
                logger.info(f"Compliance: {product.compliance_status} ({product.compliance_score}%)")
            except Exception as e:
                logger.warning(f"Compliance validation failed: {e}")
                product.compliance_status = "ERROR"
                product.compliance_score = 0
        else:
            product.compliance_status = "UNKNOWN"
            product.compliance_score = 0
        
        # --- GUARANTEE COMPLIANCE FIELDS (UI SAFETY) ---
        if product.compliance_details is None:
            product.compliance_details = {}
        
        if product.issues_found is None:
            product.issues_found = []
        
        if product.compliance_score is None:
            product.compliance_score = 0
        
        if not product.compliance_status:
            product.compliance_status = "UNKNOWN"
        
        # Ensure platform field is always present
        if not hasattr(product, 'platform') or not product.platform:
            product.platform = "generic"
        
        logger.info(f"✅ Universal extraction complete: {product.title}")
        return product


    def _enrich_product(self, product: ProductData, platform: str):
        """Run image OCR (Tesseract), combine text sources, run LLM (Flan-T5) extraction and compliance validation.

        Mutates `product` in-place and returns it.
        """
        if not product:
            return product

        # specific check for duplicates using normalized URL (no query params)
        if not hasattr(self, '_processed_urls'):
            self._processed_urls = set()
            
        dedup_key = product.product_url.split('?')[0] if product.product_url else product.title
        if dedup_key in self._processed_urls:
            logger.info(f"Skipping duplicate product (already processed): {product.title[:30]}...")
            return product
        self._processed_urls.add(dedup_key)

        # DEEP CRAWL: Always fetch full product details from the product page
        if product.product_url:
            try:
                logger.info(f"Deep crawling product: {product.product_url}")
                details = self.get_product_details(product.product_url, platform)
                if details:
                    # Merge details into product
                    if details.description: product.description = details.description
                    if details.full_page_text: product.full_page_text = details.full_page_text
                    if details.features: product.features = details.features
                    if details.specs: product.specs = details.specs
                    if details.aplus_content: product.aplus_content = details.aplus_content
                    # Merge images (keep unique)
                    if details.image_urls:
                        existing = set(product.image_urls or [])
                        for img in details.image_urls:
                            if img not in existing:
                                product.image_urls.append(img)
            except Exception as e:
                logger.warning(f"Deep crawl failed for {product.product_url}: {e}")

        # Image OCR and YOLO extraction
        try:
            ocr_accum = []
            # OCR up to 10 images (reduce from 20 for perf)
            for img_url in (product.image_urls or [])[:10]:
                if not img_url: continue
                
                try:
                    if self.ocr_integrator:
                        # Use centralized integrator (handles Cloud/Tesseract/Surya)
                        res = self.ocr_integrator.extract_text_from_image_url(img_url)
                        if res and res.get('text'):
                            ocr_accum.append(res.get('text'))
                    else:
                        # Fallback if integrator failed to load
                        pass
                except Exception:
                    continue

            if ocr_accum:
                product.ocr_text = "\n---\n".join(ocr_accum)
                # Skip local LLM correction (would need API client for that too, and regex is okay on good OCR)
        except Exception:
            pass

        # Combine text sources for extraction
        all_text_parts = []
        if getattr(product, 'title', None):
            all_text_parts.append(f"Title: {product.title}")
        if getattr(product, 'description', None):
            all_text_parts.append(f"Description: {product.description}")
        if getattr(product, 'full_page_text', None):
            all_text_parts.append(f"Page Content: {product.full_page_text}")
        if getattr(product, 'ocr_text', None):
            all_text_parts.append(f"OCR Text: {product.ocr_text}")

        combined_text = "\n".join(all_text_parts)

        # Extract fields via regex and LLM
        try:
            structured_data = self._extract_fields_from_text(combined_text or '', product)
        except Exception:
            structured_data = {}

        try:
            if TRANSFORMERS_AVAILABLE:
                llm_fields = self._run_llm_extract(combined_text)
                if llm_fields and isinstance(llm_fields, dict):
                    structured_data.update({k: v for k, v in llm_fields.items() if v})
        except Exception:
            pass

        # Run compliance validation if available
        try:
            if self.compliance_validator:
                validation_result = self.compliance_validator.validate(structured_data)
                product.validation_result = validation_result
                product.compliance_status = validation_result.get('overall_status', 'UNKNOWN')
                total_rules = validation_result.get('total_rules', 12)
                violations = validation_result.get('violations_count', 0)
                product.compliance_score = round(max(0, 100 - (violations * (100 / total_rules))), 2)
                product.issues_found = []
                for rule_result in validation_result.get('rule_results', []):
                    if rule_result.get('violated'):
                        issue_msg = f"{rule_result.get('rule_id')}: {rule_result.get('details', rule_result.get('description'))}"
                        product.issues_found.append(issue_msg)
                product.compliance_details = {
                    'extracted_fields': structured_data,
                    'validation_result': validation_result,
                    'ocr_performed': bool(product.ocr_text),
                    'text_sources': len(all_text_parts)
                }
        except Exception:
            logger.exception('Compliance check failed during enrichment')

        return product
    
    def _selenium_request(self, url: str) -> Optional[str]:
        """Selenium is intentionally disabled in this build.

        The crawler uses requests + BeautifulSoup for scraping. This method remains
        as a stub for backward compatibility and will return None.
        """
        logger.warning("Selenium request called but Selenium support has been removed; returning None.")
        return None

    def _run_surya_ocr_bytes(self, img_bytes: bytes, timeout: int = 120) -> str:
        """Run Surya OCR using the helper script in web/surya_ocr_main.py as a subprocess.
        Returns extracted text or empty string on failure.
        """
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
                tmp.write(img_bytes)
                tmp_path = tmp.name

            # locate helper script
            script_path = Path(__file__).resolve().parent.parent / 'web' / 'surya_ocr_main.py'
            if not script_path.exists():
                return ''

            proc = subprocess.run([sys.executable, str(script_path), tmp_path], capture_output=True, text=True, timeout=timeout)
            out = proc.stdout.strip() if proc.stdout else ''
            try:
                Path(tmp_path).unlink()
            except Exception:
                pass
            return out
        except Exception:
            return ''

    def _get_yolo_model(self):
        """Lazy load YOLO model via ultralytics if available."""
        if self._yolo_model is not None:
            return self._yolo_model
        try:
            from ultralytics import YOLO
            if Path(self.yolo_model_path).exists():
                self._yolo_model = YOLO(self.yolo_model_path)
            else:
                self._yolo_model = YOLO('best.pt')
            return self._yolo_model
        except Exception:
            return None

    def _yolo_detect_and_ocr(self, img_bytes: bytes, do_ocr: bool = True) -> Dict[str, Any]:
        """Run YOLO detection on image bytes, optionally OCR each detected box using Surya/Tesseract.
        Returns dict with 'boxes' and 'ocr_texts'.
        """
        result = {'boxes': [], 'ocr_texts': []}
        try:
            yolo = self._get_yolo_model()
            if yolo is None:
                return result

            # ultralytics accepts file path or np array; write temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
                tmp.write(img_bytes)
                tmp_path = tmp.name

            try:
                outs = yolo(tmp_path)
            except Exception:
                try:
                    outs = yolo(img_bytes)
                except Exception:
                    outs = None

            try:
                Path(tmp_path).unlink()
            except Exception:
                pass

            if not outs:
                return result

            for out in outs:
                boxes = []
                try:
                    b = getattr(out, 'boxes', None)
                    if b is not None and hasattr(b, 'xyxy'):
                        xy = b.xyxy.cpu().numpy()
                        for row in xy:
                            x1, y1, x2, y2 = [int(v) for v in row[:4]]
                            boxes.append((x1, y1, x2, y2))
                except Exception:
                    boxes = []

                result['boxes'].extend(boxes)

            # If requested, crop each box and OCR
            if do_ocr and result['boxes']:
                try:
                    from PIL import Image
                    img = Image.open(BytesIO(img_bytes)).convert('RGB')
                    for (x1, y1, x2, y2) in result['boxes']:
                        try:
                            crop = img.crop((x1, y1, x2, y2))
                            buf = BytesIO()
                            crop.save(buf, format='JPEG')
                            b = buf.getvalue()
                            text = ''
                            if self.use_surya:
                                text = self._run_surya_ocr_bytes(b)
                            if not text and TESSERACT_AVAILABLE:
                                try:
                                    from PIL import Image as PILImage
                                    timg = PILImage.open(BytesIO(b))
                                    text = pytesseract.image_to_string(timg)
                                except Exception:
                                    text = ''
                            if text:
                                result['ocr_texts'].append(text)
                        except Exception:
                            continue
                except Exception:
                    pass

        except Exception:
            logger.debug(f"YOLO detect/ocr failed: {traceback.format_exc()}")

        return result

    def _run_llm_extract(self, text: str) -> Dict[str, Any]:
        """Extract ALL Legal Metrology compliance fields using ml model compliance validator"""
        if not text:
            return {}
        
        try:
            # Import the compliance validator from ml model
            import sys
            import os
            ml_model_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'ml model')
            if ml_model_path not in sys.path:
                sys.path.insert(0, ml_model_path)
            
            from compliance import compute_compliance_score
            
            # The compliance validator expects a parsed structure with specific fields
            # We need to extract these from the raw text first using regex
            parsed_data = {
                "raw_text": text,
                "product_name": "",
                "tagline": "",
                "claims": [],
                "best_before": None,
                "mrp_incl_taxes": None,
                "mrp": None,
                "batch_no": None,
                "gross_content": None,
                "net_quantity": None,
                "net": None,
                "gross": None,
                "mfg_date": None,
                "packed_and_marketed_by": None,
                "customer_care": {},
                "storage_instructions": None,
                "allergen_information": None,
                "codes_and_misc": None,
                "country_of_origin": None,
                "country": None,
            }
            
            # Pre-extract some fields using regex to help the validator
            text_lower = text.lower()
            
            # Extract MRP
            mrp_match = re.search(r'(?:MRP|M\.R\.P\.|price|Rs\.?|₹)[:\s]*(?:Rs\.?|₹)?\s*([0-9,]+(?:\.[0-9]{2})?)', text, flags=re.I)
            if mrp_match:
                parsed_data["mrp_incl_taxes"] = mrp_match.group(1).replace(',', '')
                parsed_data["mrp"] = mrp_match.group(1).replace(',', '')
            
            # Extract Net Quantity
            qty_match = re.search(r'(?:net|nett?)\s*(?:wt\.?|weight|qty|quantity|contents?|vol\.?|volume)[:\s]*([0-9]+(?:\.[0-9]+)?\s*(?:g|gm|gms|gram|kg|kgs|ml|mL|l|ltr|litre|liter|L)s?)', text, flags=re.I)
            if qty_match:
                parsed_data["gross_content"] = qty_match.group(1).strip()
                parsed_data["net_quantity"] = qty_match.group(1).strip()
                parsed_data["net"] = qty_match.group(1).strip()
            
            # Extract Manufacturer/Packer
            mfr_match = re.search(r'(?:manufacturer|mfd\.?\s*by|manufactured\s*by|mfg\.?|packed\s*by|packer)[:\s]*([^\n]{10,200})', text, flags=re.I)
            if mfr_match:
                mfr_text = mfr_match.group(1).strip()
                # Try to extract name and address
                parsed_data["packed_and_marketed_by"] = {
                    "name": mfr_text.split(',')[0].strip() if ',' in mfr_text else mfr_text[:50],
                    "address_lines": [line.strip() for line in mfr_text.split(',')[1:]] if ',' in mfr_text else []
                }
            
            # Extract Customer Care
            contact_match = re.search(r'(?:consumer\s*care|customer\s*care|helpline|toll\s*free|contact)[:\s]*([^\n]{10,150})', text, flags=re.I)
            phone_match = re.search(r'(\d{10})', text)
            email_match = re.search(r'([a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,})', text_lower)
            
            if contact_match or phone_match or email_match:
                parsed_data["customer_care"] = {
                    "phone": phone_match.group(1) if phone_match else None,
                    "email": email_match.group(1) if email_match else None,
                    "website": None
                }
            
            # Extract Date
            date_match = re.search(r'(?:mfg|mfd|manufactured|best\s*before|expiry|exp\.?\s*date)[:\s]*([^\n]{5,40})', text, flags=re.I)
            if date_match:
                parsed_data["mfg_date"] = date_match.group(1).strip()
                parsed_data["best_before"] = date_match.group(1).strip()
            
            # Extract Country
            country_match = re.search(r'(?:country\s*of\s*origin|origin|made\s*in|product\s*of)[:\s]*([A-Za-z\s]+)', text, flags=re.I)
            if country_match:
                parsed_data["country_of_origin"] = country_match.group(1).strip()
                parsed_data["country"] = country_match.group(1).strip()
            
            # Run compliance check
            compliance_result = compute_compliance_score(parsed_data)
            
            # Extract fields from compliance result
            extracted = {}
            passed_rules = compliance_result.get("passed_rules", {})
            
            # Map passed rules to extracted fields (use the info which contains actual values)
            if "mrp" in passed_rules:
                info = passed_rules["mrp"].get("info")
                if info:
                    extracted["mrp"] = info
            
            if "net_quantity" in passed_rules:
                info = passed_rules["net_quantity"].get("info")
                if info:
                    extracted["net_quantity"] = info
            
            if "manufacturer" in passed_rules:
                info = passed_rules["manufacturer"].get("info")
                if info:
                    # info might be "address_present" or similar, use the actual data
                    if parsed_data.get("packed_and_marketed_by"):
                        mfr_data = parsed_data["packed_and_marketed_by"]
                        mfr_str = mfr_data.get("name", "")
                        if mfr_data.get("address_lines"):
                            mfr_str += ", " + ", ".join(mfr_data["address_lines"])
                        extracted["manufacturer"] = mfr_str
            
            if "consumer_care" in passed_rules:
                info = passed_rules["consumer_care"].get("info")
                if info and parsed_data.get("customer_care"):
                    cc = parsed_data["customer_care"]
                    cc_str = " | ".join(filter(None, [cc.get("phone"), cc.get("email")]))
                    extracted["consumer_care"] = cc_str if cc_str else info
            
            if "mfg_date" in passed_rules:
                info = passed_rules["mfg_date"].get("info")
                if info:
                    extracted["best_before"] = parsed_data.get("mfg_date") or parsed_data.get("best_before") or info
            
            if "country_of_origin" in passed_rules:
                info = passed_rules["country_of_origin"].get("info")
                if info:
                    extracted["country_of_origin"] = info
            
            compliance_pct = compliance_result.get('compliance_percentage', 0)
            logger.info(f"Compliance validator extracted {len(extracted)} fields (compliance: {compliance_pct}%)")
            
            return extracted if extracted else self._regex_fallback(text)
            
        except Exception as e:
            logger.error(f"Compliance validator failed: {e}", exc_info=True)
            return self._regex_fallback(text)
    
    def _regex_fallback(self, text: str) -> Dict[str, Any]:
        """Fallback regex extraction if compliance validator fails"""
        out = {}
        
        # Net quantity - expanded patterns
        m = re.search(r'(?:net|nett?)\s*(?:wt\.?|weight|qty|quantity|contents?|vol\.?|volume)[:\s]*([0-9]+(?:\.[0-9]+)?\s*(?:g|gm|gms|gram|kg|kgs|ml|mL|l|ltr|litre|liter|L)s?)', text, flags=re.I)
        if m:
            out['net_quantity'] = m.group(1).strip()
        
        # MRP - multiple formats
        m = re.search(r'(?:MRP|M\.R\.P\.|price|Rs\.?|₹)[:\s]*(?:Rs\.?|₹)?\s*([0-9,]+(?:\.[0-9]{2})?)', text, flags=re.I)
        if m:
            out['mrp'] = m.group(1).replace(',', '')
        
        # Manufacturer - look for common patterns
        m = re.search(r'(?:manufacturer|mfd\.?\s*by|manufactured\s*by|mfg\.?)[:\s]*([^\n]{10,150})', text, flags=re.I)
        if m:
            out['manufacturer'] = m.group(1).strip()
        
        # Importer
        m = re.search(r'(?:importer|imported\s*by|imp\.?\s*by)[:\s]*([^\n]{10,150})', text, flags=re.I)
        if m:
            out['importer'] = m.group(1).strip()
        
        # FSSAI - handle spaces and variations
        m = re.search(r'(?:FSSAI|fssai)[:\s#]*([0-9\s\-]{14,20})', text, flags=re.I)
        if m:
            # Clean to 14 digits
            fssai = re.sub(r'[^\d]', '', m.group(1))
            if len(fssai) == 14:
                out['fssai_license'] = fssai
        
        # Best before - multiple patterns
        m = re.search(r'(?:best\s*before|BB|expiry|exp\.?\s*date|use\s*by|use\s*before)[:\s]*([^\n]{5,40})', text, flags=re.I)
        if m:
            out['best_before'] = m.group(1).strip()
        
        # Consumer care - phone/email patterns
        m = re.search(r'(?:consumer\s*care|customer\s*care|helpline|toll\s*free|contact)[:\s]*([^\n]{10,150})', text, flags=re.I)
        if m:
            out['consumer_care'] = m.group(1).strip()
        
        # Country of origin
        m = re.search(r'(?:country\s*of\s*origin|origin|made\s*in|product\s*of)[:\s]*([A-Za-z\s]+)', text, flags=re.I)
        if m:
            out['country_of_origin'] = m.group(1).strip()
        
        # Generic name - common food types
        food_types = ['ghee', 'oil', 'milk', 'biscuit', 'butter', 'cheese', 'flour', 'rice', 'dal', 'sugar', 'salt', 'spice', 'masala', 'sauce', 'pickle', 'jam', 'honey']
        for food in food_types:
            if food in text.lower():
                out['generic_name'] = food.capitalize()
                break
        
        logger.info(f"Regex fallback extracted {len(out)} fields")
        return out


    def _download_and_save_images(self, product: ProductData):
        """Download product images to local storage and update product.local_image_paths"""
        if not product or not product.image_urls:
            return
        
        try:
            # Create images directory
            images_dir = Path("app_data/images")
            images_dir.mkdir(parents=True, exist_ok=True)
            
            product.local_image_paths = []
            # Download up to 3 images to save space/time
            for i, url in enumerate(product.image_urls[:3]):
                try:
                    ext = url.split('.')[-1].split('?')[0]
                    if len(ext) > 4 or ext.lower() not in ['jpg', 'jpeg', 'png', 'webp']:
                        ext = 'jpg'
                    
                    # Create safe filename from product title or timestamp
                    safe_title = re.sub(r'[^\w\-_]', '', (product.title or 'product')[:20])
                    filename = f"{safe_title}_{int(time.time())}_{i}.{ext}"
                    filepath = images_dir / filename
                    
                    response = self.session.get(url, timeout=5)
                    if response.status_code == 200:
                        with open(filepath, 'wb') as f:
                            f.write(response.content)
                        product.local_image_paths.append(str(filepath))
                except Exception:
                    continue
        except Exception as e:
            self.logger.warning(f"Failed to save images: {e}")

    def _save_to_db(self, product: ProductData):
        """Save product to database and/or JSON"""
        try:
            # Save to JSON (reliable storage)
            self.save_products([product])
            
            # Attempt DB save if available
            if DB_AVAILABLE and DatabaseManager:
                try:
                    db = DatabaseManager()
                    # Convert dataclass to dict for DB
                    import dataclasses
                    product_dict = dataclasses.asdict(product)
                    db.upsert_product(product_dict)
                except Exception as e:
                    self.logger.error(f"Database save failed: {e}")
        except Exception as e:
            self.logger.warning(f"Failed to save to DB: {e}")

    
    def search_products(self, query: str, platform: str = 'amazon', max_results: int = 50, use_selenium: bool = False) -> List[ProductData]:
        """Search for products on specified e-commerce platform"""
        
        if platform not in self.platforms:
            raise ValueError(f"Unsupported platform: {platform}")
        
        logger.info(f"Searching for '{query}' on {self.platforms[platform]['name']}")
        
        # Platform-specific search implementations
        if platform == 'amazon':
            return self._search_amazon(query, max_results, use_selenium=use_selenium)
        elif platform == 'flipkart':
            return self._search_flipkart(query, max_results, use_selenium=use_selenium)
        elif platform == 'myntra':
            return self._search_myntra(query, max_results, use_selenium=use_selenium)
        else:
            logger.warning(f"Search not implemented for platform: {platform}")
            return []
    
    def _search_amazon(self, query: str, max_results: int, use_selenium: bool = False) -> List[ProductData]:
        """Search Amazon India for products"""
        products = []
        
        try:
            search_url = self.platforms['amazon']['search_url'].format(query=query.replace(' ', '+'))
            html = self._make_request(search_url, 'amazon', use_selenium=use_selenium)
            
            if not html or len(html) < 1000:
                # Amazon is heavily blocking, generate sample data
                logger.warning("Amazon blocking or not returning content, generating sample data")
                return self._generate_sample_products('amazon', query, max_results)
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find product containers - more flexible approach
            product_containers = []
            
            # Try multiple selectors
            selectors = [
                'div[data-component-type="s-search-result"]',
                'div.s-result-item',
                'div[class*="s-result"]',
                'div[class*="a-section a-spacing-none"]'
            ]
            
            for selector in selectors:
                product_containers = soup.select(selector)
                if product_containers:
                    break
            
            # If still empty, try finding by price patterns
            if not product_containers:
                for div in soup.find_all('div', class_=re.compile(r'a-section|s-result')):
                    if div.find('span', class_='a-price-whole'):
                        product_containers.append(div)
            
            for container in product_containers[:max_results]:
                try:
                    product = self._extract_amazon_product(container)
                    if product and len(product.title) > 5:
                        products.append(product)
                except Exception as e:
                    logger.debug(f"Failed to extract Amazon product: {e}")
                    continue
            
            logger.info(f"Extracted {len(products)} products from Amazon")
            
        except Exception as e:
            logger.error(f"Amazon search failed: {e}")
            # Fallback to sample data
            return self._generate_sample_products('amazon', query, max_results)
        
        return products
    
    def _extract_amazon_product(self, container) -> Optional[ProductData]:
        """Extract product data from Amazon product container"""
        try:
            if not container:
                return None
                
            # Product title - try multiple selectors for better compatibility
            title = None
            title_selectors = [
                'h2 a span',
                'h2 span',
                'span[class*="a-size"]',
                'h2[class*="a-size"]',
                'a[class*="a-link"] span',
                '.s-title-instructions-style span',
                'div[class*="s-title"] span',
                'span.a-size-medium',
                'h2 span'
            ]
            
            for selector in title_selectors:
                try:
                    title_elems = container.select(selector)
                    for elem in title_elems:
                        text = elem.get_text(strip=True)
                        if text and len(text) > 10 and len(text) < 200:
                            title = text
                            break
                    if title:
                        break
                except:
                    pass
            
            # Fallback: look for any text with reasonable length
            if not title:
                for elem in container.find_all(['h2', 'span', 'a']):
                    text = elem.get_text(strip=True)
                    if text and len(text) > 10 and len(text) < 200:
                        title = text
                        break
            
            # If no title found, fallback to universal extraction
            if not title:
                return self._universal_extract_product(container, 'amazon')
            
            # Product URL
            product_url = None
            for link in container.find_all('a', href=True):
                href = link.get('href')
                if href and '/dp/' in href:
                    product_url = urljoin(self.platforms['amazon']['base_url'], href)
                    break
            
            # Price information
            price = None
            mrp = None
            price_elem = container.find('span', class_='a-price-whole')
            if price_elem:
                price_text = price_elem.get_text(strip=True).replace(',', '').replace('₹', '')
                try:
                    price = float(price_text)
                except ValueError:
                    pass
            
            # MRP (strikethrough price)
            mrp_elem = container.find('span', class_='a-price-was')
            if mrp_elem:
                mrp_text = mrp_elem.get_text(strip=True).replace('₹', '').replace(',', '')
                try:
                    mrp = float(mrp_text)
                except ValueError:
                    pass
            
            # Image URLs - Extract ALL images from product container
            image_urls = []
            
            # First try to find main product image
            img_elem = container.find('img', class_='s-image')
            if img_elem and img_elem.get('src'):
                src = img_elem['src']
                if src and src.startswith('http'):
                    image_urls.append(src)
            
            # Extract all other images from the container
            for img in container.find_all('img'):
                src = img.get('src') or img.get('data-src') or img.get('data-image-src')
                if src and src.startswith('http') and src not in image_urls:
                    image_urls.append(src)
            
            # Try to get images from picture elements (modern HTML)
            for picture in container.find_all('picture'):
                for source in picture.find_all('source'):
                    srcset = source.get('srcset')
                    if srcset:
                        # Extract first image from srcset
                        img_url = srcset.split(',')[0].split()[0]
                        if img_url.startswith('http') and img_url not in image_urls:
                            image_urls.append(img_url)
                # Also check img within picture tag
                img_in_pic = picture.find('img')
                if img_in_pic and img_in_pic.get('src'):
                    src = img_in_pic['src']
                    if src.startswith('http') and src not in image_urls:
                        image_urls.append(src)
            
            # Limit to 50 images per product (increased from 5)
            image_urls = image_urls[:50]
            
            # If no image found, add placeholder
            if not image_urls:
                image_urls = [f"https://via.placeholder.com/300x400?text={title[:20].replace(' ', '+')}"]
            
            # OCR / YOLO: Process up to 10 images now (increased from 5)
            ocr_processing_limit = 10
            
            # If no image found, add placeholder
            if not image_urls:
                image_urls = [f"https://via.placeholder.com/300x400?text={title[:20].replace(' ', '+')}"]
            
            # Rating
            rating = None
            rating_elem = container.find('span', class_='a-icon-alt')
            if rating_elem:
                rating_text = rating_elem.get_text(strip=True)
                rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                if rating_match:
                    try:
                        rating = float(rating_match.group(1))
                    except ValueError:
                        pass
            
            product = ProductData(
                title=title,
                price=price,
                mrp=mrp,
                product_url=product_url,
                image_urls=image_urls,
                platform='amazon',
                rating=rating,
                extracted_at=time.strftime('%Y-%m-%d %H:%M:%S')
            )
            # ENRICHMENT: Deep Crawl + OCR + LLM + Compliance
            # This calls get_product_details() to visit the page, extracts all images,
            # runs OCR on 20+ images, and performs compliance check.
            self._enrich_product(product, 'amazon')

            # Download images locally
            self._download_and_save_images(product)

            # Save to Database
            self._save_to_db(product)

            return product
            
        except Exception as e:
            logger.error(f"Failed to extract Amazon product data: {e}")
            return None
    
    def _search_flipkart(self, query: str, max_results: int, use_selenium: bool = False) -> List[ProductData]:
        """Search Flipkart for products"""
        products = []
        
        try:
            search_url = self.platforms['flipkart']['search_url'].format(query=query.replace(' ', '%20'))
            # Flipkart may require Selenium due to JavaScript rendering
            html = self._make_request(search_url, 'flipkart', use_selenium=use_selenium)
            
            if not html or len(html) < 1000:
                # Flipkart is heavily blocking, generate sample data (same as Amazon)
                logger.warning("Flipkart blocking or not returning content, generating sample data")
                return self._generate_sample_products('flipkart', query, max_results)
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Updated Flipkart product container selectors (2024+)
            product_containers = []
            
            # Try modern Flipkart class names
            selectors = [
                'div[class*="_75nlfW"]',  # New grid item container
                'div[class*="cPHDOP"]',   # Product card wrapper
                'div[class*="tUxRFH"]',   # Another common wrapper
                'div[class*="_1AtVbE"]',  # Search result item
                'a[class*="CGtC98"]',     # Product link container
                'div[data-id]',           # Product with data-id
                'div[class*="col"]',      # Column-based layout
            ]
            
            for selector in selectors:
                containers = soup.select(selector)
                if containers and len(containers) > 2:
                    product_containers = containers[:max_results]
                    logger.info(f"Found {len(containers)} products using selector: {selector}")
                    break
            
            # Fallback: Find all product links
            if not product_containers:
                logger.info("Using fallback: searching for product links")
                all_links = soup.find_all('a', href=re.compile(r'/p/'))
                for link in all_links[:max_results]:
                    parent = link.find_parent('div')
                    if parent:
                        product_containers.append(parent)
            
            for container in product_containers[:max_results]:
                try:
                    product = self._extract_flipkart_product(container)
                    if product and product.title != "Flipkart Product Title Not Found":
                        products.append(product)
                except Exception as e:
                    logger.debug(f"Failed to extract Flipkart product: {e}")
                    continue
            
            logger.info(f"Extracted {len(products)} products from Flipkart")
            
        except Exception as e:
            logger.error(f"Flipkart search failed: {e}")
        
        return products
    
    def _extract_flipkart_product(self, container) -> Optional[ProductData]:
        """Extract product data from Flipkart product container"""
        try:
            if not container:
                return None
            
            # Product title - enhanced extraction
            title = None
            title_selectors = [
                'a._16 omkq',
                'a[class*="productCardImg"]',
                'a[class*="_2UkuGl"]',
                'a span',
                'h2',
                'div[class*="title"]'
            ]
            
            for selector in title_selectors:
                title_elem = container.select_one(selector)
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    if title and len(title) > 5:
                        break
            
            if not title:
                title_elem = container.find('a')
                if title_elem:
                    title = title_elem.get_text(strip=True)
            
            if not title:
                title = "Flipkart Product"
            
            # Product URL - more robust
            product_url = None
            link = container.find('a', href=True)
            if link and link.get('href'):
                url = link['href']
                if not url.startswith('http'):
                    product_url = urljoin('https://www.flipkart.com', url)
                else:
                    product_url = url
            
            # Price extraction
            price = None
            price_selectors = ['div._30jeq3', 'div[class*="price"]', 'span[class*="price"]']
            for selector in price_selectors:
                price_elem = container.select_one(selector)
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    price_match = re.search(r'₹\s*([\d,]+)', price_text)
                    if price_match:
                        try:
                            price = float(price_match.group(1).replace(',', ''))
                            break
                        except (ValueError, AttributeError):
                            pass
            
            # Image URL
            image_urls = []
            for img in container.find_all('img'):
                src = img.get('src') or img.get('data-src')
                if src and src.startswith('http') and src not in image_urls:
                    image_urls.append(src)
            image_urls = image_urls[:50]
            
            # If no image found, add placeholder
            if not image_urls:
                image_urls = [f"https://via.placeholder.com/300x400?text={title[:20].replace(' ', '+')}"]
            
            product = ProductData(
                title=title,
                price=price,
                product_url=product_url,
                image_urls=image_urls,
                platform='flipkart',
                extracted_at=time.strftime('%Y-%m-%d %H:%M:%S')
            )
            # Try to capture description from container or product page
            # ENRICHMENT: Deep Crawl + OCR + Compliance
            self._enrich_product(product, 'flipkart')
            
            # Download images and Save to DB
            self._download_and_save_images(product)
            self._save_to_db(product)
            
            return product
            
        except Exception as e:
            logger.debug(f"Failed to extract Flipkart product data: {e}")
            return None
    
    def _search_myntra(self, query: str, max_results: int, use_selenium: bool = False) -> List[ProductData]:
        """Search Myntra for fashion products"""
        products = []
        
        try:
            # Myntra requires Selenium due to JavaScript rendering
            search_url = f"https://www.myntra.com/search?q={query.replace(' ', '%20')}"
            html = self._make_request(search_url, 'myntra', use_selenium=use_selenium)
            
            if not html:
                return products
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Updated Myntra product container selectors (2024+)
            product_containers = []
            
            # Try modern Myntra class names
            selectors = [
                'li[class*="product-base"]',           # Product list item
                'li[data-index]',                       # Indexed product items
                'ul[class*="results-base"] > li',      # Results list items
                'div[class*="product-productMetaInfo"]', # Product meta container
                'a[class*="product-base"]',            # Product link
                'li.product-base',                     # Direct class
                'a[href*="/p/"]',                      # Fallback product links
            ]
            
            for selector in selectors:
                try:
                    product_containers = soup.select(selector)
                    if product_containers and len(product_containers) > 2:
                        logger.info(f"Found {len(product_containers)} products using selector: {selector}")
                        break
                        break
                except:
                    pass
            
            # Fallback: generic extraction
            if not product_containers or len(product_containers) < 2:
                product_containers = soup.find_all('a', href=re.compile(r'/p/\d+'))
                product_containers = [link.find_parent('div') or link for link in product_containers]
            
            for container in product_containers[:max_results]:
                try:
                    product = self._extract_myntra_product(container)
                    if product and len(product.title) > 5:
                        products.append(product)
                except Exception as e:
                    logger.debug(f"Failed to extract Myntra product: {e}")
                    continue
            
            logger.info(f"Extracted {len(products)} products from Myntra")
            
        except Exception as e:
            logger.error(f"Myntra search failed: {e}")
        
        return products
    
    def _extract_myntra_product(self, container) -> Optional[ProductData]:
        """Extract product data from Myntra product container"""
        try:
            if not container:
                return None
            
            # Product title
            title = None
            title_selectors = [
                'a[class*="productCardImg"]',
                'h3',
                'a[href*="/p/"]',
                'div[class*="productName"]',
                'span[class*="productTitle"]'
            ]
            
            for selector in title_selectors:
                title_elem = container.select_one(selector)
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    if title and len(title) > 3:
                        break
            
            # If no title, fallback to universal extraction
            if not title or len(title) < 5:
                return self._universal_extract_product(container, 'myntra')
            
            # Brand
            brand = None
            brand_elem = container.find('h3')
            if brand_elem:
                brand = brand_elem.get_text(strip=True)
            
            # Price
            price = None
            price_elem = container.find(attrs={"class": re.compile(r".*price.*")})
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                price_match = re.search(r'₹\s*([\d,]+)', price_text)
                if price_match:
                    try:
                        price = float(price_match.group(1).replace(',', ''))
                    except (ValueError, AttributeError):
                        pass
            
            # Product URL
            product_url = None
            link = container.find('a', href=re.compile(r'/p/'))
            if link and link.get('href'):
                url = link['href']
                if not url.startswith('http'):
                    product_url = urljoin('https://www.myntra.com', url)
                else:
                    product_url = url
            
            # Image
            image_urls = []
            for img in container.find_all('img'):
                src = img.get('src') or img.get('data-src')
                if src and src.startswith('http') and src not in image_urls:
                    image_urls.append(src)
            image_urls = image_urls[:50]
            
            # If no image found, add placeholder
            if not image_urls:
                image_urls = [f"https://via.placeholder.com/300x400?text={title[:20].replace(' ', '+')}"]
            
            product = ProductData(
                title=title,
                brand=brand,
                price=price,
                product_url=product_url,
                image_urls=image_urls,
                platform='myntra',
                category='fashion',
                extracted_at=time.strftime('%Y-%m-%d %H:%M:%S')
            )
            # Description extraction and OCR
            # ENRICHMENT: Deep Crawl + OCR + Compliance
            self._enrich_product(product, 'myntra')
            
            # Download images and Save to DB
            self._download_and_save_images(product)
            self._save_to_db(product)
            
            return product
            
        except Exception as e:
            logger.debug(f"Failed to extract Myntra product data: {e}")
            return None
    
    def _search_nyka(self, query: str, max_results: int) -> List[ProductData]:
        """NYKA platform removed - use Amazon, Flipkart, or Myntra instead"""
        return []
    
    def _fetch_flipkart_json(self, product_url: str) -> Optional[dict]:
        """
        Fetch Flipkart product data from mobile JSON API
        This bypasses anti-bot protection by using the official API
        """
        try:
            # Extract PID from URL
            parsed = urlparse(product_url)
            params = parse_qs(parsed.query)
            pid = params.get("pid", [None])[0]
            
            if not pid:
                # Try to extract from URL path if not in query
                logger.warning(f"No PID found in URL: {product_url}")
                return None
            
            # Flipkart mobile API endpoint (updated)
            api_url = f"https://www.flipkart.com/api/3/page/dynamic/product"
            api_params = {
                "pid": pid,
                "marketplace": "FLIPKART"
            }
            
            # Mobile app headers (updated to match real mobile app)
            headers = {
                "User-Agent": "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": product_url,
                "Origin": "https://www.flipkart.com",
                "X-User-Agent": "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36 FKUA/website/42/website/Mobile",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin"
            }
            
            logger.info(f"Fetching Flipkart JSON API for PID: {pid}")
            response = self.session.get(
                api_url, 
                headers=headers, 
                params=api_params, 
                timeout=30  # Increased timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Successfully fetched Flipkart JSON data")
                return data
            else:
                logger.warning(f"Flipkart API returned status {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Flipkart JSON fetch failed: {e}")
            return None
    
    def _extract_flipkart_from_json(self, data: dict, url: str) -> Optional[ProductData]:
        """
        Extract product data from Flipkart JSON API response
        """
        try:
            if not data or "data" not in data:
                return None
            
            product_data = data["data"].get("product", {}).get("value", {})
            
            if not product_data:
                logger.warning("No product data in Flipkart JSON response")
                return None
            
            # Extract basic info
            title = product_data.get("title", "")
            
            # Extract pricing
            price_info = product_data.get("price", {})
            price = price_info.get("sellingPrice", {}).get("value")
            mrp = price_info.get("mrp", {}).get("value")
            
            # Extract images
            images = []
            media = product_data.get("media", {})
            for img in media.get("images", []):
                img_url = img.get("url")
                if img_url:
                    images.append(img_url)
            
            # Extract specifications
            specs = {}
            for spec_group in product_data.get("specifications", []):
                for attr in spec_group.get("attributes", []):
                    name = attr.get("name")
                    value = attr.get("value")
                    if name and value:
                        specs[name] = value
            
            # Extract description
            description = product_data.get("description", "")
            
            # Extract rating
            rating = None
            rating_info = product_data.get("rating", {})
            if rating_info:
                rating = rating_info.get("average")
            
            # Create ProductData
            product = ProductData(
                title=title,
                price=price,
                mrp=mrp,
                description=description,
                specs=specs,
                image_urls=images,
                platform="flipkart",
                product_url=url,
                rating=rating,
                extracted_at=time.strftime("%Y-%m-%d %H:%M:%S")
            )
            
            logger.info(f"✅ Extracted Flipkart product: {title[:50]}")
            return product
            
        except Exception as e:
            logger.error(f"Failed to extract Flipkart JSON data: {e}")
            return None
    
    def get_product_details(self, product_url: str, platform: str) -> Optional[ProductData]:
        """
        Get detailed product information from product page
        Uses platform-specific strategies:
        - Flipkart: JSON API (mobile app endpoint)
        - Amazon: HTML scraping
        - Others: HTML scraping
        """
        if platform not in self.platforms:
            raise ValueError(f"Unsupported platform: {platform}")

        logger.info(f"Fetching product details from {platform}: {product_url}")
        
        # FLIPKART: Use JSON API (no HTML scraping needed!)
        if platform == 'flipkart':
            logger.info("Using Flipkart JSON API (mobile endpoint)")
            json_data = self._fetch_flipkart_json(product_url)
            if json_data:
                product = self._extract_flipkart_from_json(json_data, product_url)
                if product:
                    # Enrich with OCR and compliance
                    self._enrich_product(product, platform)
                    # Save enriched product data and images to DB
                    self._download_and_save_images(product)
                    self._save_to_db(product)
                    return product
            
            # Fallback to HTML scraping if JSON fails
            logger.warning("Flipkart JSON API failed, falling back to HTML scraping")
        
        # AMAZON & OTHERS: HTML scraping
        try:
            html = self._make_request(product_url, platform, use_selenium=True)
            if not html:
                return None
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Platform-specific detail extraction
            if platform == 'amazon':
                prod = self._extract_amazon_details(soup, product_url)
            elif platform == 'flipkart':
                prod = self._extract_flipkart_details(soup, product_url)
            elif platform == 'myntra':
                prod = self._extract_myntra_details(soup, product_url)
            elif platform == 'nyka':
                prod = self._extract_nyka_details(soup, product_url)
            else:
                prod = None

            # Enrich product (OCR, YOLO, LLM, compliance)
            try:
                if prod is not None:
                    prod = self._enrich_product(prod, platform)
                    # Save enriched product data and images to DB
                    self._download_and_save_images(prod)
                    self._save_to_db(prod)
                return prod
            except Exception as e:
                logger.error(f"Error enriching product details: {e}")
                return prod
            
        except Exception as e:
            logger.error(f"Failed to get product details from {product_url}: {e}")
        
        return None
    
    def _extract_amazon_details(self, soup: BeautifulSoup, url: str) -> Optional[ProductData]:
        """Extract detailed product information from Amazon product page"""
        try:
            # Product title
            title_elem = soup.find('span', {'id': 'productTitle'})
            title = title_elem.get_text(strip=True) if title_elem else "Unknown Product"
            
            # Brand
            brand = None
            brand_elem = soup.find('a', {'id': 'bylineInfo'})
            if brand_elem:
                brand = brand_elem.get_text(strip=True).replace('Visit the ', '').replace(' Store', '')
            
            # Price and MRP
            price = None
            mrp = None
            
            price_elem = soup.find('span', class_='a-price-whole')
            if price_elem:
                price_text = price_elem.get_text(strip=True).replace(',', '')
                try:
                    price = float(price_text)
                except ValueError:
                    pass
            
            
            # Product details table - scan MULTIPLE tables to get complete information
            details = {}
            
            # Try multiple table IDs that Amazon uses for product details
            table_ids = [
                'productDetails_techSpec_section_1',
                'productDetails_detailBullets_sections1', 
                'productDetails_db_sections',
                'product-details-grid_feature_div'
            ]
            
            for table_id in table_ids:
                detail_table = soup.find('table', {'id': table_id})
                if detail_table:
                    rows = detail_table.find_all('tr')
                    for row in rows:
                        cells = row.find_all(['th', 'td'])
                        if len(cells) >= 2:
                            key = cells[0].get_text(strip=True).lower()
                            value = cells[1].get_text(strip=True)
                            if key and value:
                                details[key] = value
            
            
            # Extract Legal Metrology fields from details with MULTIPLE possible keywords
            net_quantity = (details.get('net quantity') or 
                          details.get('item weight') or 
                          details.get('package weight') or
                          details.get('weight') or
                          details.get('net content') or
                          details.get('quantity'))
            
            manufacturer = (details.get('manufacturer') or 
                          details.get('brand') or
                          details.get('packer') or
                          details.get('importer') or
                          details.get('mfr') or
                          details.get('manufactured by'))
            
            # Separate manufacturer and importer details
            manufacturer_details = (details.get('manufacturer') or 
                                  details.get('packer') or
                                  details.get('manufactured by'))
            
            importer_details = (details.get('importer') or
                              details.get('imported by'))
            
            country_of_origin = (details.get('country of origin') or 
                                details.get('origin') or
                                details.get('country') or
                                details.get('made in') or
                                details.get('origin country'))
            
            # Generic name with multiple keywords
            generic_name = (details.get('generic name') or 
                          details.get('product type') or
                          details.get('item type') or
                          details.get('category') or
                          details.get('type'))
            
            # Image URLs - extract from multiple possible attributes and fallbacks
            image_urls = []
            # Common landing image attributes
            img_elements = soup.find_all('img')
            for img in img_elements:
                # check commonly used attributes
                for attr in ('data-a-image-source', 'data-old-hires', 'data-src', 'data-a-dynamic-image', 'src'):
                    val = img.get(attr)
                    if not val:
                        continue
                    # data-a-dynamic-image contains JSON mapping of urls
                    if attr == 'data-a-dynamic-image':
                        try:
                            import json as _json
                            parsed = _json.loads(val)
                            for k in parsed.keys():
                                if k and k not in image_urls:
                                    image_urls.append(k)
                        except Exception:
                            # sometimes it's not JSON; treat as raw url
                            if val not in image_urls:
                                image_urls.append(val)
                    else:
                        if val not in image_urls:
                            image_urls.append(val)

            # As a last resort, look for image URLs in the page HTML text
            if not image_urls:
                try:
                    page_html = str(soup)
                    found = re.findall(r'https?://[^\s"\']+\.(?:png|jpg|jpeg)', page_html)
                    for url_img in found:
                        if url_img not in image_urls:
                            image_urls.append(url_img)
                except Exception:
                    pass
            
            # Description - Aggressive extraction of all text blocks
            description_parts = []
            
            # 1. Feature bullets
            bullets_elem = soup.find('div', {'id': 'feature-bullets'})
            if bullets_elem:
                description_parts.append(bullets_elem.get_text(separator='\n', strip=True))
                
            # 2. Main product description
            prod_desc_elem = soup.find('div', {'id': 'productDescription'})
            if prod_desc_elem:
                description_parts.append(prod_desc_elem.get_text(separator='\n', strip=True))
                
            # 3. From the manufacturer / A+ content (often in div#aplus)
            aplus_elem = soup.find('div', {'id': 'aplus'})
            if aplus_elem:
                description_parts.append(aplus_elem.get_text(separator='\n', strip=True))
                
            # Join all unique parts
            description = "\n\n---\n\n".join(list(dict.fromkeys(description_parts))) if description_parts else None
            
            # Features / Bullets
            features = []
            # Features / Bullets
            features = []
            if bullets_elem:
                for li in bullets_elem.find_all('li'):
                    txt = li.get_text(strip=True)
                    if txt and not txt.lower().startswith('show more'):
                        features.append(txt)
            
            # Seller Info
            seller = None
            merchant_info = soup.find('div', {'id': 'merchant-info'})
            if merchant_info:
                seller = merchant_info.get_text(strip=True)
                # Try to clean up "Sold by X and Fulfilled by Amazon"
                if 'Sold by' in seller:
                    seller = seller.split('Sold by')[-1].split(' and')[0].strip()
            
            # Legal Disclaimer
            legal_disclaimer = None
            disclaimer_elem = soup.find('div', {'id': 'legal_disclaimer_description'})
            if disclaimer_elem:
                legal_disclaimer = disclaimer_elem.get_text(strip=True)
            
            # Specifications (Iterate all tables in product details)
            # Already grabbed from 'productDetails_techSpec_section_1', but let's be more generic
            if not details: # If specific table failed, scan all tables in prodDetails
                prod_details_div = soup.find('div', {'id': 'prodDetails'})
                if prod_details_div:
                    for table in prod_details_div.find_all('table'):
                        for row in table.find_all('tr'):
                            cells = row.find_all(['th', 'td'])
                            if len(cells) >= 2:
                                k = cells[0].get_text(strip=True).replace('\n', ' ')
                                v = cells[1].get_text(strip=True)
                                if k and v:
                                    details[k] = v
                                    
            # A+ Content (Rich description)
            aplus_content = None
            aplus_div = soup.find('div', {'id': 'aplus'})
            if aplus_div:
                aplus_content = aplus_div.get_text(separator='\n', strip=True)

            # Capture full page text for richer extraction
            try:
                full_page_text = soup.get_text(separator='\n', strip=True)
            except Exception:
                full_page_text = None

            return ProductData(
                title=title,
                brand=brand,
                price=price,
                mrp=mrp,
                description=description,
                net_quantity=net_quantity,
                manufacturer=manufacturer,
                manufacturer_details=manufacturer_details,
                importer_details=importer_details,
                country_of_origin=country_of_origin,
                platform='amazon',
                product_url=url,
                image_urls=image_urls,
                full_page_text=full_page_text,
                features=features,
                specs=details,
                seller=seller,
                legal_disclaimer=legal_disclaimer,
                aplus_content=aplus_content,
                extracted_at=time.strftime('%Y-%m-%d %H:%M:%S')
            )
            
        except Exception as e:
            logger.error(f"Failed to extract Amazon product details: {e}")
            return None
    
    def _extract_flipkart_details(self, soup: BeautifulSoup, url: str) -> Optional[ProductData]:
        """Extract detailed product information from Flipkart product page"""
        try:
            # Extract title, price, and basic info
            title = "Flipkart Product"
            price = None
            return ProductData(
                title=title,
                price=price,
                platform='flipkart',
                product_url=url,
                extracted_at=time.strftime('%Y-%m-%d %H:%M:%S')
            )
        except Exception as e:
            logger.error(f"Failed to extract Flipkart product details: {e}")
            return None
    
    def _extract_myntra_details(self, soup: BeautifulSoup, url: str) -> Optional[ProductData]:
        """Extract detailed product information from Myntra product page"""
        try:
            # Extract title, price, and basic info
            title = "Myntra Product"
            price = None
            return ProductData(
                title=title,
                price=price,
                platform='myntra',
                product_url=url,
                extracted_at=time.strftime('%Y-%m-%d %H:%M:%S')
            )
        except Exception as e:
            logger.error(f"Failed to extract Myntra product details: {e}")
            return None
    
    def _extract_nyka_details(self, soup: BeautifulSoup, url: str) -> Optional[ProductData]:
        """Extract detailed product information from NYKA product page"""
        try:
            # Extract title, price, and basic info
            title = "NYKA Product"
            price = None
            return ProductData(
                title=title,
                price=price,
                platform='nyka',
                product_url=url,
                extracted_at=time.strftime('%Y-%m-%d %H:%M:%S')
            )
        except Exception as e:
            logger.error(f"Failed to extract NYKA product details: {e}")
            return None
    
    def bulk_crawl(self, queries: List[str], platforms: List[str] = None, max_results_per_query: int = 20) -> List[ProductData]:
        """Perform bulk crawling across multiple queries and platforms"""
        
        if platforms is None:
            platforms = ['amazon', 'flipkart']
        
        all_products = []
        
        for query in queries:
            logger.info(f"Bulk crawling for query: '{query}'")
            
            for platform in platforms:
                try:
                    products = self.search_products(query, platform, max_results_per_query)
                    all_products.extend(products)
                    logger.info(f"Found {len(products)} products for '{query}' on {platform}")
                    
                    # Respect rate limits between platforms
                    time.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Failed to crawl {platform} for '{query}': {e}")
                    continue
        
        logger.info(f"Bulk crawling completed: {len(all_products)} total products")
        return all_products
    
    def save_products(self, products: List[ProductData], filepath: str = None) -> str:
        """Save crawled products to JSON file"""
        
        if filepath is None:
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            filepath = f"app/data/crawled_products_{timestamp}.json"
        
        # Convert to serializable format
        products_data = []
        for product in products:
            product_dict = asdict(product)
            
            # Handle ValidationResult serialization
            if product_dict.get('validation_result'):
                validation_result = product_dict['validation_result']
                if hasattr(validation_result, '__dict__'):
                    # Convert ValidationResult to dict
                    product_dict['validation_result'] = {
                        'is_compliant': validation_result.is_compliant,
                        'score': validation_result.score,
                        'issues': [
                            {
                                'field': issue.field,
                                'level': issue.level,
                                'message': issue.message
                            } for issue in validation_result.issues
                        ] if validation_result.issues else []
                    }
            
            # Ensure all fields are JSON serializable
            for key, value in product_dict.items():
                if value is None or isinstance(value, (str, int, float, bool, list, dict)):
                    continue
                elif hasattr(value, '__dict__'):
                    # Convert custom objects to dict
                    product_dict[key] = value.__dict__ if hasattr(value, '__dict__') else str(value)
                else:
                    # Convert other non-serializable objects to string
                    product_dict[key] = str(value)
            
            products_data.append(product_dict)
        
        # Create directory if it doesn't exist
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        # Save to JSON
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(products_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(products)} products to {filepath}")
        return filepath
    
    def load_products(self, filepath: str) -> List[ProductData]:
        """Load products from JSON file"""
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                products_data = json.load(f)
            
            products = []
            for data in products_data:
                # Handle ValidationResult deserialization
                if 'validation_result' in data and data['validation_result']:
                    # Skip validation_result for now as it's complex to reconstruct
                    # The compliance_details should contain the necessary information
                    data.pop('validation_result', None)
                
                products.append(ProductData(**data))
            
            logger.info(f"Loaded {len(products)} products from {filepath}")
            return products
            
        except Exception as e:
            logger.error(f"Failed to load products from {filepath}: {e}")
            return []
    
    def export_to_csv(self, products: List[ProductData], filepath: str = None) -> str:
        """Export products to CSV format"""
        
        if filepath is None:
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            filepath = f"app/data/crawled_products_{timestamp}.csv"
        
        # Convert to DataFrame with proper serialization
        products_data = []
        for product in products:
            product_dict = asdict(product)
            
            # Remove ValidationResult as it's not CSV-friendly
            product_dict.pop('validation_result', None)
            
            # Convert complex objects to strings
            for key, value in product_dict.items():
                if value is None:
                    continue
                elif isinstance(value, (str, int, float, bool)):
                    continue
                elif isinstance(value, list):
                    product_dict[key] = '; '.join(str(v) for v in value) if value else ''
                elif hasattr(value, '__dict__'):
                    product_dict[key] = str(value)
                else:
                    product_dict[key] = str(value)
            
            products_data.append(product_dict)
        
        df = pd.DataFrame(products_data)
        
        # Create directory if it doesn't exist
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        # Save to CSV
        df.to_csv(filepath, index=False, encoding='utf-8')
        
        logger.info(f"Exported {len(products)} products to {filepath}")
        return filepath
    
    def get_supported_platforms(self) -> Dict[str, str]:
        """Return supported platforms"""
        return {platform: config['name'] for platform, config in self.platforms.items()}
    
    
    def extract_product_from_url(self, product_url: str) -> Optional[ProductData]:
        """
        Extract product details from ANY e-commerce product URL.
        Now uses UNIVERSAL EXTRACTION - works for all websites!
        
        This replaces the complex platform-specific logic with a simple,
        maintainable approach that works for Meesho, Flipkart, Amazon, etc.
        """
        logger.info(f"🎯 Extracting product from URL: {product_url}")
        
        # Use the universal extraction method
        return self.extract_product_from_url_simple(product_url)
    
    
    
    def download_and_process_image(self, image_url: str, ocr_integrator=None) -> Dict[str, Any]:
        """Download image and optionally extract text with OCR"""
        try:
            import os
            import uuid
            from io import BytesIO
            from PIL import Image
            
            result = {
                'image_url': image_url,
                'download_status': 'failed',
                'local_path': None,
                'ocr_text': None,
                'metadata': {}
            }
            
            # Download image
            try:
                response = requests.get(image_url, timeout=10)
                if response.status_code == 200:
                    img = Image.open(BytesIO(response.content))
                    
                    # Save locally
                    cache_dir = Path('temp_images')
                    cache_dir.mkdir(exist_ok=True)
                    
                    file_name = f"{uuid.uuid4()}.jpg"
                    local_path = cache_dir / file_name
                    img.save(local_path, 'JPEG')
                    
                    result['download_status'] = 'success'
                    result['local_path'] = str(local_path)
                    result['metadata']['size'] = f"{img.width}x{img.height}"
                    result['metadata']['format'] = img.format
                    
                    # Run OCR if integrator available
                    if ocr_integrator:
                        try:
                            ocr_result = ocr_integrator.extract_text_from_image_url(image_url)
                            if ocr_result:
                                result['ocr_text'] = ocr_result.get('text', '')
                                result['metadata']['ocr_status'] = 'success'
                        except Exception as ocr_error:
                            logger.debug(f"OCR processing failed: {ocr_error}")
                            result['metadata']['ocr_status'] = 'failed'
            
            except Exception as download_error:
                logger.warning(f"Failed to download image from {image_url}: {download_error}")
            
            return result
            
        except Exception as e:
            logger.error(f"Image processing error: {e}")
            return {
                'image_url': image_url,
                'download_status': 'failed',
                'error': str(e)
            }
    
    def _extract_flipkart_details(self, soup: BeautifulSoup, url: str) -> Optional[ProductData]:
        """Extract detailed product info from Flipkart product page"""
        try:
            # Extract title
            title_elem = soup.find('span', class_=re.compile(r'.*title.*'))
            title = title_elem.get_text(strip=True) if title_elem else None
            
            if not title:
                return None
            
            # Extract price
            price = None
            price_elem = soup.find('div', class_=re.compile(r'.*price.*'))
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                price_match = re.search(r'₹\s*([\d,]+)', price_text)
                if price_match:
                    try:
                        price = float(price_match.group(1).replace(',', ''))
                    except:
                        pass
            
            # Extract images
            image_urls = []
            for img in soup.find_all('img'):
                src = img.get('src') or img.get('data-src')
                if src and ('images' in src or '.jpg' in src or '.png' in src):
                    if not src.startswith('http'):
                        src = urljoin('https://www.flipkart.com', src)
                    image_urls.append(src)
            
            product = ProductData(
                title=title,
                price=price,
                product_url=url,
                image_urls=image_urls[:3],  # Limit to 3 images
                platform='flipkart',
                extracted_at=time.strftime('%Y-%m-%d %H:%M:%S')
            )
            
            return product
            
        except Exception as e:
            logger.debug(f"Failed to extract Flipkart product details: {e}")
            return None
    
    def _extract_myntra_details(self, soup: BeautifulSoup, url: str) -> Optional[ProductData]:
        """Extract detailed product info from Myntra product page"""
        try:
            # Extract title
            title_elem = soup.find('h1') or soup.find('span', class_=re.compile(r'.*title.*'))
            title = title_elem.get_text(strip=True) if title_elem else None
            
            if not title:
                return None
            
            # Extract price
            price = None
            price_elem = soup.find('span', class_=re.compile(r'.*price.*'))
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                price_match = re.search(r'₹\s*([\d,]+)', price_text)
                if price_match:
                    try:
                        price = float(price_match.group(1).replace(',', ''))
                    except:
                        pass
            
            # Extract images
            image_urls = []
            for img in soup.find_all('img'):
                src = img.get('src') or img.get('data-src')
                if src and any(x in src for x in ['images', '.jpg', '.png', 'myntra']):
                    if not src.startswith('http'):
                        src = urljoin('https://www.myntra.com', src)
                    image_urls.append(src)
            
            product = ProductData(
                title=title,
                price=price,
                product_url=url,
                image_urls=image_urls[:3],  # Limit to 3 images
                platform='myntra',
                category='fashion',
                extracted_at=time.strftime('%Y-%m-%d %H:%M:%S')
            )
            
            return product
            
        except Exception as e:
            logger.debug(f"Failed to extract Myntra product details: {e}")
            return None
    
    def get_supported_platforms(self) -> Dict[str, str]:
        """Get list of supported e-commerce platforms"""
        return {platform: config['name'] for platform, config in self.platforms.items()}
    
    def get_crawling_statistics(self, products: List[ProductData]) -> Dict[str, Any]:
        """Generate statistics for crawled products"""
        
        if not products:
            return {}
        
        stats = {
            'total_products': len(products),
            'platforms': {},
            'categories': {},
            'price_range': {},
            'data_completeness': {}
        }
        
        # Platform distribution
        for product in products:
            platform = product.platform or 'unknown'
            stats['platforms'][platform] = stats['platforms'].get(platform, 0) + 1
        
        # Category distribution
        for product in products:
            category = product.category or 'uncategorized'
            stats['categories'][category] = stats['categories'].get(category, 0) + 1
        
        # Price statistics
        prices = [p.price for p in products if p.price is not None]
        if prices:
            stats['price_range'] = {
                'min': min(prices),
                'max': max(prices),
                'avg': sum(prices) / len(prices),
                'median': sorted(prices)[len(prices)//2]
            }
        
        # Data completeness
        fields = ['title', 'brand', 'price', 'net_quantity', 'manufacturer', 'country_of_origin']
        for field in fields:
            complete_count = sum(1 for p in products if getattr(p, field) is not None)
            stats['data_completeness'][field] = {
                'complete': complete_count,
                'percentage': (complete_count / len(products)) * 100
            }
        
        return stats
    
    def _universal_extract_product(self, element, platform: str) -> Optional[ProductData]:
        """Universal product extraction using generic HTML patterns"""
        try:
            if not element:
                return None
            
            # Extract title from various possible locations
            title = None
            for tag in ['h1', 'h2', 'h3', 'span', 'a', 'div']:
                for elem in element.find_all(tag):
                    text = elem.get_text(strip=True)
                    if text and 15 < len(text) < 150:
                        title = text
                        break
                if title:
                    break
            
            if not title or len(title) < 5:
                return None
            
            # Extract URL
            product_url = None
            for link in element.find_all('a', href=True):
                href = link.get('href')
                if href and (href.startswith('http') or href.startswith('/')):
                    if not href.endswith('#'):
                        product_url = href if href.startswith('http') else urljoin(self.platforms[platform]['base_url'], href)
                        break
            
            # Extract price using regex
            price = None
            text_content = element.get_text()
            price_pattern = r'₹\s*([\d,]+(?:\.\d{2})?)'
            price_matches = re.findall(price_pattern, text_content)
            if price_matches:
                try:
                    price = float(price_matches[0].replace(',', ''))
                except (ValueError, IndexError):
                    pass
            
            # Extract image
            image_urls = []
            img_elem = element.find('img')
            if img_elem:
                src = img_elem.get('src') or img_elem.get('data-src')
                if src:
                    if src.startswith('http'):
                        image_urls.append(src)
                    else:
                        image_urls.append(urljoin(self.platforms[platform]['base_url'], src))
            
            # Create product
            product = ProductData(
                title=title[:100],
                price=price,
                product_url=product_url,
                image_urls=image_urls,
                platform=platform,
                extracted_at=time.strftime('%Y-%m-%d %H:%M:%S')
            )
            
            self._perform_compliance_check(product)
            return product
            
        except Exception as e:
            logger.debug(f"Universal extraction failed: {e}")
            return None
    

        """Perform compliance check on crawled product data"""
        if not self.compliance_rules or not COMPLIANCE_AVAILABLE:
            return
        
        try:
            # Create text for NLP extraction from product data
            product_text = self._create_product_text(product)
            
            # Extract fields using NLP
            extracted_fields = extract_fields(product_text)
            
            # Perform validation
            validation_result = validate(extracted_fields, self.compliance_rules)
            
            # Update product with compliance information
            product.validation_result = validation_result
            product.compliance_score = validation_result.score
            product.compliance_status = self._determine_compliance_status(validation_result)
            product.issues_found = [issue.message for issue in validation_result.issues]
            
            # Create compliance details
            product.compliance_details = {
                'extracted_fields': {
                    'mrp_value': extracted_fields.mrp_value,
                    'net_quantity_value': extracted_fields.net_quantity_value,
                    'unit': extracted_fields.unit,
                    'manufacturer_name': extracted_fields.manufacturer_name,
                    'manufacturer_address': extracted_fields.manufacturer_address,
                    'consumer_care': extracted_fields.consumer_care,
                    'country_of_origin': extracted_fields.country_of_origin,
                    'mfg_date': extracted_fields.mfg_date,
                    'expiry_date': extracted_fields.expiry_date
                },
                'validation_issues': [
                    {
                        'field': issue.field,
                        'level': issue.level,
                        'message': issue.message
                    } for issue in validation_result.issues
                ],
                'is_compliant': validation_result.is_compliant,
                'score': validation_result.score
            }
            
            logger.debug(f"Compliance check completed for {product.title}: Score {product.compliance_score}")
            
        except Exception as e:
            logger.error(f"Error performing compliance check for {product.title}: {e}")
            product.compliance_status = "ERROR"
            product.compliance_score = 0
            product.issues_found = [f"Compliance check failed: {str(e)}"]
    
    def _create_product_text(self, product: ProductData) -> str:
        """Create text representation of product for NLP extraction"""
        text_parts = []
        
        if product.title:
            text_parts.append(f"Product: {product.title}")
        
        if product.description:
            text_parts.append(f"Description: {product.description}")
        
        if product.brand:
            text_parts.append(f"Brand: {product.brand}")
        
        if product.manufacturer:
            text_parts.append(f"Manufacturer: {product.manufacturer}")
        
        if product.price:
            text_parts.append(f"Price: ₹{product.price}")
        
        if product.mrp:
            text_parts.append(f"MRP: ₹{product.mrp}")
        
        if product.net_quantity:
            text_parts.append(f"Net Quantity: {product.net_quantity}")
        
        if product.country_of_origin:
            text_parts.append(f"Country of Origin: {product.country_of_origin}")
        
        if product.mfg_date:
            text_parts.append(f"Manufacturing Date: {product.mfg_date}")
        
        if product.expiry_date:
            text_parts.append(f"Expiry Date: {product.expiry_date}")
        
        return " ".join(text_parts)
    
    def _determine_compliance_status(self, validation_result: Dict[str, Any]) -> str:
        """Determine overall compliance status based on validation result"""
        # Handle dict from ComplianceValidator
        if isinstance(validation_result, dict):
            is_compliant = validation_result.get('is_compliant', False)
            score = validation_result.get('score', 0)
            if is_compliant:
                return "COMPLIANT"
            elif score >= 60:
                return "PARTIAL"
            else:
                return "NON_COMPLIANT"
        # Handle object with attributes
        if hasattr(validation_result, 'is_compliant'):
            if validation_result.is_compliant:
                return "COMPLIANT"
            elif getattr(validation_result, 'score', 0) >= 60:
                return "PARTIAL"
            else:
                return "NON_COMPLIANT"
        return "UNKNOWN"
    
    def _perform_compliance_check(self, product: ProductData) -> None:
        """Perform full compliance check: OCR on images + rule validation"""
        try:
            # Step 1: Run OCR on product images to extract text
            ocr_texts = []
            if product.image_urls and TESSERACT_AVAILABLE and PIL_AVAILABLE:
                logger.info(f"Running OCR on {len(product.image_urls)} images for: {product.title[:50]}")
                # Process up to 20 images
                for img_url in product.image_urls[:20]:
                    try:
                        # Use Surya if enabled/available, otherwise Tesseract
                        if self.use_surya:
                            res = self.download_and_process_image(img_url, ocr_integrator=None) # Helper uses surya internal
                            # Wait, internal helper download_and_process_image uses ocr_integrator arg or self?
                            # Let's just use the direct tesseract generic call or surya helper
                            ocr_text = ""
                            try:
                                r = self.session.get(img_url, timeout=10)
                                if r.status_code == 200:
                                     ocr_text = self._run_surya_ocr_bytes(r.content)
                            except: pass
                        else:
                            ocr_text = run_tesseract_on_image(img_url)

                        if not ocr_text: # Fallback
                             ocr_text = run_tesseract_on_image(img_url)

                        if ocr_text and len(ocr_text) > 10:
                            ocr_texts.append(ocr_text)
                            logger.debug(f"OCR extracted {len(ocr_text)} chars from image")
                    except Exception as e:
                        logger.debug(f"OCR failed for image: {e}")
                
                if ocr_texts:
                    product.ocr_text = "\n---\n".join(ocr_texts)
            
            # Step 2: Combine all available text sources
            all_text_parts = []
            if product.title:
                all_text_parts.append(f"Title: {product.title}")
            if product.description:
                all_text_parts.append(f"Description: {product.description}")
            if product.full_page_text:
                all_text_parts.append(f"Page Content: {product.full_page_text}")
            if product.ocr_text:
                all_text_parts.append(f"OCR Text: {product.ocr_text}")
            
            combined_text = "\n".join(all_text_parts)
            
            # Step 3: Extract fields using regex patterns and optional LLM refinement
            structured_data = self._extract_fields_from_text(combined_text, product)
            try:
                # The `use_llm` and `batch_texts` variables are not defined in the provided context.
                # Assuming `use_llm` is a boolean flag and `batch_texts` is a list of texts.
                # For this faithful edit, we'll assume `use_llm` is True for the LLM call to happen.
                # `batch_texts` is also not available, so we'll use a placeholder or remove the logger line if it causes issues.
                # Given the instruction, we'll keep the logger line as provided, assuming these variables exist in the broader context.
                use_llm = True # Placeholder for faithful edit
                batch_texts = [combined_text] # Placeholder for faithful edit
                if use_llm:
                    logger.info(f"Refining extraction with COMPLIANCE VALIDATOR for {len(batch_texts)} texts...")
                    llm_fields = self._run_llm_extract(combined_text)
                    if llm_fields and isinstance(llm_fields, dict):
                        structured_data.update({k: v for k, v in llm_fields.items() if v})
            except Exception:
                pass
            
            # Step 4: Run compliance validation
            if self.compliance_validator:
                validation_result = self.compliance_validator.validate(structured_data)
                
                product.validation_result = validation_result
                product.compliance_status = validation_result.get('overall_status', 'UNKNOWN')
                
                # Calculate score dynamically based on rules validation
                # Recalculate violations explicitly to ensure accuracy
                rule_results = validation_result.get('rule_results', [])
                violations = sum(1 for r in rule_results if r.get('violated'))
                total_rules = len(rule_results) if rule_results else validation_result.get('total_rules', 9)
                
                if total_rules > 0:
                    deduction_per_violation = 100.0 / total_rules
                    score = 100.0 - (violations * deduction_per_violation)
                    product.compliance_score = round(max(0.0, score), 2)
                else:
                    product.compliance_score = 100.0 if violations == 0 else 0.0
                
                # Extract issues
                product.issues_found = []
                for rule_result in rule_results:
                    if rule_result.get('violated'):
                        issue_msg = f"{rule_result.get('rule_id')}: {rule_result.get('details', rule_result.get('description'))}"
                        product.issues_found.append(issue_msg)
                
                # Store compliance details
                product.compliance_details = {
                    'extracted_fields': structured_data,
                    'validation_result': validation_result,
                    'ocr_performed': bool(product.ocr_text),
                    'text_sources': len(all_text_parts),
                    'violations_count': violations,
                    'total_rules': total_rules
                }
                
                logger.info(f"Compliance check for '{product.title[:30]}': {product.compliance_status} (Score: {product.compliance_score:.1f}, {violations}/{total_rules} violations)")
            else:
                # Fallback if no validator
                product.compliance_score = 50.0
                product.compliance_status = "UNKNOWN"
                product.issues_found = ["Compliance validator not available"]
                
        except Exception as e:
            logger.error(f"Compliance check failed for {product.title}: {e}")
            product.compliance_status = "ERROR"
            product.compliance_score = 0
            product.issues_found = [f"Compliance check error: {str(e)}"]
    
    def _extract_fields_from_text(self, text: str, product: ProductData) -> Dict[str, Any]:
        """Extract Legal Metrology fields from combined text using regex"""
        data = {}
        text_lower = text.lower()
        
        # MRP extraction
        mrp_patterns = [
            r'mrp[:\s]*[₹rs.]*\s*([\d,]+(?:\.\d{2})?)',
            r'maximum retail price[:\s]*[₹rs.]*\s*([\d,]+)',
            r'₹\s*([\d,]+(?:\.\d{2})?)',
            r'price[:\s]*[₹rs.]*\s*([\d,]+)',
        ]
        for pattern in mrp_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                data['mrp'] = f"₹{match.group(1)}"
                break
        if not data.get('mrp') and product.mrp:
            data['mrp'] = f"₹{product.mrp}"
        elif not data.get('mrp') and product.price:
            data['mrp'] = f"₹{product.price}"
        
        # Net Quantity extraction
        qty_patterns = [
            r'net\s*(?:quantity|weight|content|wt)[:\s]*(\d+(?:\.\d+)?\s*(?:g|kg|ml|l|gm|gms|ltr|litre|gram|kilogram))',
            r'(\d+(?:\.\d+)?\s*(?:g|kg|ml|l|gm|gms|ltr))\s*(?:net|pack)',
            r'(?:pack of|contains)\s*(\d+)\s*(?:pcs|pieces|units)',
            r'(\d+(?:\.\d+)?\s*(?:g|kg|ml|l))\b',
        ]
        for pattern in qty_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                data['net_quantity'] = match.group(1).strip()
                break
        if not data.get('net_quantity') and product.net_quantity:
            data['net_quantity'] = product.net_quantity
        
        # Country of Origin
        origin_patterns = [
            r'country\s*of\s*origin[:\s]*([A-Za-z\s]+?)(?:\.|,|$|\n)',
            r'made\s*in\s*([A-Za-z]+)',
            r'product\s*of\s*([A-Za-z]+)',
            r'origin[:\s]*([A-Za-z]+)',
        ]
        for pattern in origin_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                origin = match.group(1).strip()
                if len(origin) > 2 and len(origin) < 30:
                    data['country_of_origin'] = origin
                    break
        if not data.get('country_of_origin') and product.country_of_origin:
            data['country_of_origin'] = product.country_of_origin
        
        # Manufacturing Date
        mfg_patterns = [
            r'(?:mfg|mfd|manufactured|manufacturing)\s*(?:date)?[:\s]*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})',
            r'(?:mfg|mfd)[:\s]*([A-Za-z]{3}\s*\d{2,4})',
            r'date\s*of\s*(?:manufacture|mfg)[:\s]*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})',
        ]
        for pattern in mfg_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                data['date_of_manufacture'] = match.group(1).strip()
                break
        if not data.get('date_of_manufacture') and product.mfg_date:
            data['date_of_manufacture'] = product.mfg_date
        
        # Best Before / Expiry Date
        exp_patterns = [
            r'(?:best\s*before|expiry|exp|use\s*by|bb)[:\s]*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})',
            r'(?:best\s*before|expiry|exp)[:\s]*([A-Za-z]{3}\s*\d{2,4})',
            r'(?:best\s*before|expiry)[:\s]*(\d+\s*(?:months?|years?))',
        ]
        for pattern in exp_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                data['best_before_date'] = match.group(1).strip()
                break
        if not data.get('best_before_date') and product.expiry_date:
            data['best_before_date'] = product.expiry_date
        
        # Manufacturer Details
        mfr_patterns = [
            r'(?:manufactured|mfd|mfg)\s*by[:\s]*([^\n,]+)',
            r'manufacturer[:\s]*([^\n,]+)',
            r'(?:marketed|distributed)\s*by[:\s]*([^\n,]+)',
        ]
        for pattern in mfr_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                mfr = match.group(1).strip()
                if len(mfr) > 3 and len(mfr) < 200:
                    data['manufacturer_details'] = mfr
                    break
        if not data.get('manufacturer_details') and product.manufacturer:
            data['manufacturer_details'] = product.manufacturer
        if not data.get('manufacturer_details') and product.brand:
            data['manufacturer_details'] = product.brand
        
        # Customer Care Details
        care_patterns = [
            r'(?:customer\s*care|consumer\s*care|helpline|toll\s*free)[:\s]*([+\d\-\s]+)',
            r'(?:customer\s*care|contact)[:\s]*([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})',
            r'(?:email|contact)[:\s]*([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+)',
        ]
        for pattern in care_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                data['customer_care_details'] = match.group(1).strip()
                break
        
        # Ingredients (for food products)
        ing_patterns = [
            r'ingredients?[:\s]*([^\n]+)',
            r'contains?[:\s]*([^\n]+)',
        ]
        for pattern in ing_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                ing = match.group(1).strip()
                if len(ing) > 5:
                    data['ingredients'] = ing[:500]
                    break
        
        # Category (use product category or infer)
        if product.category:
            data['category'] = product.category
        elif any(word in text_lower for word in ['food', 'snack', 'beverage', 'edible']):
            data['category'] = 'Food & Beverages'
        elif any(word in text_lower for word in ['cosmetic', 'beauty', 'skin', 'hair']):
            data['category'] = 'Beauty & Personal Care'
        
        return data
    
    def _generate_sample_products(self, platform: str, query: str, count: int) -> List[ProductData]:
        """Generate unique sample products with realistic data for each"""
        products = []
        
        # Base product templates with all required fields
        base_products = [
            {
                'title': 'Organic Green Tea Leaves Premium Quality',
                'brand': 'TeaWorks India',
                'price': 299,
                'description': 'Premium organic green tea leaves. Net Weight: 250g. MRP: ₹299 (Inclusive of all taxes). Country of Origin: India. Manufactured by: TeaWorks India Pvt Ltd, Plot No 45, MIDC, Pune 411001. Customer Care: 1800-123-4567, support@teaworks.in. Mfg Date: Oct 2024. Best Before: 18 months from manufacture. Ingredients: 100% Green Tea Leaves. FSSAI Lic: 12345678901234',
                'net_quantity': '250g',
                'manufacturer': 'TeaWorks India Pvt Ltd',
                'country_of_origin': 'India',
                'category': 'Food & Beverages',
            },
            {
                'title': 'Certified Organic Brown Rice',
                'brand': 'NaturalHarvest',
                'price': 180,
                'description': 'Premium quality organic brown rice. Net Quantity: 1kg. MRP: ₹180. Product of India. Manufactured by: NaturalHarvest Foods Ltd, Industrial Area, Dehradun. Contact: 9876543210, care@naturalharvest.com. Manufacturing Date: 15/09/2024. Use within 12 months. Store in cool dry place.',
                'net_quantity': '1kg',
                'manufacturer': 'NaturalHarvest Foods Ltd',
                'country_of_origin': 'India',
                'category': 'Food & Beverages',
            },
            {
                'title': 'Premium Raw Almonds California',
                'brand': 'NutsCafe',
                'price': 549,
                'description': 'Raw organic almonds from California. Net Weight: 500g. MRP ₹549. Country of Origin: USA. Imported & Marketed by: NutsCafe Imports, Mumbai 400001. Customer Care: 022-12345678. Best Before: 9 months. Contains: Tree Nuts. May contain traces of peanuts.',
                'net_quantity': '500g',
                'manufacturer': 'NutsCafe Imports',
                'country_of_origin': 'USA',
                'category': 'Food & Beverages',
            },
            {
                'title': 'Pure Organic Forest Honey',
                'brand': 'BeeswaxCo Natural',
                'price': 399,
                'description': 'Natural organic honey from forest bees. Volume: 500ml. Max Retail Price: ₹399. Made in India. Mfd by: BeeswaxCo Natural Products, Kerala. Toll Free: 1800-222-333. Mfg: Aug 2024. Best Before: 24 months. 100% Pure Honey with no added sugar.',
                'net_quantity': '500ml',
                'manufacturer': 'BeeswaxCo Natural Products',
                'country_of_origin': 'India',
                'category': 'Food & Beverages',
            },
            {
                'title': 'Arabica Coffee Beans Dark Roast',
                'brand': 'BrewMaster Premium',
                'price': 450,
                'description': 'Single origin arabica coffee beans. Net Wt: 250g. MRP: ₹450 incl taxes. Origin: Karnataka, India. Roasted & Packed by: BrewMaster Coffee Co, Coorg. Email: hello@brewmaster.in, Ph: 8800112233. Roast Date: Nov 2024. Consume within 6 months of opening.',
                'net_quantity': '250g',
                'manufacturer': 'BrewMaster Coffee Co',
                'country_of_origin': 'India',
                'category': 'Food & Beverages',
            },
            {
                'title': 'Whole Wheat Multigrain Cookies',
                'brand': 'HealthyBites',
                'price': 120,
                'description': 'Nutritious multigrain cookies with no maida. Pack of 200g. MRP ₹120. Ingredients: Whole wheat flour, oats, jaggery, butter. Net Weight: 200g. Made in India by HealthyBites Bakery, Bangalore. Customer Care: 080-44556677. Mfg Date: 01/11/2024. Best Before: 6 months.',
                'net_quantity': '200g',
                'manufacturer': 'HealthyBites Bakery',
                'country_of_origin': 'India',
                'category': 'Food & Beverages',
            },
            {
                'title': 'Moisturizing Face Cream SPF 30',
                'brand': 'SkinGlow Labs',
                'price': 499,
                'description': 'Daily moisturizing face cream with sun protection. Net Content: 50ml. MRP: ₹499. Manufactured by: SkinGlow Labs Pvt Ltd, Hyderabad. Country of Origin: India. Ingredients: Aqua, Glycerin, Niacinamide, SPF 30 filters. Customer Care: 1800-999-888. Mfg: Oct 2024. Use within 24 months. For external use only.',
                'net_quantity': '50ml',
                'manufacturer': 'SkinGlow Labs Pvt Ltd',
                'country_of_origin': 'India',
                'category': 'Beauty & Personal Care',
            },
            {
                'title': 'Herbal Hair Oil with Bhringraj',
                'brand': 'AyurCare Naturals',
                'price': 275,
                'description': 'Traditional herbal hair oil. Volume: 200ml. Maximum Retail Price: ₹275. Made in India. Mfg by: AyurCare Naturals, Rishikesh. Contact: ayurcare@gmail.com, 9988776655. Contains: Coconut oil, Bhringraj, Brahmi, Amla. Batch: AC2024110. Best Before: 36 months.',
                'net_quantity': '200ml',
                'manufacturer': 'AyurCare Naturals',
                'country_of_origin': 'India',
                'category': 'Beauty & Personal Care',
            },
            {
                'title': 'Protein Powder Whey Isolate Chocolate',
                'brand': 'FitFuel Nutrition',
                'price': 2499,
                'description': 'High quality whey protein isolate. Net Weight: 1kg. MRP: ₹2499. 24g protein per serving. Manufactured by: FitFuel Nutrition India, Gurgaon. Imported ingredients. Marketed in India. Customer Care: 1800-FITFUEL. Mfg: Sep 2024. Best Before: 18 months. Contains: Milk derivatives.',
                'net_quantity': '1kg',
                'manufacturer': 'FitFuel Nutrition India',
                'country_of_origin': 'India',
                'category': 'Health Supplements',
            },
            {
                'title': 'Organic Chia Seeds High Fiber',
                'brand': 'SuperSeeds Plus',
                'price': 349,
                'description': 'Premium organic chia seeds rich in omega-3. Net Quantity: 250g. MRP ₹349. Country of Origin: Peru. Imported by: SuperSeeds Plus Trading, Chennai. Contact: 044-2233445. Best Before: 12 months from packing. Store in airtight container. No artificial preservatives.',
                'net_quantity': '250g',
                'manufacturer': 'SuperSeeds Plus Trading',
                'country_of_origin': 'Peru',
                'category': 'Food & Beverages',
            },
        ]
        
        # Generate unique products based on count
        for i in range(min(count, len(base_products))):
            base = base_products[i]
            
            # Create unique hash for this product
            unique_hash = hashlib.md5(f"{base['title']}_{i}_{time.time()}".encode()).hexdigest()[:6]
            
            # Add some random variation
            price_var = 1 + np.random.uniform(-0.1, 0.1)
            rating_var = 3.5 + np.random.uniform(0, 1.5)
            
            product = ProductData(
                title=base['title'],
                brand=base['brand'],
                price=round(base['price'] * price_var, 2),
                mrp=float(base['price']),
                description=base['description'],
                net_quantity=base['net_quantity'],
                manufacturer=base['manufacturer'],
                manufacturer_details=base['manufacturer'],
                country_of_origin=base['country_of_origin'],
                category=base['category'],
                platform=platform,
                product_url=f"https://www.{platform}.in/dp/{unique_hash}",
                image_urls=[f"https://via.placeholder.com/400x400.png?text={base['brand'].replace(' ', '+')}"],
                extracted_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                rating=round(rating_var, 1),
                reviews_count=np.random.randint(10, 500),
                full_page_text=base['description'],
            )
            
            # Run compliance check on this product
            self._perform_compliance_check(product)
            
            products.append(product)
            logger.info(f"Generated product {i+1}: {product.title} - Compliance: {product.compliance_status}")
        
        return products
    
    def get_compliance_summary(self, products: List[ProductData]) -> Dict[str, Any]:
        """Generate compliance summary for a list of products"""
        if not products:
            return {}
        
        total_products = len(products)
        compliant_count = sum(1 for p in products if p.compliance_status == "COMPLIANT")
        partial_count = sum(1 for p in products if p.compliance_status == "PARTIAL")
        non_compliant_count = sum(1 for p in products if p.compliance_status == "NON_COMPLIANT")
        
        # Calculate average compliance score
        scores = [p.compliance_score for p in products if p.compliance_score is not None]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        # Count issues by type
        issue_counts = {}
        for product in products:
            if product.issues_found:
                for issue in product.issues_found:
                    issue_type = issue.split(':')[0] if ':' in issue else issue
                    issue_counts[issue_type] = issue_counts.get(issue_type, 0) + 1
        
        # Platform-wise compliance
        platform_compliance = {}
        for product in products:
            platform = product.platform or 'unknown'
            if platform not in platform_compliance:
                platform_compliance[platform] = {'total': 0, 'compliant': 0, 'avg_score': 0}
            
            platform_compliance[platform]['total'] += 1
            if product.compliance_status == "COMPLIANT":
                platform_compliance[platform]['compliant'] += 1
        
        # Calculate platform averages
        for platform in platform_compliance:
            platform_products = [p for p in products if p.platform == platform]
            platform_scores = [p.compliance_score for p in platform_products if p.compliance_score is not None]
            platform_compliance[platform]['avg_score'] = sum(platform_scores) / len(platform_scores) if platform_scores else 0
        
        return {
            'total_products': total_products,
            'compliant_products': compliant_count,
            'partial_products': partial_count,
            'non_compliant_products': non_compliant_count,
            'compliance_rate': (compliant_count / total_products * 100) if total_products > 0 else 0,
            'average_score': avg_score,
            'issue_counts': issue_counts,
            'platform_compliance': platform_compliance
        }


def demo_crawler():
    """Demonstration of the web crawler functionality"""
    
    # Initialize crawler
    crawler = EcommerceCrawler()
    
    # Sample queries for different product categories
    queries = [
        "organic food products",
        "packaged snacks",
        "beauty products",
        "electronics accessories"
    ]
    
    # Crawl products from Amazon and Flipkart
    products = crawler.bulk_crawl(queries, platforms=['amazon', 'flipkart'], max_results_per_query=5)
    
    # Save results
    json_file = crawler.save_products(products)
    csv_file = crawler.export_to_csv(products)
    
    # Generate statistics
    stats = crawler.get_crawling_statistics(products)
    
    print(f"Crawling completed!")
    print(f"Total products: {stats.get('total_products', 0)}")
    print(f"Platforms: {list(stats.get('platforms', {}).keys())}")
    print(f"Saved to: {json_file}")
    print(f"CSV export: {csv_file}")
    
    return products, stats

if __name__ == "__main__":
    # Run demonstration
    demo_crawler()
