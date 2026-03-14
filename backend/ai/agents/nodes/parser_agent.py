import re
from core.logger import get_logger

logger = get_logger(__name__)


async def parser_agent(state: dict) -> dict:
    """
    Parses raw contract text — cleans, normalizes, detects contract type.
    Updates state with: clean_text, contract_type, text_length, metadata.
    """
    text = state.get("raw_text", "")
    filename = state.get("filename", "")

    # Clean text
    clean = _clean_text(text)
    contract_type = _detect_type(clean, filename)
    metadata = _extract_metadata(clean)

    logger.info("parser_agent.done", contract_type=contract_type, chars=len(clean))

    return {
        **state,
        "clean_text": clean,
        "contract_type": contract_type,
        "text_length": len(clean),
        "metadata": metadata,
    }


def _clean_text(text: str) -> str:
    # Normalize whitespace
    text = re.sub(r'\r\n', '\n', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]{2,}', ' ', text)
    # Remove page numbers like "Page 1 of 10"
    text = re.sub(r'Page \d+ of \d+', '', text, flags=re.IGNORECASE)
    return text.strip()


def _detect_type(text: str, filename: str) -> str:
    combined = (text + filename).lower()
    patterns = [
        (["non-disclosure", "nda", "confidential agreement"], "NDA"),
        (["employment agreement", "offer letter", "employment contract"], "Employment Agreement"),
        (["service level agreement", "sla"], "Service Level Agreement"),
        (["master service", "master services", "msa"], "Master Services Agreement"),
        (["software license", "saas", "subscription agreement"], "SaaS/License Agreement"),
        (["partnership agreement", "joint venture"], "Partnership Agreement"),
        (["vendor agreement", "supplier agreement", "procurement"], "Vendor Agreement"),
        (["consulting agreement", "consulting services"], "Consulting Agreement"),
        (["non-compete", "non-solicitation"], "Non-Compete Agreement"),
    ]
    for keywords, label in patterns:
        if any(k in combined for k in keywords):
            return label
    return "Commercial Agreement"


def _extract_metadata(text: str) -> dict:
    """Best-effort extraction of parties, dates from text."""
    parties = []
    # Look for "between X and Y" pattern
    m = re.search(r'between\s+([A-Z][^,\n]+?)\s+(?:and|&)\s+([A-Z][^,\n]+?)(?:\s*[,.(]|\n)', text)
    if m:
        parties = [m.group(1).strip(), m.group(2).strip()]

    # Look for dates
    dates = re.findall(r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}\b', text)

    return {
        "detected_parties": parties[:2],
        "detected_dates": dates[:5],
    }
