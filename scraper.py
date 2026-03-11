# utils/scraper.py
import requests
from bs4 import BeautifulSoup
import time
from typing import List, Dict, Any, Optional
import logging
from urllib.parse import urljoin, urlparse
import random

# লগিং সেটআপ
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebScraper:
    """ওয়েব স্ক্র্যাপার ক্লাস - শুধু অনুমোদিত সাইট থেকে ডাটা আনে"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.timeout = 10
        self.retry_count = 2
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def _make_request(self, url: str) -> Optional[requests.Response]:
        """রিকোয়েস্ট পাঠানোর জন্য অভ্যন্তরীণ ফাংশন"""
        for attempt in range(self.retry_count):
            try:
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < self.retry_count - 1:
                    time.sleep(random.uniform(1, 3))  # র্যান্ডম ডেলay
                else:
                    logger.error(f"All attempts failed for {url}")
                    return None
        return None
    
    def _extract_headlines_from_tags(self, soup: BeautifulSoup, tags: List[str], limit: int) -> List[str]:
        """ট্যাগ থেকে হেডলাইন এক্সট্রাক্ট করে"""
        headlines = []
        for tag in tags:
            for elem in soup.find_all(tag)[:limit * 2]:  # একটু বেশি নিই
                text = elem.get_text().strip()
                # ফিল্টার: খুব ছোট বা খুব বড় বাদ দিই
                if text and 10 <= len(text) <= 150 and text not in headlines:
                    headlines.append(text)
                if len(headlines) >= limit:
                    break
            if len(headlines) >= limit:
                break
        return headlines[:limit]
    
    def _extract_articles_from_selectors(self, soup: BeautifulSoup, selectors: List[str], base_url: str, limit: int) -> List[Dict]:
        """সিলেক্টর ব্যবহার করে আর্টিকেল এক্সট্রাক্ট করে"""
        articles = []
        
        # বিভিন্ন সিলেক্টর ব্যবহার করে চেষ্টা করি
        for selector in selectors:
            elements = soup.select(selector)[:limit * 2]
            for elem in elements:
                title_elem = elem.find(['h1', 'h2', 'h3', 'h4']) or elem.find('a')
                link_elem = elem.find('a')
                
                if title_elem and link_elem:
                    title = title_elem.get_text().strip()
                    link = link_elem.get('href', '')
                    
                    # ভ্যালিডেশন
                    if title and len(title) >= 5:
                        # লিংক ফিক্স করা
                        if link and not link.startswith('http'):
                            link = urljoin(base_url, link)
                        
                        # ডুপ্লিকেট চেক
                        if not any(a['url'] == link for a in articles):
                            articles.append({
                                'title': title,
                                'url': link,
                                'source': urlparse(base_url).netloc
                            })
                            
                            if len(articles) >= limit:
                                return articles
        
        return articles[:limit]
    
    def fetch_headlines(self, url: str, limit: int = 5) -> List[str]:
        """ওয়েবসাইট থেকে হেডলাইন সংগ্রহ করে"""
        logger.info(f"Fetching headlines from {url}")
        
        try:
            response = self._make_request(url)
            if not response:
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # হেডলাইন খোঁজার জন্য বিভিন্ন ট্যাগ
            headlines = self._extract_headlines_from_tags(
                soup, 
                ['h1', 'h2', 'h3', '.headline', '.title', '.card-title'], 
                limit
            )
            
            logger.info(f"Found {len(headlines)} headlines from {url}")
            return headlines
            
        except Exception as e:
            logger.error(f"Headline scraping error for {url}: {e}")
            return []
    
    def fetch_articles(self, url: str, limit: int = 3) -> List[Dict]:
        """আর্টিকেল সংগ্রহ করে (শিরোনাম + লিংক)"""
        logger.info(f"Fetching articles from {url}")
        
        try:
            response = self._make_request(url)
            if not response:
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # বিভিন্ন সিলেক্টর ব্যবহার করে চেষ্টা
            selectors = [
                'article',
                '.post',
                '.card',
                '.story',
                '.news-item',
                '.article-card',
                'div[class*="post"]',
                'div[class*="article"]'
            ]
            
            articles = self._extract_articles_from_selectors(soup, selectors, url, limit)
            
            logger.info(f"Found {len(articles)} articles from {url}")
            return articles
            
        except Exception as e:
            logger.error(f"Article scraping error for {url}: {e}")
            return []
    
    def search_website(self, url: str, keyword: str) -> List[str]:
        """ওয়েবসাইটে কীওয়ার্ড সার্চ করে"""
        logger.info(f"Searching for '{keyword}' in {url}")
        
        try:
            response = self._make_request(url)
            if not response:
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            results = []
            # সার্চের জন্য ট্যাগ
            search_tags = ['h1', 'h2', 'h3', 'p', '.description', '.summary']
            
            for tag in search_tags:
                elements = soup.select(tag) if '.' in tag else soup.find_all(tag)
                
                for elem in elements:
                    text = elem.get_text().strip()
                    if keyword.lower() in text.lower() and len(text) < 250:
                        # কনটেক্সট সহ দেখাই
                        context = self._get_search_context(text, keyword)
                        if context not in results:
                            results.append(context)
                            
                        if len(results) >= 5:
                            logger.info(f"Found {len(results)} results for '{keyword}'")
                            return results
            
            logger.info(f"Found {len(results)} results for '{keyword}'")
            return results
            
        except Exception as e:
            logger.error(f"Search error for {url}: {e}")
            return []
    
    def _get_search_context(self, text: str, keyword: str, context_length: int = 100) -> str:
        """সার্চ রেজাল্টে কীওয়ার্ডের কনটেক্সট দেখায়"""
        try:
            keyword_lower = keyword.lower()
            text_lower = text.lower()
            index = text_lower.find(keyword_lower)
            
            if index == -1:
                return text[:150] + "..."
            
            # কীওয়ার্ডের চারপাশ থেকে কনটেক্সট নিই
            start = max(0, index - 30)
            end = min(len(text), index + len(keyword) + 30)
            
            context = text[start:end]
            if start > 0:
                context = "..." + context
            if end < len(text):
                context = context + "..."
                
            return context
        except:
            return text[:150] + "..."
    
    def get_site_metadata(self, url: str) -> Dict[str, Any]:
        """সাইটের মেটাডাটা সংগ্রহ করে"""
        try:
            response = self._make_request(url)
            if not response:
                return {}
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            metadata = {
                'title': soup.find('title').get_text().strip() if soup.find('title') else None,
                'description': None,
                'keywords': None,
                'og_title': None,
                'og_image': None
            }
            
            # মেটা ট্যাগ থেকে ডাটা
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc and meta_desc.get('content'):
                metadata['description'] = meta_desc['content']
            
            meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
            if meta_keywords and meta_keywords.get('content'):
                metadata['keywords'] = meta_keywords['content']
            
            # Open Graph ট্যাগ
            og_title = soup.find('meta', property='og:title')
            if og_title and og_title.get('content'):
                metadata['og_title'] = og_title['content']
            
            og_image = soup.find('meta', property='og:image')
            if og_image and og_image.get('content'):
                metadata['og_image'] = og_image['content']
            
            return metadata
            
        except Exception as e:
            logger.error(f"Metadata scraping error: {e}")
            return {}

# স্ক্র্যাপারের ইনস্ট্যান্স
scraper = WebScraper()

# এক্সপোর্ট ফাংশন
def fetch_headlines(url: str, limit: int = 5) -> List[str]:
    """হেডলাইন ফেচ করার জন্য হেল্পার ফাংশন"""
    return scraper.fetch_headlines(url, limit)

def fetch_articles(url: str, limit: int = 3) -> List[Dict]:
    """আর্টিকেল ফেচ করার জন্য হেল্পার ফাংশন"""
    return scraper.fetch_articles(url, limit)

def search_website(url: str, keyword: str) -> List[str]:
    """সার্চ করার জন্য হেল্পার ফাংশন"""
    return scraper.search_website(url, keyword)

def get_website_metadata(url: str) -> Dict[str, Any]:
    """সাইট মেটাডাটা পাওয়ার ফাংশন"""
    return scraper.get_site_metadata(url)

# ব্যাচ প্রসেসিং ফাংশন
def fetch_multiple_headlines(websites: Dict[str, Dict], limit: int = 3) -> Dict[str, Any]:
    """একাধিক সাইট থেকে হেডলাইন সংগ্রহ করে"""
    results = {}
    for name, info in websites.items():
        if info.get('active', True):
            headlines = fetch_headlines(info['url'], limit)
            if headlines:
                results[name] = {
                    'name': info['name'],
                    'headlines': headlines
                }
            time.sleep(1)  # রেট লিমিটিং
    return results