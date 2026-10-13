from ai.agents.nodes.parser_agent import parser_agent
from ai.agents.nodes.risk_agent import risk_agent
from ai.agents.nodes.obligation_agent import obligation_agent
from core.logger import get_logger

logger = get_logger(__name__)


async def run_analysis_graph(text: str, filename: str, contract_id: str) -> dict:
    logger.info(f"graph.start contract_id={contract_id}")
    state = {
        "contract_id": contract_id,
        "raw_text": text,
        "filename": filename,
    }

    try:
        state = await parser_agent(state)
        state = await risk_agent(state)
        state = await obligation_agent(state)

        analysis = state.get("analysis", {})
        analysis["obligations_extracted"] = state.get("obligations", [])
        analysis["contract_type"] = state.get("contract_type", "Contract")

        logger.info(f"graph.complete contract_id={contract_id}")
        return analysis

    except Exception as e:
        import traceback
        logger.error(f"graph.failed contract_id={contract_id} error={e}")
        traceback.print_exc()
        return {
            "contract_id": contract_id,
            "executive_summary": "Analysis encountered an error.",
            "summary": f"Error: {str(e)[:200]}",
            "risk_score": 50,
            "risk_level": "medium",
            "llm_provider": "error",
            "obligations_extracted": [],
        }