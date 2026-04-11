"""
Source Registry — Trusted medical evidence sources.
Each source has: domain, parser strategy, specialty tags, crawl schedule, legal notes.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class SourceType(str, Enum):
    API = "api"
    HTML = "html"
    XML = "xml"
    RSS = "rss"
    PDF = "pdf"
    STRUCTURED = "structured"


class SourceTier(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class CrawlFrequency(str, Enum):
    REALTIME = "realtime"  # on-demand per query
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


@dataclass
class TrustedSource:
    id: str
    name: str
    domain: str
    base_url: str
    source_type: SourceType
    tier: SourceTier
    specialties: list[str] = field(default_factory=list)
    crawl_frequency: CrawlFrequency = CrawlFrequency.WEEKLY
    parser: str = "html"
    api_endpoint: Optional[str] = None
    legal_note: str = ""
    enabled: bool = True
    rate_limit_seconds: float = 1.0


# ============================================================
# HIGH-PRIORITY SOURCES
# ============================================================

SOURCES: list[TrustedSource] = [
    TrustedSource(
        id="pubmed",
        name="PubMed",
        domain="pubmed.ncbi.nlm.nih.gov",
        base_url="https://pubmed.ncbi.nlm.nih.gov",
        source_type=SourceType.API,
        tier=SourceTier.HIGH,
        specialties=["all"],
        crawl_frequency=CrawlFrequency.REALTIME,
        parser="entrez_api",
        api_endpoint="https://eutils.ncbi.nlm.nih.gov/entrez/eutils/",
        legal_note="NCBI Entrez API. Free with API key. Respect rate limits (10/sec with key, 3/sec without).",
        rate_limit_seconds=0.11,
    ),
    TrustedSource(
        id="pmc",
        name="PubMed Central",
        domain="ncbi.nlm.nih.gov",
        base_url="https://www.ncbi.nlm.nih.gov/pmc/",
        source_type=SourceType.API,
        tier=SourceTier.HIGH,
        specialties=["all"],
        crawl_frequency=CrawlFrequency.REALTIME,
        parser="entrez_api",
        api_endpoint="https://eutils.ncbi.nlm.nih.gov/entrez/eutils/",
        legal_note="Open-access full-text articles via NCBI API.",
        rate_limit_seconds=0.11,
    ),
    TrustedSource(
        id="ncbi_books",
        name="NCBI Bookshelf",
        domain="ncbi.nlm.nih.gov",
        base_url="https://www.ncbi.nlm.nih.gov/books/",
        source_type=SourceType.API,
        tier=SourceTier.HIGH,
        specialties=["all"],
        crawl_frequency=CrawlFrequency.REALTIME,
        parser="entrez_api",
        api_endpoint="https://eutils.ncbi.nlm.nih.gov/entrez/eutils/",
        legal_note="Open-access medical textbooks and references.",
        rate_limit_seconds=0.11,
    ),
    TrustedSource(
        id="who",
        name="World Health Organization",
        domain="who.int",
        base_url="https://www.who.int",
        source_type=SourceType.HTML,
        tier=SourceTier.HIGH,
        specialties=["public_health", "infectious_disease", "epidemiology"],
        crawl_frequency=CrawlFrequency.WEEKLY,
        parser="html",
        legal_note="Public health information. Publicly accessible.",
    ),
    TrustedSource(
        id="cdc",
        name="Centers for Disease Control and Prevention",
        domain="cdc.gov",
        base_url="https://www.cdc.gov",
        source_type=SourceType.HTML,
        tier=SourceTier.HIGH,
        specialties=["public_health", "infectious_disease", "preventive_medicine"],
        crawl_frequency=CrawlFrequency.WEEKLY,
        parser="html",
        legal_note="US government public domain content.",
    ),
    TrustedSource(
        id="nih",
        name="National Institutes of Health",
        domain="nih.gov",
        base_url="https://www.nih.gov",
        source_type=SourceType.HTML,
        tier=SourceTier.HIGH,
        specialties=["all"],
        crawl_frequency=CrawlFrequency.WEEKLY,
        parser="html",
        legal_note="US government public domain content.",
    ),
    TrustedSource(
        id="nice",
        name="NICE Guidelines",
        domain="nice.org.uk",
        base_url="https://www.nice.org.uk/guidance",
        source_type=SourceType.HTML,
        tier=SourceTier.HIGH,
        specialties=["all"],
        crawl_frequency=CrawlFrequency.WEEKLY,
        parser="html",
        legal_note="Open Govt License. UK clinical guidelines.",
    ),
    TrustedSource(
        id="cochrane",
        name="Cochrane Library",
        domain="cochranelibrary.com",
        base_url="https://www.cochranelibrary.com",
        source_type=SourceType.HTML,
        tier=SourceTier.HIGH,
        specialties=["all"],
        crawl_frequency=CrawlFrequency.WEEKLY,
        parser="html",
        legal_note="Abstracts publicly accessible. Full text may require subscription.",
    ),
    TrustedSource(
        id="fda",
        name="U.S. Food and Drug Administration",
        domain="fda.gov",
        base_url="https://www.fda.gov",
        source_type=SourceType.HTML,
        tier=SourceTier.HIGH,
        specialties=["pharmacology", "clinical_pharmacology"],
        crawl_frequency=CrawlFrequency.WEEKLY,
        parser="html",
        legal_note="US government public domain content.",
    ),
    TrustedSource(
        id="uspstf",
        name="US Preventive Services Task Force",
        domain="uspreventiveservicestaskforce.org",
        base_url="https://www.uspreventiveservicestaskforce.org",
        source_type=SourceType.HTML,
        tier=SourceTier.HIGH,
        specialties=["preventive_medicine", "family_medicine", "internal_medicine"],
        crawl_frequency=CrawlFrequency.MONTHLY,
        parser="html",
        legal_note="Public screening/prevention recommendations.",
    ),
    TrustedSource(
        id="ema",
        name="European Medicines Agency",
        domain="ema.europa.eu",
        base_url="https://www.ema.europa.eu",
        source_type=SourceType.HTML,
        tier=SourceTier.HIGH,
        specialties=["pharmacology"],
        crawl_frequency=CrawlFrequency.WEEKLY,
        parser="html",
        legal_note="Public regulatory information.",
    ),
    # ============================================================
    # MEDIUM-PRIORITY SOURCES
    # ============================================================
    TrustedSource(
        id="medlineplus",
        name="MedlinePlus",
        domain="medlineplus.gov",
        base_url="https://medlineplus.gov",
        source_type=SourceType.XML,
        tier=SourceTier.MEDIUM,
        specialties=["all"],
        crawl_frequency=CrawlFrequency.WEEKLY,
        parser="xml",
        api_endpoint="https://wsearch.nlm.nih.gov/ws/query",
        legal_note="NLM public domain. XML web service available.",
    ),
    TrustedSource(
        id="opentextbc",
        name="OpenTextBC Anatomy & Physiology",
        domain="opentextbc.ca",
        base_url="https://opentextbc.ca/anatomyandphysiology/",
        source_type=SourceType.HTML,
        tier=SourceTier.MEDIUM,
        specialties=["anatomy", "physiology"],
        crawl_frequency=CrawlFrequency.MONTHLY,
        parser="html",
        legal_note="CC BY 4.0 open textbook.",
    ),
    TrustedSource(
        id="statpearls",
        name="StatPearls (NCBI Bookshelf)",
        domain="ncbi.nlm.nih.gov",
        base_url="https://www.ncbi.nlm.nih.gov/books/NBK430685/",
        source_type=SourceType.API,
        tier=SourceTier.MEDIUM,
        specialties=["all"],
        crawl_frequency=CrawlFrequency.REALTIME,
        parser="entrez_api",
        legal_note="CC BY 4.0 via NCBI Bookshelf. Open-access medical reference.",
        rate_limit_seconds=0.11,
    ),
    TrustedSource(
        id="dimensions",
        name="Dimensions.ai",
        domain="dimensions.ai",
        base_url="https://app.dimensions.ai",
        source_type=SourceType.API,
        tier=SourceTier.MEDIUM,
        specialties=["all"],
        crawl_frequency=CrawlFrequency.REALTIME,
        parser="dimensions_api",
        api_endpoint="https://app.dimensions.ai/api/dsl",
        legal_note="Free tier API for research. Metadata publicly accessible.",
        rate_limit_seconds=1.0,
    ),
    TrustedSource(
        id="icd11_who",
        name="WHO ICD-11 Classification",
        domain="icd.who.int",
        base_url="https://icd.who.int",
        source_type=SourceType.API,
        tier=SourceTier.HIGH,
        specialties=["all"],
        crawl_frequency=CrawlFrequency.MONTHLY,
        parser="icd_api",
        api_endpoint="https://id.who.int/icd/release/11/2024-01/mms",
        legal_note="WHO ICD-11 API. Free registration required. ICD-11 is the current standard (ICD-10 is outdated).",
        rate_limit_seconds=0.5,
    ),
    TrustedSource(
        id="medicated",
        name="Medicated",
        domain="medicated.com",
        base_url="https://www.medicated.com",
        source_type=SourceType.HTML,
        tier=SourceTier.MEDIUM,
        specialties=["pharmacology", "all"],
        crawl_frequency=CrawlFrequency.WEEKLY,
        parser="html",
        legal_note="Public drug information resource.",
    ),
    TrustedSource(
        id="drugbank_open",
        name="DrugBank Open Data",
        domain="go.drugbank.com",
        base_url="https://go.drugbank.com",
        source_type=SourceType.STRUCTURED,
        tier=SourceTier.MEDIUM,
        specialties=["pharmacology", "clinical_pharmacology"],
        crawl_frequency=CrawlFrequency.MONTHLY,
        parser="structured",
        legal_note="Open data subset. CC BY-NC 4.0.",
    ),
]


def get_source(source_id: str) -> TrustedSource | None:
    return next((s for s in SOURCES if s.id == source_id), None)


def get_sources_by_tier(tier: SourceTier) -> list[TrustedSource]:
    return [s for s in SOURCES if s.tier == tier and s.enabled]


def get_sources_by_specialty(specialty: str) -> list[TrustedSource]:
    return [s for s in SOURCES if s.enabled and ("all" in s.specialties or specialty in s.specialties)]


def get_realtime_sources() -> list[TrustedSource]:
    return [s for s in SOURCES if s.crawl_frequency == CrawlFrequency.REALTIME and s.enabled]
