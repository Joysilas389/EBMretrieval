"""
Answer Engine v5 - Medical NER-powered evidence synthesis.
Uses medical-named-entity-recognition + drug-named-entity-recognition for
domain awareness instead of hardcoded maps.
RULES:
  1. NEVER output an incomplete sentence.
  2. Use NER libraries for medical context, not hardcoded lists.
  3. Full readable paragraphs with natural flow.
  4. Superscript citations after paragraphs.
"""

import asyncio
import logging
import os
import time
import hashlib
import re
from typing import Optional

import httpx

from models import (
    AssembledAnswer, AnswerBlock, Citation, EvidenceChunk,
    EvidenceLevel, SourceCategory,
)
from models.specialties import classify_query_specialty
from nlp import normalize_query, expand_synonyms, extract_search_terms, score_relevance
from nlp.multilingual import detect_language, translate_to_english, translate_from_english
from nlp.medical_context import extract_medical_context, filter_chunks_by_context, get_context_summary
from crawlers.pubmed_crawler import (
    search_pubmed, fetch_pubmed_abstracts, article_to_citation,
    article_to_chunks, search_ncbi_books,
)
from crawlers.medlineplus_crawler import search_medlineplus
from crawlers.who_crawler import search_who
from crawlers.cdc_crawler import search_cdc
from crawlers.openfda_crawler import search_openfda_drugs
from crawlers.europepmc_crawler import search_europe_pmc
from search import search_documents

logger = logging.getLogger(__name__)

EMERGENCY_KEYWORDS = [
    "chest pain emergency", "cannot breathe", "heart attack now", "stroke symptoms now",
    "unconscious", "not breathing", "severe bleeding", "anaphylaxis",
    "seizure now", "suicidal", "overdose", "choking", "cardiac arrest",
]
EMERGENCY_WARNING = (
    "⚠️ EMERGENCY: If this is a medical emergency, call your local emergency number "
    "immediately (911, 999, 112, 193). This tool is for education and reference only."
)
TEACHING_LABELS = [
    "The Problem", "Simplest Picture", "Mechanism Step by Step",
    "Clinical Bridge", "Investigations & Why", "Treatment Logic", "Contrast & Edge Cases",
]


def _check_emergency(query: str) -> Optional[str]:
    q = query.lower()
    for kw in EMERGENCY_KEYWORDS:
        if kw in q:
            return EMERGENCY_WARNING
    return None


# ============================================================
# TEXT PROCESSING - Complete sentences only, strip HTML, never break words
# ============================================================
def _strip_html(text: str) -> str:
    """Remove ALL HTML/XML tags from text."""
    text = re.sub(r'<[^>]+>', ' ', text)  # Replace tags with space
    text = re.sub(r'&[a-zA-Z]+;', ' ', text)  # Remove HTML entities
    text = re.sub(r'&#\d+;', ' ', text)  # Remove numeric entities
    text = re.sub(r'\s+', ' ', text)  # Collapse whitespace
    return text.strip()


def _clean_text(text: str) -> str:
    """Clean text: strip HTML, fix spacing, remove labels. NEVER break words."""
    # First strip any HTML/XML tags
    text = _strip_html(text)
    # Fix missing space after period ONLY when followed by uppercase and preceded by lowercase letter + period
    text = re.sub(r'\.([A-Z][a-z])', r'. \1', text)
    # Fix colon followed by uppercase without space
    text = re.sub(r':([A-Z])', r': \1', text)
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove section labels at start
    text = re.sub(
        r'^(OBJECTIVE|BACKGROUND|METHODS|RESULTS|CONCLUSIONS|INTRODUCTION|FINDINGS|PURPOSE|AIMS?|CONTEXT|SETTING|DESIGN|PARTICIPANTS?|INTERVENTIONS?|MAIN OUTCOME|MEASUREMENTS?):\s*',
        '', text, flags=re.IGNORECASE
    )
    return text.strip()


def _complete_sentences(text: str) -> list[str]:
    """Extract ONLY complete sentences. Never returns partial or broken sentences."""
    text = _clean_text(text)
    if not text:
        return []

    # Split on sentence boundaries: period/exclamation/question followed by space and uppercase
    parts = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)

    sentences = []
    for p in parts:
        p = p.strip()
        if len(p) < 25:
            continue

        # Must start with uppercase letter (indicates sentence start, not a broken fragment)
        if not p[0].isupper():
            continue

        # Must end with sentence punctuation
        if p[-1] in '.!?':
            sentences.append(p)
        else:
            # Find the last sentence-ending punctuation
            last = -1
            for i in range(len(p) - 1, 0, -1):
                if p[i] in '.!?' and i > 20:
                    # Make sure we're not cutting inside a number like "140.90"
                    if i + 1 < len(p) and p[i + 1:i + 2].isdigit():
                        continue
                    last = i
                    break
            if last > 25:
                sentences.append(p[:last + 1])
            # Otherwise discard - it is a fragment

    return sentences


def _relevance_score(query: str, text: str) -> float:
    """Score relevance between query and text. Generous - prefers to include rather than exclude."""
    if not text or not query:
        return 0.0
    q_lower = query.lower()
    t_lower = text.lower()
    stop = {'what','how','does','the','for','and','are','this','that','with','from',
            'about','can','could','would','should','will','is','was','were','been',
            'be','have','has','had','do','tell','explain','describe','give','show','me','my'}
    q_words = [w for w in re.findall(r'\b\w+\b', q_lower) if len(w) > 2 and w not in stop]
    if not q_words:
        return 0.5  # No meaningful words extracted - do not penalize, return neutral score
    matches = sum(1 for w in q_words if w in t_lower)
    coverage = matches / len(q_words)
    phrase_bonus = 0.2 if q_lower.replace("?", "").strip() in t_lower else 0.0
    # Any single keyword match is enough to keep the result
    if matches >= 1:
        return min(1.0, 0.3 + coverage * 0.4 + phrase_bonus)
    return 0.05


def _filter_by_topic(chunks: list[EvidenceChunk], query: str) -> list[EvidenceChunk]:
    """
    Hard filter: reject chunks that are clearly NOT about the query topic.
    Extract the main subject from the query, then check if each chunk's
    citation title OR text contains at least one key subject word.
    This prevents "hypertension" queries from returning lupus articles.
    """
    q_lower = query.lower()

    # Extract subject words - nouns that define WHAT the query is about
    stop = {
        'what', 'how', 'does', 'the', 'for', 'and', 'are', 'this', 'that',
        'with', 'from', 'about', 'can', 'could', 'would', 'should', 'will',
        'is', 'was', 'were', 'been', 'be', 'have', 'has', 'had', 'do',
        'tell', 'explain', 'describe', 'give', 'show', 'me', 'my', 'your',
        'treatment', 'management', 'diagnosis', 'guidelines', 'causes',
        'symptoms', 'mechanism', 'pathophysiology', 'prevention', 'prognosis',
        'screening', 'workup', 'differential', 'compare', 'versus',
    }
    subject_words = [w for w in re.findall(r'\b\w+\b', q_lower) if len(w) > 3 and w not in stop]

    if not subject_words:
        return chunks  # Can't determine subject - keep everything

    kept = []
    for chunk in chunks:
        text_lower = chunk.text.lower()
        title_lower = (chunk.citation.title or "").lower()
        combined = text_lower + " " + title_lower

        # Check if ANY subject word appears in the chunk text or its source title
        has_subject = any(sw in combined for sw in subject_words)

        if has_subject:
            kept.append(chunk)
        # else: discard - this chunk is about a different topic entirely

    # If filtering removed too much (>80%), the subject extraction was too aggressive - return all
    if len(kept) < len(chunks) * 0.2 and len(chunks) > 3:
        return chunks

    return kept


# ============================================================
# MAIN
# ============================================================
async def generate_answer(
    query: str,
    max_sources: int = 10,
    max_words: int = 2000,
    teaching_mode: bool = False,
    citation_density: str = "standard",
    source_preference: str = "balanced",
    specialty_filter: Optional[str] = None,
    language: Optional[str] = None,
) -> AssembledAnswer:
    start_time = time.time()

    # Language - ONLY translate if user explicitly set a non-English language in settings
    # Never auto-detect, it misidentifies English medical terms as other languages
    detected_lang = "en"
    search_query = query
    if language and language != "en":
        detected_lang = language
        search_query = translate_to_english(query, detected_lang)

    # MEDICAL NER CONTEXT - replaces all hardcoded domain logic
    med_ctx = extract_medical_context(search_query)
    logger.info(f"Medical context: diseases={len(med_ctx.diseases)}, drugs={len(med_ctx.drugs)}, intent={med_ctx.intent}")

    # Use enhanced query from NER for better search precision
    effective_query = med_ctx.enhanced_query or search_query

    # Preprocessing
    normalized = normalize_query(effective_query)
    variants = expand_synonyms(normalized)
    terms = extract_search_terms(normalized)
    specialties = classify_query_specialty(search_query) if not specialty_filter else [specialty_filter]

    warnings: list[str] = []
    emergency = _check_emergency(search_query)
    if emergency:
        warnings.append(emergency)

    # Show recognized entities as context note
    ctx_summary = get_context_summary(med_ctx)
    if ctx_summary:
        warnings.insert(0, ctx_summary)

    # Parallel retrieval
    all_chunks: list[EvidenceChunk] = []
    per_src = max(3, max_sources // 3)
    is_drug = med_ctx.is_drug_related or med_ctx.intent in ("treatment", "safety", "drug_info")

    tasks = [
        _retrieve_pubmed(normalized, variants, per_src),
        _retrieve_books(normalized, max_results=3),
        _retrieve_from_index(normalized, terms, specialty_filter, per_src),
        _retrieve_medlineplus(normalized, max_results=per_src),
        _retrieve_who(normalized, max_results=per_src),
        _retrieve_cdc(normalized, max_results=per_src),
        _retrieve_europe_pmc(normalized, max_results=per_src),
    ]
    if is_drug:
        tasks.append(_retrieve_openfda(normalized, max_results=per_src))

    results = await asyncio.gather(*tasks, return_exceptions=True)
    for result in results:
        if isinstance(result, list):
            all_chunks.extend(result)
        elif isinstance(result, Exception):
            logger.warning(f"Retrieval error: {result}")

    # TOPIC-FOCUS FILTER - reject chunks not actually about the query topic
    all_chunks = _filter_by_topic(all_chunks, search_query)

    # Score relevance
    for chunk in all_chunks:
        chunk.relevance_score = _relevance_score(search_query, chunk.text)

    # MEDICAL CONTEXT FILTERING - NER-based, not hardcoded
    all_chunks = filter_chunks_by_context(all_chunks, search_query, med_ctx)

    # Remove only truly irrelevant results
    all_chunks = [c for c in all_chunks if c.relevance_score >= 0.05]
    all_chunks.sort(key=lambda c: c.relevance_score, reverse=True)

    # Deduplicate
    seen: set[str] = set()
    unique: list[EvidenceChunk] = []
    for chunk in all_chunks:
        fp = hashlib.md5(chunk.text[:120].lower().encode()).hexdigest()
        if fp not in seen:
            seen.add(fp)
            unique.append(chunk)
    selected = unique[:max_sources * 3]

    # Build citations
    cmap: dict[str, int] = {}
    citations: list[Citation] = []
    for chunk in selected:
        cid = chunk.citation.id
        if cid not in cmap:
            cmap[cid] = len(citations)
            citations.append(chunk.citation)

    # SYNTHESIS - Three modes:
    # 1. Evidence found + Claude key -> Claude synthesizes from evidence (best quality)
    # 2. No evidence + Claude key -> Claude answers from knowledge (still useful, clearly labeled)
    # 3. No Claude key -> Extractive assembly from evidence (fallback)
    claude_key = os.getenv("ANTHROPIC_API_KEY", "")
    logger.info(f"Claude API key configured: {bool(claude_key)}, selected chunks: {len(selected)}")
    if claude_key:
        if selected:
            # Mode 1: Claude synthesizes retrieved evidence
            logger.info("Using MODE 1: Claude synthesis from retrieved evidence")
            blocks = await _synthesize_with_claude(
                search_query, selected, citations, cmap, claude_key,
                teaching_mode, max_words
            )
        else:
            # Mode 2: No evidence found - Claude answers from its own knowledge
            logger.info("Using MODE 2: Claude direct answer (no evidence found)")
            blocks = await _claude_direct_answer(
                search_query, claude_key, teaching_mode, max_words
            )
            warnings.insert(0,
                "No published sources were found in our database for this query. "
                "The following answer is AI-generated with web-searched references."
            )
    elif teaching_mode:
        logger.info("Using MODE 3a: Extractive teaching (no API key)")
        blocks = _assemble_teaching(search_query, selected, cmap, max_words)
    else:
        logger.info("Using MODE 3b: Extractive assembly (no API key)")
        blocks = _assemble_prose(search_query, selected, cmap, max_words)

    if detected_lang != "en":
        for block in blocks:
            block.text = translate_from_english(block.text, detected_lang)

    # Standard disclaimer
    warnings.append(
        "This information is for educational and reference purposes only. "
        "It does not replace professional medical judgment."
    )
    if any(c.year and c.year < 2020 for c in citations):
        warnings.append("Some sources may predate recent guideline updates.")

    confidence = "moderate"
    if claude_key:
        # Claude is answering - confidence is based on whether sources were found
        if len(citations) >= 3:
            confidence = "high"
        elif len(citations) >= 1:
            confidence = "moderate"
        else:
            confidence = "ai-generated"
    else:
        # Extractive mode - confidence based on source count
        if len(citations) >= 5 and selected and selected[0].relevance_score > 0.4:
            confidence = "high"
        elif len(citations) < 2:
            confidence = "low"

    elapsed = int((time.time() - start_time) * 1000)

    return AssembledAnswer(
        query=query, blocks=blocks, citations=citations[:max_sources],
        specialties=specialties, confidence=confidence, warnings=warnings,
        teaching_mode=teaching_mode, retrieval_time_ms=elapsed,
        total_sources_consulted=len(all_chunks),
    )


async def compare_conditions(condition_a: str, condition_b: str, max_sources: int = 8) -> dict:
    a = await generate_answer(condition_a, max_sources=max_sources // 2, max_words=800)
    b = await generate_answer(condition_b, max_sources=max_sources // 2, max_words=800)
    return {
        "condition_a": {"name": condition_a, "blocks": [{"text": bl.text, "type": bl.block_type} for bl in a.blocks],
                        "citations": [{"title": c.title, "url": c.url, "source": c.source_name} for c in a.citations], "confidence": a.confidence},
        "condition_b": {"name": condition_b, "blocks": [{"text": bl.text, "type": bl.block_type} for bl in b.blocks],
                        "citations": [{"title": c.title, "url": c.url, "source": c.source_name} for c in b.citations], "confidence": b.confidence},
        "retrieval_time_ms": a.retrieval_time_ms + b.retrieval_time_ms,
    }


# ============================================================
# CLAUDE SYNTHESIS - LLM-powered answer generation from retrieved evidence
# ============================================================
async def _synthesize_with_claude(
    query: str,
    chunks: list[EvidenceChunk],
    citations: list[Citation],
    cmap: dict[str, int],
    api_key: str,
    teaching_mode: bool,
    max_words: int,
) -> list[AnswerBlock]:
    """
    Claude synthesizes the answer using retrieved evidence + web search for additional sources.
    Web search lets Claude find real, verifiable references from medical journals.
    """
    # Build evidence context
    evidence_text = ""
    for i, cit in enumerate(citations[:15]):
        cit_chunks = [c for c in chunks if c.citation.id == cit.id]
        chunk_text = " ".join(_strip_html(c.text) for c in cit_chunks[:3])
        if chunk_text:
            source_info = cit.source_name or ""
            if cit.journal:
                source_info += f", {cit.journal}"
            if cit.year:
                source_info += f" ({cit.year})"
            evidence_text += f"\n[Source {i+1}] {cit.title} - {source_info}\n{chunk_text}\n"

    system_prompt = """You are an expert medical evidence assistant used by doctors, residents, and medical students worldwide.

HOW TO RESPOND:
- Answer EXACTLY what was asked. The question determines the structure.
- If they ask about guidelines, give the specific recommendations with thresholds and drug choices.
- If they ask about dosing, give dosing directly with specific drugs, doses, frequencies.
- If they ask about mechanism, explain the mechanism from first principles.
- If they ask a broad question, give a comprehensive structured answer.
- Start with a direct answer. No preamble.
- Use section headings with ** only when naturally needed.
- Use bullet points for drug lists and classification criteria. Use prose for explanations.
- Include specific numbers: BP targets, drug doses, lab values, staging criteria.
- Cite inline with [1], [2] etc. for EVERY major claim.
- Use web search to find additional high-quality sources: systematic reviews, meta-analyses, clinical guidelines from 2021-2026.
- Prioritize: Cochrane, NEJM, Lancet, JAMA, BMJ, AHA/ACC, ESC, NICE, WHO guidelines.
- NEVER fabricate citations. Only cite sources you found via search or from the evidence provided.
- At the END, list ALL references:
  **References**
  [1] Authors. Title. Journal. Year. URL
  [2] Authors. Title. Journal. Year. URL
- Aim for 8-15 references. Every reference must have a real URL."""

    user_msg = f"""{query}

Background evidence from our database:
{evidence_text}

Use web search to find additional current medical evidence. Cite everything with [1], [2] etc. List all references at the end."""

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            logger.info(f"Calling Claude API with web_search, evidence: {len(chunks)} chunks")
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 8192,
                    "system": system_prompt,
                    "tools": [{"type": "web_search_20250305", "name": "web_search", "max_uses": 5}],
                    "messages": [{"role": "user", "content": user_msg}],
                },
            )

            if resp.status_code != 200:
                error_text = resp.text[:500]
                logger.error(f"Claude API error {resp.status_code}: {error_text}")
                # If web search tool is not enabled, retry WITHOUT it
                if "tool" in error_text.lower() or resp.status_code == 400:
                    logger.info("Retrying without web_search tool")
                    return await _synthesize_without_websearch(
                        query, evidence_text, api_key, system_prompt, chunks, cmap, citations, max_words
                    )
                return _assemble_prose(query, chunks, cmap, max_words)

            data = resp.json()
            content = data.get("content", [])
            logger.info(f"Claude response: {len(content)} content blocks, stop_reason={data.get('stop_reason')}")

            # Extract text from all content blocks (web search responses have mixed block types)
            answer_text = ""
            for block in content:
                if block.get("type") == "text":
                    answer_text += block.get("text", "")
                # web_search_tool_result and server_tool_use blocks are internal, skip them

            if not answer_text:
                logger.warning("Claude returned no text content")
                return _assemble_prose(query, chunks, cmap, max_words)

            logger.info(f"Claude answer: {len(answer_text)} chars")

            # Extract references from Claude response and merge with existing
            ref_citations = _extract_claude_references(answer_text, citations)
            citations.clear()
            citations.extend(ref_citations)
            cmap.clear()
            for i, c in enumerate(citations):
                cmap[c.id] = i

            return _parse_claude_response(answer_text, cmap, citations)

    except Exception as e:
        logger.error(f"Claude synthesis error: {e}", exc_info=True)
        return _assemble_prose(query, chunks, cmap, max_words)


async def _synthesize_without_websearch(
    query: str, evidence_text: str, api_key: str, system_prompt: str,
    chunks: list, cmap: dict, citations: list, max_words: int,
) -> list[AnswerBlock]:
    """Fallback: Claude synthesis without web search tool (if not enabled on account)."""
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 8192,
                    "system": system_prompt,
                    "messages": [{"role": "user", "content": f"{query}\n\nEvidence:\n{evidence_text}\n\nCite with [1], [2] etc. List references at the end."}],
                },
            )
            if resp.status_code != 200:
                logger.error(f"Claude fallback error {resp.status_code}")
                return _assemble_prose(query, chunks, cmap, max_words)

            answer_text = ""
            for block in resp.json().get("content", []):
                if block.get("type") == "text":
                    answer_text += block.get("text", "")

            if not answer_text:
                return _assemble_prose(query, chunks, cmap, max_words)

            ref_citations = _extract_claude_references(answer_text, citations)
            citations.clear()
            citations.extend(ref_citations)
            cmap.clear()
            for i, c in enumerate(citations):
                cmap[c.id] = i

            return _parse_claude_response(answer_text, cmap, citations)
    except Exception as e:
        logger.error(f"Claude fallback error: {e}")
        return _assemble_prose(query, chunks, cmap, max_words)


def _extract_claude_references(answer_text: str, existing_citations: list[Citation]) -> list[Citation]:
    """
    Extract reference list from the AI response and merge with existing retrieval citations.
    Parses references like:
      [1] Authors. Title. Journal. Year. https://url
    """
    all_citations = list(existing_citations)
    seen_ids = {c.id for c in all_citations}

    # Find references section
    ref_section = ""
    for marker in ["**References**", "**References:**", "## References", "References:", "**Sources**", "**Sources:**"]:
        idx = answer_text.find(marker)
        if idx != -1:
            ref_section = answer_text[idx:]
            break

    if not ref_section:
        # Try finding lines that look like [1] Author...
        lines = answer_text.split('\n')
        ref_lines = []
        collecting = False
        for line in lines:
            if re.match(r'^\[?\d+\]?\s*\w', line.strip()) and ('http' in line or '.' in line.split(',')[0] if ',' in line else False):
                collecting = True
            if collecting:
                ref_lines.append(line)
        ref_section = '\n'.join(ref_lines)

    if not ref_section:
        return all_citations

    # Parse each reference line
    ref_pattern = re.compile(r'\[(\d+)\]\s*(.+?)(?:\n|$)')
    for match in ref_pattern.finditer(ref_section):
        ref_num = match.group(1)
        ref_text = match.group(2).strip()

        # Extract URL if present
        url_match = re.search(r'(https?://\S+)', ref_text)
        url = url_match.group(1).rstrip('.,;)') if url_match else ""

        # Extract year
        year_match = re.search(r'\b(20\d{2})\b', ref_text)
        year = year_match.group(1) if year_match else ""

        # Clean title - everything before the URL or the first period-separated segment
        title = ref_text
        if url:
            title = ref_text[:ref_text.find(url)].rstrip('. ')
        # Remove trailing dots and clean
        title = title.strip().rstrip('.')

        ref_id = f"claude_ref_{ref_num}"
        if ref_id not in seen_ids and title:
            cit = Citation(
                id=ref_id,
                title=title,
                url=url,
                source_id="web_search",
                source_name="Web Search",
                source_category=SourceCategory.JOURNAL_ARTICLE,
                evidence_level=EvidenceLevel.SYSTEMATIC_REVIEW if 'meta-analysis' in title.lower() or 'systematic review' in title.lower() else EvidenceLevel.SINGLE_STUDY,
                excerpt="",
                year=int(year) if year else None,
                pub_date=year,
            )
            # Try to determine journal from the reference text
            if 'lancet' in ref_text.lower():
                cit.journal = "The Lancet"
            elif 'nejm' in ref_text.lower() or 'new england' in ref_text.lower():
                cit.journal = "NEJM"
            elif 'jama' in ref_text.lower():
                cit.journal = "JAMA"
            elif 'bmj' in ref_text.lower():
                cit.journal = "BMJ"
            elif 'cochrane' in ref_text.lower():
                cit.journal = "Cochrane Library"
                cit.evidence_level = EvidenceLevel.SYSTEMATIC_REVIEW
            elif 'circulation' in ref_text.lower():
                cit.journal = "Circulation"
            elif 'blood' in ref_text.lower():
                cit.journal = "Blood"

            all_citations.append(cit)
            seen_ids.add(ref_id)

    return all_citations


def _parse_claude_response(text: str, cmap: dict[str, int], citations: list[Citation]) -> list[AnswerBlock]:
    """Parse AI prose response into AnswerBlocks with citation indices."""
    blocks: list[AnswerBlock] = []

    # Split by markdown headings or double newlines
    sections = re.split(r'\n\n+', text.strip())

    for section in sections:
        section = section.strip()
        if not section:
            continue

        # Check if this is a heading (starts with ** or ##)
        heading_match = re.match(r'^(?:\*\*|#{1,3})\s*(.+?)(?:\*\*|)\s*$', section)
        if heading_match:
            blocks.append(AnswerBlock(text=heading_match.group(1).strip(), block_type="heading"))
            continue

        # Extract citation numbers from text like [1], [2], [1,3]
        cit_numbers = set()
        for m in re.finditer(r'\[(\d+(?:,\s*\d+)*)\]', section):
            for num_str in m.group(1).split(','):
                num = int(num_str.strip()) - 1  # Convert to 0-indexed
                if 0 <= num < len(citations):
                    cit_numbers.add(num)

        # Clean citation markers from display text - they'll be shown as superscripts by frontend
        display_text = section.strip()

        if display_text:
            blocks.append(AnswerBlock(
                text=display_text,
                citation_indices=sorted(cit_numbers),
                block_type="paragraph",
            ))

    return blocks if blocks else [AnswerBlock(text=text, block_type="paragraph")]


async def _claude_direct_answer(
    query: str, api_key: str, teaching_mode: bool, max_words: int,
) -> list[AnswerBlock]:
    """When retrieval finds NO evidence, Claude uses web search + own knowledge."""
    system_prompt = """You are an expert medical evidence assistant used by doctors worldwide.
- Answer exactly what was asked. The question determines the structure.
- Use web search to find current evidence: systematic reviews, meta-analyses, guidelines.
- Cite inline with [1], [2]. Only cite real sources.
- Include specific clinical details: drug names, doses, thresholds.
- At the END, list references: [1] Authors. Title. Journal. Year. URL
- Aim for 8-15 references."""

    user_msg = f"{query}\n\nSearch for evidence and provide a comprehensive answer. List references at the end."
    headers = {"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"}

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            # Try with web search
            resp = await client.post("https://api.anthropic.com/v1/messages", headers=headers, json={
                "model": "claude-sonnet-4-20250514", "max_tokens": 8192, "system": system_prompt,
                "tools": [{"type": "web_search_20250305", "name": "web_search", "max_uses": 5}],
                "messages": [{"role": "user", "content": user_msg}],
            })
            if resp.status_code != 200:
                logger.warning(f"Web search failed ({resp.status_code}), retrying without")
                resp = await client.post("https://api.anthropic.com/v1/messages", headers=headers, json={
                    "model": "claude-sonnet-4-20250514", "max_tokens": 8192, "system": system_prompt,
                    "messages": [{"role": "user", "content": user_msg}],
                })
                if resp.status_code != 200:
                    return [AnswerBlock(text=f"Unable to generate answer. Try again.", block_type="paragraph")]

            answer_text = ""
            for block in resp.json().get("content", []):
                if block.get("type") == "text":
                    answer_text += block.get("text", "")
            if not answer_text:
                return [AnswerBlock(text=f"No answer generated.", block_type="paragraph")]

            new_citations = _extract_claude_references(answer_text, [])
            return _parse_claude_response(answer_text, {c.id: i for i, c in enumerate(new_citations)}, new_citations)
    except Exception as e:
        logger.error(f"Claude direct error: {e}")
        return [AnswerBlock(text=f"Unable to generate answer. Try again later.", block_type="paragraph")]


# ============================================================
# PROSE ASSEMBLY - Extractive fallback when Claude API is unavailable
# ============================================================
def _build_para(chunks: list[EvidenceChunk], used: set[str], cmap: dict[str, int],
                min_sent: int = 2, max_sent: int = 5) -> Optional[AnswerBlock]:
    """Build a paragraph from complete sentences. Never returns incomplete text."""
    sentences = []
    cit_indices = []
    for chunk in chunks:
        for sent in _complete_sentences(chunk.text):
            h = hashlib.md5(sent[:60].lower().encode()).hexdigest()
            if h in used or len(sent) < 25:
                continue
            used.add(h)
            sentences.append(sent)
            ci = cmap.get(chunk.citation.id)
            if ci is not None and ci not in cit_indices:
                cit_indices.append(ci)
            if len(sentences) >= max_sent:
                break
        if len(sentences) >= max_sent:
            break
    if len(sentences) < min_sent:
        # Still return what we have if we got at least 1 good sentence
        if not sentences:
            return None
    text = " ".join(sentences)
    return AnswerBlock(text=text, citation_indices=cit_indices, block_type="paragraph")


def _assemble_prose(query: str, chunks: list[EvidenceChunk], cmap: dict[str, int], max_words: int) -> list[AnswerBlock]:
    blocks: list[AnswerBlock] = []
    if not chunks:
        blocks.append(AnswerBlock(
            text=f"No relevant evidence was found for \"{query}\". Try using more specific medical terminology or rephrasing your question.",
            block_type="paragraph"))
        return blocks

    used: set[str] = set()
    wc = 0

    # Overview
    para = _build_para(chunks[:5], used, cmap, min_sent=2, max_sent=5)
    if para:
        blocks.append(para)
        wc += len(para.text.split())

    # Key Evidence
    if len(chunks) > 3 and wc < max_words:
        blocks.append(AnswerBlock(text="Key Evidence", block_type="heading"))
        for chunk in chunks[3:]:
            if wc >= max_words:
                break
            p = _build_para([chunk], used, cmap, min_sent=1, max_sent=4)
            if p and len(p.text.split()) > 12:
                blocks.append(p)
                wc += len(p.text.split())

    # Additional Context from non-journal sources
    other = [c for c in chunks if c.citation.source_id not in {"pubmed", "europe_pmc"}]
    if other and wc < max_words:
        blocks.append(AnswerBlock(text="Additional Context", block_type="heading"))
        for chunk in other[:4]:
            if wc >= max_words:
                break
            p = _build_para([chunk], used, cmap, min_sent=1, max_sent=3)
            if p and len(p.text.split()) > 12:
                blocks.append(p)
                wc += len(p.text.split())

    return blocks


def _assemble_teaching(query: str, chunks: list[EvidenceChunk], cmap: dict[str, int], max_words: int) -> list[AnswerBlock]:
    blocks: list[AnswerBlock] = []
    if not chunks:
        blocks.append(AnswerBlock(text=f"Insufficient evidence for \"{query}\".", block_type="paragraph"))
        return blocks
    used: set[str] = set()
    per = max(1, len(chunks) // len(TEACHING_LABELS))
    for i, label in enumerate(TEACHING_LABELS):
        blocks.append(AnswerBlock(text=label, block_type="heading"))
        layer = chunks[i * per:(i + 1) * per + 1]
        p = _build_para(layer, used, cmap, min_sent=1, max_sent=4) if layer else None
        blocks.append(p if p else AnswerBlock(text="Further evidence needed for this aspect.", block_type="paragraph"))
    return blocks


# ============================================================
# RETRIEVAL HELPERS (unchanged)
# ============================================================
async def _retrieve_pubmed(query, variants, max_results):
    try:
        pmids = await search_pubmed(query, max_results=max_results)
        if not pmids:
            for v in variants[1:3]:
                pmids = await search_pubmed(v, max_results=max_results // 2)
                if pmids: break
        if not pmids: return []
        articles = await fetch_pubmed_abstracts(pmids)
        chunks = []
        for a in articles:
            chunks.extend(article_to_chunks(a, article_to_citation(a)))
        return chunks
    except Exception as e:
        logger.error(f"PubMed error: {e}"); return []

async def _retrieve_books(query, max_results=3):
    try:
        books = await search_ncbi_books(query, max_results=max_results)
        return [EvidenceChunk(text=b["title"], citation=Citation(
            id=f"book_{b['id']}", title=b["title"], url=b["url"],
            source_id="ncbi_books", source_name="NCBI Bookshelf",
            source_category=SourceCategory.TEXTBOOK_CHAPTER,
            evidence_level=EvidenceLevel.TEXTBOOK, excerpt=b["title"],
        ), section="title") for b in books]
    except Exception as e:
        logger.error(f"Books error: {e}"); return []

async def _retrieve_from_index(query, terms, specialty, max_results):
    try:
        results = await search_documents(" ".join(terms) if terms else query, max_results=max_results, specialty=specialty)
        return [EvidenceChunk(text=r.snippet, citation=Citation(
            id=r.doc_id, title=r.title, url=r.url, source_id=r.source_id,
            source_name=r.source_id, pub_date=r.pub_date or "", excerpt=r.snippet,
            specialty_tags=r.specialty_tags,
        ), relevance_score=r.score) for r in results]
    except Exception as e:
        logger.error(f"Index error: {e}"); return []

async def _retrieve_medlineplus(q, max_results=5):
    try: return await search_medlineplus(q, max_results=max_results)
    except Exception as e: logger.error(f"MedlinePlus error: {e}"); return []

async def _retrieve_who(q, max_results=5):
    try: return await search_who(q, max_results=max_results)
    except Exception as e: logger.error(f"WHO error: {e}"); return []

async def _retrieve_cdc(q, max_results=5):
    try: return await search_cdc(q, max_results=max_results)
    except Exception as e: logger.error(f"CDC error: {e}"); return []

async def _retrieve_openfda(q, max_results=5):
    try: return await search_openfda_drugs(q, max_results=max_results)
    except Exception as e: logger.error(f"OpenFDA error: {e}"); return []

async def _retrieve_europe_pmc(q, max_results=5):
    try: return await search_europe_pmc(q, max_results=max_results)
    except Exception as e: logger.error(f"Europe PMC error: {e}"); return []
