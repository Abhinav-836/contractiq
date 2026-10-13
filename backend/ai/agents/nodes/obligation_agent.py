# ai/agents/nodes/obligation_agent.py
import re

from core.logger import get_logger

logger = get_logger(__name__)

OBLIGATION_KEYWORDS = [
    "shall", "must", "required to", "obligated to", "agrees to",
    "will provide", "will deliver", "will pay", "will notify",
    "responsible for", "duty to",
]

_CLIENT_WORDS = ("company", "client", "buyer", "customer")
_VENDOR_WORDS = ("developer", "vendor", "provider", "supplier", "contractor")


async def obligation_agent(state: dict) -> dict:
    text = state.get("clean_text") or state.get("raw_text") or ""
    obligations = _extract_obligations(text)
    logger.info(f"obligation_agent.done count={len(obligations)}")
    return {**state, "obligations": obligations}


def _extract_obligations(text: str) -> list[dict]:
    obligations: list[dict] = []
    sentences = re.split(r"(?<=[.;])\s+", text)

    for sentence in sentences:
        sentence = sentence.strip()
        if not (20 <= len(sentence) <= 500):
            continue

        s_lower = sentence.lower()
        if not any(kw in s_lower for kw in OBLIGATION_KEYWORDS):
            continue

        first_word = sentence.split()[0].lower().rstrip(".,;:")

        party_prefix = ""
        if any(w in s_lower for w in _CLIENT_WORDS):
            party_prefix = "COMPANY shall "
        elif any(w in s_lower for w in _VENDOR_WORDS):
            party_prefix = "DEVELOPER shall "

        # Build description without double-prefixing
        if party_prefix and first_word not in (_CLIENT_WORDS + _VENDOR_WORDS):
            description = f"{party_prefix}{sentence[0].lower()}{sentence[1:]}"
        else:
            description = sentence

        words = sentence.split()[:8]
        title = " ".join(words) + ("..." if len(words) == 8 else "")

        due_date = None
        m = re.search(r"within\s+(\d+)\s+(days?|months?|weeks?)", s_lower)
        if m:
            due_date = f"Within {m.group(1)} {m.group(2)}"

        priority = "medium"
        if any(w in s_lower for w in ("immediately", "forthwith", "promptly", "as soon as")):
            priority = "high"

        obligations.append({
            "title": title[:100],
            "description": description[:500],
            "due_date": due_date,
            "priority": priority,
        })

        if len(obligations) >= 15:
            break

    return obligations