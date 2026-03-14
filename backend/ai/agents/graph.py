from ai.agents.nodes.parser_agent import parser_agent
from ai.agents.nodes.risk_agent import risk_agent
from ai.agents.nodes.obligation_agent import obligation_agent
from core.logger import get_logger

logger = get_logger(__name__)


async def run_analysis_graph(text: str, filename: str, contract_id: str) -> dict:
    """
    Runs the multi-agent analysis pipeline:
    1. Parser Agent  → cleans text, detects contract type
    2. Risk Agent    → calls LLM for full risk analysis (with fallbacks)
    3. Obligation Agent → extracts obligations from text

    Returns merged analysis dict ready for DB storage.
    """
    logger.info(f"🚀 Starting analysis graph for contract {contract_id}")
    
    # Initial state
    state = {
        "contract_id": contract_id,
        "raw_text": text,
        "filename": filename,
    }

    try:
        # Node 1: Parse
        logger.info(f"📝 Running parser agent for contract {contract_id}")
        state = await parser_agent(state)
        logger.info(f"✅ Parser agent complete - contract type: {state.get('contract_type')}")

        # Node 2: Risk analysis (LLM call with fallbacks)
        logger.info(f"🤖 Running risk agent for contract {contract_id}")
        state = await risk_agent(state)
        logger.info(f"✅ Risk agent complete - provider: {state.get('analysis', {}).get('llm_provider')}")

        # Node 3: Obligation extraction
        logger.info(f"📋 Running obligation agent for contract {contract_id}")
        state = await obligation_agent(state)
        logger.info(f"✅ Obligation agent complete - found: {len(state.get('obligations', []))} obligations")

        # Merge into final result
        analysis = state.get("analysis", {})
        analysis["obligations_extracted"] = state.get("obligations", [])
        analysis["contract_type"] = state.get("contract_type", "Contract")

        logger.info(f"✅ Analysis graph complete for contract {contract_id}")
        return analysis
        
    except Exception as e:
        logger.error(f"❌ Analysis graph failed for contract {contract_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Return basic analysis so contract doesn't get stuck
        return {
            "contract_id": contract_id,
            "executive_summary": "Analysis encountered an error. Please try again.",
            "summary": f"Error: {str(e)[:200]}",
            "risk_score": 50,
            "risk_level": "medium",
            "llm_provider": "error",
            "obligations_extracted": []
        }