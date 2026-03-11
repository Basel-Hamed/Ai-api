from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
import uvicorn
import os
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from googletrans import Translator
import json
from pathlib import Path

app = FastAPI(
    title="প্রাইভেট ওয়েবসাইট API",
    description="শুধুমাত্র আপনার দেওয়া ওয়েবসাইট থেকে তথ্য আনে",
    version="1.0.0"
)

# CORS সেটআপ
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# অনুবাদক
translator = Translator()

# ================== কনফিগারেশন ==================

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
    },
    "ndtv": {
        "name": "NDTV",
        "url": "https://www.ndtv.com",
        "category": "news",
        "language": "en"
    },
    "reuters": {
        "name": "Reuters",
        "url": "https://www.reuters.com",
        "category": "news",
        "language": "en"
    },
    "apnews": {
        "name": "AP News",
        "url": "https://apnews.com",
        "category": "news",
        "language": "en"
    }
}

# ================== ইউটিলিটি ফাংশন ==================

def fetch_headlines(url: str, limit: int = 5):
    """একটি ওয়েবসাইট থেকে হেডলাইন স্ক্র্যাপ করে"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        headlines = []
        
        # কমন হেডলাইন সিলেক্টর
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

def fetch_articles(url: str, limit: int = 3):
    """একটি ওয়েবসাইট থেকে আর্টিকেল লিংক স্ক্র্যাপ করে"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        articles = []
        
        # লিংক খোঁজা
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

def search_website(url: str, keyword: str):
    """একটি ওয়েবসাইটে কীওয়ার্ড সার্চ করে"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        results = []
        text_content = soup.get_text()
        
        if keyword.lower() in text_content.lower():
            # কনটেক্সট খোঁজা
            sentences = text_content.split('.')
            for sentence in sentences:
                if keyword.lower() in sentence.lower():
                    results.append(sentence.strip())
                    if len(results) >= 5:
                        break
        
        return results[:5]
    except Exception as e:
        return []

def translate_text(text: str, dest: str = "bn"):
    """টেক্সট বাংলায় অনুবাদ করে"""
    try:
        result = translator.translate(text, dest=dest)
        return result.text
    except:
        return text

def translate_batch(texts: list, dest: str = "bn"):
    """একাধিক টেক্সট অনুবাদ করে"""
    results = []
    for text in texts:
        try:
            translated = translate_text(text, dest)
            results.append(translated)
        except:
            results.append(text)
    return results

# ================== API এন্ডপয়েন্ট ==================

@app.get("/")
async def root():
    sites = ALLOWED_WEBSITES
    return {
        "name": "🔒 প্রাইভেট ওয়েবসাইট API",
        "description": "শুধুমাত্র আপনার কনফিগার করা সাইট থেকে তথ্য আনে",
        "total_sites": len(sites),
        "endpoints": {
            "সাইট লিস্ট": "/sites",
            "সাইট অনুযায়ী": "/sites/{site_name}",
            "হেডলাইন": "/headlines/{site_name}",
            "আর্টিকেল": "/articles/{site_name}",
            "সার্চ": "/search/{site_name}?q=কীওয়ার্ড",
            "অনুবাদ": "/translate?text=hello"
        }
    }

@app.get("/sites")
async def list_sites(category: Optional[str] = None):
    sites = ALLOWED_WEBSITES
    
    if category:
        filtered = {}
        for name, info in sites.items():
            if info["category"] == category:
                filtered[name] = info
        sites = filtered
    
    simplified = {}
    for name, info in sites.items():
        simplified[name] = {
            "name": info["name"],
            "category": info["category"],
            "language": info["language"]
        }
    
    return {
        "total": len(simplified),
        "categories": list(set(info["category"] for info in ALLOWED_WEBSITES.values())),
        "sites": simplified
    }

@app.get("/sites/{site_name}")
async def site_info(site_name: str):
    if site_name not in ALLOWED_WEBSITES:
        raise HTTPException(status_code=403, detail=f"'{site_name}' অনুমোদিত নয়")
    
    info = ALLOWED_WEBSITES[site_name]
    return {
        "name": site_name,
        "info": info
    }

@app.get("/headlines/{site_name}")
async def get_headlines(
    site_name: str,
    limit: int = Query(5, ge=1, le=10),
    translate: bool = Query(True)
):
    if site_name not in ALLOWED_WEBSITES:
        raise HTTPException(status_code=403, detail=f"'{site_name}' অনুমোদিত নয়")
    
    info = ALLOWED_WEBSITES[site_name]
    
    try:
        headlines = fetch_headlines(info["url"], limit)
        
        result = {
            "site": site_name,
            "name": info["name"],
            "url": info["url"],
            "category": info["category"],
            "timestamp": datetime.now().isoformat(),
            "headlines": headlines
        }
        
        if translate and headlines:
            bangla = translate_batch(headlines)
            result["bangla"] = bangla
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ডাটা আনা যায়নি: {str(e)}")

@app.get("/articles/{site_name}")
async def get_articles(
    site_name: str,
    limit: int = Query(3, ge=1, le=5),
    translate_titles: bool = Query(True)
):
    if site_name not in ALLOWED_WEBSITES:
        raise HTTPException(status_code=403, detail=f"'{site_name}' অনুমোদিত নয়")
    
    info = ALLOWED_WEBSITES[site_name]
    
    try:
        articles = fetch_articles(info["url"], limit)
        
        result = {
            "site": site_name,
            "name": info["name"],
            "url": info["url"],
            "articles": articles
        }
        
        if translate_titles and articles:
            titles = [a["title"] for a in articles]
            bangla_titles = translate_batch(titles)
            
            for i, article in enumerate(articles):
                article["bangla_title"] = bangla_titles[i]
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/search/{site_name}")
async def search_site(
    site_name: str,
    q: str = Query(..., description="কী খুঁজবেন?"),
    translate_results: bool = Query(True)
):
    if site_name not in ALLOWED_WEBSITES:
        raise HTTPException(status_code=403, detail=f"'{site_name}' অনুমোদিত নয়")
    
    info = ALLOWED_WEBSITES[site_name]
    
    try:
        results = search_website(info["url"], q)
        
        response = {
            "site": site_name,
            "keyword": q,
            "matches": len(results),
            "results": results
        }
        
        if translate_results and results:
            bangla = translate_batch(results)
            response["bangla"] = bangla
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/translate")
async def translate(text: str = Query(...), dest: str = "bn"):
    try:
        translated = translate_text(text, dest)
        return {"original": text, "translated": translated}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/categories")
async def list_categories():
    categories = {}
    for name, info in ALLOWED_WEBSITES.items():
        cat = info["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append({
            "name": name,
            "title": info["name"]
        })
    return categories

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    print("\n" + "="*50)
    print("🔒 প্রাইভেট ওয়েবসাইট API চালু হচ্ছে...")
    print(f"📊 অনুমোদিত সাইট: {len(ALLOWED_WEBSITES)} টি")
    for name, info in ALLOWED_WEBSITES.items():
        print(f"   ✓ {name}: {info['name']} ({info['category']})")
    print("="*50)
    
    port = int(os.getenv("PORT", 8000))
    print(f"📍 পোর্ট: {port}")
    print("="*50 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=port)
