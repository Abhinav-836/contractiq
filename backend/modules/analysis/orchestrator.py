# modules/analysis/orchestrator.py
import traceback

from sqlalchemy.ext.asyncio import AsyncSession

from ai.agents.graph import run_analysis_graph
from core.logger import get_logger
from modules.obligations.repository import ObligationRepository
from modules.alerts.repository import AlertRepository

logger = get_logger(__name__)


async def orchestrate_analysis(
    contract_id: str,
    text: str,
    filename: str,
    db: AsyncSession,
) -> dict:
    """
    Runs the multi-agent analysis graph, then persists obligations and alerts.
    Reuses the caller's DB session — does NOT open its own.
    """
    logger.info(f"orchestrator.start contract_id={contract_id}")

    try:
        result = await run_analysis_graph(
            text=text,
            filename=filename,
            contract_id=contract_id,
        )

        logger.info(
            f"orchestrator.graph_done provider={result.get('llm_provider')} "
            f"risk={result.get('risk_level')} score={result.get('risk_score')}"
        )

        obligations = result.get("obligations_extracted", [])
        if obligations:
            created = await _create_obligations(db, contract_id, obligations)
            logger.info(f"orchestrator.obligations_created count={created}")

        await _create_alerts_from_analysis(db, contract_id, result)

        return result

    except Exception as e:
        logger.error(f"orchestrator.failed contract_id={contract_id} error={e}")
        traceback.print_exc()
        return {
            "contract_id": contract_id,
            "executive_summary": "Analysis encountered an error.",
            "summary": f"Error: {str(e)[:200]}",
            "risk_score": 50,
            "risk_level": "medium",
            "llm_provider": "error",
            "llm_model": "none",
            "clauses": [],
            "recommendations": ["Please re-upload or try again later."],
            "obligations_extracted": [],
        }


async def _create_obligations(db: AsyncSession, contract_id: str, obligations: list) -> int:
    repo = ObligationRepository(db)
    created = 0
    for obl in obligations:
        try:
            await repo.create(
                contract_id=contract_id,
                title=(obl.get("title") or "Contract Obligation")[:100],
                description=(obl.get("description") or "")[:500] or None,
                due_date=obl.get("due_date"),
                priority=obl.get("priority", "medium"),
            )
            created += 1
        except Exception as e:
            logger.error(f"orchestrator.obligation_create_failed error={e}")
    await db.flush()
    return created


async def _create_alerts_from_analysis(db: AsyncSession, contract_id: str, analysis: dict):
    repo = AlertRepository(db)
    created = 0

    clauses = analysis.get("clauses", []) or []
    high_risk = [c for c in clauses if (c or {}).get("risk_level") == "high"]
    for clause in high_risk[:3]:
        try:
            await repo.create(
                contract_id=contract_id,
                type="risk",
                title=f"High Risk: {clause.get('clause_type', 'Clause')}",
                message=(clause.get("explanation") or "Review required")[:200],
            )
            created += 1
        except Exception as e:
            logger.error(f"orchestrator.alert_create_failed error={e}")

    for obl in analysis.get("obligations_extracted", []) or []:
        if obl.get("priority") == "high":
            try:
                await repo.create(
                    contract_id=contract_id,
                    type="obligation",
                    title="Critical Obligation",
                    message=(obl.get("description") or "Important obligation")[:200],
                )
                created += 1
            except Exception as e:
                logger.error(f"orchestrator.obligation_alert_failed error={e}")

    await db.flush()
    if created:
        logger.info(f"orchestrator.alerts_created count={created}")