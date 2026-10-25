import asyncio
import logging

import aiofiles
from pypdf import PdfReader

logger = logging.getLogger(__name__)


class ExtractionError(Exception):
    """Raised when no usable text can be pulled from an uploaded file."""


async def extract_text_from_file(file_path: str, file_type: str) -> str:
    """
    Returns the extracted text, or raises ExtractionError.

    Previously errors were returned as text ("[PDF extraction error: ...]"),
    which the pipeline then sent to the LLM and "analyzed" as if it were a contract.
    """
    ext = (file_type or "").lower()
    if ext == ".txt":
        text = await _extract_txt(file_path)
    elif ext == ".pdf":
        text = await asyncio.to_thread(_extract_pdf, file_path)
    elif ext == ".docx":
        text = await asyncio.to_thread(_extract_docx, file_path)
    else:
        raise ExtractionError(f"Unsupported file type: {ext}")
    return (text or "").strip()


async def _extract_txt(file_path: str) -> str:
    async with aiofiles.open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return await f.read()


def _extract_pdf(file_path: str) -> str:
    try:
        reader = PdfReader(file_path)
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
        logger.error(f"pdf_extract_failed error={e}")
        raise ExtractionError(f"Could not read PDF: {e}")


def _extract_docx(file_path: str) -> str:
    try:
        from docx import Document

        doc = Document(file_path)
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