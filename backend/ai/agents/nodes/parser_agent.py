import re

from core.logger import get_logger

logger = get_logger(__name__)


async def parser_agent(state: dict) -> dict:
    text = state.get("raw_text", "")
    filename = state.get("filename", "")

    clean = _clean_text(text)
    contract_type = _detect_type(clean, filename)
    metadata = _extract_metadata(clean)

    logger.info(f"parser_agent.done contract_type={contract_type} chars={len(clean)}")

    return {
        **state,
        "clean_text": clean,
        "contract_type": contract_type,
        "text_length": len(clean),
        "metadata": metadata,
    }


def _clean_text(text: str) -> str:
    text = re.sub(r"\r\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"Page \d+ of \d+", "", text, flags=re.IGNORECASE)
    return text.strip()


# Order matters — most specific first
_TYPE_PATTERNS: list[tuple[list[str], str]] = [
    (["non-disclosure", "nda", "confidentiality agreement"], "NDA"),
    (["employment agreement", "offer letter", "employment contract"], "Employment Agreement"),
    (["service level agreement", "service level"], "Service Level Agreement"),
    (["master service", "master services", "master agreement"], "Master Services Agreement"),
    (["software license", "saas", "subscription agreement"], "SaaS/License Agreement"),
    (["partnership agreement", "joint venture"], "Partnership Agreement"),
    (["vendor agreement", "supplier agreement", "procurement agreement"], "Vendor Agreement"),
    (["consulting agreement", "consulting services"], "Consulting Agreement"),
    (["non-compete", "non-solicitation"], "Non-Compete Agreement"),
]


def _detect_type(text: str, filename: str) -> str:
    combined = f"{text} {filename}".lower()
    for keywords, label in _TYPE_PATTERNS:
        if any(k in combined for k in keywords):
            return label
    return "Commercial Agreement"


def _extract_metadata(text: str) -> dict:
    parties: list[str] = []
    m = re.search(
        r"between\s+([A-Z][^,\n]{1,80}?)\s+(?:and|&)\s+([A-Z][^,\n]{1,80}?)(?:\s*[,.(]|\n|$)",
        text,
    )
    if m:
        parties = [m.group(1).strip(), m.group(2).strip()]

    dates = re.findall(
        r"\b(?:January|February|March|April|May|June|July|August|September|"
        r"October|November|December)\s+\d{1,2},\s+\d{4}\b",
        text,
    )

    return {
        "detected_parties": parties[:2],
        "detected_dates": dates[:5],
    }