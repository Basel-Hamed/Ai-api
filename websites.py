# config/websites.py
# ===============================================
# 📌 গুরুত্বপূর্ণ: শুধুমাত্র এখানেই সাইট যোগ করুন
# API শুধু এই লিস্টের সাইট থেকেই ডাটা আনতে পারবে
# ===============================================

# ---------- আপনার পছন্দের ওয়েবসাইট লিস্ট ----------
ALLOWED_WEBSITES = {
    # বাংলা নিউজ সাইট
    "prothomalo_eng": {
        "url": "https://en.prothomalo.com",
        "name": "Prothom Alo English",
        "category": "news",
        "language": "en",
        "active": True,
        "type": "news"
    },
    
    "dailystar": {
        "url": "https://www.thedailystar.net",
        "name": "The Daily Star",
        "category": "news",
        "language": "en",
        "active": True,
        "type": "news"
    },
    
    # আন্তর্জাতিক নিউজ
    "bbc": {
        "url": "https://www.bbc.com/news",
        "name": "BBC News",
        "category": "international",
        "language": "en",
        "active": True,
        "type": "news"
    },
    
    "cnn": {
        "url": "https://www.cnn.com/world",
        "name": "CNN",
        "category": "international",
        "language": "en",
        "active": True,
        "type": "news"
    },
    
    # টেকনোলজি সাইট
    "techcrunch": {
        "url": "https://techcrunch.com",
        "name": "TechCrunch",
        "category": "technology",
        "language": "en",
        "active": True,
        "type": "tech"
    },
    
    "theverge": {
        "url": "https://www.theverge.com",
        "name": "The Verge",
        "category": "technology",
        "language": "en",
        "active": True,
        "type": "tech"
    },
    
    # স্পোর্টস
    "espn": {
        "url": "https://www.espn.com",
        "name": "ESPN",
        "category": "sports",
        "language": "en",
        "active": True,
        "type": "sports"
    },
    
    # বিজনেস সাইট
    "bloomberg": {
        "url": "https://www.bloomberg.com",
        "name": "Bloomberg",
        "category": "business",
        "language": "en",
        "active": True,
        "type": "business"
    },
    
    "reuters": {
        "url": "https://www.reuters.com",
        "name": "Reuters",
        "category": "business",
        "language": "en",
        "active": True,
        "type": "business"
    },
    
    # ============================================
    # ⭐ আপনার নতুন সাইট এখানে যোগ করুন:
    # 
    # "site_name": {
    #     "url": "https://your-site.com",
    #     "name": "Your Site Name",
    #     "category": "news/tech/sports/business",
    #     "language": "en",
    #     "active": True,
    #     "type": "news/tech/sports"
    # },
    # ============================================
}

# ---------- হেল্পার ফাংশন ----------
def get_allowed_websites():
    """অনুমোদিত ওয়েবসাইটের তালিকা রিটার্ন করে"""
    return {name: info for name, info in ALLOWED_WEBSITES.items() if info.get("active", True)}

def is_website_allowed(name):
    """চেক করে যে সাইটটি অনুমোদিত কিনা"""
    return name in ALLOWED_WEBSITES and ALLOWED_WEBSITES[name].get("active", True)

def get_website_info(name):
    """সাইটের তথ্য রিটার্ন করে"""
    return ALLOWED_WEBSITES.get(name, {})

def get_websites_by_category(category):
    """ক্যাটাগরি অনুযায়ী সাইট ফিল্টার করে"""
    return {
        name: info for name, info in ALLOWED_WEBSITES.items() 
        if info.get("category") == category and info.get("active", True)
    }

def get_websites_by_type(site_type):
    """টাইপ অনুযায়ী সাইট ফিল্টার করে (news/tech/sports)"""
    return {
        name: info for name, info in ALLOWED_WEBSITES.items() 
        if info.get("type") == site_type and info.get("active", True)
    }

def get_all_categories():
    """সব ক্যাটাগরির তালিকা রিটার্ন করে"""
    categories = set()
    for info in ALLOWED_WEBSITES.values():
        if info.get("active", True):
            categories.add(info.get("category", "other"))
    return sorted(list(categories))

def get_all_types():
    """সব টাইপের তালিকা রিটার্ন করে"""
    types = set()
    for info in ALLOWED_WEBSITES.values():
        if info.get("active", True):
            types.add(info.get("type", "other"))
    return sorted(list(types))

def get_active_sites_count():
    """অ্যাক্টিভ সাইটের সংখ্যা রিটার্ন করে"""
    return len(get_allowed_websites())

def add_new_website(name, url, site_name, category, language="en", site_type="news"):
    """
    নতুন সাইট যোগ করার ফাংশন
    (ডাইনামিকভাবে যোগ করতে চাইলে ব্যবহার করুন)
    """
    ALLOWED_WEBSITES[name] = {
        "url": url,
        "name": site_name,
        "category": category,
        "language": language,
        "active": True,
        "type": site_type
    }
    return True

# API-র জন্য সামারি তথ্য
def get_websites_summary():
    """সব সাইটের সংক্ষিপ্ত তথ্য"""
    sites = get_allowed_websites()
    summary = {
        "total": len(sites),
        "categories": get_all_categories(),
        "types": get_all_types(),
        "sites": {}
    }
    
    for name, info in sites.items():
        summary["sites"][name] = {
            "name": info["name"],
            "category": info["category"],
            "type": info.get("type", "unknown"),
            "language": info["language"]
        }
    
    return summary