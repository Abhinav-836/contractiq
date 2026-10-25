# ai/agents/nodes/risk_agent.py
import json
import os
import re

import yaml

from ai.llm.router import get_llm_client, get_fallback_clients
from core.logger import get_logger

logger = get_logger(__name__)

# This file: backend/ai/agents/nodes/risk_agent.py
# Prompt:    backend/ai/prompts/risk.yaml   (two levels up, NOT three)
_PROMPT_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "prompts", "risk.yaml")
)

_FALLBACK_PROMPT = {
    "system": "You are a contract analysis AI. Respond with valid JSON only.",
    "user_template": (
        "Analyze this contract and return ONE JSON object with keys: "
        "executive_summary (string), summary (string), risk_score (0-100 number), "
        "risk_level (low|medium|high), parties (array of strings), "
        "key_dates (array of {label, date}), clauses (array of {clause_type, risk_level, "
        "clause_text, explanation, recommendation}), recommendations (array of strings).\n"
        "Contract text:\n<contract>\n{contract_text}\n</contract>"
    ),
}

_prompt_cache: dict | None = None


def _load_prompt() -> dict:
    global _prompt_cache
    if _prompt_cache is not None:
        return _prompt_cache
    try:
        with open(_PROMPT_PATH, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if data and "system" in data and "user_template" in data:
            logger.info(f"prompt.loaded path={_PROMPT_PATH}")
            _prompt_cache = data
            return data
        logger.warning(f"prompt.malformed path={_PROMPT_PATH}")
    except Exception as e:
        logger.error(f"prompt.load_failed path={_PROMPT_PATH} error={e}")
    _prompt_cache = _FALLBACK_PROMPT
    return _prompt_cache


async def risk_agent(state: dict) -> dict:
    text = state.get("clean_text") or state.get("raw_text") or ""

    if len(text.strip()) < 100:
        logger.warning(f"risk_agent.short_text chars={len(text)}")
        return {
            **state,
            "analysis": {
                "executive_summary": "Contract text too short for meaningful analysis.",
                "summary": f"Only {len(text.strip())} characters of text could be extracted.",
                "risk_score": 0.0,
                "risk_level": "low",
                "parties": [],
                "key_dates": [],
                "clauses": [],
                "recommendations": ["Upload a complete, text-based contract document."],
                "llm_provider": "system",
                "llm_model": "none",
            },
        }

    truncated = text[:15000]
    prompt = _load_prompt()
    system = prompt["system"]
    user = prompt["user_template"].replace("{contract_text}", truncated)

    analysis: dict | None = None
    error_history: list[str] = []

    candidates = [(get_llm_client().provider_name, get_llm_client())] + get_fallback_clients()
    for i, (provider, client) in enumerate(candidates):
        try:
            logger.info(f"risk_agent.try provider={provider} model={client.model_name}")
            raw = await client.complete(system=system, user=user, json_mode=True)
            parsed = _normalize(_parse_llm_response(raw))
            if not parsed["executive_summary"] and not parsed["clauses"]:
                raise ValueError("LLM response missing summary and clauses")
            analysis = parsed
            analysis["llm_provider"] = provider
            analysis["llm_model"] = client.model_name
            if i > 0:
                analysis["fallback_used"] = True
                analysis["fallback_chain"] = error_history
            logger.info(f"risk_agent.success provider={provider}")
            break
        except Exception as e:
            msg = f"{provider} failed: {str(e)[:300]}"
            logger.error(f"risk_agent.provider_failed {msg}")
            error_history.append(msg)

    if analysis is None:
        # Mock should never fail, but never leave the pipeline without a result
        from ai.llm.mock_client import MockLLMClient
        mock = MockLLMClient()
        analysis = _normalize(json.loads(await mock.complete(system, user)))
        analysis.update(llm_provider="mock", llm_model=mock.model_name,
                        fallback_used=True, fallback_chain=error_history)

    metadata = state.get("metadata", {}) or {}
    if not analysis.get("parties") and metadata.get("detected_parties"):
        analysis["parties"] = metadata["detected_parties"]

    logger.info(
        f"risk_agent.complete provider={analysis.get('llm_provider')} "
        f"risk_level={analysis.get('risk_level')} score={analysis.get('risk_score')}"
    )
    return {**state, "analysis": analysis}


# ─────────────────────────────────────────────────────────────────────────────
# Parsing & normalization — LLM output is untrusted. Anything that reaches the
# DB must match AnalysisOut, otherwise GET /analysis/contract/{id} returns 500.
# ─────────────────────────────────────────────────────────────────────────────

def _parse_llm_response(raw: str) -> dict:
    if not raw or not raw.strip():
        raise ValueError("Empty LLM response")

    cleaned = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if not m:
            raise ValueError(f"LLM returned non-JSON: {raw[:200]}")
        data = json.loads(m.group(0))

    if not isinstance(data, dict):
        raise ValueError(f"LLM returned {type(data).__name__}, expected object")
    return data


def _level(value, default: str = "medium") -> str:
    v = str(value or "").strip().lower()
    if v.startswith("high") or v in ("critical", "severe"):
        return "high"
    if v.startswith("med") or v == "moderate":
        return "medium"
    if v.startswith("low") or v == "minimal":
        return "low"
    return default


def _level_from_score(score: float) -> str:
    if score > 60:
        return "high"
    if score > 30:
        return "medium"
    return "low"


def _str(value) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (list, tuple)):
        return "; ".join(_str(v) for v in value if v)
    if isinstance(value, dict):
        return _str(value.get("name") or value.get("text") or json.dumps(value))
    return str(value)


def _normalize(data: dict) -> dict:
    # risk_score: accept 72, "72", "72/100", 0.72
    score = None
    raw_score = data.get("risk_score")
    try:
        if isinstance(raw_score, str):
            m = re.search(r"\d+(\.\d+)?", raw_score)
            raw_score = m.group(0) if m else None
        if raw_score is not None:
            score = float(raw_score)
            if 0 < score <= 1:
                score *= 100
            score = max(0.0, min(100.0, round(score, 1)))
    except (TypeError, ValueError):
        score = None

    if score is None:
        level = _level(data.get("risk_level"))
        score = {"low": 20.0, "medium": 50.0, "high": 75.0}[level]
    else:
        level = _level(data.get("risk_level"), default=_level_from_score(score))

    clauses = []
    for c in data.get("clauses") or []:
        if not isinstance(c, dict):
            continue
        clause_type = _str(c.get("clause_type") or c.get("type") or c.get("name"))
        if not clause_type:
            continue
        clauses.append({
            "clause_type": clause_type[:120],
            "risk_level": _level(c.get("risk_level") or c.get("risk")),
            "clause_text": _str(c.get("clause_text") or c.get("text") or c.get("excerpt"))[:1500],
            "explanation": _str(c.get("explanation") or c.get("analysis") or c.get("risk_explanation"))[:1500],
            "recommendation": _str(c.get("recommendation")) or None,
        })

    key_dates = []
    for d in data.get("key_dates") or []:
        if isinstance(d, dict):
            label = _str(d.get("label") or d.get("name") or d.get("type"))
            date = _str(d.get("date") or d.get("value"))
            if label or date:
                key_dates.append({"label": label or "Date", "date": date or "Not specified"})
        elif isinstance(d, str) and d.strip():
            key_dates.append({"label": "Date", "date": d.strip()})

    parties = [p for p in (_str(x) for x in (data.get("parties") or [])) if p][:10]
    recommendations = [r for r in (_str(x) for x in (data.get("recommendations") or [])) if r][:15]

    return {
        "executive_summary": _str(data.get("executive_summary")),
        "summary": _str(data.get("summary")),
        "risk_score": score,
        "risk_level": level,
        "parties": parties,
        "key_dates": key_dates,
        "clauses": clauses,
        "recommendations": recommendations,
    }