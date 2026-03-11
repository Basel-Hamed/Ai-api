from googletrans import Translator
from typing import List

translator = Translator()

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
