from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, Dict, List
import uvicorn
import os
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from googletrans import Translator
from pydantic import BaseModel

# ================== Pydantic Models ==================
class SiteInfo(BaseModel):
    name: str
    category: str
    language: str

class SiteListResponse(BaseModel):
    total: int
    categories: List[str]
    sites: Dict[str, SiteInfo]

class HeadlineResponse(BaseModel):
    site: str
    name: str
    url: str
    category: str
    timestamp: str
    headlines: List[str]
    bangla: Optional[List[str]] = None

# ================== FastAPI App ==================
app = FastAPI(
    title="সাইবার সিকিউরিটি API",
    description="শুধুমাত্র সাইবার সিকিউরিটি ওয়েবসাইট থেকে তথ্য আনে",
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

# ================== সাইবার সিকিউরিটি ওয়েবসাইট লিংক ==================
ALLOWED_WEBSITES = {
    "kali": {
        "name": "Kali Linux Official",
        "url": "https://www.kali.org/blog/",
        "category": "security",
        "language": "en"
    },
    "hackthebox": {
        "name": "Hack The Box Blog",
        "url": "https://www.hackthebox.com/blog",
        "category": "security",
        "language": "en"
    },
    "tryhackme": {
        "name": "TryHackMe Blog",
        "url": "https://tryhackme.com/blog",
        "category": "security",
        "language": "en"
    },
    "cybrary": {
        "name": "Cybrary Blog",
        "url": "https://www.cybrary.it/blog/",
        "category": "security",
        "language": "en"
    },
    "securityweek": {
        "name": "Security Week",
        "url": "https://www.securityweek.com",
        "category": "security",
        "language": "en"
    },
    "darkreading": {
        "name": "Dark Reading",
        "url": "https://www.darkreading.com",
        "category": "security",
        "language": "en"
    },
    "thehackernews": {
        "name": "The Hacker News",
        "url": "https://thehackernews.com",
        "category": "security",
        "language": "en"
    },
    "infosecurity": {
        "name": "Infosecurity Magazine",
        "url": "https://www.infosecurity-magazine.com",
        "category": "security",
        "language": "en"
    },
    "portswigger": {
        "name": "PortSwigger Research",
        "url": "https://portswigger.net/research",
        "category": "security",
        "language": "en"
    },
    "sans": {
        "name": "SANS Institute",
        "url": "https://www.sans.org/blog/",
        "category": "security",
        "language": "en"
    }
}

# ================== ইউটিলিটি ফাংশন ==================
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

def translate_text(text: str, dest: str = "bn") -> str:
    """Translate text to target language"""
    try:
        result = translator.translate(text, dest=dest)
        return result.text
    except Exception as e:
        return text

def translate_batch(texts: List[str], dest: str = "bn") -> List[str]:
    """Translate multiple texts"""
    results = []
    for text in texts:
        try:
            translated = translate_text(text, dest)
            results.append(translated)
        except:
            results.append(text)
    return results

# ================== API এন্ডপয়েন্ট ==================
@app.get("/", response_model=None)
async def root():
    """হোম পেজ"""
    return {
        "name": "🛡️ সাইবার সিকিউরিটি API",
        "description": "শুধুমাত্র সাইবার সিকিউরিটি ওয়েবসাইট থেকে তথ্য আনে",
        "total_sites": len(ALLOWED_WEBSITES),
        "message": "নিচের এন্ডপয়েন্ট ব্যবহার করে তথ্য নিন",
        "endpoints": {
            "সাইট লিস্ট": "/sites",
            "সাইট অনুযায়ী": "/sites/{site_name}",
            "হেডলাইন": "/headlines/{site_name}",
            "অনুবাদ": "/translate?text=hello"
        }
    }

@app.get("/sites", response_model=SiteListResponse)
async def list_sites():
    """সব সাইবার সিকিউরিটি সাইটের তালিকা"""
    
    simplified = {}
    for name, info in ALLOWED_WEBSITES.items():
        simplified[name] = SiteInfo(
            name=info["name"],
            category=info["category"],
            language=info["language"]
        )
    
    return SiteListResponse(
        total=len(simplified),
        categories=["security"],
        sites=simplified
    )

@app.get("/sites/{site_name}", response_model=None)
async def site_info(site_name: str):
    """একটি নির্দিষ্ট সাইটের তথ্য দেখায়"""
    if site_name not in ALLOWED_WEBSITES:
        raise HTTPException(status_code=403, detail=f"'{site_name}' অনুমোদিত নয়")
    
    info = ALLOWED_WEBSITES[site_name]
    return {
        "name": site_name,
        "info": info
    }

@app.get("/headlines/{site_name}", response_model=HeadlineResponse)
async def get_headlines(
    site_name: str,
    limit: int = Query(5, ge=1, le=10),
    translate: bool = Query(True, description="বাংলায় অনুবাদ করবে?")
):
    """একটি সাইট থেকে হেডলাইন আনে"""
    
    if site_name not in ALLOWED_WEBSITES:
        raise HTTPException(status_code=403, detail=f"'{site_name}' অনুমোদিত নয়")
    
    info = ALLOWED_WEBSITES[site_name]
    
    try:
        headlines = fetch_headlines(info["url"], limit)
        
        result = HeadlineResponse(
            site=site_name,
            name=info["name"],
            url=info["url"],
            category=info["category"],
            timestamp=datetime.now().isoformat(),
            headlines=headlines
        )
        
        if translate and headlines:
            result.bangla = translate_batch(headlines)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ডাটা আনা যায়নি: {str(e)}")

@app.get("/translate", response_model=None)
async def translate(
    text: str = Query(..., description="যে টেক্সট অনুবাদ করতে চান"),
    dest: str = Query("bn", description="টার্গেট ভাষা")
):
    """টেক্সট বাংলায় অনুবাদ করে"""
    try:
        translated = translate_text(text, dest)
        return {
            "original": text,
            "translated": translated
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health", response_model=None)
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
