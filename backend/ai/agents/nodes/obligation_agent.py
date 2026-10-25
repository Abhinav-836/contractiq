# ai/agents/nodes/obligation_agent.py
import re

from core.logger import get_logger

logger = get_logger(__name__)

OBLIGATION_KEYWORDS = [
    "shall", "must", "required to", "obligated to", "agrees to",
    "will provide", "will deliver", "will pay", "will notify",
    "responsible for", "duty to",
]


async def obligation_agent(state: dict) -> dict:
    text = state.get("clean_text") or state.get("raw_text") or ""
    obligations = _extract_obligations(text)
    logger.info(f"obligation_agent.done count={len(obligations)}")
    return {**state, "obligations": obligations}


def _extract_obligations(text: str) -> list[dict]:
    obligations: list[dict] = []
    seen: set[str] = set()
    sentences = re.split(r"(?<=[.;])\s+|\n{2,}", text)

    for sentence in sentences:
        sentence = sentence.strip()
        if not (20 <= len(sentence) <= 500):
            continue

        s_lower = sentence.lower()
        if not any(re.search(rf"\b{re.escape(kw)}\b", s_lower) for kw in OBLIGATION_KEYWORDS):
            continue
        if s_lower in seen:
            continue
        seen.add(s_lower)

        # Use the sentence verbatim. The old "COMPANY shall " / "DEVELOPER shall "
        # prefixing produced garbage like "COMPANY shall the Client must pay ...".
        description = " ".join(sentence.split())

        all_words = description.split()
        title = " ".join(all_words[:8]) + ("..." if len(all_words) > 8 else "")

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