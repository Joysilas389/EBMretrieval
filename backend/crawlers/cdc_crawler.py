"""
CDC Crawler — retrieves health information from CDC.gov.
CDC content is US government public domain.
Uses CDC's search and direct topic page access.
"""

import logging
import re
import hashlib

import httpx
from bs4 import BeautifulSoup

from models import Citation, EvidenceChunk, EvidenceLevel, SourceCategory

logger = logging.getLogger(__name__)

CDC_SEARCH = "https://search.cdc.gov/search/index.html"
CDC_BASE = "https://www.cdc.gov"


async def search_cdc(query: str, max_results: int = 5) -> list[EvidenceChunk]:
    """Search CDC for health topics and guidelines."""
    chunks = []

    # Strategy 1: CDC search API
    try:
        params = {
            "query": query,
            "dession": "CDC-Main",
            "utf8": "✓",
            "affiliate": "cdc-main",
        }
        search_url = f"https://search.cdc.gov/search?query={query}&utf8=✓&affiliate=cdc-main"

        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            resp = await client.get(search_url, headers={
                "User-Agent": "EBMRetrieval/1.0 (Medical Evidence Retrieval)",
                "Accept": "text/html",
            })
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "lxml")
                for result in soup.select(".result, .search-result-item, article")[:max_results]:
                    title_el = result.select_one("h2 a, h3 a, a.result-title, .title a")
                    if not title_el:
                        title_el = result.select_one("a[href]")
                    if not title_el:
                        continue

                    title = title_el.get_text(strip=True)
                    href = title_el.get("href", "")
                    if not href:
                        continue

                    snippet_el = result.select_one("p, .snippet, .description")
                    snippet = snippet_el.get_text(strip=True) if snippet_el else ""

                    if not snippet or len(snippet) < 20:
                        snippet = title

                    citation = Citation(
                        id=f"cdc_{hashlib.md5(href.encode()).hexdigest()[:8]}",
                        title=title,
                        url=href if href.startswith("http") else CDC_BASE + href,
                        source_id="cdc",
                        source_name="CDC",
                        source_category=SourceCategory.PUBLIC_HEALTH,
                        evidence_level=EvidenceLevel.GUIDELINE,
                        excerpt=snippet[:300],
                    )
                    chunks.append(EvidenceChunk(
                        text=snippet[:600],
                        citation=citation,
                        section="search_result",
                    ))
    except Exception as e:
        logger.warning(f"CDC search error: {e}")

    # Strategy 2: Direct topic page fetch for common conditions
    try:
        direct = await _cdc_topic_direct(query)
        chunks.extend(direct)
    except Exception as e:
        logger.warning(f"CDC direct topic error: {e}")

    return chunks[:max_results * 2]


async def _cdc_topic_direct(query: str) -> list[EvidenceChunk]:
    """Try fetching CDC topic pages directly."""
    TOPIC_MAP = {
        "diabetes": "/diabetes/index.html",
        "heart disease": "/heart-disease/index.html",
        "hypertension": "/bloodpressure/index.html",
        "stroke": "/stroke/index.html",
        "cancer": "/cancer/index.html",
        "flu": "/flu/index.html",
        "influenza": "/flu/index.html",
        "hiv": "/hiv/index.html",
        "covid": "/covid/index.html",
        "pneumonia": "/pneumonia/index.html",
        "tuberculosis": "/tb/index.html",
        "tb": "/tb/index.html",
        "malaria": "/malaria/index.html",
        "cholesterol": "/cholesterol/index.html",
        "obesity": "/obesity/index.html",
        "asthma": "/asthma/index.html",
        "copd": "/copd/index.html",
        "hepatitis": "/hepatitis/index.html",
        "kidney": "/kidneydisease/index.html",
        "arthritis": "/arthritis/index.html",
        "vaccination": "/vaccines/index.html",
        "vaccine": "/vaccines/index.html",
        "sepsis": "/sepsis/index.html",
        "antibiotic resistance": "/drugresistance/index.html",
    }

    q_lower = query.lower()
    matching = []
    for kw, path in TOPIC_MAP.items():
        if kw in q_lower:
            matching.append((kw, path))

    if not matching:
        return []

    chunks = []
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        for kw, path in matching[:2]:
            try:
                url = CDC_BASE + path
                resp = await client.get(url, headers={
                    "User-Agent": "EBMRetrieval/1.0"
                })
                if resp.status_code != 200:
                    continue

                soup = BeautifulSoup(resp.text, "lxml")
                for tag in soup.find_all(["script", "style", "nav", "footer"]):
                    tag.decompose()

                title = ""
                h1 = soup.find("h1")
                if h1:
                    title = h1.get_text(strip=True)

                main = soup.find("main") or soup.find("article") or soup.body
                if not main:
                    continue

                paragraphs = []
                for p in main.find_all(["p"]):
                    text = p.get_text(strip=True)
                    if len(text) > 40:
                        paragraphs.append(text)

                full_text = " ".join(paragraphs[:15])
                if len(full_text) < 50:
                    continue

                citation = Citation(
                    id=f"cdc_{hashlib.md5(url.encode()).hexdigest()[:8]}",
                    title=title or f"CDC: {kw}",
                    url=url,
                    source_id="cdc",
                    source_name="CDC",
                    source_category=SourceCategory.PUBLIC_HEALTH,
                    evidence_level=EvidenceLevel.GUIDELINE,
                    excerpt=full_text[:300],
                )

                for i in range(0, len(full_text), 500):
                    ct = full_text[i:i + 500]
                    if len(ct) > 30:
                        chunks.append(EvidenceChunk(
                            text=ct, citation=citation,
                            section="topic_page", chunk_index=i // 500,
                        ))
            except Exception as e:
                logger.warning(f"CDC topic fetch error: {e}")

    return chunks
