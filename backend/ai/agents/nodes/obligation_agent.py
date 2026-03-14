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
    """
    Extracts obligations from contract text using pattern matching.
    Updates state with: obligations list.
    """
    text = state.get("clean_text", state.get("raw_text", ""))
    obligations = _extract_obligations(text)

    logger.info("obligation_agent.done", count=len(obligations))
    return {**state, "obligations": obligations}


def _extract_obligations(text: str) -> list:
    obligations = []
    sentences = re.split(r'(?<=[.;])\s+', text)

    for i, sentence in enumerate(sentences):
        sentence = sentence.strip()
        if len(sentence) < 20 or len(sentence) > 500:
            continue

        s_lower = sentence.lower()
        if not any(kw in s_lower for kw in OBLIGATION_KEYWORDS):
            continue

        # Determine party for description
        party_prefix = ""
        if re.search(r'\b(company|client|buyer|customer)\b', s_lower):
            party_prefix = "COMPANY shall "
        elif re.search(r'\b(developer|vendor|provider|supplier|contractor)\b', s_lower):
            party_prefix = "DEVELOPER shall "

        # Create title (first few words)
        words = sentence.split()[:8]
        title = " ".join(words) + ("..." if len(words) == 8 else "")
        
        # Create full description with party context
        if party_prefix and not sentence.lower().startswith(tuple(p.lower().strip() for p in party_prefix.split())):
            description = party_prefix + sentence[0].lower() + sentence[1:]
        else:
            description = sentence

        # Determine due date if mentioned
        due_date = None
        date_match = re.search(
            r'within\s+(\d+)\s+(days?|months?|weeks?)',
            s_lower
        )
        if date_match:
            due_date = f"Within {date_match.group(1)} {date_match.group(2)}"

        # Determine priority
        priority = "medium"
        if "immediately" in s_lower or "forthwith" in s_lower:
            priority = "high"
        elif "promptly" in s_lower or "as soon as" in s_lower:
            priority = "high"
        elif "reasonable" in s_lower:
            priority = "medium"
        else:
            priority = "medium"

        obligations.append({
            "title": title[:100],  # Title field for the model
            "description": description[:500],  # Description field
            "due_date": due_date,
            "priority": priority,
            # No obligated_party field - will be handled by repository
        })

        if len(obligations) >= 15:
            break

    return obligations