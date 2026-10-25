from ai.agents.nodes.parser_agent import parser_agent
from ai.agents.nodes.risk_agent import risk_agent
from ai.agents.nodes.obligation_agent import obligation_agent
from core.logger import get_logger

logger = get_logger(__name__)


async def run_analysis_graph(text: str, filename: str, contract_id: str) -> dict:
    """
    parser → risk (LLM with fallback chain) → obligations.

    Errors propagate to the caller, which marks the contract as failed.
    (Previously an error dict was returned and saved as a "completed" analysis
    whose summary read "Analysis encountered an error".)
    """
    logger.info(f"graph.start contract_id={contract_id}")
    state = {"contract_id": contract_id, "raw_text": text, "filename": filename}

    state = await parser_agent(state)
    state = await risk_agent(state)
    state = await obligation_agent(state)

    analysis = dict(state.get("analysis") or {})
    analysis["obligations_extracted"] = state.get("obligations", [])
    analysis["contract_type"] = state.get("contract_type", "Contract")

    logger.info(f"graph.complete contract_id={contract_id}")
    return analysis