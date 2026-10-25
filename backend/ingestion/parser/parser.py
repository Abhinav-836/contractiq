import asyncio
import base64
import io
import logging

import httpx
from pypdf import PdfReader

from core.config import settings

logger = logging.getLogger(__name__)

# Below this many characters a PDF is treated as scanned/image-only
MIN_PDF_TEXT_CHARS = 100
# Gemini accepts inline PDFs up to ~20MB per request
MAX_OCR_BYTES = 19 * 1024 * 1024


class ExtractionError(Exception):
    """Raised when no usable text can be pulled from an uploaded file."""


async def extract_text(data: bytes, file_type: str) -> str:
    """
    Extract text from an uploaded file's bytes, or raise ExtractionError.

    Works on bytes (not a disk path) because files now live in Postgres —
    Render's disk is wiped on every deploy.
    """
    ext = (file_type or "").lower()
    if ext == ".txt":
        return _decode_txt(data).strip()
    if ext == ".docx":
        return (await asyncio.to_thread(_extract_docx, data)).strip()
    if ext == ".pdf":
        text = ""
        try:
            text = (await asyncio.to_thread(_extract_pdf, data)).strip()
        except ExtractionError as e:
            if "password" in str(e).lower():
                raise
            logger.warning(f"pdf_text_layer_failed error={e}")

        if len(text) >= MIN_PDF_TEXT_CHARS:
            return text

        # Scanned / image-only PDF → OCR with Gemini (reads PDFs natively)
        ocr = await _ocr_pdf_with_gemini(data)
        if ocr:
            return ocr
        if text:
            return text
        raise ExtractionError(
            "No readable text found. This looks like a scanned PDF and OCR is unavailable."
        )
    raise ExtractionError(f"Unsupported file type: {ext}")


def _decode_txt(data: bytes) -> str:
    for enc in ("utf-8-sig", "utf-16", "cp1252"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="ignore")


def _extract_pdf(data: bytes) -> str:
    try:
        reader = PdfReader(io.BytesIO(data))
        if reader.is_encrypted:
            try:
                reader.decrypt("")
            except Exception:
                raise ExtractionError("PDF is password-protected")
        parts = []
        for page in reader.pages:
            t = page.extract_text() or ""
            if t.strip():
                parts.append(t.strip())
        return "\n\n".join(parts)
    except ExtractionError:
        raise
    except Exception as e:
        raise ExtractionError(f"Could not read PDF: {e}")


def _extract_docx(data: bytes) -> str:
    try:
        from docx import Document

        doc = Document(io.BytesIO(data))
        parts = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        for table in doc.tables:
            for row in table.rows:
                cells = [c.text.strip() for c in row.cells if c.text.strip()]
                if cells:
                    parts.append(" | ".join(cells))
        return "\n".join(parts)
    except Exception as e:
        logger.error(f"docx_extract_failed error={e}")
        raise ExtractionError(f"Could not read DOCX: {e}")


async def _ocr_pdf_with_gemini(data: bytes) -> str:
    """Transcribe a scanned PDF. Returns "" if Gemini isn't configured or fails."""
    if not settings.GEMINI_API_KEY:
        logger.warning("ocr.skipped reason=no_gemini_key")
        return ""
    if len(data) > MAX_OCR_BYTES:
        logger.warning(f"ocr.skipped reason=too_large bytes={len(data)}")
        return ""

    model = settings.GEMINI_MODEL.replace("models/", "")
    generation_config = {"temperature": 0, "maxOutputTokens": 16000}
    if "2.5-flash" in model:
        # Thinking tokens count against maxOutputTokens; plain transcription doesn't need them
        generation_config["thinkingConfig"] = {"thinkingBudget": 0}

    payload = {
        "contents": [{
            "parts": [
                {"inline_data": {"mime_type": "application/pdf",
                                 "data": base64.b64encode(data).decode("ascii")}},
                {"text": (
                    "Transcribe all text in this document exactly as written, in reading order. "
                    "Output plain text only — no commentary, no summaries, no markdown."
                )},
            ]
        }],
        "generationConfig": generation_config,
    }

    try:
        logger.info(f"ocr.start model={model} bytes={len(data)}")
        async with httpx.AsyncClient(timeout=180) as client:
            resp = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                json=payload,
                headers={"x-goog-api-key": settings.GEMINI_API_KEY},
            )
            resp.raise_for_status()
            result = resp.json()
        parts = (result.get("candidates") or [{}])[0].get("content", {}).get("parts", [])
        text = "".join(p.get("text", "") for p in parts).strip()
        logger.info(f"ocr.done chars={len(text)}")
        return text
    except Exception as e:
        logger.error(f"ocr.failed error={str(e)[:300]}")
        return ""