"""
Medical Context Engine — provides domain-aware query understanding.
Uses:
  - medical-named-entity-recognition: disease/condition detection (zero deps, MIT)
  - drug-named-entity-recognition: drug/medication detection (zero deps, MIT)

These libraries contain built-in medical knowledge bases covering thousands of
diseases, conditions, drugs, and medications. No UMLS license required.
No hardcoded domain mapping needed.
"""

import re
import logging
from typing import Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Lazy-loaded — NOT imported at module level to save startup memory
_disease_finder = None
_drug_finder = None
_ner_init_done = False


def _init_ner():
    """Lazy-load NER libraries on first use, not at startup."""
    global _disease_finder, _drug_finder, _ner_init_done
    if _ner_init_done:
        return
    _ner_init_done = True

    try:
        from medical_named_entity_recognition import find_diseases
        _disease_finder = find_diseases
        logger.info("Medical NER loaded (lazy)")
    except ImportError:
        logger.warning("medical-named-entity-recognition not available")

    try:
        from drug_named_entity_recognition import find_drugs
        _drug_finder = find_drugs
        logger.info("Drug NER loaded (lazy)")
    except ImportError:
        logger.warning("drug-named-entity-recognition not available")


@dataclass
class MedicalContext:
    """Extracted medical context from a query."""
    original_query: str
    diseases: list[dict] = field(default_factory=list)
    drugs: list[dict] = field(default_factory=list)
    primary_disease: str = ""
    primary_drug: str = ""
    enhanced_query: str = ""
    intent: str = "general"
    is_drug_related: bool = False
    is_disease_related: bool = False
    entity_count: int = 0


def _tokenize(text: str) -> list[str]:
    """Simple word tokenizer."""
    return re.findall(r"(?:\w|'|'|-)+", text)


def extract_medical_context(query: str) -> MedicalContext:
    """
    Extract medical entities from a query using NER libraries.
    This replaces all hardcoded domain mapping with real medical knowledge.
    """
    ctx = MedicalContext(original_query=query)
    tokens = _tokenize(query)

    if not tokens:
        ctx.enhanced_query = query
        return ctx

    # Lazy-load NER libraries on first call
    _init_ner()

    # Extract diseases/conditions
    if _disease_finder is not None:
        try:
            disease_results = _disease_finder(tokens, is_ignore_case=True)
            if disease_results:
                for match in disease_results:
                    if isinstance(match, dict):
                        ctx.diseases.append(match)
                    elif isinstance(match, (list, tuple)) and len(match) >= 2:
                        ctx.diseases.append({
                            "name": str(match[0]),
                            "start": match[1] if len(match) > 1 else 0,
                        })
                ctx.is_disease_related = len(ctx.diseases) > 0
                if ctx.diseases:
                    # Get the primary disease (first/most prominent)
                    first = ctx.diseases[0]
                    ctx.primary_disease = first.get("name", str(first)) if isinstance(first, dict) else str(first)
        except Exception as e:
            logger.warning(f"Disease NER error: {e}")

    # Extract drugs/medications
    if _drug_finder is not None:
        try:
            drug_results = _drug_finder(tokens, is_ignore_case=True)
            if drug_results:
                for match in drug_results:
                    if isinstance(match, dict):
                        ctx.drugs.append(match)
                    elif isinstance(match, (list, tuple)) and len(match) >= 2:
                        ctx.drugs.append({
                            "name": str(match[0]),
                            "start": match[1] if len(match) > 1 else 0,
                        })
                ctx.is_drug_related = len(ctx.drugs) > 0
                if ctx.drugs:
                    first = ctx.drugs[0]
                    ctx.primary_drug = first.get("name", str(first)) if isinstance(first, dict) else str(first)
        except Exception as e:
            logger.warning(f"Drug NER error: {e}")

    ctx.entity_count = len(ctx.diseases) + len(ctx.drugs)

    # Build enhanced query using recognized entities
    ctx.enhanced_query = _build_enhanced_query(query, ctx)

    # Classify intent
    ctx.intent = _classify_medical_intent(query, ctx)

    return ctx


def _build_enhanced_query(query: str, ctx: MedicalContext) -> str:
    """
    Build an enhanced search query using recognized medical entities.
    This ensures we search for the exact medical concept the user means,
    not a keyword-level approximation.
    """
    parts = [query]

    # If we found a specific disease, add its canonical name to boost precision
    if ctx.primary_disease and ctx.primary_disease.lower() not in query.lower():
        parts.append(ctx.primary_disease)

    # If we found a specific drug, add it
    if ctx.primary_drug and ctx.primary_drug.lower() not in query.lower():
        parts.append(ctx.primary_drug)

    return " ".join(parts)


def _classify_medical_intent(query: str, ctx: MedicalContext) -> str:
    """Classify the medical intent of the query."""
    q = query.lower()

    if any(w in q for w in ["treat", "therapy", "management", "medication", "drug", "dose", "prescri"]):
        return "treatment"
    if any(w in q for w in ["diagnos", "workup", "differential", "test", "lab", "imaging", "screen"]):
        return "diagnostic"
    if any(w in q for w in ["mechanism", "pathophysiology", "how does", "why does", "cause", "pathway"]):
        return "mechanism"
    if any(w in q for w in ["vs", "versus", "compare", "difference between"]):
        return "comparison"
    if any(w in q for w in ["guideline", "recommendation", "protocol"]):
        return "guideline"
    if any(w in q for w in ["side effect", "adverse", "reaction", "contraindic", "interaction"]):
        return "safety"
    if any(w in q for w in ["prognosis", "survival", "outcome", "mortality"]):
        return "prognosis"

    # Use NER results to infer
    if ctx.is_drug_related and not ctx.is_disease_related:
        return "drug_info"
    if ctx.is_disease_related and not ctx.is_drug_related:
        return "disease_info"

    return "general"


def filter_chunks_by_context(chunks: list, query: str, ctx: MedicalContext) -> list:
    """
    Filter retrieved evidence chunks using medical context.
    Removes chunks that are about a DIFFERENT disease/drug than what the user asked about.
    This is the core anti-drift mechanism.
    """
    if ctx.entity_count == 0:
        return chunks  # No entities recognized, can't filter

    filtered = []
    q_lower = query.lower()

    for chunk in chunks:
        text_lower = chunk.text.lower()
        keep = True

        # If user asked about a specific disease, check the chunk mentions it
        if ctx.primary_disease:
            disease_lower = ctx.primary_disease.lower()
            # Extract key words from the disease name
            disease_words = [w for w in disease_lower.split() if len(w) > 3]

            if disease_words:
                # At least one key word from the disease name should appear in the chunk
                has_disease_word = any(dw in text_lower for dw in disease_words)

                # Also check if the chunk is about a DIFFERENT disease with a similar abbreviation
                # e.g., "acute chest syndrome" vs "acute coronary syndrome"
                if not has_disease_word:
                    # Check if original query words appear
                    query_key_words = [w for w in q_lower.split() if len(w) > 3 and w not in {
                        "what", "treatment", "management", "diagnosis", "about",
                        "guidelines", "mechanism", "pathophysiology", "causes",
                    }]
                    has_query_word = any(qw in text_lower for qw in query_key_words) if query_key_words else True

                    if not has_query_word:
                        keep = False
                        chunk.relevance_score *= 0.15  # Heavy penalty

        # If user asked about a specific drug, prefer chunks mentioning it
        if ctx.primary_drug:
            drug_lower = ctx.primary_drug.lower()
            if drug_lower not in text_lower:
                # Don't hard-reject, but penalize
                chunk.relevance_score *= 0.5

        if keep:
            filtered.append(chunk)
        else:
            # Still include but with very low score as fallback
            chunk.relevance_score *= 0.1
            filtered.append(chunk)

    # Sort by adjusted relevance
    filtered.sort(key=lambda c: c.relevance_score, reverse=True)
    return filtered


def get_context_summary(ctx: MedicalContext) -> Optional[str]:
    """Generate a human-readable context note if helpful."""
    parts = []
    if ctx.diseases:
        names = [d.get("name", str(d)) if isinstance(d, dict) else str(d) for d in ctx.diseases[:3]]
        names_str = ", ".join(str(n) for n in names if n)
        if names_str:
            parts.append(f"Conditions identified: {names_str}")
    if ctx.drugs:
        names = [d.get("name", str(d)) if isinstance(d, dict) else str(d) for d in ctx.drugs[:3]]
        names_str = ", ".join(str(n) for n in names if n)
        if names_str:
            parts.append(f"Medications identified: {names_str}")
    return ". ".join(parts) if parts else None
