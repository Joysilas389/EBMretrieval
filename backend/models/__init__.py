"""
Core data models for EBMRetrieval.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class EvidenceLevel(str, Enum):
    SYSTEMATIC_REVIEW = "systematic_review"
    RCT = "rct"
    COHORT = "cohort"
    CASE_CONTROL = "case_control"
    CASE_REPORT = "case_report"
    EXPERT_OPINION = "expert_opinion"
    GUIDELINE = "guideline"
    TEXTBOOK = "textbook"
    PUBLIC_HEALTH = "public_health"
    UNKNOWN = "unknown"


class SourceCategory(str, Enum):
    JOURNAL_ARTICLE = "journal_article"
    GUIDELINE = "guideline"
    REVIEW = "review"
    SYSTEMATIC_REVIEW = "systematic_review"
    TEXTBOOK_CHAPTER = "textbook_chapter"
    PUBLIC_HEALTH = "public_health"
    DRUG_INFO = "drug_info"
    PROTOCOL = "protocol"
    EDUCATIONAL = "educational"
    UNKNOWN = "unknown"


@dataclass
class Citation:
    """A single citable source."""
    id: str
    title: str
    url: str
    source_id: str  # key from source_registry
    source_name: str
    authors: list[str] = field(default_factory=list)
    journal: str = ""
    year: Optional[int] = None
    pub_date: Optional[str] = None
    last_updated: Optional[str] = None
    source_category: SourceCategory = SourceCategory.UNKNOWN
    evidence_level: EvidenceLevel = EvidenceLevel.UNKNOWN
    excerpt: str = ""
    specialty_tags: list[str] = field(default_factory=list)
    access_date: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    pmid: Optional[str] = None
    doi: Optional[str] = None
    reliability: str = "standard"


@dataclass
class EvidenceChunk:
    """A chunk of text from a source, with citation traceability."""
    text: str
    citation: Citation
    relevance_score: float = 0.0
    section: str = ""
    chunk_index: int = 0


@dataclass
class AnswerBlock:
    """A block of the assembled answer with inline citation references."""
    text: str
    citation_indices: list[int] = field(default_factory=list)
    block_type: str = "paragraph"  # paragraph, heading, list_item, warning, pearl


@dataclass
class AssembledAnswer:
    """The final answer object returned to the frontend."""
    query: str
    blocks: list[AnswerBlock]
    citations: list[Citation]
    specialties: list[str]
    confidence: str = "moderate"  # high, moderate, low, uncertain
    warnings: list[str] = field(default_factory=list)
    teaching_mode: bool = False
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    retrieval_time_ms: int = 0
    total_sources_consulted: int = 0


@dataclass
class SearchResult:
    """Internal search result from the index."""
    doc_id: str
    title: str
    snippet: str
    url: str
    source_id: str
    score: float
    pub_date: Optional[str] = None
    specialty_tags: list[str] = field(default_factory=list)


@dataclass
class IndexedDocument:
    """A document stored in the search index."""
    doc_id: str
    title: str
    content: str
    url: str
    source_id: str
    source_name: str
    authors: str = ""
    journal: str = ""
    pub_date: str = ""
    year: int = 0
    specialty_tags: str = ""  # comma-separated
    evidence_level: str = ""
    source_category: str = ""
    excerpt: str = ""
    pmid: str = ""
    doi: str = ""
    indexed_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    freshness_score: float = 1.0
