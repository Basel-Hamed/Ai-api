from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, Dict, List
import uvicorn
import os
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from googletrans import Translator

# ================== FastAPI App ==================
app = FastAPI(
    title="সাইবার সিকিউরিটি API",
    description="শুধুমাত্র সাইবার সিকিউরিটি ওয়েবসাইট থেকে তথ্য আনে",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

translator = Translator()

# ================== সাইবার সিকিউরিটি সাইট ==================
ALLOWED_WEBSITES = {
    "thehackernews": {
        "name": "The Hacker News",
        "url": "https://thehackernews.com",
        "category": "security",
        "language": "en"
    },
    "kali": {
        "name": "Kali Linux",
        "url": "https://www.kali.org/blog/",
        "category": "security",
        "language": "en"
    },
    "portswigger": {
        "name": "PortSwigger Research",
        "url": "https://portswigger.net/research",
        "category": "security",
        "language": "en"
    },
    "darkreading": {
        "name": "Dark Reading",
        "url": "https://www.darkreading.com",
        "category": "security",
        "language": "en"
    },
    "securityweek": {
        "name": "Security Week",
        "url": "https://www.securityweek.com",
        "category": "security",
        "language": "en"
    }
}

# ================== Utility Functions ==================
def fetch_headlines(url: str, limit: int = 5) -> List[str]:
    """Fetch headlines from a website"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        headlines = []
        selectors = ['h1', 'h2', 'h3', '.headline', '.title', '.entry-title', '.post-title']
        
        for selector in selectors:
            elements = soup.select(selector)
            for elem in elements[:limit]:
                text = elem.get_text().strip()
                if text and len(text) > 15 and text not in headlines:
                    headlines.append(text)
                    if len(headlines) >= limit:
                        break
            if len(headlines) >= limit:
                break
        
        return headlines[:limit]
    except Exception as e:
        return [f"Error: {str(e)}"]

def translate_batch(texts: List[str], dest: str = "bn") -> List[str]:
    """Translate multiple texts"""
    results = []
    for text in texts:
        try:
            result = translator.translate(text, dest=dest)
            results.append(result.text)
        except:
            results.append(text)
    return results

# ================== API Endpoints ==================
@app.get("/")
async def root():
    """হোম পেজ"""
    return {
        "name": "🛡️ সাইবার সিকিউরিটি API",
        "description": "শুধুমাত্র সাইবার সিকিউরিটি ওয়েবসাইট থেকে তথ্য আনে",
        "total_sites": len(ALLOWED_WEBSITES),
        "endpoints": {
            "সাইট লিস্ট": "/sites",
            "হেডলাইন": "/headlines/{site_name}",
            "অনুবাদ": "/translate?text=hello"
        }
    }

@app.get("/sites")
async def list_sites():
    """সব সাইবার সিকিউরিটি সাইটের তালিকা"""
    simplified = {}
    for name, info in ALLOWED_WEBSITES.items():
        simplified[name] = {
            "name": info["name"],
            "category": info["category"],
            "language": info["language"]
        }
    
    return {
        "total": len(simplified),
        "categories": ["security"],
        "sites": simplified
    }

@app.get("/headlines/{site_name}")
async def get_headlines(
    site_name: str,
    limit: int = Query(5, ge=1, le=10),
    translate: bool = Query(True)
):
    """একটি সাইট থেকে হেডলাইন আনে"""
    
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
            result["bangla"] = translate_batch(headlines)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ডাটা আনা যায়নি: {str(e)}")

@app.get("/translate")
async def translate(
    text: str = Query(..., description="যে টেক্সট অনুবাদ করতে চান"),
    dest: str = Query("bn", description="টার্গেট ভাষা")
):
    """টেক্সট বাংলায় অনুবাদ করে"""
    try:
        result = translator.translate(text, dest=dest)
        return {
            "original": text,
            "translated": result.text
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """হেলথ চেক"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# ================== Main ==================
if __name__ == "__main__":
    print("\n" + "="*50)
    print("🛡️ সাইবার সিকিউরিটি API চালু হচ্ছে...")
    print(f"📊 সাইট সংখ্যা: {len(ALLOWED_WEBSITES)} টি")
    for name, info in ALLOWED_WEBSITES.items():
        print(f"   ✓ {name}: {info['name']}")
    print("="*50)
    
    port = int(os.getenv("PORT", 8000))
    print(f"📍 পোর্ট: {port}")
    print("="*50 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=port)
