"""
Database connection manager for PostgreSQL on Render.
Handles: connection pooling, schema init, health checks.
"""

import os
import logging
from contextlib import asynccontextmanager
from typing import Optional

import asyncpg

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://medscribe_hcee_user:2hzupPdJmkAdCVZdtkemPZ1QrPiU1chr@dpg-d74g1j0gjchc73b6r2v0-a/medscribe_hcee"
)

# Global connection pool
_pool: Optional[asyncpg.Pool] = None


async def get_pool() -> asyncpg.Pool:
    """Get or create the connection pool."""
    global _pool
    if _pool is None or _pool._closed:
        _pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=2,
            max_size=10,
            command_timeout=30,
            statement_cache_size=0,
        )
        logger.info("PostgreSQL connection pool created")
    return _pool


async def close_pool():
    """Close the connection pool."""
    global _pool
    if _pool and not _pool._closed:
        await _pool.close()
        _pool = None
        logger.info("PostgreSQL connection pool closed")


async def init_db():
    """Initialize all database tables and extensions. Uses advisory lock to prevent race conditions."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("SELECT pg_advisory_lock(12345)")
        try:
            try:
                await conn.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
            except Exception:
                pass

            await conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    doc_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    url TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    source_name TEXT NOT NULL DEFAULT '',
                    authors TEXT DEFAULT '',
                    journal TEXT DEFAULT '',
                    pub_date TEXT DEFAULT '',
                    year INTEGER DEFAULT 0,
                    specialty_tags TEXT DEFAULT '',
                    evidence_level TEXT DEFAULT '',
                    source_category TEXT DEFAULT '',
                    excerpt TEXT DEFAULT '',
                    pmid TEXT DEFAULT '',
                    doi TEXT DEFAULT '',
                    indexed_at TIMESTAMPTZ DEFAULT NOW(),
                    freshness_score REAL DEFAULT 1.0,
                    language TEXT DEFAULT 'en',
                    icd_codes TEXT DEFAULT '',
                    embedding BYTEA DEFAULT NULL
                );
            """)

            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_documents_fts
                ON documents USING GIN (
                    to_tsvector('english', coalesce(title, '') || ' ' || coalesce(content, '') || ' ' || coalesce(specialty_tags, ''))
                );
            """)

            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_documents_title_trgm
                ON documents USING GIN (title gin_trgm_ops);
            """)

            await conn.execute("CREATE INDEX IF NOT EXISTS idx_documents_source ON documents (source_id);")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_documents_year ON documents (year DESC);")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_documents_specialty ON documents USING GIN (specialty_tags gin_trgm_ops);")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_documents_icd ON documents USING GIN (icd_codes gin_trgm_ops);")

            await conn.execute("""
                CREATE TABLE IF NOT EXISTS crawl_log (
                    id SERIAL PRIMARY KEY,
                    source_id TEXT NOT NULL,
                    url TEXT NOT NULL,
                    status TEXT NOT NULL,
                    message TEXT DEFAULT '',
                    crawled_at TIMESTAMPTZ DEFAULT NOW(),
                    duration_ms INTEGER DEFAULT 0
                );
            """)

            await conn.execute("""
                CREATE TABLE IF NOT EXISTS icd_codes (
                    code TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    parent_code TEXT DEFAULT '',
                    chapter TEXT DEFAULT '',
                    block TEXT DEFAULT '',
                    category TEXT DEFAULT '',
                    description TEXT DEFAULT '',
                    synonyms TEXT DEFAULT '',
                    indexed_at TIMESTAMPTZ DEFAULT NOW()
                );
            """)
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_icd_title_trgm ON icd_codes USING GIN (title gin_trgm_ops);")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_icd_synonyms_trgm ON icd_codes USING GIN (synonyms gin_trgm_ops);")

            await conn.execute("""
                CREATE TABLE IF NOT EXISTS pdf_guidelines (
                    id SERIAL PRIMARY KEY,
                    url TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    source_id TEXT DEFAULT '',
                    content TEXT DEFAULT '',
                    specialty_tags TEXT DEFAULT '',
                    parsed_at TIMESTAMPTZ DEFAULT NOW(),
                    page_count INTEGER DEFAULT 0,
                    file_hash TEXT DEFAULT ''
                );
            """)

            await conn.execute("""
                CREATE TABLE IF NOT EXISTS condition_comparisons (
                    id SERIAL PRIMARY KEY,
                    condition_a TEXT NOT NULL,
                    condition_b TEXT NOT NULL,
                    comparison_data JSONB DEFAULT '{}',
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
            """)

            logger.info("Database schema initialized successfully")
        finally:
            await conn.execute("SELECT pg_advisory_unlock(12345)")


async def get_document_count() -> int:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchval("SELECT COUNT(*) FROM documents")
        return row or 0


async def drop_all_tables():
    """Drop all tables — use for clean reset of the medscribe_hcee DB."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("SELECT pg_advisory_lock(12345)")
        try:
            await conn.execute("DROP TABLE IF EXISTS documents CASCADE;")
            await conn.execute("DROP TABLE IF EXISTS crawl_log CASCADE;")
            await conn.execute("DROP TABLE IF EXISTS icd_codes CASCADE;")
            await conn.execute("DROP TABLE IF EXISTS pdf_guidelines CASCADE;")
            await conn.execute("DROP TABLE IF EXISTS condition_comparisons CASCADE;")
            logger.info("All tables dropped")
        finally:
            await conn.execute("SELECT pg_advisory_unlock(12345)")
