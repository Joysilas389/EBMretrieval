"""
Multilingual support — language detection and translation.
Uses langdetect + deep-translator (Google Translate free tier).
Translates queries to English for retrieval, translates answers back.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

SUPPORTED_LANGUAGES = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "pt": "Portuguese",
    "de": "German",
    "it": "Italian",
    "zh": "Chinese",
    "ja": "Japanese",
    "ko": "Korean",
    "ar": "Arabic",
    "hi": "Hindi",
    "sw": "Swahili",
    "ru": "Russian",
    "tr": "Turkish",
    "nl": "Dutch",
    "pl": "Polish",
    "ha": "Hausa",
    "yo": "Yoruba",
    "ig": "Igbo",
    "am": "Amharic",
    "tw": "Twi",
}


def detect_language(text: str) -> str:
    """Detect the language of input text. Returns ISO 639-1 code."""
    try:
        from langdetect import detect
        lang = detect(text)
        return lang if lang in SUPPORTED_LANGUAGES else "en"
    except Exception:
        return "en"


def translate_to_english(text: str, source_lang: str) -> str:
    """Translate text to English for retrieval."""
    if source_lang == "en":
        return text
    try:
        from deep_translator import GoogleTranslator
        translated = GoogleTranslator(source=source_lang, target="en").translate(text)
        return translated or text
    except Exception as e:
        logger.warning(f"Translation to EN failed: {e}")
        return text


def translate_from_english(text: str, target_lang: str) -> str:
    """Translate English text to target language."""
    if target_lang == "en":
        return text
    try:
        from deep_translator import GoogleTranslator
        # Translate in chunks to avoid length limits
        chunks = _split_text(text, 4500)
        translated_chunks = []
        for chunk in chunks:
            result = GoogleTranslator(source="en", target=target_lang).translate(chunk)
            translated_chunks.append(result or chunk)
        return " ".join(translated_chunks)
    except Exception as e:
        logger.warning(f"Translation to {target_lang} failed: {e}")
        return text


def _split_text(text: str, max_len: int) -> list[str]:
    """Split text into chunks at sentence boundaries."""
    if len(text) <= max_len:
        return [text]
    chunks = []
    current = ""
    for sentence in text.split(". "):
        if len(current) + len(sentence) + 2 > max_len:
            if current:
                chunks.append(current)
            current = sentence
        else:
            current = f"{current}. {sentence}" if current else sentence
    if current:
        chunks.append(current)
    return chunks


def get_supported_languages() -> dict:
    return SUPPORTED_LANGUAGES
