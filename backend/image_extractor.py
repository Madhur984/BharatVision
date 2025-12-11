"""
Image Extraction Module
Handles downloading and processing images from crawler links
"""

import requests
import logging
import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from PIL import Image
from io import BytesIO
import hashlib
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class ImageExtractor:
    """Extract and download images from URLs"""
    
    def __init__(self, cache_dir: str = "app/data/crawled_images", max_retries: int = 3):
        """
        Initialize image extractor
        
        Args:
            cache_dir: Directory to cache downloaded images
            max_retries: Maximum retry attempts for failed downloads
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.download_log = self.cache_dir / "download_log.json"
        self._load_download_log()
    
    def _load_download_log(self):
        """Load existing download log"""
        if self.download_log.exists():
            try:
                with open(self.download_log, 'r') as f:
                    self.log_data = json.load(f)
            except Exception as e:
                logger.warning(f"Could not load download log: {e}")
                self.log_data = {}
        else:
            self.log_data = {}
    
    def _save_download_log(self):
        """Save download log"""
        try:
            with open(self.download_log, 'w') as f:
                json.dump(self.log_data, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save download log: {e}")
    
    def _generate_filename(self, url: str, index: int = 0) -> str:
        """Generate unique filename for image"""
        # Create hash of URL
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        # Get file extension from URL or default to jpg
        ext = self._get_extension(url)
        return f"img_{url_hash}_{index}{ext}"
    
    def _get_extension(self, url: str) -> str:
        """Extract file extension from URL"""
        try:
            # Remove query parameters
            path = url.split('?')[0]
            # Get extension
            ext = Path(path).suffix.lower()
            # Validate extension
            valid_exts = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']
            return ext if ext in valid_exts else '.jpg'
        except:
            return '.jpg'
    
    def download_image(self, url: str, timeout: int = 10) -> Optional[Dict[str, Any]]:
        """
        Download single image from URL
        
        Args:
            url: Image URL
            timeout: Request timeout in seconds
            
        Returns:
            Dict with image metadata or None if failed
        """
        if not url:
            return None
        
        try:
            # Check if already downloaded
            url_hash = hashlib.md5(url.encode()).hexdigest()
            if url_hash in self.log_data:
                return self.log_data[url_hash]
            
            # Download image
            for attempt in range(self.max_retries):
                try:
                    response = self.session.get(url, timeout=timeout, stream=True)
                    
                    if response.status_code == 200:
                        # Validate image
                        img_data = response.content
                        img = Image.open(BytesIO(img_data))
                        
                        # Generate filename
                        filename = self._generate_filename(url)
                        filepath = self.cache_dir / filename
                        
                        # Save image
                        with open(filepath, 'wb') as f:
                            f.write(img_data)
                        
                        # Create metadata
                        metadata = {
                            'url': url,
                            'local_path': str(filepath),
                            'filename': filename,
                            'size': len(img_data),
                            'dimensions': img.size,
                            'format': img.format,
                            'downloaded_at': datetime.now().isoformat()
                        }
                        
                        # Log
                        self.log_data[url_hash] = metadata
                        self._save_download_log()
                        
                        logger.info(f"✓ Downloaded: {filename} ({len(img_data)} bytes)")
                        return metadata
                    
                    elif response.status_code in [429, 503, 502, 504]:
                        if attempt < self.max_retries - 1:
                            wait_time = (attempt + 1) * 2
                            logger.warning(f"Rate limited, retrying in {wait_time}s...")
                            import time
                            time.sleep(wait_time)
                            continue
                
                except Exception as e:
                    logger.debug(f"Attempt {attempt + 1} failed: {str(e)}")
                    if attempt < self.max_retries - 1:
                        import time
                        time.sleep(1)
                        continue
            
            logger.warning(f"✗ Failed to download: {url}")
            return None
            
        except Exception as e:
            logger.error(f"Error downloading image {url}: {str(e)}")
            return None
    
    def download_images(self, urls: List[str], max_images: int = 10) -> List[Dict[str, Any]]:
        """
        Download multiple images
        
        Args:
            urls: List of image URLs
            max_images: Maximum images to download
            
        Returns:
            List of image metadata dictionaries
        """
        results = []
        
        for i, url in enumerate(urls[:max_images]):
            if not url or not isinstance(url, str):
                continue
            
            result = self.download_image(url)
            if result:
                results.append(result)
        
        logger.info(f"Downloaded {len(results)}/{min(len(urls), max_images)} images")
        return results
    
    def extract_images_from_html(self, html: str, base_url: str = "") -> List[str]:
        """
        Extract image URLs from HTML content
        
        Args:
            html: HTML content
            base_url: Base URL for relative links
            
        Returns:
            List of absolute image URLs
        """
        from bs4 import BeautifulSoup
        
        urls = []
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find all img tags
            for img in soup.find_all('img', limit=20):
                src = img.get('src') or img.get('data-src')
                
                if src:
                    # Convert relative URLs to absolute
                    if src.startswith('http'):
                        urls.append(src)
                    elif src.startswith('//'):
                        urls.append('https:' + src)
                    elif base_url and src.startswith('/'):
                        from urllib.parse import urljoin
                        urls.append(urljoin(base_url, src))
            
            logger.info(f"Extracted {len(urls)} image URLs from HTML")
            return urls
            
        except Exception as e:
            logger.error(f"Error extracting images from HTML: {str(e)}")
            return urls
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get statistics about cached images"""
        try:
            total_size = sum(f.stat().st_size for f in self.cache_dir.glob('img_*'))
            total_files = len(list(self.cache_dir.glob('img_*')))
            
            return {
                'total_cached_images': total_files,
                'total_cache_size_mb': round(total_size / (1024 * 1024), 2),
                'cache_directory': str(self.cache_dir)
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {str(e)}")
            return {}
    
    def clear_cache(self):
        """Clear all cached images"""
        try:
            import shutil
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self.log_data = {}
            self._save_download_log()
            logger.info("Cache cleared successfully")
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")


# Convenience functions
def download_images_from_urls(urls: List[str], cache_dir: str = "app/data/crawled_images") -> List[Dict[str, Any]]:
    """Download images from list of URLs"""
    extractor = ImageExtractor(cache_dir)
    return extractor.download_images(urls)


def extract_and_download(html: str, base_url: str = "", cache_dir: str = "app/data/crawled_images") -> List[Dict[str, Any]]:
    """Extract images from HTML and download them"""
    extractor = ImageExtractor(cache_dir)
    urls = extractor.extract_images_from_html(html, base_url)
    return extractor.download_images(urls)
