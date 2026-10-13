import logging
from pypdf import PdfReader
import aiofiles

logger = logging.getLogger(__name__)


async def extract_text_from_file(file_path: str, file_type: str) -> str:
    try:
        if file_type == ".txt":
            return await extract_from_txt(file_path)
        if file_type == ".pdf":
            return await extract_from_pdf(file_path)
        if file_type in (".doc", ".docx"):
            return await extract_from_docx(file_path)
        return f"Unsupported file type: {file_type}"
    except Exception as e:
        logger.error(f"extract_text_from_file error={e}")
        return f"Error extracting text: {e}"


async def extract_from_txt(file_path: str) -> str:
    try:
        async with aiofiles.open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return (await f.read()).strip()
    except Exception as e:
        logger.error(f"txt_extract_failed error={e}")
        return ""


async def extract_from_pdf(file_path: str) -> str:
    try:

        parts: list[str] = []
        with open(file_path, "rb") as f:
            reader = PdfReader(f)

            if reader.metadata:
                if reader.metadata.title:
                    parts.append(f"Title: {reader.metadata.title}")
                if reader.metadata.author:
                    parts.append(f"Author: {reader.metadata.author}")

            for i, page in enumerate(reader.pages):
                t = page.extract_text()
                if t and t.strip():
                    parts.append(f"--- Page {i + 1} ---")
                    parts.append(t.strip())

        return "\n".join(parts)
    except Exception as e:
        logger.error(f"pdf_extract_failed error={e}")
        return f"[PDF extraction error: {e}]"


async def extract_from_docx(file_path: str) -> str:
    try:
        from docx import Document

        doc = Document(file_path)
        parts: list[str] = []
        for p in doc.paragraphs:
            if p.text.strip():
                parts.append(p.text.strip())
        for table in doc.tables:
            for row in table.rows:
                row_text = [c.text.strip() for c in row.cells if c.text.strip()]
                if row_text:
                    parts.append(" | ".join(row_text))
        return "\n".join(parts)
    except Exception as e:
        logger.error(f"docx_extract_failed error={e}")
        return f"[DOCX extraction error: {e}]"