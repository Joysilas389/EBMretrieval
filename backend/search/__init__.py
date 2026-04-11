"""
Search index using PostgreSQL full-text search + trigram fuzzy matching.
Replaces SQLite FTS5 entirely.
"""

import logging
import struct
from typing import Optional
from datetime import datetime

from models import IndexedDocument, SearchResult
from search.database import get_pool

logger = logging.getLogger(__name__)


async def upsert_document(doc: IndexedDocument):
    """Insert or update a document in the PostgreSQL index."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO documents
            (doc_id, title, content, url, source_id, source_name, authors, journal,
             pub_date, year, specialty_tags, evidence_level, source_category,
             excerpt, pmid, doi, indexed_at, freshness_score, language, icd_codes)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18,$19,$20)
            ON CONFLICT (doc_id) DO UPDATE SET
                title=EXCLUDED.title, content=EXCLUDED.content, url=EXCLUDED.url,
                source_name=EXCLUDED.source_name, authors=EXCLUDED.authors,
                journal=EXCLUDED.journal, pub_date=EXCLUDED.pub_date, year=EXCLUDED.year,
                specialty_tags=EXCLUDED.specialty_tags, evidence_level=EXCLUDED.evidence_level,
                source_category=EXCLUDED.source_category, excerpt=EXCLUDED.excerpt,
                pmid=EXCLUDED.pmid, doi=EXCLUDED.doi, indexed_at=EXCLUDED.indexed_at,
                freshness_score=EXCLUDED.freshness_score, language=EXCLUDED.language,
                icd_codes=EXCLUDED.icd_codes
        """, doc.doc_id, doc.title, doc.content, doc.url, doc.source_id,
            doc.source_name, doc.authors, doc.journal, doc.pub_date,
            doc.year, doc.specialty_tags, doc.evidence_level,
            doc.source_category, doc.excerpt, doc.pmid, doc.doi,
            doc.indexed_at, doc.freshness_score,
            getattr(doc, 'language', 'en'),
            getattr(doc, 'icd_codes', ''))


async def search_documents(
    query: str,
    max_results: int = 20,
    source_id: Optional[str] = None,
    specialty: Optional[str] = None,
    language: Optional[str] = None,
    year_min: Optional[int] = None,
) -> list[SearchResult]:
    """Full-text + fuzzy search over PostgreSQL documents."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Build dynamic query with FTS ranking + trigram similarity
        conditions = []
        params = []
        param_idx = 1

        # Full-text search condition
        conditions.append(f"""
            to_tsvector('english', coalesce(title,'') || ' ' || coalesce(content,'') || ' ' || coalesce(specialty_tags,''))
            @@ plainto_tsquery('english', ${param_idx})
        """)
        params.append(query)
        param_idx += 1

        if source_id:
            conditions.append(f"source_id = ${param_idx}")
            params.append(source_id)
            param_idx += 1

        if specialty:
            conditions.append(f"specialty_tags ILIKE ${param_idx}")
            params.append(f"%{specialty}%")
            param_idx += 1

        if language:
            conditions.append(f"language = ${param_idx}")
            params.append(language)
            param_idx += 1

        if year_min:
            conditions.append(f"year >= ${param_idx}")
            params.append(year_min)
            param_idx += 1

        where_clause = " AND ".join(conditions)

        sql = f"""
            SELECT doc_id, title, excerpt, url, source_id, pub_date, specialty_tags,
                   ts_rank(
                       to_tsvector('english', coalesce(title,'') || ' ' || coalesce(content,'') || ' ' || coalesce(specialty_tags,'')),
                       plainto_tsquery('english', $1)
                   ) AS rank_score,
                   similarity(title, $1) AS sim_score
            FROM documents
            WHERE {where_clause}
            ORDER BY rank_score DESC, sim_score DESC
            LIMIT ${param_idx}
        """
        params.append(max_results)

        try:
            rows = await conn.fetch(sql, *params)
            return [
                SearchResult(
                    doc_id=row["doc_id"],
                    title=row["title"],
                    snippet=row["excerpt"][:200] if row["excerpt"] else "",
                    url=row["url"],
                    source_id=row["source_id"],
                    score=float(row["rank_score"]) + float(row["sim_score"]) * 0.3,
                    pub_date=row["pub_date"],
                    specialty_tags=row["specialty_tags"].split(",") if row["specialty_tags"] else [],
                )
                for row in rows
            ]
        except Exception as e:
            logger.warning(f"Search error (falling back to fuzzy): {e}")
            # Fallback: trigram similarity search
            return await _fuzzy_search(conn, query, max_results)


async def _fuzzy_search(conn, query: str, max_results: int) -> list[SearchResult]:
    """Fallback fuzzy search using trigram similarity."""
    try:
        rows = await conn.fetch("""
            SELECT doc_id, title, excerpt, url, source_id, pub_date, specialty_tags,
                   similarity(title, $1) AS score
            FROM documents
            WHERE similarity(title, $1) > 0.1
               OR title ILIKE '%' || $1 || '%'
               OR content ILIKE '%' || $1 || '%'
            ORDER BY score DESC
            LIMIT $2
        """, query, max_results)
        return [
            SearchResult(
                doc_id=row["doc_id"],
                title=row["title"],
                snippet=row["excerpt"][:200] if row["excerpt"] else "",
                url=row["url"],
                source_id=row["source_id"],
                score=float(row["score"]),
                pub_date=row["pub_date"],
                specialty_tags=row["specialty_tags"].split(",") if row["specialty_tags"] else [],
            )
            for row in rows
        ]
    except Exception as e:
        logger.error(f"Fuzzy search error: {e}")
        return []


async def get_document(doc_id: str) -> Optional[dict]:
    """Get a single document by ID."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM documents WHERE doc_id = $1", doc_id)
        return dict(row) if row else None


async def log_crawl(source_id: str, url: str, status: str, message: str = "", duration_ms: int = 0):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO crawl_log (source_id, url, status, message, duration_ms)
            VALUES ($1, $2, $3, $4, $5)
        """, source_id, url, status, message, duration_ms)


async def search_icd(query: str, max_results: int = 10) -> list[dict]:
    """Search ICD-11 codes."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT code, title, chapter, description,
                   similarity(title, $1) AS score
            FROM icd_codes
            WHERE title ILIKE '%' || $1 || '%'
               OR synonyms ILIKE '%' || $1 || '%'
               OR code ILIKE '%' || $1 || '%'
            ORDER BY score DESC
            LIMIT $2
        """, query, max_results)
        return [dict(r) for r in rows]


async def upsert_icd_code(code: str, title: str, parent: str = "", chapter: str = "",
                           description: str = "", synonyms: str = ""):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO icd_codes (code, title, parent_code, chapter, description, synonyms)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (code) DO UPDATE SET
                title=EXCLUDED.title, parent_code=EXCLUDED.parent_code,
                chapter=EXCLUDED.chapter, description=EXCLUDED.description,
                synonyms=EXCLUDED.synonyms
        """, code, title, parent, chapter, description, synonyms)
