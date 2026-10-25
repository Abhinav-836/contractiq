# modules/contracts/service.py
import os
import logging
import traceback

import aiofiles
from fastapi import UploadFile, HTTPException, BackgroundTasks
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.constants import ALLOWED_FILE_EXTENSIONS
from db.session import AsyncSessionLocal
from modules.contracts.models import Contract
from modules.contracts.repository import ContractRepository
from modules.analysis.repository import AnalysisRepository
from modules.analysis.orchestrator import orchestrate_analysis
from ingestion.parser import extract_text_from_file, ExtractionError

logger = logging.getLogger(__name__)

MIN_TEXT_CHARS = 100


class ContractService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ContractRepository(db)

    async def get_all(self, user_id: str, skip=0, limit=50, status=None):
        return await self.repo.list_all(user_id, skip, limit, status)

    async def get_stats(self, user_id: str):
        return await self.repo.stats(user_id)

    async def get_owned(self, contract_id: str, user_id: str) -> Contract:
        """
        Fetch a contract the caller owns. Returns 404 (not 403) for other users'
        contracts so ids can't be probed. Contracts with user_id=NULL are no
        longer treated as public.
        """
        contract = await self.repo.get_by_id(contract_id)
        if not contract or contract.user_id != user_id:
            raise HTTPException(404, "Contract not found")
        return contract

    async def upload(self, file: UploadFile, background_tasks: BackgroundTasks, user_id: str):
        filename = os.path.basename(file.filename or "").strip()
        if not filename:
            raise HTTPException(400, "File has no name")

        ext = os.path.splitext(filename)[1].lower()
        if ext == ".doc":
            raise HTTPException(400, "Legacy .doc files aren't supported. Save as .docx or PDF and re-upload.")
        if ext not in ALLOWED_FILE_EXTENSIONS:
            raise HTTPException(400, f"File type '{ext or 'unknown'}' not allowed. Use PDF, DOCX or TXT.")

        # Read at most limit+1 bytes so a huge upload can't exhaust memory
        content = await file.read(settings.max_file_size_bytes + 1)
        if len(content) > settings.max_file_size_bytes:
            raise HTTPException(413, f"File exceeds {settings.MAX_FILE_SIZE_MB}MB limit")
        if not content:
            raise HTTPException(400, "File is empty")

        logger.info(f"contracts.upload filename={filename} bytes={len(content)} ext={ext}")

        contract = await self.repo.create(
            filename=filename,
            file_type=ext,
            file_size=len(content),
            file_path="",
            user_id=user_id,
        )

        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        file_path = os.path.join(settings.UPLOAD_DIR, f"{contract.id}{ext}")
        try:
            async with aiofiles.open(file_path, "wb") as f:
                await f.write(content)
        except Exception as e:
            logger.error(f"contracts.file_write_failed error={e}")
            raise HTTPException(500, "Could not store the uploaded file")

        await self.repo.update_file_path(contract.id, file_path)
        await self.db.commit()

        background_tasks.add_task(_run_analysis_task, contract.id, file_path, ext, filename)

        return {
            "id": contract.id,
            "filename": filename,
            "status": "processing",
            "message": "Contract uploaded. AI analysis started.",
        }

    async def reanalyze(self, contract: Contract, background_tasks: BackgroundTasks):
        if contract.status == "processing":
            raise HTTPException(409, "Analysis is already running for this contract")
        if not contract.file_path or not os.path.exists(contract.file_path):
            # Render's disk is ephemeral — the file is gone after a redeploy/restart
            raise HTTPException(
                410, "The original file is no longer on the server. Please upload the contract again."
            )
        await self.repo.update_status(contract.id, "processing")
        await self.db.commit()
        background_tasks.add_task(
            _run_analysis_task, contract.id, contract.file_path, contract.file_type, contract.filename
        )
        return {"message": "Analysis triggered", "contract_id": contract.id, "status": "processing"}

    async def delete(self, contract: Contract):
        file_path = contract.file_path
        await self.repo.delete_with_children(contract.id)
        await self.db.commit()
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError as e:
                logger.warning(f"contracts.file_delete_failed path={file_path} error={e}")
        return {"message": "Contract deleted successfully"}


# ─────────────────────────────────────────────────────────────────────────────
# Background task — creates its OWN session
# ─────────────────────────────────────────────────────────────────────────────

async def _run_analysis_task(contract_id: str, file_path: str, file_type: str, filename: str) -> None:
    logger.info(f"analysis_task.start contract_id={contract_id} file={filename}")

    async with AsyncSessionLocal() as db:
        repo = ContractRepository(db)
        try:
            await repo.update_status(contract_id, "processing")
            await db.commit()

            try:
                text = await extract_text_from_file(file_path, file_type)
            except ExtractionError as e:
                logger.warning(f"analysis_task.extract_failed contract_id={contract_id} error={e}")
                text = ""

            if len(text) < MIN_TEXT_CHARS:
                # Scanned/image-only PDFs land here. Don't invent an analysis of a
                # placeholder string — mark it failed so the UI can tell the user.
                logger.warning(f"analysis_task.no_text contract_id={contract_id} chars={len(text)}")
                await repo.update_status(contract_id, "failed", extracted_text=text or None)
                await db.commit()
                return

            await repo.update_status(contract_id, "processing", extracted_text=text)
            await db.commit()

            # Clear results of any previous run so re-analysis doesn't duplicate
            # obligations and alerts.
            from modules.analysis.models import Analysis
            from modules.obligations.models import Obligation
            from modules.alerts.models import Alert
            for model in (Analysis, Obligation, Alert):
                await db.execute(delete(model).where(model.contract_id == contract_id))
            await db.flush()

            analysis_data = await orchestrate_analysis(
                contract_id=contract_id, text=text, filename=filename, db=db
            )

            await AnalysisRepository(db).create(
                contract_id=contract_id,
                data=analysis_data,
                llm_provider=analysis_data.get("llm_provider", "unknown"),
            )

            risk_level = analysis_data.get("risk_level") or "medium"
            await repo.update_status(contract_id, "completed", risk_level=risk_level)
            await db.commit()

            logger.info(
                f"analysis_task.complete contract_id={contract_id} "
                f"risk={risk_level} provider={analysis_data.get('llm_provider')}"
            )

        except Exception as e:
            logger.error(f"analysis_task.failed contract_id={contract_id} error={e}")
            traceback.print_exc()
            # The session is in a failed transaction state — it MUST be rolled
            # back before it can be used again, otherwise the status update below
            # raises PendingRollbackError and the contract stays "processing" forever.
            try:
                await db.rollback()
                await repo.update_status(contract_id, "failed")
                await db.commit()
            except Exception as db_err:
                logger.error(f"analysis_task.status_update_failed error={db_err}")