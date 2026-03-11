import requests
from bs4 import BeautifulSoup
from typing import List, Dict

def fetch_headlines(url: str, limit: int = 5) -> List[str]:
    """Fetch headlines from a website"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        headlines = []
        selectors = ['h1', 'h2', 'h3', '.headline', '.title', '.article-title']
        
        for selector in selectors:
            elements = soup.select(selector)
            for elem in elements[:limit]:
                text = elem.get_text().strip()
                if text and len(text) > 20 and text not in headlines:
                    headlines.append(text)
                    if len(headlines) >= limit:
                        break
            if len(headlines) >= limit:
                break
        
        return headlines[:limit]
    except Exception as e:
        return [f"Error: {str(e)}"]

def fetch_articles(url: str, limit: int = 3) -> List[Dict]:
    """Fetch article links from a website"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        articles = []
        for link in soup.find_all('a', href=True)[:limit*3]:
            href = link['href']
            text = link.get_text().strip()
            
            if text and len(text) > 15 and href.startswith('http'):
                articles.append({
                    "title": text,
                    "url": href
                })
                if len(articles) >= limit:
                    break
        
        return articles[:limit]
    except Exception as e:
        return []

def search_website(url: str, keyword: str) -> List[str]:
    """Search for keyword in website content"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        results = []
        text_content = soup.get_text()
        
        if keyword.lower() in text_content.lower():
            sentences = text_content.split('.')
            for sentence in sentences:
                if keyword.lower() in sentence.lower():
                    results.append(sentence.strip())
                    if len(results) >= 5:
                        break
        
        return results[:5]
    except Exception as e:
        return []
