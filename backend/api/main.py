"""
EBMRetrieval API Server v2 — FastAPI with PostgreSQL.
Endpoints: /api/answer, /api/compare, /api/icd, /api/pdf, /api/languages, etc.
"""

import logging
import os
import sys
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from search.database import init_db, get_document_count, close_pool, drop_all_tables
from api.answer_engine import generate_answer, compare_conditions
from models.specialties import SPECIALTIES
from models.source_registry import SOURCES
from models.icd11 import seed_icd11_codes, lookup_icd11
from nlp.multilingual import get_supported_languages

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Drop old tables and reinitialize for clean EBMRetrieval schema
    first_run = os.getenv("RESET_DB", "false").lower() == "true"
    if first_run:
        await drop_all_tables()
    await init_db()
    doc_count = await get_document_count()
    logger.info(f"DB initialized. Documents: {doc_count}")
    # Seed ICD-11 codes
    try:
        await seed_icd11_codes()
    except Exception as e:
        logger.warning(f"ICD-11 seed skipped: {e}")
    yield
    await close_pool()


app = FastAPI(
    title="EBMRetrieval API",
    description="Evidence-Based Medicine Retrieval Engine — PostgreSQL backed",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url, "http://localhost:3000", "http://localhost:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# REQUEST / RESPONSE MODELS
# ============================================================
class AnswerRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=2000)
    max_sources: int = Field(default=10, ge=1, le=30)
    max_words: int = Field(default=2000, ge=100, le=16000)
    teaching_mode: bool = False
    citation_density: str = "standard"
    source_preference: str = "balanced"
    specialty_filter: Optional[str] = None
    language: Optional[str] = None


class CompareRequest(BaseModel):
    condition_a: str = Field(..., min_length=2, max_length=500)
    condition_b: str = Field(..., min_length=2, max_length=500)
    max_sources: int = Field(default=8, ge=2, le=20)


class CitationResponse(BaseModel):
    id: str
    title: str
    url: str
    source_name: str
    authors: list[str] = []
    journal: str = ""
    year: Optional[int] = None
    pub_date: str = ""
    source_category: str = ""
    evidence_level: str = ""
    excerpt: str = ""
    specialty_tags: list[str] = []
    pmid: str = ""
    doi: str = ""
    reliability: str = "standard"
    access_date: str = ""


class AnswerBlockResponse(BaseModel):
    text: str
    citation_indices: list[int] = []
    block_type: str = "paragraph"


class AnswerResponse(BaseModel):
    query: str
    blocks: list[AnswerBlockResponse]
    citations: list[CitationResponse]
    specialties: list[str]
    confidence: str
    warnings: list[str]
    teaching_mode: bool
    retrieval_time_ms: int
    total_sources_consulted: int


class PDFParseRequest(BaseModel):
    url: str = Field(..., min_length=10, max_length=2000)


# ============================================================
# ENDPOINTS
# ============================================================
# Simple visit counter (in-memory, resets on restart — upgrade to DB for persistence)
_visit_count = 0
_query_count = 0

@app.get("/api/health")
async def health():
    try:
        doc_count = await get_document_count()
    except Exception:
        doc_count = -1
    return {
        "status": "ok",
        "database": "postgresql",
        "documents_indexed": doc_count,
        "sources_registered": len(SOURCES),
        "version": "3.0.0",
        "total_queries": _query_count,
        "claude_api": "configured" if os.getenv("ANTHROPIC_API_KEY") else "NOT configured",
    }


@app.get("/api/stats")
async def stats():
    """Simple analytics — visit and query counts."""
    return {
        "queries": _query_count,
        "visits": _visit_count,
    }


@app.post("/api/visit")
async def track_visit():
    """Track a page visit."""
    global _visit_count
    _visit_count += 1
    return {"visits": _visit_count}


@app.post("/api/answer", response_model=AnswerResponse)
async def get_answer(req: AnswerRequest):
    global _query_count
    _query_count += 1
    try:
        result = await generate_answer(
            query=req.query,
            max_sources=req.max_sources,
            max_words=req.max_words,
            teaching_mode=req.teaching_mode,
            citation_density=req.citation_density,
            source_preference=req.source_preference,
            specialty_filter=req.specialty_filter,
            language=req.language,
        )
        return AnswerResponse(
            query=result.query,
            blocks=[
                AnswerBlockResponse(text=b.text, citation_indices=b.citation_indices, block_type=b.block_type)
                for b in result.blocks
            ],
            citations=[
                CitationResponse(
                    id=c.id, title=c.title, url=c.url, source_name=c.source_name,
                    authors=c.authors, journal=c.journal, year=c.year,
                    pub_date=c.pub_date or "",
                    source_category=c.source_category.value if hasattr(c.source_category, 'value') else str(c.source_category),
                    evidence_level=c.evidence_level.value if hasattr(c.evidence_level, 'value') else str(c.evidence_level),
                    excerpt=c.excerpt, specialty_tags=c.specialty_tags,
                    pmid=c.pmid or "", doi=c.doi or "",
                    reliability=c.reliability, access_date=c.access_date,
                )
                for c in result.citations
            ],
            specialties=result.specialties,
            confidence=result.confidence,
            warnings=result.warnings,
            teaching_mode=result.teaching_mode,
            retrieval_time_ms=result.retrieval_time_ms,
            total_sources_consulted=result.total_sources_consulted,
        )
    except Exception as e:
        logger.error(f"Answer error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/compare")
async def compare(req: CompareRequest):
    try:
        result = await compare_conditions(req.condition_a, req.condition_b, req.max_sources)
        return result
    except Exception as e:
        logger.error(f"Compare error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


class SimulationRequest(BaseModel):
    topic: str


@app.post("/api/generate-simulation")
async def generate_simulation(req: SimulationRequest):
    """Generate an interactive simulation for any medical topic using Claude API."""
    import httpx

    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise HTTPException(status_code=503, detail="AI simulation generation requires an API key. Contact the administrator.")

    prompt = f"""Generate an interactive medical simulation for: "{req.topic}"

Return ONLY valid JSON (no markdown, no backticks, no preamble) with this exact structure:
{{
  "title": "Topic Title",
  "steps": [
    {{
      "name": "Step Name",
      "explanation": "Detailed first-principles mechanistic explanation (3-5 sentences minimum). Explain the WHY at a molecular/cellular/physiological level. Include specific proteins, receptors, pathways, ion channels, enzymes as relevant.",
      "clinical": "Clinical bedside application (3-5 sentences minimum). Include specific diseases, drugs, lab tests, clinical signs that relate to this step. Mention drug names, diagnostic criteria, treatment implications.",
      "svg": "<svg viewBox='0 0 320 180' xmlns='http://www.w3.org/2000/svg' style='width:100%;max-width:340px;margin:0 auto;display:block'> ... SVG content showing this step visually with shapes, labels, arrows, colors ... </svg>"
    }}
  ]
}}

Requirements:
- Generate 4-6 steps covering the complete process
- Each SVG must be a valid, self-contained SVG element (viewBox='0 0 320 180')
- Use colors: #3498db (blue), #e74c3c (red), #27ae60 (green), #e67e22 (orange), #9b59b6 (purple)
- SVG should show anatomical/molecular diagrams appropriate to the topic — use shapes, text labels, arrows
- Explanations must be detailed, not summaries — written at medical student/resident level
- Clinical sections must include specific drug names, disease associations, diagnostic tests
- ONLY output the JSON object, nothing else"""

    try:
        async with httpx.AsyncClient(timeout=90) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 8000,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )

            if resp.status_code != 200:
                logger.error(f"Claude API error: {resp.status_code}")
                raise HTTPException(status_code=502, detail="AI service temporarily unavailable")

            data = resp.json()
            text = ""
            for block in data.get("content", []):
                if block.get("type") == "text":
                    text += block.get("text", "")

            # Clean and parse JSON
            text = text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1] if "\n" in text else text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()

            import json
            result = json.loads(text)

            # Sanitize SVGs — remove any script tags for safety
            import re
            for step in result.get("steps", []):
                svg = step.get("svg", "")
                svg = re.sub(r'<script[^>]*>.*?</script>', '', svg, flags=re.DOTALL | re.IGNORECASE)
                svg = re.sub(r'\bon\w+\s*=', '', svg)  # Remove event handlers
                step["svg"] = svg

            return result

    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error: {e}")
        raise HTTPException(status_code=502, detail="AI generated invalid response. Try again.")
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="AI request timed out. Try a simpler topic.")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Simulation generation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/icd")
async def icd_search(q: str = Query("", min_length=2)):
    try:
        results = await lookup_icd11(q)
        return results
    except Exception as e:
        logger.error(f"ICD search error: {e}")
        return []


@app.post("/api/pdf/parse")
async def parse_pdf(req: PDFParseRequest):
    try:
        from parsers.pdf_parser import parse_pdf_guideline
        result = await parse_pdf_guideline(req.url)
        if not result:
            raise HTTPException(status_code=400, detail="Could not parse PDF")
        return {
            "title": result.get("title", ""),
            "page_count": result.get("page_count", 0),
            "sections_count": len(result.get("sections", [])),
            "tables_count": len(result.get("tables", [])),
            "recommendations": result.get("recommendations", []),
            "text_preview": result.get("text", "")[:1000],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF parse error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/specialties")
async def list_specialties(category: Optional[str] = None):
    specs = SPECIALTIES
    if category:
        specs = [s for s in specs if s.category == category]
    return [{"id": s.id, "name": s.name, "category": s.category} for s in specs]


@app.get("/api/sources")
async def list_sources():
    return [
        {"id": s.id, "name": s.name, "domain": s.domain, "tier": s.tier.value, "type": s.source_type.value, "enabled": s.enabled}
        for s in SOURCES
    ]


@app.get("/api/languages")
async def list_languages():
    return get_supported_languages()


@app.get("/api/suggest")
async def suggest(q: str = Query("", min_length=2)):
    suggestions = [
        "What is the treatment for hypertension?",
        "Mechanism of action of metformin",
        "Differential diagnosis of chest pain",
        "COVID-19 vaccine efficacy",
        "Management of acute myocardial infarction",
        "Pathophysiology of heart failure",
        "Antibiotic selection for pneumonia",
        "Cardiac cycle physiology",
        "Compare asthma vs COPD",
        "ICD-11 code for diabetes",
    ]
    q_lower = q.lower()
    matches = [s for s in suggestions if q_lower in s.lower()]
    return matches[:5] if matches else suggestions[:5]


@app.post("/api/admin/seed")
async def seed_index():
    """Trigger index seeding (admin endpoint)."""
    try:
        from workers.seed_index import seed_from_pubmed
        await seed_from_pubmed()
        count = await get_document_count()
        return {"status": "ok", "documents": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/admin/reset-db")
async def reset_database():
    """Reset database — drops and recreates all tables."""
    try:
        await drop_all_tables()
        await init_db()
        await seed_icd11_codes()
        return {"status": "ok", "message": "Database reset and reinitialized"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("api.main:app", host="0.0.0.0", port=port, reload=True)
