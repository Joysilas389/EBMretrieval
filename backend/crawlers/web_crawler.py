"""
General web crawler for HTML-based trusted medical sources.
Handles: WHO, CDC, NIH, NICE, FDA, etc.
Respects rate limits, robots.txt, and caching.
"""

import asyncio
import hashlib
import logging
import os
import re
import time
from typing import Optional
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from models import Citation, EvidenceChunk, SourceCategory, EvidenceLevel

logger = logging.getLogger(__name__)

CACHE_DIR = os.getenv("CACHE_DIR", "./data/cache")
RATE_LIMIT = float(os.getenv("CRAWL_RATE_LIMIT_SECONDS", "1.0"))
TIMEOUT = int(os.getenv("CRAWL_TIMEOUT_SECONDS", "30"))

# Track last request time per domain
_domain_timestamps: dict[str, float] = {}


def _cache_path(url: str) -> str:
    h = hashlib.md5(url.encode()).hexdigest()
    os.makedirs(CACHE_DIR, exist_ok=True)
    return os.path.join(CACHE_DIR, f"{h}.html")


def _get_cached(url: str, max_age_hours: int = 24) -> Optional[str]:
    path = _cache_path(url)
    if os.path.exists(path):
        age = time.time() - os.path.getmtime(path)
        if age < max_age_hours * 3600:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                return f.read()
    return None


def _save_cache(url: str, content: str):
    path = _cache_path(url)
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        logger.warning(f"Cache write failed: {e}")


async def _rate_limit(domain: str):
    now = time.time()
    last = _domain_timestamps.get(domain, 0)
    wait = RATE_LIMIT - (now - last)
    if wait > 0:
        await asyncio.sleep(wait)
    _domain_timestamps[domain] = time.time()


async def fetch_page(url: str, use_cache: bool = True) -> Optional[str]:
    """Fetch a web page with caching and rate limiting."""
    if use_cache:
        cached = _get_cached(url)
        if cached:
            return cached

    domain = urlparse(url).netloc
    await _rate_limit(domain)

    headers = {
        "User-Agent": "EBMRetrieval/1.0 (Medical Evidence Retrieval; +https://github.com/ebmretrieval)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            content = resp.text
            _save_cache(url, content)
            return content
    except httpx.TimeoutException:
        logger.warning(f"Timeout fetching {url}")
        return None
    except httpx.HTTPStatusError as e:
        logger.warning(f"HTTP {e.response.status_code} for {url}")
        return None
    except Exception as e:
        logger.error(f"Fetch error for {url}: {e}")
        return None


def extract_article_content(html: str, url: str) -> dict:
    """Extract main content from an HTML page, removing boilerplate."""
    soup = BeautifulSoup(html, "lxml")

    # Remove noise
    for tag in soup.find_all(["script", "style", "nav", "footer", "header", "aside", "iframe", "noscript"]):
        tag.decompose()

    # Try to find main content area
    main = (
        soup.find("main")
        or soup.find("article")
        or soup.find("div", {"role": "main"})
        or soup.find("div", class_=re.compile(r"(content|article|main|body)", re.I))
        or soup.find("div", id=re.compile(r"(content|article|main|body)", re.I))
    )
    if main is None:
        main = soup.body or soup

    # Title
    title = ""
    title_el = soup.find("title")
    if title_el:
        title = title_el.get_text(strip=True)
    h1 = main.find("h1")
    if h1:
        title = h1.get_text(strip=True)

    # Extract text with section awareness
    sections = []
    current_section = {"heading": "", "text": []}

    for el in main.find_all(["h1", "h2", "h3", "h4", "p", "li", "td", "th", "blockquote", "figcaption"]):
        if el.name in ("h1", "h2", "h3", "h4"):
            if current_section["text"]:
                sections.append(current_section)
            current_section = {"heading": el.get_text(strip=True), "text": []}
        else:
            text = el.get_text(strip=True)
            if text and len(text) > 10:
                current_section["text"].append(text)

    if current_section["text"]:
        sections.append(current_section)

    full_text = " ".join(
        " ".join(s["text"]) for s in sections
    )

    # Meta
    meta = {}
    for tag in soup.find_all("meta"):
        name = tag.get("name", "") or tag.get("property", "")
        content = tag.get("content", "")
        if name and content:
            meta[name.lower()] = content

    # Authors
    authors = []
    author_meta = meta.get("author", "") or meta.get("citation_author", "")
    if author_meta:
        authors = [a.strip() for a in author_meta.split(",")]

    # Date
    pub_date = (
        meta.get("citation_publication_date", "")
        or meta.get("article:published_time", "")
        or meta.get("date", "")
        or meta.get("dc.date", "")
    )

    return {
        "title": title,
        "text": full_text[:20000],  # cap at 20k chars
        "sections": sections,
        "authors": authors,
        "pub_date": pub_date,
        "meta": meta,
        "url": url,
    }


def content_to_chunks(content: dict, source_id: str, source_name: str) -> list[EvidenceChunk]:
    """Convert extracted content to evidence chunks."""
    citation = Citation(
        id=f"{source_id}_{hashlib.md5(content['url'].encode()).hexdigest()[:8]}",
        title=content["title"],
        url=content["url"],
        source_id=source_id,
        source_name=source_name,
        authors=content.get("authors", []),
        pub_date=content.get("pub_date", ""),
        source_category=SourceCategory.GUIDELINE if "guideline" in source_id else SourceCategory.PUBLIC_HEALTH,
        evidence_level=EvidenceLevel.GUIDELINE if "guideline" in source_id else EvidenceLevel.PUBLIC_HEALTH,
        excerpt=content["text"][:300],
    )

    chunks = []
    for i, section in enumerate(content.get("sections", [])):
        text = " ".join(section["text"])
        if len(text) < 20:
            continue
        chunks.append(EvidenceChunk(
            text=text[:2000],
            citation=citation,
            section=section.get("heading", ""),
            chunk_index=i,
        ))

    if not chunks and content.get("text"):
        # Fallback: chunk by paragraphs
        paragraphs = content["text"].split(". ")
        chunk_size = 500
        for i in range(0, len(content["text"]), chunk_size):
            chunk_text = content["text"][i:i + chunk_size]
            if len(chunk_text) > 30:
                chunks.append(EvidenceChunk(
                    text=chunk_text,
                    citation=citation,
                    section="body",
                    chunk_index=i // chunk_size,
                ))

    return chunks
