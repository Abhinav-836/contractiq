import asyncio
import threading

def run_pipeline_in_thread(contract_id: str, file_path: str, file_type: str, filename: str):
    """Runs the async pipeline in a fresh thread with its own event loop."""
    asyncio.run(_pipeline(contract_id, file_path, file_type, filename))


async def run_ingestion_pipeline(contract_id: str, file_path: str, file_type: str, filename: str):
    """Called by FastAPI BackgroundTasks - spawns a thread to avoid event loop conflicts."""
    t = threading.Thread(
        target=run_pipeline_in_thread,
        args=(contract_id, file_path, file_type, filename),
        daemon=True
    )
    t.start()


async def extract_text(file_path: str, file_type: str) -> str:
    ext = file_type.lower()
    if ext == ".txt":
        import aiofiles
        async with aiofiles.open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return await f.read()
    elif ext == ".pdf":
        from ingestion.parser.pdf import parse_pdf
        return await parse_pdf(file_path)
    elif ext in (".doc", ".docx"):
        from ingestion.parser.docx import parse_docx
        return await parse_docx(file_path)
    return ""


async def _pipeline(contract_id: str, file_path: str, file_type: str, filename: str):
    from sqlalchemy.ext.asyncio import AsyncSession
    from db.session import AsyncSessionLocal
    from modules.contracts.repository import ContractRepository
    from modules.analysis.repository import AnalysisRepository
    from modules.analysis.orchestrator import orchestrate_analysis
    import logging
    logger = logging.getLogger(__name__)

    logger.info(f"pipeline.start contract_id={contract_id} filename={filename}")
    print(f"[PIPELINE] Starting analysis for: {filename}")

    async with AsyncSessionLocal() as db:
        try:
            text = await extract_text(file_path, file_type)
            if not text.strip():
                text = f"Contract document: {filename}"
            print(f"[PIPELINE] Extracted {len(text)} chars from {filename}")

            contract_repo = ContractRepository(db)
            await contract_repo.update_status(contract_id, "processing", extracted_text=text)
            await db.commit()

            analysis_data = await orchestrate_analysis(contract_id, text, filename)
            risk_level = analysis_data.get("risk_level", "medium")
            llm_provider = analysis_data.get("llm_provider", "mock")
            print(f"[PIPELINE] Analysis done. Risk={risk_level} Provider={llm_provider}")

            analysis_repo = AnalysisRepository(db)
            await analysis_repo.create(contract_id, analysis_data, llm_provider)

            await contract_repo.update_status(contract_id, "completed", risk_level=risk_level)
            await db.commit()

            print(f"[PIPELINE] COMPLETE for {filename} - status=completed risk={risk_level}")

        except Exception as e:
            import traceback
            print(f"[PIPELINE] FAILED for {filename}: {e}")
            traceback.print_exc()
            try:
                await ContractRepository(db).update_status(contract_id, "failed")
                await db.commit()
            except Exception:
                pass