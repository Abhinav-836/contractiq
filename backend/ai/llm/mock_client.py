import hashlib
import json

from ai.llm.base import BaseLLMClient
from core.logger import get_logger

logger = get_logger(__name__)


def _stable_score(text: str) -> int:
    """Deterministic 40-85 range from text hash."""
    h = int(hashlib.sha256(text.encode()).hexdigest(), 16)
    return 40 + (h % 46)


class MockLLMClient(BaseLLMClient):
    @property
    def provider_name(self) -> str:
        return "mock"

    @property
    def model_name(self) -> str:
        return "contractiq-mock-v1"

    async def complete(self, system: str, user: str, json_mode: bool = True) -> str:
        logger.info("mock.complete called")
        text = user.lower()

        if any(w in text for w in ("non-disclosure", "nda", "confidential")):
            ctype, risk = "Non-Disclosure Agreement", "low"
        elif any(w in text for w in ("employment", "employee", "salary")):
            ctype, risk = "Employment Agreement", "medium"
        elif any(w in text for w in ("service level", "sla", "uptime")):
            ctype, risk = "Service Level Agreement", "medium"
        elif any(w in text for w in ("enterprise", "license", "saas")):
            ctype, risk = "Enterprise License Agreement", "high"
        elif any(w in text for w in ("master service", "msa")):
            ctype, risk = "Master Services Agreement", "medium"
        else:
            ctype, risk = "Commercial Agreement", "medium"

        score = _stable_score(text)
        if risk == "low":
            score = min(score, 30)
        elif risk == "high":
            score = max(score, 65)

        result = {
            "executive_summary": (
                f"This {ctype} presents a {risk} risk profile. Key areas requiring "
                "attention include liability limitations, termination rights, and IP ownership."
            ),
            "summary": f"The {ctype} is a {'standard' if risk == 'low' else 'complex'} document.",
            "risk_score": float(score),
            "risk_level": risk,
            "parties": ["Party A (Client)", "Party B (Vendor/Provider)"],
            "key_dates": [
                {"label": "Effective Date", "date": "Upon execution"},
                {"label": "Initial Term", "date": "12 months"},
                {"label": "Auto-Renewal", "date": "Annual"},
            ],
            "clauses": [
                {
                    "clause_type": "Termination",
                    "risk_level": "high" if score > 60 else "medium",
                    "clause_text": "30 days notice required for termination.",
                    "explanation": "Short notice period may be insufficient.",
                    "recommendation": "Negotiate 60-90 day notice period.",
                },
                {
                    "clause_type": "Liability Cap",
                    "risk_level": "high",
                    "clause_text": "Liability limited to fees paid.",
                    "explanation": "Cap may be too low for potential damages.",
                    "recommendation": "Increase liability cap to 12 months fees.",
                },
                {
                    "clause_type": "Indemnification",
                    "risk_level": "medium",
                    "clause_text": "Mutual indemnification for third-party claims.",
                    "explanation": "Standard but needs IP infringement coverage.",
                    "recommendation": "Add explicit IP indemnification.",
                },
            ],
            "recommendations": [
                "Review liability cap and negotiate increase",
                "Check auto-renewal terms",
                "Verify data processing compliance",
            ],
        }
        return json.dumps(result)