"""
MedlinePlus Crawler — uses NLM's free XML web service.
Endpoint: https://wsearch.nlm.nih.gov/ws/query
Returns health topic summaries from MedlinePlus (US government public domain).
"""

import logging
import xml.etree.ElementTree as ET
from typing import Optional

import httpx

from models import Citation, EvidenceChunk, EvidenceLevel, SourceCategory

logger = logging.getLogger(__name__)

MEDLINEPLUS_API = "https://wsearch.nlm.nih.gov/ws/query"


async def search_medlineplus(query: str, max_results: int = 5) -> list[EvidenceChunk]:
    """Search MedlinePlus health topics via NLM web service."""
    params = {
        "db": "healthTopics",
        "term": query,
        "retmax": str(max_results),
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(MEDLINEPLUS_API, params=params)
            resp.raise_for_status()
            return _parse_medlineplus_xml(resp.text, query)
    except Exception as e:
        logger.warning(f"MedlinePlus search error: {e}")
        return []


def _parse_medlineplus_xml(xml_text: str, query: str) -> list[EvidenceChunk]:
    """Parse MedlinePlus XML response."""
    chunks = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        logger.warning(f"MedlinePlus XML parse error: {e}")
        return []

    for doc in root.findall(".//document"):
        try:
            url = doc.get("url", "")
            title = ""
            snippet = ""

            for content in doc.findall("content"):
                name = content.get("name", "")
                # Get ALL text including from child elements
                raw = "".join(content.itertext()) or content.text or ""
                # Also strip any remaining HTML tags
                raw = re.sub(r'<[^>]+>', ' ', raw)
                raw = re.sub(r'&[a-zA-Z]+;', ' ', raw)
                raw = re.sub(r'\s+', ' ', raw).strip()
                if name == "title":
                    title = raw
                elif name == "FullSummary":
                    snippet = raw[:2000]
                elif name == "snippet" and not snippet:
                    snippet = raw[:1000]

            if not title or not snippet:
                continue

            citation = Citation(
                id=f"medlineplus_{hash(url) & 0xFFFFFFFF:08x}",
                title=title,
                url=url,
                source_id="medlineplus",
                source_name="MedlinePlus (NLM)",
                source_category=SourceCategory.PUBLIC_HEALTH,
                evidence_level=EvidenceLevel.PUBLIC_HEALTH,
                excerpt=snippet[:300],
            )

            # Split summary into chunks
            sentences = snippet.split(". ")
            chunk_text = ""
            for sent in sentences:
                chunk_text += sent + ". "
                if len(chunk_text) > 300:
                    chunks.append(EvidenceChunk(
                        text=chunk_text.strip(),
                        citation=citation,
                        section="summary",
                    ))
                    chunk_text = ""
            if chunk_text.strip():
                chunks.append(EvidenceChunk(
                    text=chunk_text.strip(),
                    citation=citation,
                    section="summary",
                ))

        except Exception as e:
            logger.warning(f"MedlinePlus doc parse error: {e}")
            continue

    return chunks
