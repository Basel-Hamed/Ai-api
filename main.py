# main.py
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
import uvicorn
import os
from datetime import datetime

# নিজস্ব মডিউল ইম্পোর্ট
from config.websites import (
    get_allowed_websites, 
    is_website_allowed, 
    get_website_info,
    get_websites_by_category
)
from utils.scraper import fetch_headlines, fetch_articles, search_website
from utils.translator import translate_text, translate_batch

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

# ================== API এন্ডপয়েন্ট ==================

@app.get("/")
async def root():
    """হোম পেজ - অনুমোদিত সাইটের সংখ্যা দেখায়"""
    sites = get_allowed_websites()
    return {
        "name": "🔒 প্রাইভেট ওয়েবসাইট API",
        "description": "শুধুমাত্র আপনার কনফিগার করা সাইট থেকে তথ্য আনে",
        "total_sites": len(sites),
        "message": "নিচের এন্ডপয়েন্ট ব্যবহার করে তথ্য নিন",
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
async def list_sites(
    category: Optional[str] = Query(None, description="ক্যাটাগরি ফিল্টার")
):
    """অনুমোদিত সব ওয়েবসাইটের তালিকা দেখায়"""
    if category:
        sites = get_websites_by_category(category)
    else:
        sites = get_allowed_websites()
    
    # শুধু প্রয়োজনীয় তথ্য দেখায়
    simplified = {}
    for name, info in sites.items():
        simplified[name] = {
            "name": info["name"],
            "category": info["category"],
            "language": info["language"]
        }
    
    return {
        "total": len(simplified),
        "categories": list(set(info["category"] for info in sites.values())),
        "sites": simplified
    }

@app.get("/sites/{site_name}")
async def site_info(site_name: str):
    """একটি নির্দিষ্ট সাইটের তথ্য দেখায়"""
    if not is_website_allowed(site_name):
        raise HTTPException(
            status_code=403,
            detail=f"❌ '{site_name}' অনুমোদিত নয়। শুধু কনফিগার করা সাইট থেকে তথ্য নেওয়া যাবে"
        )
    
    info = get_website_info(site_name)
    return {
        "name": site_name,
        "info": {
            "name": info.get("name"),
            "url": info.get("url"),
            "category": info.get("category"),
            "language": info.get("language")
        }
    }

@app.get("/headlines/{site_name}")
async def get_headlines(
    site_name: str,
    limit: int = Query(5, ge=1, le=10),
    translate: bool = Query(True, description="বাংলায় অনুবাদ করবে?")
):
    """একটি সাইট থেকে হেডলাইন আনে"""
    
    # চেক করে যে সাইটটি অনুমোদিত কিনা
    if not is_website_allowed(site_name):
        raise HTTPException(
            status_code=403,
            detail=f"❌ '{site_name}' অনুমোদিত নয়। শুধু কনফিগার করা সাইট থেকে তথ্য নেওয়া যাবে"
        )
    
    info = get_website_info(site_name)
    
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
    """একটি সাইট থেকে আর্টিকেলের লিংক আনে"""
    
    if not is_website_allowed(site_name):
        raise HTTPException(
            status_code=403,
            detail=f"❌ '{site_name}' অনুমোদিত নয়"
        )
    
    info = get_website_info(site_name)
    
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
    """একটি সাইটে কীওয়ার্ড সার্চ করে"""
    
    if not is_website_allowed(site_name):
        raise HTTPException(
            status_code=403,
            detail=f"❌ '{site_name}' অনুমোদিত নয়"
        )
    
    info = get_website_info(site_name)
    
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

@app.get("/categories")
async def list_categories():
    """ক্যাটাগরি অনুযায়ী সাইটের তালিকা"""
    sites = get_allowed_websites()
    categories = {}
    
    for name, info in sites.items():
        cat = info["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append({
            "name": name,
            "title": info["name"]
        })
    
    return categories

@app.get("/help")
async def help_page():
    """ব্যবহার বিধি"""
    sites = get_allowed_websites()
    
    return {
        "title": "📘 API ব্যবহার করার নিয়ম",
        "important": "⚠️ এই API শুধু কনফিগার করা সাইট থেকে তথ্য দেয়",
        "available_sites": [f"{name} ({info['name']})" for name, info in sites.items()],
        "how_to_use": {
            "সাইট লিস্ট দেখুন": "/sites",
            "হেডলাইন দেখুন": "/headlines/bbc?limit=5&translate=true",
            "আর্টিকেল দেখুন": "/articles/techcrunch?limit=3",
            "সার্চ করুন": "/search/bbc?q=bangladesh",
            "অনুবাদ করুন": "/translate?text=Hello"
        },
        "note": "🔧 নতুন সাইট যোগ করতে config/websites.py এডিট করুন"
    }

# Render-এর জন্য পরিবর্তিত অংশ
if __name__ == "__main__":
    try:
        sites = get_allowed_websites()
        print("\n" + "="*50)
        print("🔒 প্রাইভেট ওয়েবসাইট API চালু হচ্ছে...")
        print(f"📊 অনুমোদিত সাইট: {len(sites)} টি")
        for name, info in sites.items():
            print(f"   ✓ {name}: {info['name']}")
        print("="*50)
        
        # Render-এ পোর্ট ডায়নামিকভাবে সেট করা
        port = int(os.getenv("PORT", 8000))
        print(f"📍 পোর্ট: {port}")
        print("="*50 + "\n")
        
        uvicorn.run(app, host="0.0.0.0", port=port)
    except Exception as e:
        print(f"❌ Error: {e}")