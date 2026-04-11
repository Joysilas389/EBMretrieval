"""
NLP utilities for query processing.
All local, no external AI APIs.
Handles: normalization, synonym expansion, abbreviation expansion,
         specialty classification, basic extractive summarization.
"""

import re
from typing import Optional

# ============================================================
# MEDICAL ABBREVIATION EXPANSION
# ============================================================
ABBREVIATIONS: dict[str, str] = {
    "mi": "myocardial infarction",
    "chf": "congestive heart failure",
    "copd": "chronic obstructive pulmonary disease",
    "dm": "diabetes mellitus",
    "htn": "hypertension",
    "cad": "coronary artery disease",
    "ckd": "chronic kidney disease",
    "dvt": "deep vein thrombosis",
    "pe": "pulmonary embolism",
    "uti": "urinary tract infection",
    "acs": "acute coronary syndrome",
    "afib": "atrial fibrillation",
    "tia": "transient ischemic attack",
    "cva": "cerebrovascular accident stroke",
    "gerd": "gastroesophageal reflux disease",
    "ibd": "inflammatory bowel disease",
    "sle": "systemic lupus erythematosus",
    "ra": "rheumatoid arthritis",
    "ms": "multiple sclerosis",
    "tb": "tuberculosis",
    "hiv": "human immunodeficiency virus",
    "aids": "acquired immunodeficiency syndrome",
    "ards": "acute respiratory distress syndrome",
    "aki": "acute kidney injury",
    "bph": "benign prostatic hyperplasia",
    "pcos": "polycystic ovary syndrome",
    "osa": "obstructive sleep apnea",
    "gbs": "guillain-barre syndrome",
    "tbi": "traumatic brain injury",
    "sah": "subarachnoid hemorrhage",
    "pud": "peptic ulcer disease",
    "nsaid": "nonsteroidal anti-inflammatory drug",
    "acei": "ACE inhibitor angiotensin converting enzyme inhibitor",
    "arb": "angiotensin receptor blocker",
    "ssri": "selective serotonin reuptake inhibitor",
    "ppi": "proton pump inhibitor",
    "ct": "computed tomography",
    "mri": "magnetic resonance imaging",
    "ecg": "electrocardiogram",
    "ekg": "electrocardiogram",
    "cbc": "complete blood count",
    "bmp": "basic metabolic panel",
    "cmp": "comprehensive metabolic panel",
    "lfts": "liver function tests",
    "tsh": "thyroid stimulating hormone",
    "abg": "arterial blood gas",
    "lp": "lumbar puncture",
    "csf": "cerebrospinal fluid",
    "sofa": "sequential organ failure assessment",
    "nstemi": "non-ST elevation myocardial infarction",
    "stemi": "ST elevation myocardial infarction",
    "cabg": "coronary artery bypass graft",
    "pci": "percutaneous coronary intervention",
}

# ============================================================
# MEDICAL SYNONYMS
# ============================================================
SYNONYMS: dict[str, list[str]] = {
    "heart attack": ["myocardial infarction", "MI", "acute coronary syndrome"],
    "high blood pressure": ["hypertension", "HTN", "elevated blood pressure"],
    "diabetes": ["diabetes mellitus", "DM", "type 2 diabetes", "type 1 diabetes"],
    "stroke": ["cerebrovascular accident", "CVA", "ischemic stroke", "hemorrhagic stroke"],
    "kidney failure": ["renal failure", "chronic kidney disease", "CKD", "acute kidney injury"],
    "blood clot": ["thrombosis", "DVT", "pulmonary embolism", "thrombus"],
    "cancer": ["malignancy", "neoplasm", "carcinoma", "tumor"],
    "infection": ["infectious disease", "sepsis", "bacteremia"],
    "headache": ["cephalgia", "migraine", "tension headache"],
    "chest pain": ["angina", "chest discomfort", "thoracic pain"],
    "shortness of breath": ["dyspnea", "breathlessness", "respiratory distress"],
    "swelling": ["edema", "oedema", "anasarca"],
    "rash": ["dermatitis", "exanthem", "urticaria", "skin eruption"],
    "fever": ["pyrexia", "febrile", "hyperthermia"],
    "pain": ["nociception", "algesia", "ache"],
    "pregnancy": ["gestation", "gravid", "prenatal", "antenatal"],
}


def normalize_query(query: str) -> str:
    """Normalize a medical query: lowercase, expand abbreviations, clean."""
    q = query.strip()
    if not q:
        return q

    # Don't lowercase entirely — preserve case for acronyms, but work lowercase internally
    q_lower = q.lower()

    # Expand known abbreviations
    words = q_lower.split()
    expanded = []
    for word in words:
        clean = re.sub(r"[^\w]", "", word)
        if clean in ABBREVIATIONS:
            expanded.append(ABBREVIATIONS[clean])
        else:
            expanded.append(word)

    return " ".join(expanded)


def expand_synonyms(query: str) -> list[str]:
    """Return synonym-expanded query variants."""
    variants = [query]
    q_lower = query.lower()

    for term, syns in SYNONYMS.items():
        if term in q_lower:
            for syn in syns[:2]:  # limit expansion
                variants.append(q_lower.replace(term, syn))

    # Also check if query matches any synonym
    for term, syns in SYNONYMS.items():
        for syn in syns:
            if syn.lower() in q_lower:
                variants.append(q_lower.replace(syn.lower(), term))
                break

    return list(set(variants))[:5]


def extract_search_terms(query: str) -> list[str]:
    """Extract key search terms from a query."""
    # Remove common question words
    stop_words = {
        "what", "is", "are", "how", "does", "do", "the", "a", "an", "in",
        "of", "for", "to", "and", "or", "can", "could", "would", "should",
        "with", "this", "that", "these", "those", "my", "me", "i", "we",
        "you", "your", "it", "its", "was", "were", "been", "be", "being",
        "have", "has", "had", "will", "shall", "may", "might", "must",
        "about", "from", "between", "which", "why", "when", "where",
        "tell", "explain", "describe", "define", "give", "show",
    }

    normalized = normalize_query(query)
    words = re.findall(r'\b\w+\b', normalized.lower())
    terms = [w for w in words if w not in stop_words and len(w) > 1]
    return terms


def classify_query_intent(query: str) -> str:
    """Classify query intent: diagnostic, treatment, mechanism, comparison, definition, guideline."""
    q = query.lower()

    if any(w in q for w in ["treat", "therapy", "management", "medication", "drug", "dose", "prescrib"]):
        return "treatment"
    if any(w in q for w in ["diagnos", "workup", "differential", "test", "lab", "imaging", "screen"]):
        return "diagnostic"
    if any(w in q for w in ["mechanism", "pathophysiology", "how does", "why does", "cause", "pathway"]):
        return "mechanism"
    if any(w in q for w in ["vs", "versus", "compare", "difference between", "compared to"]):
        return "comparison"
    if any(w in q for w in ["guideline", "recommendation", "protocol", "standard of care"]):
        return "guideline"
    if any(w in q for w in ["what is", "define", "definition", "overview"]):
        return "definition"
    if any(w in q for w in ["prognosis", "survival", "outcome", "mortality"]):
        return "prognosis"
    if any(w in q for w in ["prevent", "prophylaxis", "risk factor"]):
        return "prevention"

    return "general"


def score_relevance(query: str, text: str) -> float:
    """Score text relevance to query (0.0 to 1.0)."""
    if not text or not query:
        return 0.0

    terms = extract_search_terms(query)
    if not terms:
        return 0.0

    text_lower = text.lower()
    matches = sum(1 for t in terms if t in text_lower)
    base_score = matches / len(terms) if terms else 0.0

    # Bonus for exact phrase match
    if query.lower() in text_lower:
        base_score = min(1.0, base_score + 0.3)

    # Bonus for terms appearing close together
    if len(terms) > 1:
        # Check if first two terms appear within 50 chars of each other
        for i, t1 in enumerate(terms[:-1]):
            idx1 = text_lower.find(t1)
            if idx1 >= 0:
                idx2 = text_lower.find(terms[i + 1], max(0, idx1 - 50))
                if 0 <= idx2 - idx1 <= 50:
                    base_score = min(1.0, base_score + 0.15)
                    break

    return round(min(1.0, base_score), 3)


def extractive_summary(chunks: list[str], query: str, max_sentences: int = 8) -> str:
    """Create an extractive summary by selecting the most relevant sentences."""
    sentences = []
    for chunk in chunks:
        # Split into sentences
        for sent in re.split(r'(?<=[.!?])\s+', chunk):
            sent = sent.strip()
            if len(sent) > 20:
                score = score_relevance(query, sent)
                sentences.append((score, sent))

    # Sort by relevance
    sentences.sort(key=lambda x: x[0], reverse=True)

    # Take top sentences
    selected = [s[1] for s in sentences[:max_sentences]]
    return " ".join(selected)
