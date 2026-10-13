# ai/agents/nodes/risk_agent.py
import json
import os
import re

import yaml

from ai.llm.router import get_llm_client, get_fallback_clients
from core.logger import get_logger

logger = get_logger(__name__)

# File lives at: ai/agents/nodes/risk_agent.py
# Prompt lives at: prompts/risk.yaml (project root)
_PROMPT_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "prompts", "risk.yaml")
)


def _load_prompt() -> dict:
    """Load prompt from YAML, with sane default fallback."""
    try:
        if os.path.exists(_PROMPT_PATH):
            with open(_PROMPT_PATH, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if data and "system" in data and "user_template" in data:
                logger.info(f"prompt.loaded path={_PROMPT_PATH}")
                return data
            logger.warning(f"prompt.malformed path={_PROMPT_PATH}")
    except Exception as e:
        logger.warning(f"prompt.load_failed path={_PROMPT_PATH} error={e}")

    return {
        "system": "You are a contract analysis AI. Respond with valid JSON only.",
        "user_template": (
            "Analyze this contract and respond with a single JSON object. "
            "Contract text:\n<contract>\n{contract_text}\n</contract>"
        ),
    }


async def risk_agent(state: dict) -> dict:
    text = state.get("clean_text") or state.get("raw_text") or ""

    if len(text.strip()) < 100:
        logger.warning(f"risk_agent.short_text chars={len(text)}")
        return {
            **state,
            "analysis": {
                "executive_summary": "Contract text too short for meaningful analysis.",
                "summary": f"The provided contract text is only {len(text)} characters long.",
                "risk_score": 0,
                "risk_level": "unknown",
                "parties": [],
                "key_dates": [],
                "clauses": [],
                "recommendations": ["Please upload a complete contract document."],
                "llm_provider": "system",
                "llm_model": "none",
            },
        }

    truncated = text[:15000]
    logger.info(f"risk_agent.text_truncated chars={len(truncated)}")

    prompt = _load_prompt()
    system = prompt["system"]
    user = prompt["user_template"].replace("{contract_text}", truncated)

    analysis: dict | None = None
    error_history: list[str] = []

    # 1) Primary — Ollama Cloud
    try:
        primary = get_llm_client()
        logger.info(f"risk_agent.primary provider={primary.provider_name} model={primary.model_name}")
        raw = await primary.complete(system=system, user=user, json_mode=True)
        analysis = _parse_llm_response(raw)
        analysis["llm_provider"] = primary.provider_name
        analysis["llm_model"] = primary.model_name
        logger.info("risk_agent.primary_success")
    except Exception as e:
        msg = f"ollama failed: {e}"
        logger.error(f"risk_agent.primary_failed error={msg}")
        error_history.append(msg)

    # 2) Fallbacks — Gemini → OpenAI → Mock
    if not analysis:
        for provider, client in get_fallback_clients():
            try:
                logger.info(f"risk_agent.fallback provider={provider}")
                raw = await client.complete(system=system, user=user, json_mode=True)
                analysis = _parse_llm_response(raw)
                analysis["llm_provider"] = provider
                analysis["llm_model"] = client.model_name
                analysis["fallback_used"] = True
                analysis["fallback_chain"] = error_history
                logger.info(f"risk_agent.fallback_success provider={provider}")
                break
            except Exception as e:
                msg = f"{provider} failed: {e}"
                logger.error(f"risk_agent.fallback_failed error={msg}")
                error_history.append(msg)

    # 3) Ultimate fallback — Mock
    if not analysis:
        from ai.llm.mock_client import MockLLMClient
        logger.warning(f"risk_agent.all_failed errors={error_history}")
        mock = MockLLMClient()
        raw = await mock.complete(system=system, user=user, json_mode=True)
        analysis = _parse_llm_response(raw)
        analysis["llm_provider"] = "mock"
        analysis["llm_model"] = mock.model_name
        analysis["fallback_used"] = True
        analysis["fallback_chain"] = error_history

    # Validate core fields
    if not analysis.get("risk_level") or analysis.get("risk_level") == "N/A":
        logger.warning("risk_agent.invalid_analysis — using mock")
        from ai.llm.mock_client import MockLLMClient
        mock = MockLLMClient()
        raw = await mock.complete(system=system, user=user, json_mode=True)
        analysis = _parse_llm_response(raw)
        analysis["llm_provider"] = "mock-fallback"
        analysis["llm_model"] = mock.model_name

    # Merge metadata
    metadata = state.get("metadata", {}) or {}
    if not analysis.get("parties") and metadata.get("detected_parties"):
        analysis["parties"] = metadata["detected_parties"]

    logger.info(
        f"risk_agent.complete provider={analysis.get('llm_provider')} "
        f"risk_level={analysis.get('risk_level')} score={analysis.get('risk_score')}"
    )

    return {**state, "analysis": analysis}


def _parse_llm_response(raw: str) -> dict:
    if not raw:
        raise ValueError("Empty LLM response")

    # Strip markdown fences
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if m:
            return json.loads(m.group(0))
        raise ValueError(f"LLM returned non-JSON: {raw[:200]}")