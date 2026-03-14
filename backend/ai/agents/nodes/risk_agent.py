# ai/agents/nodes/risk_agent.py
import json
import yaml
import os
import re
from ai.llm.router import get_llm_client, get_fallback_clients
from core.logger import get_logger

logger = get_logger(__name__)
_PROMPT_PATH = os.path.join(os.path.dirname(__file__), "../../prompts/risk.yaml")


def _load_prompt() -> dict:
    """Load prompt from YAML file with fallback"""
    try:
        if os.path.exists(_PROMPT_PATH):
            with open(_PROMPT_PATH, "r") as f:
                data = yaml.safe_load(f)
                logger.info(f"Loaded prompt from {_PROMPT_PATH}")
                return data
    except Exception as e:
        logger.warning(f"Failed to load prompt from {_PROMPT_PATH}: {e}")
    
    # Return default prompt
    return {
        "system": "You are a contract analysis AI. Respond with valid JSON only.",
        "user_template": "Analyze this contract and respond with JSON:\n{contract_text}",
    }


async def risk_agent(state: dict) -> dict:
    """
    Calls LLM with cleaned contract text.
    Fallback chain: Ollama (GPT-OS 20B) -> Gemini -> OpenAI -> Mock
    """
    text = state.get("clean_text", state.get("raw_text", ""))
    filename = state.get("filename", "")
    contract_type = state.get("contract_type", "Contract")

    # Check if we have actual text
    if not text or len(text.strip()) < 100:
        logger.warning(f"Contract text too short: {len(text)} chars")
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
                "llm_model": "none"
            }
        }

    # Truncate to avoid token limits (GPT-OS 20B has 20k context)
    truncated = text[:15000] if len(text) > 15000 else text
    logger.info(f"Contract text truncated to {len(truncated)} chars")

    prompt = _load_prompt()
    system = prompt["system"]
    user_template = prompt["user_template"]
    
    # Format the user template with contract text
    user = user_template.replace("{contract_text}", truncated)

    analysis = None
    error_history = []

    # Try primary (Ollama with GPT-OS 20B)
    try:
        primary_client = get_llm_client()
        logger.info("risk_agent.calling_llm", provider="ollama", model="gpt-os-20b", attempt=1)
        raw = await primary_client.complete(system=system, user=user, json_mode=True)
        analysis = _parse_llm_response(raw)
        analysis["llm_provider"] = "ollama"
        analysis["llm_model"] = primary_client.model_name
        logger.info("risk_agent.success", provider="ollama", model="gpt-os-20b")
    except Exception as e:
        error_msg = f"Ollama failed: {str(e)}"
        logger.error("risk_agent.failed", provider="ollama", error=error_msg)
        error_history.append(error_msg)

    # Try fallbacks in order if primary failed
    if not analysis:
        fallback_clients = get_fallback_clients()
        
        for provider, client in fallback_clients:
            try:
                logger.info("risk_agent.calling_llm", provider=provider, attempt="fallback")
                raw = await client.complete(system=system, user=user, json_mode=True)
                analysis = _parse_llm_response(raw)
                analysis["llm_provider"] = provider
                analysis["llm_model"] = client.model_name
                analysis["fallback_used"] = True
                analysis["fallback_chain"] = error_history
                logger.info("risk_agent.success", provider=provider)
                break
            except Exception as e:
                error_msg = f"{provider} failed: {str(e)}"
                logger.error("risk_agent.failed", provider=provider, error=error_msg)
                error_history.append(error_msg)
                continue

    # Ultimate fallback - if all LLMs failed, use mock
    if not analysis:
        from ai.llm.mock_client import MockLLMClient
        logger.warning("risk_agent.all_llms_failed", errors=error_history)
        mock_client = MockLLMClient()
        raw = await mock_client.complete(system=system, user=user, json_mode=True)
        analysis = _parse_llm_response(raw)
        analysis["llm_provider"] = "mock"
        analysis["llm_model"] = "contractiq-mock-v1"
        analysis["fallback_used"] = True
        analysis["fallback_chain"] = error_history

    # Validate analysis has required fields
    if not analysis.get("risk_level") or analysis.get("risk_level") == "N/A":
        logger.warning("LLM returned invalid analysis, using mock fallback")
        from ai.llm.mock_client import MockLLMClient
        mock_client = MockLLMClient()
        raw = await mock_client.complete(system=system, user=user, json_mode=True)
        analysis = _parse_llm_response(raw)
        analysis["llm_provider"] = "mock-fallback"
        analysis["llm_model"] = "contractiq-mock-v1"

    # Merge detected metadata into analysis
    metadata = state.get("metadata", {})
    if not analysis.get("parties") and metadata.get("detected_parties"):
        analysis["parties"] = metadata["detected_parties"]

    logger.info("risk_agent.complete", 
                provider=analysis.get("llm_provider"),
                risk_level=analysis.get("risk_level"),
                score=analysis.get("risk_score"))

    return {**state, "analysis": analysis}


def _parse_llm_response(raw: str) -> dict:
    """Parse LLM response, handling JSON extraction if needed"""
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Try to extract JSON from response
        m = re.search(r'\{.*\}', raw, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except:
                pass
        raise ValueError(f"LLM returned non-JSON: {raw[:200]}")