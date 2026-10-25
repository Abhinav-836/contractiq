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


# Order matters — most specific first. Matched on word boundaries so "nda"
# no longer matches "standard"/"calendar"/"agenda".
_TYPE_PATTERNS: list[tuple[list[str], str]] = [
    (["non-disclosure", "nda", "confidentiality agreement", "mutual confidentiality"], "NDA"),
    (["employment agreement", "offer letter", "employment contract"], "Employment Agreement"),
    (["service level agreement", "sla"], "Service Level Agreement"),
    (["master services agreement", "master service agreement", "msa"], "Master Services Agreement"),
    (["software license", "license agreement", "saas", "subscription agreement"], "SaaS/License Agreement"),
    (["partnership agreement", "joint venture"], "Partnership Agreement"),
    (["vendor agreement", "supplier agreement", "procurement agreement", "purchase agreement"], "Vendor Agreement"),
    (["consulting agreement", "consulting services agreement"], "Consulting Agreement"),
    (["testing agreement", "test agreement", "testing services agreement"], "Testing Services Agreement"),
    (["lease agreement", "rental agreement"], "Lease Agreement"),
    (["non-compete", "non-solicitation"], "Non-Compete Agreement"),
]

# A document's type is decided by its title, not by words that appear somewhere
# in the body (almost every contract has a confidentiality section, which made
# the old full-text substring match label most contracts as NDAs).
_TITLE_REGION_CHARS = 1500
_HEADING_RE = re.compile(
    r"^\s*([A-Z][A-Za-z&/\-\s]{2,80}?\b(?:AGREEMENT|Agreement|CONTRACT|Contract))\s*$",
    re.MULTILINE,
)


def _matches(keywords: list[str], text: str) -> bool:
    return any(re.search(rf"\b{re.escape(k)}\b", text) for k in keywords)


def _detect_type(text: str, filename: str) -> str:
    name = re.sub(r"[_\-.]+", " ", filename).lower()
    head = text[:_TITLE_REGION_CHARS]
    title_region = f"{name}\n{head.lower()}"

    # 1) Known type named in the filename or title area
    for keywords, label in _TYPE_PATTERNS:
        if _matches(keywords, title_region):
            return label

    # 2) The document's own heading, e.g. "TESTING SERVICES AGREEMENT"
    m = _HEADING_RE.search(head)
    if m:
        heading = " ".join(m.group(1).split())
        if 2 <= len(heading.split()) <= 8:
            return heading.title()

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