"""
OpenFDA Crawler — retrieves drug labels, adverse events, and recalls.
Uses the official OpenFDA API (free, no key required, public domain).
Endpoint: https://api.fda.gov/
"""

import logging
import hashlib

import httpx

from models import Citation, EvidenceChunk, EvidenceLevel, SourceCategory

logger = logging.getLogger(__name__)

OPENFDA_BASE = "https://api.fda.gov"


async def search_openfda_drugs(query: str, max_results: int = 5) -> list[EvidenceChunk]:
    """Search OpenFDA drug labels for drug information."""
    chunks = []

    # Drug labels endpoint
    try:
        label_chunks = await _search_drug_labels(query, max_results)
        chunks.extend(label_chunks)
    except Exception as e:
        logger.warning(f"OpenFDA drug label error: {e}")

    # Adverse events (if query seems drug-related)
    drug_keywords = ["side effect", "adverse", "reaction", "safety", "warning", "interaction"]
    if any(kw in query.lower() for kw in drug_keywords):
        try:
            ae_chunks = await _search_adverse_events(query, max_results=3)
            chunks.extend(ae_chunks)
        except Exception as e:
            logger.warning(f"OpenFDA adverse events error: {e}")

    return chunks[:max_results * 2]


async def _search_drug_labels(query: str, max_results: int) -> list[EvidenceChunk]:
    """Search FDA drug labels."""
    params = {
        "search": f'openfda.generic_name:"{query}" OR openfda.brand_name:"{query}" OR purpose:"{query}" OR indications_and_usage:"{query}"',
        "limit": str(min(max_results, 5)),
    }

    chunks = []
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(f"{OPENFDA_BASE}/drug/label.json", params=params)
            if resp.status_code != 200:
                return []

            data = resp.json()
            results = data.get("results", [])

            for item in results:
                openfda = item.get("openfda", {})
                generic_names = openfda.get("generic_name", [])
                brand_names = openfda.get("brand_name", [])
                name = (generic_names[0] if generic_names else
                        brand_names[0] if brand_names else "Unknown Drug")

                # Gather useful sections
                sections = []
                for field in ["indications_and_usage", "dosage_and_administration",
                              "warnings", "adverse_reactions", "drug_interactions",
                              "mechanism_of_action", "contraindications"]:
                    content = item.get(field, [])
                    if content:
                        text = content[0] if isinstance(content, list) else content
                        sections.append((field.replace("_", " ").title(), text[:500]))

                if not sections:
                    continue

                spl_id = item.get("id", hashlib.md5(name.encode()).hexdigest()[:8])
                url = f"https://dailymed.nlm.nih.gov/dailymed/search.cfm?query={name}"

                citation = Citation(
                    id=f"fda_{spl_id[:12]}",
                    title=f"{name} — FDA Drug Label",
                    url=url,
                    source_id="fda",
                    source_name="FDA (OpenFDA)",
                    source_category=SourceCategory.DRUG_INFO,
                    evidence_level=EvidenceLevel.GUIDELINE,
                    excerpt=sections[0][1][:300] if sections else "",
                )

                for sec_name, sec_text in sections:
                    chunks.append(EvidenceChunk(
                        text=f"{sec_name}: {sec_text}",
                        citation=citation,
                        section=sec_name.lower(),
                    ))

    except Exception as e:
        logger.warning(f"OpenFDA label search error: {e}")

    return chunks


async def _search_adverse_events(query: str, max_results: int = 3) -> list[EvidenceChunk]:
    """Search FDA adverse event reports."""
    params = {
        "search": f'patient.drug.medicinalproduct:"{query}"',
        "count": "patient.reaction.reactionmeddrapt.exact",
        "limit": "10",
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(f"{OPENFDA_BASE}/drug/event.json", params=params)
            if resp.status_code != 200:
                return []

            data = resp.json()
            results = data.get("results", [])

            if not results:
                return []

            # Summarize top adverse events
            top_reactions = [f"{r['term']} ({r['count']} reports)" for r in results[:8]]
            summary = f"Most reported adverse events for {query}: " + ", ".join(top_reactions)

            citation = Citation(
                id=f"fda_ae_{hashlib.md5(query.encode()).hexdigest()[:8]}",
                title=f"FDA Adverse Event Reports — {query}",
                url=f"https://api.fda.gov/drug/event.json?search=patient.drug.medicinalproduct:%22{query}%22",
                source_id="fda",
                source_name="FDA (OpenFDA FAERS)",
                source_category=SourceCategory.DRUG_INFO,
                evidence_level=EvidenceLevel.PUBLIC_HEALTH,
                excerpt=summary[:300],
            )

            return [EvidenceChunk(
                text=summary,
                citation=citation,
                section="adverse_events",
            )]

    except Exception as e:
        logger.warning(f"OpenFDA AE error: {e}")
        return []
