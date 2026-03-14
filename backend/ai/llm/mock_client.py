import json
import random
from ai.llm.base import BaseLLMClient
from core.logger import get_logger

logger = get_logger(__name__)


class MockLLMClient(BaseLLMClient):
    @property
    def provider_name(self) -> str:
        return "mock"

    @property
    def model_name(self) -> str:
        return "contractiq-mock-v1"

    async def complete(self, system: str, user: str, json_mode: bool = True) -> str:
        """
        Smart mock that reads the contract text and generates a realistic analysis.
        Used as ultimate fallback when all LLMs fail.
        """
        logger.info("Using mock LLM client (final fallback)")
        text = user.lower()

        # Detect contract type
        if any(w in text for w in ["non-disclosure", "nda", "confidential"]):
            ctype, risk, score = "Non-Disclosure Agreement", "low", random.randint(15, 30)
        elif any(w in text for w in ["employment", "employee", "salary"]):
            ctype, risk, score = "Employment Agreement", "medium", random.randint(35, 55)
        elif any(w in text for w in ["service level", "sla", "uptime"]):
            ctype, risk, score = "Service Level Agreement", "medium", random.randint(40, 65)
        elif any(w in text for w in ["enterprise", "license", "saas"]):
            ctype, risk, score = "Enterprise License Agreement", "high", random.randint(65, 85)
        elif any(w in text for w in ["master service", "msa"]):
            ctype, risk, score = "Master Services Agreement", "medium", random.randint(45, 70)
        else:
            ctype, risk, score = "Commercial Agreement", random.choice(["medium", "high"]), random.randint(40, 75)

        result = {
            "executive_summary": f"This {ctype} presents a {risk} risk profile. Key areas requiring attention include liability limitations, termination rights, and intellectual property ownership.",
            "summary": f"The {ctype} is a {'standard' if risk == 'low' else 'complex'} commercial document.",
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
                    "recommendation": "Negotiate 60-90 day notice period."
                },
                {
                    "clause_type": "Liability Cap",
                    "risk_level": "high",
                    "clause_text": "Liability limited to fees paid.",
                    "explanation": "Cap may be too low for potential damages.",
                    "recommendation": "Increase liability cap to 12 months fees."
                },
                {
                    "clause_type": "Indemnification",
                    "risk_level": "medium",
                    "clause_text": "Mutual indemnification for third-party claims.",
                    "explanation": "Standard but needs IP infringement coverage.",
                    "recommendation": "Add explicit IP indemnification."
                }
            ],
            "recommendations": [
                "Review liability cap and negotiate increase",
                "Check auto-renewal terms",
                "Verify data processing compliance"
            ]
        }

        return json.dumps(result)