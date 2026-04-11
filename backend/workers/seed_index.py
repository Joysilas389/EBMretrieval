"""
Seed the PostgreSQL index with initial documents from PubMed.
Run: python -m workers.seed_index
"""

import asyncio
import logging
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from search.database import init_db, get_document_count
from search import upsert_document, log_crawl
from models import IndexedDocument
from crawlers.pubmed_crawler import search_pubmed, fetch_pubmed_abstracts

logging.basicConfig(level="INFO")
logger = logging.getLogger(__name__)

SEED_QUERIES = [
    "hypertension treatment guidelines 2024",
    "diabetes mellitus management",
    "acute myocardial infarction",
    "pneumonia antibiotic therapy",
    "stroke thrombolysis guidelines",
    "heart failure management",
    "asthma treatment guidelines",
    "chronic kidney disease staging",
    "sepsis management surviving sepsis",
    "COVID-19 treatment guidelines",
    "atrial fibrillation anticoagulation",
    "depression treatment SSRI",
    "rheumatoid arthritis treatment",
    "inflammatory bowel disease",
    "epilepsy treatment guidelines",
    "breast cancer screening",
    "colorectal cancer screening",
    "prenatal care guidelines",
    "pediatric fever management",
    "osteoporosis prevention treatment",
    "malaria treatment WHO",
    "tuberculosis treatment",
    "HIV antiretroviral therapy",
    "sickle cell disease management",
    "preeclampsia management",
]


async def seed_from_pubmed():
    logger.info("Starting PubMed seed into PostgreSQL...")
    total = 0

    for query in SEED_QUERIES:
        logger.info(f"Seeding: {query}")
        start = time.time()

        try:
            pmids = await search_pubmed(query, max_results=5)
            if not pmids:
                logger.warning(f"No results for: {query}")
                continue

            articles = await fetch_pubmed_abstracts(pmids)

            for article in articles:
                if not article.get("abstract"):
                    continue

                doc = IndexedDocument(
                    doc_id=f"pubmed_{article['pmid']}",
                    title=article["title"],
                    content=article["abstract"],
                    url=article["url"],
                    source_id="pubmed",
                    source_name="PubMed",
                    authors=", ".join(article.get("authors", [])[:5]),
                    journal=article.get("journal", ""),
                    pub_date=article.get("year", ""),
                    year=int(article["year"]) if article.get("year", "").isdigit() else 0,
                    specialty_tags=",".join(article.get("mesh_terms", [])[:5]),
                    evidence_level="unknown",
                    source_category="journal_article",
                    excerpt=article["abstract"][:300],
                    pmid=article["pmid"],
                    doi=article.get("doi", ""),
                )
                await upsert_document(doc)
                total += 1

            elapsed = int((time.time() - start) * 1000)
            await log_crawl("pubmed", f"seed:{query}", "success", f"{len(articles)} articles", elapsed)
            await asyncio.sleep(0.35)

        except Exception as e:
            logger.error(f"Error seeding '{query}': {e}")
            try:
                await log_crawl("pubmed", f"seed:{query}", "error", str(e))
            except Exception:
                pass

    count = await get_document_count()
    logger.info(f"Seed complete. Total documents: {total}. In DB: {count}")


async def main():
    await init_db()
    await seed_from_pubmed()


if __name__ == "__main__":
    asyncio.run(main())
