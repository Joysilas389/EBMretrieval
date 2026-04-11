"""
PDF Guideline Parser — extracts structured medical content from public PDF guidelines.
Handles: WHO, CDC, NICE, USPSTF, AHA/ACC, and other publicly accessible guideline PDFs.
Uses PyMuPDF (fitz) and pdfplumber for robust extraction.
"""

import hashlib
import logging
import os
import re
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# Try fitz first (faster), fall back to pdfplumber
try:
    import fitz  # PyMuPDF
    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False


async def download_pdf(url: str, cache_dir: str = "/tmp/pdf_cache") -> Optional[str]:
    """Download a PDF to local cache. Returns file path or None."""
    os.makedirs(cache_dir, exist_ok=True)
    file_hash = hashlib.md5(url.encode()).hexdigest()
    path = os.path.join(cache_dir, f"{file_hash}.pdf")

    if os.path.exists(path):
        return path

    try:
        async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
            resp = await client.get(url, headers={
                "User-Agent": "EBMRetrieval/1.0 (Medical Evidence Retrieval)"
            })
            resp.raise_for_status()
            content_type = resp.headers.get("content-type", "")
            if "pdf" not in content_type and not url.endswith(".pdf"):
                logger.warning(f"Not a PDF: {content_type} for {url}")
                return None
            with open(path, "wb") as f:
                f.write(resp.content)
            return path
    except Exception as e:
        logger.error(f"PDF download error for {url}: {e}")
        return None


def extract_pdf_fitz(path: str) -> dict:
    """Extract text and structure from PDF using PyMuPDF."""
    doc = fitz.open(path)
    pages = []
    full_text = []
    sections = []
    current_section = {"heading": "", "text": []}

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text")
        pages.append({"page": page_num + 1, "text": text})
        full_text.append(text)

        # Detect headings by font size analysis
        blocks = page.get_text("dict", flags=fitz.TEXTFLAGS_TEXT)["blocks"]
        for block in blocks:
            if "lines" not in block:
                continue
            for line in block["lines"]:
                line_text = "".join(span["text"] for span in line["spans"]).strip()
                if not line_text:
                    continue
                # Check if this looks like a heading (larger font, bold, short)
                max_size = max((span["size"] for span in line["spans"]), default=12)
                is_bold = any("Bold" in (span.get("font", "") or "") for span in line["spans"])
                if (max_size > 13 or is_bold) and len(line_text) < 120:
                    if current_section["text"]:
                        sections.append(current_section)
                    current_section = {"heading": line_text, "text": []}
                else:
                    if len(line_text) > 10:
                        current_section["text"].append(line_text)

    if current_section["text"]:
        sections.append(current_section)

    doc.close()

    # Extract tables if possible
    tables = _extract_tables_fitz(path)

    return {
        "text": "\n".join(full_text),
        "pages": pages,
        "sections": sections,
        "tables": tables,
        "page_count": len(pages),
        "file_hash": hashlib.md5(open(path, "rb").read()).hexdigest()[:16],
    }


def _extract_tables_fitz(path: str) -> list[dict]:
    """Try extracting tables from PDF."""
    tables = []
    if not HAS_PDFPLUMBER:
        return tables
    try:
        with pdfplumber.open(path) as pdf:
            for i, page in enumerate(pdf.pages[:20]):  # Limit pages
                page_tables = page.extract_tables()
                for t_idx, table in enumerate(page_tables or []):
                    if table and len(table) > 1:
                        tables.append({
                            "page": i + 1,
                            "index": t_idx,
                            "headers": table[0] if table[0] else [],
                            "rows": table[1:],
                        })
    except Exception as e:
        logger.warning(f"Table extraction error: {e}")
    return tables


def extract_pdf_pdfplumber(path: str) -> dict:
    """Fallback extraction using pdfplumber."""
    pages = []
    full_text = []
    tables = []

    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            pages.append({"page": i + 1, "text": text})
            full_text.append(text)

            page_tables = page.extract_tables()
            for t_idx, table in enumerate(page_tables or []):
                if table and len(table) > 1:
                    tables.append({
                        "page": i + 1,
                        "index": t_idx,
                        "headers": table[0],
                        "rows": table[1:],
                    })

    return {
        "text": "\n".join(full_text),
        "pages": pages,
        "sections": [],
        "tables": tables,
        "page_count": len(pages),
        "file_hash": hashlib.md5(open(path, "rb").read()).hexdigest()[:16],
    }


async def parse_pdf_guideline(url: str) -> Optional[dict]:
    """Download and parse a PDF guideline. Returns structured content."""
    path = await download_pdf(url)
    if not path:
        return None

    try:
        if HAS_FITZ:
            result = extract_pdf_fitz(path)
        elif HAS_PDFPLUMBER:
            result = extract_pdf_pdfplumber(path)
        else:
            logger.error("No PDF library available (need PyMuPDF or pdfplumber)")
            return None

        result["url"] = url

        # Extract title from first page
        if result["pages"]:
            first_text = result["pages"][0]["text"]
            lines = [l.strip() for l in first_text.split("\n") if l.strip()]
            result["title"] = lines[0][:200] if lines else "Untitled Guideline"

        # Extract recommendations
        result["recommendations"] = _extract_recommendations(result["text"])

        return result
    except Exception as e:
        logger.error(f"PDF parse error for {url}: {e}")
        return None


def _extract_recommendations(text: str) -> list[str]:
    """Extract recommendation statements from guideline text."""
    recommendations = []
    patterns = [
        r"(?:Recommendation|RECOMMENDATION)\s*\d*[:\.]?\s*(.+?)(?:\n|$)",
        r"(?:We recommend|We suggest|It is recommended|Should be|Should not)\s+(.+?)(?:\.\s|\n)",
        r"(?:Grade [A-D]|Level [I-V]|Class [I-V])\s*[:\.]?\s*(.+?)(?:\.\s|\n)",
        r"(?:Strong recommendation|Weak recommendation|Conditional recommendation)\s*[:\.]?\s*(.+?)(?:\.\s|\n)",
    ]
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
        for m in matches:
            clean = m.strip()
            if 20 < len(clean) < 500:
                recommendations.append(clean)

    return recommendations[:30]
