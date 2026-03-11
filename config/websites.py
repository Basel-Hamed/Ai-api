from typing import Dict, List, Optional

ALLOWED_WEBSITES = {
    "bbc": {
        "name": "BBC News",
        "url": "https://www.bbc.com/news",
        "category": "news",
        "language": "en"
    },
    "cnn": {
        "name": "CNN",
        "url": "https://www.cnn.com",
        "category": "news",
        "language": "en"
    },
    "techcrunch": {
        "name": "TechCrunch",
        "url": "https://techcrunch.com",
        "category": "technology",
        "language": "en"
    },
    "theverge": {
        "name": "The Verge",
        "url": "https://www.theverge.com",
        "category": "technology",
        "language": "en"
    },
    "espn": {
        "name": "ESPN",
        "url": "https://www.espn.com",
        "category": "sports",
        "language": "en"
    }
}

def get_allowed_websites():
    return ALLOWED_WEBSITES

def is_website_allowed(site_name: str) -> bool:
    return site_name in ALLOWED_WEBSITES

def get_website_info(site_name: str) -> Optional[Dict]:
    return ALLOWED_WEBSITES.get(site_name)

def get_websites_by_category(category: str) -> Dict:
    return {name: info for name, info in ALLOWED_WEBSITES.items() 
            if info["category"] == category}
