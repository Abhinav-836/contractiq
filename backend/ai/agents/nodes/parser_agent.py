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


# Matched on word boundaries so "nda" no longer matches "standard"/"calendar"/"agenda".
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
    # [ \t] not \s: a heading is a single line, it must not swallow the line above it
    r"^[ \t]*([A-Z][A-Za-z&/\- \t]{2,80}?\b(?:AGREEMENT|Agreement|CONTRACT|Contract))[ \t]*$",
    re.MULTILINE,
)


def _first_match_pos(keywords: list[str], text: str) -> int:
    """Position of the earliest whole-word match of any keyword, or -1."""
    positions = [m.start() for k in keywords if (m := re.search(rf"\b{re.escape(k)}\b", text))]
    return min(positions) if positions else -1


def _detect_type(text: str, filename: str) -> str:
    name = re.sub(r"[_\-.()]+", " ", filename).lower()
    head = text[:_TITLE_REGION_CHARS]

    # 1) The filename usually names the document ("..._Testing_Agreement_...")
    for keywords, label in _TYPE_PATTERNS:
        if _first_match_pos(keywords, name) >= 0:
            return label

    # 2) In the opening text, the EARLIEST match wins — the title comes first.
    #    Checking patterns in priority order instead let a passing reference like
    #    "...under a separate Non-Disclosure Agreement" override "TEST AGREEMENT".
    head_lower = head.lower()
    best_label, best_pos = None, len(head_lower) + 1
    for keywords, label in _TYPE_PATTERNS:
        pos = _first_match_pos(keywords, head_lower)
        if 0 <= pos < best_pos:
            best_label, best_pos = label, pos

    # 3) The document's own heading, e.g. "WEBSITE DEVELOPMENT AGREEMENT". It wins
    #    when it comes before any keyword match: a title we don't have a pattern
    #    for beats a passing mention of another contract type further down.
    m = _HEADING_RE.search(head)
    if m and m.end() <= best_pos:  # no known type inside the heading itself
        heading = " ".join(m.group(1).split())
        if 2 <= len(heading.split()) <= 8:
            return heading.title()

    return best_label or "Commercial Agreement"


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