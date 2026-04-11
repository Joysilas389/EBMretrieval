"""
Tests for EBMRetrieval v2.
Run: python -m pytest tests/ -v
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nlp import (
    normalize_query, expand_synonyms, extract_search_terms,
    classify_query_intent, score_relevance,
)
from nlp.multilingual import detect_language, get_supported_languages
from models.specialties import classify_query_specialty, get_specialty, get_clinical_specialties
from models.source_registry import get_source, get_sources_by_tier, SourceTier


class TestNLP:
    def test_normalize_abbreviation(self):
        assert "myocardial infarction" in normalize_query("treatment for MI")

    def test_expand_synonyms(self):
        variants = expand_synonyms("heart attack treatment")
        assert len(variants) >= 2

    def test_extract_terms(self):
        terms = extract_search_terms("What is the treatment for diabetes?")
        assert "treatment" in terms
        assert "what" not in terms

    def test_classify_treatment(self):
        assert classify_query_intent("treatment for hypertension") == "treatment"

    def test_classify_mechanism(self):
        assert classify_query_intent("mechanism of action of metformin") == "mechanism"

    def test_classify_comparison(self):
        assert classify_query_intent("ACE inhibitor vs ARB") == "comparison"

    def test_relevance_scoring(self):
        score = score_relevance("diabetes treatment", "Treatment of type 2 diabetes mellitus.")
        assert score > 0.3

    def test_irrelevant_scoring(self):
        score = score_relevance("diabetes treatment", "The weather is nice today.")
        assert score < 0.2


class TestMultilingual:
    def test_detect_english(self):
        assert detect_language("What is hypertension?") == "en"

    def test_supported_languages(self):
        langs = get_supported_languages()
        assert "en" in langs
        assert "es" in langs
        assert "fr" in langs
        assert "sw" in langs


class TestSpecialties:
    def test_classify_cardiac(self):
        assert "cardiology" in classify_query_specialty("chest pain cardiac workup")

    def test_classify_default(self):
        assert "internal_medicine" in classify_query_specialty("abcxyz unknown")

    def test_get_specialty(self):
        spec = get_specialty("cardiology")
        assert spec is not None
        assert spec.name == "Cardiology"

    def test_clinical_count(self):
        assert len(get_clinical_specialties()) > 20


class TestSourceRegistry:
    def test_pubmed_exists(self):
        assert get_source("pubmed") is not None
        assert get_source("pubmed").tier == SourceTier.HIGH

    def test_dimensions_exists(self):
        assert get_source("dimensions") is not None

    def test_icd11_exists(self):
        assert get_source("icd11_who") is not None

    def test_medicated_exists(self):
        assert get_source("medicated") is not None

    def test_high_tier_count(self):
        high = get_sources_by_tier(SourceTier.HIGH)
        assert len(high) >= 5


class TestICD11:
    def test_seed_data(self):
        from models.icd11 import ICD11_SEED
        assert len(ICD11_SEED) > 30
        codes = [c[0] for c in ICD11_SEED]
        assert "BA00" in codes  # Hypertension
        assert "5A11" in codes  # T2DM
        assert "1F20" in codes  # COVID-19


class TestAPI:
    @pytest.fixture
    def client(self):
        """Create test client — skips DB-dependent tests if no PostgreSQL."""
        try:
            from fastapi.testclient import TestClient
            from api.main import app
            return TestClient(app)
        except Exception:
            pytest.skip("PostgreSQL not available for testing")

    def test_health(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["database"] == "postgresql"

    def test_specialties(self, client):
        resp = client.get("/api/specialties")
        assert resp.status_code == 200
        assert len(resp.json()) > 30

    def test_sources(self, client):
        resp = client.get("/api/sources")
        assert resp.status_code == 200
        assert len(resp.json()) > 5

    def test_languages(self, client):
        resp = client.get("/api/languages")
        assert resp.status_code == 200
        assert "en" in resp.json()

    def test_suggest(self, client):
        resp = client.get("/api/suggest?q=diab")
        assert resp.status_code == 200
        assert len(resp.json()) > 0
