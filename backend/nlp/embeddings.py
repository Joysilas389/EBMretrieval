"""
Vector embeddings for semantic search — runs locally, no external AI APIs.
Uses sentence-transformers (all-MiniLM-L6-v2) for lightweight medical text embedding.
Embeddings stored in PostgreSQL as BYTEA for simplicity.
"""

import logging
import struct
from typing import Optional

logger = logging.getLogger(__name__)

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

# Lazy-loaded model
_model = None
_model_name = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384


def _get_model():
    """Lazy-load the sentence transformer model."""
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer(_model_name)
            logger.info(f"Loaded embedding model: {_model_name}")
        except ImportError:
            logger.warning("sentence-transformers not installed, embeddings disabled")
            return None
        except Exception as e:
            logger.warning(f"Failed to load embedding model: {e}")
            return None
    return _model


def embed_text(text: str) -> Optional[bytes]:
    """Embed text into a vector. Returns bytes for PostgreSQL storage."""
    model = _get_model()
    if model is None:
        return None
    try:
        text = text[:2000]  # Limit input length
        embedding = model.encode(text, show_progress_bar=False, normalize_embeddings=True)
        return embedding.tobytes()
    except Exception as e:
        logger.warning(f"Embedding error: {e}")
        return None


def embed_texts(texts: list[str]) -> list[Optional[bytes]]:
    """Batch embed multiple texts."""
    model = _get_model()
    if model is None:
        return [None] * len(texts)
    try:
        truncated = [t[:2000] for t in texts]
        embeddings = model.encode(truncated, show_progress_bar=False, normalize_embeddings=True, batch_size=32)
        return [e.tobytes() for e in embeddings]
    except Exception as e:
        logger.warning(f"Batch embedding error: {e}")
        return [None] * len(texts)


def bytes_to_vector(data: bytes) -> np.ndarray:
    """Convert stored bytes back to numpy vector."""
    return np.frombuffer(data, dtype=np.float32)


def cosine_similarity(a: bytes, b: bytes) -> float:
    """Compute cosine similarity between two embedding byte arrays."""
    va = bytes_to_vector(a)
    vb = bytes_to_vector(b)
    dot = np.dot(va, vb)
    norm_a = np.linalg.norm(va)
    norm_b = np.linalg.norm(vb)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(dot / (norm_a * norm_b))


async def semantic_search(query: str, pool, max_results: int = 10) -> list[dict]:
    """
    Semantic search using vector similarity.
    Fetches documents with embeddings, computes cosine similarity in Python.
    For production, consider pgvector extension.
    """
    query_embedding = embed_text(query)
    if query_embedding is None:
        return []

    async with pool.acquire() as conn:
        # Get documents that have embeddings
        rows = await conn.fetch("""
            SELECT doc_id, title, excerpt, url, source_id, pub_date, specialty_tags, embedding
            FROM documents
            WHERE embedding IS NOT NULL
            LIMIT 500
        """)

    if not rows:
        return []

    # Compute similarities
    results = []
    query_vec = bytes_to_vector(query_embedding)
    for row in rows:
        if row["embedding"]:
            doc_vec = bytes_to_vector(row["embedding"])
            sim = float(np.dot(query_vec, doc_vec))
            results.append({
                "doc_id": row["doc_id"],
                "title": row["title"],
                "snippet": row["excerpt"][:200] if row["excerpt"] else "",
                "url": row["url"],
                "source_id": row["source_id"],
                "score": sim,
                "pub_date": row["pub_date"],
                "specialty_tags": row["specialty_tags"].split(",") if row["specialty_tags"] else [],
            })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:max_results]


def is_available() -> bool:
    """Check if embedding model can be loaded."""
    return _get_model() is not None
