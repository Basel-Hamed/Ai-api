from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import requests
from bs4 import BeautifulSoup
from googletrans import Translator
from typing import Dict, List, Any

app = FastAPI(title="সাইবার সিকিউরিটি API")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

translator = Translator()

SITES = {
    "thehackernews": {
        "name": "The Hacker News",
        "url": "https://thehackernews.com"
    },
    "kali": {
        "name": "Kali Linux",
        "url": "https://www.kali.org/blog/"
    }
}

def fetch_headlines(url: str, limit: int = 5) -> List[str]:
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        headlines = []
        for h in soup.find_all(['h1', 'h2', 'h3'])[:limit]:
            text = h.get_text().strip()
            if text and len(text) > 10:
                headlines.append(text)
        return headlines
    except:
        return []

@app.get("/")
def root() -> Dict[str, Any]:
    return {"message": "🛡️ API Running", "sites": len(SITES)}

@app.get("/sites")
def list_sites() -> Dict[str, Any]:
    return SITES

@app.get("/headlines/{site}")
def headlines(site: str, limit: int = 5, translate: bool = True) -> Dict[str, Any]:
    if site not in SITES:
        raise HTTPException(404, "Site not found")
    
    headlines = fetch_headlines(SITES[site]["url"], limit)
    result = {"site": site, "name": SITES[site]["name"], "headlines": headlines}
    
    if translate and headlines:
        try:
            result["bangla"] = [translator.translate(h, dest="bn").text for h in headlines]
        except:
            pass
    
    return result

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
