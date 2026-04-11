"""
Europe PMC Crawler — free open API for biomedical and life sciences literature.
Covers PubMed, PMC, and additional European sources.
API: https://www.ebi.ac.uk/europepmc/webservices/rest/
No API key required. Public domain metadata.
"""

import logging
import hashlib

import httpx

from models import Citation, EvidenceChunk, EvidenceLevel, SourceCategory

logger = logging.getLogger(__name__)

EUROPEPMC_API = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"


async def search_europe_pmc(query: str, max_results: int = 5) -> list[EvidenceChunk]:
    """Search Europe PMC for open-access biomedical literature."""
    params = {
        "query": query,
        "resultType": "core",
        "pageSize": str(max_results),
        "format": "json",
        "sort": "RELEVANCE",
    }

    chunks = []
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(EUROPEPMC_API, params=params)
            resp.raise_for_status()
            data = resp.json()

            results = data.get("resultList", {}).get("result", [])
            for item in results:
                title = item.get("title", "").strip()
                abstract = item.get("abstractText", "").strip()
                pmid = item.get("pmid", "")
                pmcid = item.get("pmcid", "")
                doi = item.get("doi", "")
                source = item.get("source", "")
                journal = item.get("journalTitle", "")
                year = item.get("pubYear", "")
                authors_list = item.get("authorList", {}).get("author", [])
                authors = [a.get("fullName", "") for a in authors_list[:5] if a.get("fullName")]

                if not title:
                    continue

                # Build URL
                if pmcid:
                    url = f"https://europepmc.org/article/PMC/{pmcid}"
                elif pmid:
                    url = f"https://europepmc.org/article/MED/{pmid}"
                elif doi:
                    url = f"https://doi.org/{doi}"
                else:
                    url = f"https://europepmc.org/search?query={query}"

                # Determine evidence level from pub type
                pub_types = item.get("pubTypeList", {}).get("pubType", [])
                ev_level = EvidenceLevel.UNKNOWN
                if "review" in " ".join(pub_types).lower():
                    ev_level = EvidenceLevel.SYSTEMATIC_REVIEW
                elif "clinical trial" in " ".join(pub_types).lower():
                    ev_level = EvidenceLevel.RCT

                citation = Citation(
                    id=f"epmc_{pmid or pmcid or hashlib.md5(title.encode()).hexdigest()[:8]}",
                    title=title,
                    url=url,
                    source_id="europe_pmc",
                    source_name="Europe PMC",
                    authors=authors,
                    journal=journal,
                    year=int(year) if year.isdigit() else None,
                    pub_date=year,
                    source_category=SourceCategory.JOURNAL_ARTICLE,
                    evidence_level=ev_level,
                    excerpt=(abstract or title)[:300],
                    pmid=pmid,
                    doi=doi,
                )

                text = abstract or title
                # Chunk the abstract
                if len(text) > 400:
                    for i in range(0, len(text), 400):
                        ct = text[i:i + 400]
                        if len(ct) > 30:
                            chunks.append(EvidenceChunk(
                                text=ct, citation=citation,
                                section="abstract", chunk_index=i // 400,
                            ))
                else:
                    chunks.append(EvidenceChunk(
                        text=text, citation=citation, section="abstract",
                    ))

    except Exception as e:
        logger.warning(f"Europe PMC search error: {e}")

    return chunks
