"""
WHO Crawler — retrieves fact sheets, disease outbreak news, and guidelines.
Uses WHO's public site search and fact sheet pages.
WHO content is publicly accessible for health information purposes.
"""

import logging
import re
import hashlib

import httpx
from bs4 import BeautifulSoup

from models import Citation, EvidenceChunk, EvidenceLevel, SourceCategory

logger = logging.getLogger(__name__)

WHO_SEARCH_URL = "https://search.who.int/search"
WHO_BASE = "https://www.who.int"


async def search_who(query: str, max_results: int = 5) -> list[EvidenceChunk]:
    """Search WHO site for fact sheets and guidelines."""
    chunks = []

    # Strategy 1: WHO site search
    try:
        search_chunks = await _who_site_search(query, max_results)
        chunks.extend(search_chunks)
    except Exception as e:
        logger.warning(f"WHO site search error: {e}")

    # Strategy 2: Direct fact sheet URL guessing for common topics
    try:
        direct_chunks = await _who_factsheet_direct(query)
        chunks.extend(direct_chunks)
    except Exception as e:
        logger.warning(f"WHO factsheet direct error: {e}")

    return chunks[:max_results * 2]


async def _who_site_search(query: str, max_results: int) -> list[EvidenceChunk]:
    """Use WHO's search endpoint."""
    params = {
        "query": query,
        "page": "1",
        "pagesize": str(max_results),
        "sortorder": "relevance",
        "default_operator": "AND",
    }
    headers = {
        "User-Agent": "EBMRetrieval/1.0 (Medical Evidence Retrieval)",
        "Accept": "text/html",
    }

    chunks = []
    try:
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            resp = await client.get(WHO_SEARCH_URL, params=params, headers=headers)
            if resp.status_code != 200:
                return []

            soup = BeautifulSoup(resp.text, "lxml")

            # Parse search results
            for result in soup.select(".search-result, .result-item, article")[:max_results]:
                title_el = result.select_one("h3 a, h2 a, .title a, a.result-title")
                if not title_el:
                    title_el = result.select_one("a")
                if not title_el:
                    continue

                title = title_el.get_text(strip=True)
                href = title_el.get("href", "")
                if href and not href.startswith("http"):
                    href = WHO_BASE + href

                snippet_el = result.select_one("p, .description, .snippet, .summary")
                snippet = snippet_el.get_text(strip=True) if snippet_el else title

                if not title or not href or len(snippet) < 20:
                    continue

                citation = Citation(
                    id=f"who_{hashlib.md5(href.encode()).hexdigest()[:8]}",
                    title=title,
                    url=href,
                    source_id="who",
                    source_name="World Health Organization",
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
        logger.warning(f"WHO search parse error: {e}")

    return chunks


async def _who_factsheet_direct(query: str) -> list[EvidenceChunk]:
    """Try to fetch WHO fact sheets directly for well-known conditions."""
    # Map common medical terms to WHO fact sheet paths
    FACTSHEET_MAP = {
        "malaria": "/news-room/fact-sheets/detail/malaria",
        "tuberculosis": "/news-room/fact-sheets/detail/tuberculosis",
        "tb": "/news-room/fact-sheets/detail/tuberculosis",
        "hiv": "/news-room/fact-sheets/detail/hiv-aids",
        "aids": "/news-room/fact-sheets/detail/hiv-aids",
        "diabetes": "/news-room/fact-sheets/detail/diabetes",
        "hypertension": "/news-room/fact-sheets/detail/hypertension",
        "cancer": "/news-room/fact-sheets/detail/cancer",
        "asthma": "/news-room/fact-sheets/detail/asthma",
        "copd": "/news-room/fact-sheets/detail/chronic-obstructive-pulmonary-disease-(copd)",
        "cholera": "/news-room/fact-sheets/detail/cholera",
        "dengue": "/news-room/fact-sheets/detail/dengue-and-severe-dengue",
        "hepatitis": "/news-room/fact-sheets/detail/hepatitis-b",
        "influenza": "/news-room/fact-sheets/detail/influenza-(seasonal)",
        "measles": "/news-room/fact-sheets/detail/measles",
        "pneumonia": "/news-room/fact-sheets/detail/pneumonia",
        "depression": "/news-room/fact-sheets/detail/depression",
        "epilepsy": "/news-room/fact-sheets/detail/epilepsy",
        "stroke": "/news-room/fact-sheets/detail/the-top-10-causes-of-death",
        "obesity": "/news-room/fact-sheets/detail/obesity-and-overweight",
        "antimicrobial resistance": "/news-room/fact-sheets/detail/antimicrobial-resistance",
    }

    q_lower = query.lower()
    matching_paths = []
    for keyword, path in FACTSHEET_MAP.items():
        if keyword in q_lower:
            matching_paths.append(path)

    if not matching_paths:
        return []

    chunks = []
    async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
        for path in matching_paths[:2]:
            try:
                url = WHO_BASE + path
                resp = await client.get(url, headers={
                    "User-Agent": "EBMRetrieval/1.0 (Medical Evidence Retrieval)"
                })
                if resp.status_code != 200:
                    continue

                soup = BeautifulSoup(resp.text, "lxml")

                # Remove noise
                for tag in soup.find_all(["script", "style", "nav", "footer", "header"]):
                    tag.decompose()

                # Get title
                title = ""
                h1 = soup.find("h1")
                if h1:
                    title = h1.get_text(strip=True)

                # Get main content
                main = soup.find("main") or soup.find("article") or soup.find("div", class_=re.compile(r"content", re.I))
                if not main:
                    main = soup.body

                if not main:
                    continue

                # Extract paragraphs
                paragraphs = []
                for p in main.find_all(["p", "li"]):
                    text = p.get_text(strip=True)
                    if len(text) > 30:
                        paragraphs.append(text)

                if not paragraphs:
                    continue

                full_text = " ".join(paragraphs[:20])

                citation = Citation(
                    id=f"who_{hashlib.md5(url.encode()).hexdigest()[:8]}",
                    title=title or f"WHO: {query}",
                    url=url,
                    source_id="who",
                    source_name="World Health Organization",
                    source_category=SourceCategory.GUIDELINE,
                    evidence_level=EvidenceLevel.GUIDELINE,
                    excerpt=full_text[:300],
                )

                # Split into chunks
                for i in range(0, len(full_text), 500):
                    chunk_text = full_text[i:i + 500]
                    if len(chunk_text) > 30:
                        chunks.append(EvidenceChunk(
                            text=chunk_text,
                            citation=citation,
                            section="factsheet",
                            chunk_index=i // 500,
                        ))

            except Exception as e:
                logger.warning(f"WHO factsheet fetch error for {path}: {e}")

    return chunks
