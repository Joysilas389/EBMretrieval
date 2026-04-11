"""
PubMed / NCBI Entrez crawler.
Uses the official NCBI E-utilities API (free, legal, rate-limited).
Retrieves abstracts, metadata, and open-access full-text links.
"""

import asyncio
import logging
import os
import xml.etree.ElementTree as ET
from typing import Optional
from datetime import datetime

import httpx

from models import Citation, EvidenceChunk, EvidenceLevel, SourceCategory

logger = logging.getLogger(__name__)

NCBI_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
NCBI_API_KEY = os.getenv("NCBI_API_KEY", "")
NCBI_EMAIL = os.getenv("NCBI_EMAIL", "ebmretrieval@example.com")
RATE_LIMIT = 0.11 if NCBI_API_KEY else 0.34  # 10/sec with key, 3/sec without


def _base_params() -> dict:
    params = {"tool": "ebmretrieval", "email": NCBI_EMAIL}
    if NCBI_API_KEY:
        params["api_key"] = NCBI_API_KEY
    return params


async def search_pubmed(query: str, max_results: int = 10, sort: str = "relevance") -> list[str]:
    """Search PubMed and return list of PMIDs."""
    params = {
        **_base_params(),
        "db": "pubmed",
        "term": query,
        "retmax": str(max_results),
        "sort": sort,
        "retmode": "json",
    }
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(f"{NCBI_BASE}esearch.fcgi", params=params)
            resp.raise_for_status()
            data = resp.json()
            return data.get("esearchresult", {}).get("idlist", [])
    except Exception as e:
        logger.error(f"PubMed search error: {e}")
        return []


async def fetch_pubmed_abstracts(pmids: list[str]) -> list[dict]:
    """Fetch article metadata and abstracts for given PMIDs."""
    if not pmids:
        return []
    params = {
        **_base_params(),
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "xml",
        "rettype": "abstract",
    }
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(f"{NCBI_BASE}efetch.fcgi", params=params)
            resp.raise_for_status()
            return _parse_pubmed_xml(resp.text)
    except Exception as e:
        logger.error(f"PubMed fetch error: {e}")
        return []


def _parse_pubmed_xml(xml_text: str) -> list[dict]:
    """Parse PubMed XML response into structured dicts."""
    results = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        logger.error(f"XML parse error: {e}")
        return []

    for article in root.findall(".//PubmedArticle"):
        try:
            medline = article.find(".//MedlineCitation")
            if medline is None:
                continue

            pmid_el = medline.find("PMID")
            pmid = pmid_el.text if pmid_el is not None else ""

            art = medline.find(".//Article")
            if art is None:
                continue

            title_el = art.find("ArticleTitle")
            title = "".join(title_el.itertext()) if title_el is not None else "Untitled"

            # Abstract
            abstract_parts = []
            abstract_el = art.find("Abstract")
            if abstract_el is not None:
                for at in abstract_el.findall("AbstractText"):
                    label = at.get("Label", "")
                    text = "".join(at.itertext())
                    if label:
                        abstract_parts.append(f"{label}: {text}")
                    else:
                        abstract_parts.append(text)
            abstract = " ".join(abstract_parts)

            # Authors
            authors = []
            for author in art.findall(".//Author"):
                last = author.find("LastName")
                first = author.find("ForeName")
                if last is not None:
                    name = last.text or ""
                    if first is not None:
                        name = f"{name} {first.text}"
                    authors.append(name)

            # Journal
            journal_el = art.find(".//Journal/Title")
            journal = journal_el.text if journal_el is not None else ""

            # Date
            year = ""
            date_el = art.find(".//Journal/JournalIssue/PubDate/Year")
            if date_el is not None:
                year = date_el.text or ""

            # DOI
            doi = ""
            for eid in article.findall(".//ArticleIdList/ArticleId"):
                if eid.get("IdType") == "doi":
                    doi = eid.text or ""
                    break

            # MeSH terms for specialty detection
            mesh_terms = []
            for mesh in medline.findall(".//MeshHeading/DescriptorName"):
                if mesh.text:
                    mesh_terms.append(mesh.text)

            # Publication type
            pub_types = []
            for pt in art.findall(".//PublicationTypeList/PublicationType"):
                if pt.text:
                    pub_types.append(pt.text)

            results.append({
                "pmid": pmid,
                "title": title,
                "abstract": abstract,
                "authors": authors,
                "journal": journal,
                "year": year,
                "doi": doi,
                "mesh_terms": mesh_terms,
                "pub_types": pub_types,
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            })
        except Exception as e:
            logger.warning(f"Error parsing article: {e}")
            continue

    return results


async def search_pmc(query: str, max_results: int = 5) -> list[str]:
    """Search PMC for open-access full-text articles."""
    params = {
        **_base_params(),
        "db": "pmc",
        "term": f"{query} AND open access[filter]",
        "retmax": str(max_results),
        "retmode": "json",
    }
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(f"{NCBI_BASE}esearch.fcgi", params=params)
            resp.raise_for_status()
            data = resp.json()
            return data.get("esearchresult", {}).get("idlist", [])
    except Exception as e:
        logger.error(f"PMC search error: {e}")
        return []


async def search_ncbi_books(query: str, max_results: int = 5) -> list[dict]:
    """Search NCBI Bookshelf (StatPearls, open textbooks)."""
    params = {
        **_base_params(),
        "db": "books",
        "term": query,
        "retmax": str(max_results),
        "retmode": "xml",
    }
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(f"{NCBI_BASE}esearch.fcgi", params=params)
            resp.raise_for_status()
            # Parse IDs then fetch details
            root = ET.fromstring(resp.text)
            ids = [el.text for el in root.findall(".//Id") if el.text]
            if not ids:
                return []

            # Fetch summaries
            summary_params = {
                **_base_params(),
                "db": "books",
                "id": ",".join(ids[:max_results]),
                "retmode": "xml",
            }
            resp2 = await client.get(f"{NCBI_BASE}esummary.fcgi", params=summary_params)
            resp2.raise_for_status()
            return _parse_books_summary(resp2.text)
    except Exception as e:
        logger.error(f"NCBI Books search error: {e}")
        return []


def _parse_books_summary(xml_text: str) -> list[dict]:
    """Parse NCBI Books summary XML."""
    results = []
    try:
        root = ET.fromstring(xml_text)
        for doc in root.findall(".//DocSum"):
            rid = ""
            title = ""
            for item in doc.findall("Item"):
                name = item.get("Name", "")
                if name == "Title":
                    title = item.text or ""
                elif name == "RID":
                    rid = item.text or ""
            if rid and title:
                results.append({
                    "id": rid,
                    "title": title,
                    "url": f"https://www.ncbi.nlm.nih.gov/books/{rid}/",
                    "source": "ncbi_books",
                })
    except Exception as e:
        logger.error(f"Books parse error: {e}")
    return results


def classify_evidence_level(pub_types: list[str]) -> EvidenceLevel:
    """Classify evidence level from publication types."""
    pts = " ".join(pub_types).lower()
    if "systematic review" in pts or "meta-analysis" in pts:
        return EvidenceLevel.SYSTEMATIC_REVIEW
    if "randomized controlled trial" in pts:
        return EvidenceLevel.RCT
    if "practice guideline" in pts or "guideline" in pts:
        return EvidenceLevel.GUIDELINE
    if "review" in pts:
        return EvidenceLevel.EXPERT_OPINION
    if "case reports" in pts:
        return EvidenceLevel.CASE_REPORT
    return EvidenceLevel.UNKNOWN


def article_to_citation(article: dict) -> Citation:
    """Convert a parsed PubMed article dict to a Citation."""
    return Citation(
        id=f"pubmed_{article['pmid']}",
        title=article["title"],
        url=article["url"],
        source_id="pubmed",
        source_name="PubMed",
        authors=article.get("authors", []),
        journal=article.get("journal", ""),
        year=int(article["year"]) if article.get("year", "").isdigit() else None,
        pub_date=article.get("year", ""),
        source_category=SourceCategory.JOURNAL_ARTICLE,
        evidence_level=classify_evidence_level(article.get("pub_types", [])),
        excerpt=article.get("abstract", "")[:500],
        pmid=article["pmid"],
        doi=article.get("doi", ""),
    )


def article_to_chunks(article: dict, citation: Citation) -> list[EvidenceChunk]:
    """Split article abstract into evidence chunks."""
    abstract = article.get("abstract", "")
    if not abstract:
        return []

    # Split on labeled sections (BACKGROUND:, METHODS:, etc.)
    chunks = []
    sections = abstract.split("\n")
    for i, section in enumerate(sections):
        section = section.strip()
        if not section:
            continue
        # Detect section labels
        sec_name = ""
        for label in ["BACKGROUND", "OBJECTIVE", "METHODS", "RESULTS", "CONCLUSIONS", "INTRODUCTION", "FINDINGS"]:
            if section.upper().startswith(f"{label}:"):
                sec_name = label.lower()
                break
        chunks.append(EvidenceChunk(
            text=section,
            citation=citation,
            section=sec_name,
            chunk_index=i,
        ))

    if not chunks:
        # Fallback: treat entire abstract as one chunk
        chunks.append(EvidenceChunk(
            text=abstract,
            citation=citation,
            section="abstract",
            chunk_index=0,
        ))

    return chunks
