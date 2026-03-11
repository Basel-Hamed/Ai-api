# utils/translator.py
from googletrans import Translator, LANGUAGES
import time
import logging
from typing import List, Optional, Dict, Any
from functools import lru_cache
import hashlib
import json
import os

# লগিং সেটআপ
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BanglaTranslator:
    """টেক্সট বাংলায় অনুবাদ করার জন্য ক্লাস - উন্নত সংস্করণ"""
    
    def __init__(self, cache_size: int = 100, use_cache: bool = True):
        """
        ট্রান্সলেটর ইনিশিয়ালাইজেশন
        
        Args:
            cache_size: ক্যাশে সাইজ (কতগুলো ট্রান্সলেশন সংরক্ষণ করবে)
            use_cache: ক্যাশে ব্যবহার করবে কিনা
        """
        self.translator = Translator()
        self.retry_count = 3
        self.retry_delay = 1  # সেকেন্ড
        self.batch_delay = 0.3  # ব্যাচ ট্রান্সলেশনের মধ্যে ডেলay
        self.use_cache = use_cache
        self.cache = {}
        self.cache_size = cache_size
        
        # ভাষা কোড ভ্যালিডেশন
        self.supported_languages = LANGUAGES
        logger.info(f"BanglaTranslator initialized with cache_size={cache_size}")
    
    def _get_cache_key(self, text: str, dest: str) -> str:
        """ক্যাশে কী জেনারেট করে"""
        text_hash = hashlib.md5(f"{text}_{dest}".encode()).hexdigest()
        return text_hash
    
    def _get_from_cache(self, text: str, dest: str) -> Optional[str]:
        """ক্যাশে থেকে ট্রান্সলেশন খুঁজে আনে"""
        if not self.use_cache:
            return None
        
        key = self._get_cache_key(text, dest)
        cached = self.cache.get(key)
        
        if cached:
            logger.debug(f"Cache hit for: {text[:30]}...")
            return cached
        return None
    
    def _add_to_cache(self, text: str, dest: str, translation: str):
        """ক্যাশে ট্রান্সলেশন যোগ করে"""
        if not self.use_cache:
            return
        
        key = self._get_cache_key(text, dest)
        
        # ক্যাশে সাইজ ম্যানেজমেন্ট
        if len(self.cache) >= self.cache_size:
            # এলিমিনেট FIFO পদ্ধতি
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
        
        self.cache[key] = translation
        logger.debug(f"Added to cache: {text[:30]}...")
    
    def translate(self, text: str, dest: str = 'bn', src: str = 'auto') -> str:
        """
        টেক্সট অনুবাদ করে
        
        Args:
            text: অনুবাদ করার টেক্সট
            dest: টার্গেট ভাষা (ডিফল্ট: bn - বাংলা)
            src: সোর্স ভাষা (ডিফল্ট: auto - স্বয়ংক্রিয়)
        
        Returns:
            অনুবাদকৃত টেক্সট
        """
        if not text or not text.strip():
            return ""
        
        # টেক্সট ট্রিম
        text = text.strip()
        
        # ক্যাশে চেক
        cached = self._get_from_cache(text, dest)
        if cached:
            return cached
        
        # ভাষা ভ্যালিডেশন
        if dest not in self.supported_languages and dest != 'auto':
            logger.warning(f"Unsupported destination language: {dest}. Using 'bn'")
            dest = 'bn'
        
        # রিট্রাই লজিক
        for attempt in range(self.retry_count):
            try:
                logger.debug(f"Translating: {text[:50]}... (attempt {attempt + 1})")
                
                result = self.translator.translate(text, src=src, dest=dest)
                
                if result and result.text:
                    translated = result.text.strip()
                    
                    # ক্যাশে যোগ
                    self._add_to_cache(text, dest, translated)
                    
                    logger.debug(f"Translation successful: {translated[:50]}...")
                    return translated
                else:
                    logger.warning(f"Empty translation result for: {text[:50]}...")
                    
            except Exception as e:
                logger.error(f"Translation error (attempt {attempt + 1}): {e}")
                
                if attempt < self.retry_count - 1:
                    # এক্সপোনেনশিয়াল ব্যাকঅফ
                    wait_time = self.retry_delay * (2 ** attempt)
                    logger.info(f"Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                else:
                    # সব চেষ্টা ব্যর্থ হলে
                    logger.error(f"All translation attempts failed for: {text[:50]}...")
                    return self._get_fallback_text(text, dest)
        
        return self._get_fallback_text(text, dest)
    
    def _get_fallback_text(self, text: str, dest: str) -> str:
        """ট্রান্সলেশন ব্যর্থ হলে ফallback টেক্সট"""
        if dest == 'bn':
            return f"[অনুবাদ ব্যর্থ: {text[:100]}]"
        else:
            return f"[Translation failed: {text[:100]}]"
    
    def translate_batch(self, texts: List[str], dest: str = 'bn', src: str = 'auto') -> List[str]:
        """
        একাধিক টেক্সট একসাথে অনুবাদ করে
        
        Args:
            texts: টেক্সটের লিস্ট
            dest: টার্গেট ভাষা
            src: সোর্স ভাষা
        
        Returns:
            অনুবাদকৃত টেক্সটের লিস্ট
        """
        if not texts:
            return []
        
        logger.info(f"Batch translating {len(texts)} texts")
        results = []
        
        for i, text in enumerate(texts):
            try:
                # ইন্ডিভিজুয়াল ট্রান্সলেশন
                translated = self.translate(text, dest, src)
                results.append(translated)
                
                # রেট লিমিট এড়াতে ডেলay
                if i < len(texts) - 1:  # শেষ আইটেমের পর না
                    time.sleep(self.batch_delay)
                    
            except Exception as e:
                logger.error(f"Batch translation error at index {i}: {e}")
                results.append(self._get_fallback_text(text, dest))
        
        logger.info(f"Batch translation completed. Success: {len([r for r in results if not r.startswith('[')])}/{len(texts)}")
        return results
    
    def detect_language(self, text: str) -> Dict[str, Any]:
        """টেক্সটের ভাষা ডিটেক্ট করে"""
        try:
            result = self.translator.detect(text)
            return {
                'lang': result.lang,
                'confidence': result.confidence,
                'language_name': self.supported_languages.get(result.lang, 'Unknown')
            }
        except Exception as e:
            logger.error(f"Language detection error: {e}")
            return {
                'lang': 'unknown',
                'confidence': 0,
                'error': str(e)
            }
    
    def get_supported_languages(self) -> Dict[str, str]:
        """সাপোর্টেড ভাষার লিস্ট রিটার্ন করে"""
        return self.supported_languages
    
    def clear_cache(self):
        """ক্যাশে ক্লিয়ার করে"""
        cache_size = len(self.cache)
        self.cache.clear()
        logger.info(f"Cache cleared. {cache_size} items removed.")
    
    def translate_with_detection(self, text: str, dest: str = 'bn') -> Dict[str, Any]:
        """
        ভাষা ডিটেক্ট করে ট্রান্সলেশন করে
        
        Returns:
            ট্রান্সলেশন সহ ভাষার তথ্য
        """
        detected = self.detect_language(text)
        translated = self.translate(text, dest)
        
        return {
            'original': text,
            'translated': translated,
            'detected_language': detected['lang'],
            'detected_language_name': detected.get('language_name', 'Unknown'),
            'confidence': detected.get('confidence', 0)
        }


# ট্রান্সলেটরের ইনস্ট্যান্স (সিঙ্গেলটন)
_translator_instance = None

def get_translator() -> BanglaTranslator:
    """সিঙ্গেলটন ট্রান্সলেটর ইনস্ট্যান্স রিটার্ন করে"""
    global _translator_instance
    if _translator_instance is None:
        _translator_instance = BanglaTranslator()
    return _translator_instance

# হেল্পার ফাংশন
def translate_text(text: str, dest: str = 'bn') -> str:
    """টেক্সট অনুবাদ করার জন্য হেল্পার ফাংশন"""
    translator = get_translator()
    return translator.translate(text, dest)

def translate_batch(texts: List[str], dest: str = 'bn') -> List[str]:
    """একাধিক টেক্সট অনুবাদ করার জন্য হেল্পার ফাংশন"""
    translator = get_translator()
    return translator.translate_batch(texts, dest)

def detect_language(text: str) -> str:
    """টেক্সটের ভাষা ডিটেক্ট করে"""
    translator = get_translator()
    result = translator.detect_language(text)
    return result.get('lang', 'unknown')

def translate_with_info(text: str, dest: str = 'bn') -> Dict[str, Any]:
    """ট্রান্সলেশন সহ ভাষার তথ্য রিটার্ন করে"""
    translator = get_translator()
    return translator.translate_with_detection(text, dest)

def clear_translation_cache():
    """ট্রান্সলেশন ক্যাশে ক্লিয়ার করে"""
    translator = get_translator()
    translator.clear_cache()

def get_supported_languages() -> Dict[str, str]:
    """সাপোর্টেড ভাষার লিস্ট রিটার্ন করে"""
    translator = get_translator()
    return translator.get_supported_languages()