# modules/analysis/orchestrator.py
from ai.agents.graph import run_analysis_graph
from core.logger import get_logger
from modules.obligations.repository import ObligationRepository
from modules.alerts.repository import AlertRepository
import json
import logging

logger = get_logger(__name__)


async def orchestrate_analysis(contract_id: str, text: str, filename: str) -> dict:
    """
    Main orchestrator — runs the multi-agent analysis graph.
    Returns structured analysis dict and creates obligations/alerts.
    """
    logger.info(f"🎯 Starting orchestrated analysis for contract {contract_id}")
    
    try:
        # Run the analysis graph with Ollama (primary) and fallbacks
        logger.info(f"🤖 Calling AI agents for contract {contract_id}")
        result = await run_analysis_graph(
            text=text,
            filename=filename,
            contract_id=contract_id
        )
        
        logger.info(f"✅ AI analysis complete for contract {contract_id}")
        logger.info(f"📊 Provider used: {result.get('llm_provider')}")
        logger.info(f"📊 Risk level: {result.get('risk_level')}")
        logger.info(f"📊 Risk score: {result.get('risk_score')}")
        
        # Create obligations from extracted data
        obligations = result.get("obligations_extracted", [])
        if obligations:
            logger.info(f"📋 Creating {len(obligations)} obligations for contract {contract_id}")
            created_count = await _create_obligations(contract_id, obligations)
            logger.info(f"✅ Created {created_count} obligations for contract {contract_id}")
        else:
            logger.info(f"📋 No obligations to create for contract {contract_id}")
        
        # Create alerts for high-risk items
        await _create_alerts_from_analysis(contract_id, result)
        
        # Log completion
        logger.info(
            f"✅ Orchestration complete for contract {contract_id}",
            extra={
                "risk_level": result.get("risk_level"),
                "risk_score": result.get("risk_score"),
                "obligations_count": len(obligations),
                "provider": result.get("llm_provider")
            }
        )
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Orchestration failed for contract {contract_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Return a basic result structure so the contract doesn't get stuck
        return {
            "contract_id": contract_id,
            "executive_summary": "Analysis encountered an error. Please try again or contact support.",
            "summary": f"Error during analysis: {str(e)[:200]}",
            "risk_score": 50,
            "risk_level": "medium",
            "llm_provider": "error",
            "llm_model": "none",
            "clauses": [],
            "recommendations": ["Please re-upload the contract or try again later"],
            "obligations_extracted": []
        }


async def _create_obligations(contract_id: str, obligations: list) -> int:
    """Create obligations in database"""
    from db.session import AsyncSessionLocal
    from modules.obligations.repository import ObligationRepository
    
    async with AsyncSessionLocal() as db:
        repo = ObligationRepository(db)
        created_count = 0
        
        for obl in obligations:
            try:
                # FIXED: Use correct field names that match the model
                title = obl.get("title", "Contract Obligation")
                description = obl.get("description", "")
                due_date = obl.get("due_date")
                priority = obl.get("priority", "medium")
                
                # Create obligation with correct parameters
                await repo.create(
                    contract_id=contract_id,
                    title=title[:100],  # Ensure title length
                    description=description[:500] if description else None,
                    due_date=due_date,
                    priority=priority,
                    # obligated_party is NOT passed here
                )
                created_count += 1
                logger.debug(f"✅ Created obligation for contract {contract_id}")
            except Exception as e:
                logger.error(f"❌ Failed to create obligation: {str(e)}")
                logger.debug(f"Obligation data: {obl}")
        
        await db.commit()
        return created_count


async def _create_alerts_from_analysis(contract_id: str, analysis: dict):
    """Create alerts based on analysis results"""
    from db.session import AsyncSessionLocal
    from modules.alerts.repository import AlertRepository
    
    async with AsyncSessionLocal() as db:
        alert_repo = AlertRepository(db)
        alert_count = 0
        
        # Check for high-risk clauses
        clauses = analysis.get("clauses", [])
        high_risk_clauses = [c for c in clauses if c.get("risk_level") == "high"]
        
        for clause in high_risk_clauses[:3]:  # Limit to top 3
            try:
                await alert_repo.create(
                    contract_id=contract_id,
                    type="risk",
                    title=f"High Risk: {clause.get('clause_type', 'Clause')}",
                    message=clause.get("explanation", "This clause requires attention")[:200],
                )
                alert_count += 1
            except Exception as e:
                logger.error(f"❌ Failed to create alert: {str(e)}")
        
        # Check for upcoming obligations with high priority
        obligations = analysis.get("obligations_extracted", [])
        for obligation in obligations:
            if obligation.get("priority") == "high":
                try:
                    await alert_repo.create(
                        contract_id=contract_id,
                        type="obligation",
                        title="Critical Obligation",
                        message=obligation.get("description", "Important obligation detected")[:200],
                    )
                    alert_count += 1
                except Exception as e:
                    logger.error(f"❌ Failed to create obligation alert: {str(e)}")
        
        await db.commit()
        if alert_count > 0:
            logger.info(f"✅ Created {alert_count} alerts for contract {contract_id}")