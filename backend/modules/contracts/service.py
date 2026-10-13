# modules/contracts/service.py
import os
import logging
import traceback

import aiofiles
from fastapi import UploadFile, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.constants import ALLOWED_FILE_EXTENSIONS, MAX_FILE_SIZE
from db.session import AsyncSessionLocal
from modules.contracts.models import Contract
from modules.contracts.repository import ContractRepository
from modules.analysis.repository import AnalysisRepository
from modules.analysis.orchestrator import orchestrate_analysis

try:
    from ingestion.parser.parser import extract_text_from_file
except ImportError:
    from ingestion.parser import extract_text_from_file  # type: ignore

logger = logging.getLogger(__name__)


class ContractService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ContractRepository(db)

    async def get_all(self, user_id=None, skip=0, limit=50, status=None):
        try:
            return await self.repo.list_all(user_id, skip, limit, status)
        except Exception as e:
            logger.error(f"contracts.list_failed error={e}")
            return []

    async def get_stats(self):
        try:
            return await self.repo.stats()
        except Exception as e:
            logger.error(f"contracts.stats_failed error={e}")
            return {
                "total_contracts": 0, "processing": 0, "completed": 0, "failed": 0,
                "high_risk": 0, "medium_risk": 0, "low_risk": 0,
            }

    async def get_one(self, contract_id: str):
        contract = await self.repo.get_by_id(contract_id)
        if not contract:
            raise HTTPException(404, f"Contract '{contract_id}' not found")
        return contract

    async def upload(self, file: UploadFile, background_tasks: BackgroundTasks, user_id=None):
        try:
            ext = os.path.splitext(file.filename)[1].lower()
            if ext not in ALLOWED_FILE_EXTENSIONS:
                raise HTTPException(400, f"File type '{ext}' not allowed")

            content = await file.read()
            if len(content) > MAX_FILE_SIZE:
                raise HTTPException(400, f"File exceeds {settings.MAX_FILE_SIZE_MB}MB limit")

            logger.info(f"contracts.upload filename={file.filename} bytes={len(content)} ext={ext}")

            contract = await self.repo.create(
                filename=file.filename,
                file_type=ext,
                file_size=len(content),
                file_path="",
                user_id=user_id,
            )

            file_path = os.path.join(settings.UPLOAD_DIR, f"{contract.id}{ext}")
            os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

            async with aiofiles.open(file_path, "wb") as f:
                await f.write(content)

            await self.repo.update_file_path(contract.id, file_path)
            await self.db.commit()

            logger.info(f"contracts.file_saved path={file_path}")

            # Background task opens its own DB session — do NOT pass self.db
            background_tasks.add_task(
                _run_analysis_task,
                contract.id,
                file_path,
                ext,
                file.filename,
            )

            return {
                "id": contract.id,
                "filename": file.filename,
                "status": "processing",
                "message": "Contract uploaded. AI analysis started.",
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"contracts.upload_failed error={e}")
            traceback.print_exc()
            raise HTTPException(500, f"Upload failed: {e}")

    async def delete(self, contract_id: str, user_id: str):
        contract = await self.repo.get_by_id(contract_id)
        if not contract:
            raise HTTPException(404, "Contract not found")
        if os.path.exists(contract.file_path):
            os.remove(contract.file_path)
        await self.db.delete(contract)
        await self.db.commit()
        return {"message": "Contract deleted successfully"}


# ─────────────────────────────────────────────────────────────────────────────
# Background task — creates its OWN session
# ─────────────────────────────────────────────────────────────────────────────

async def _run_analysis_task(
    contract_id: str, file_path: str, file_type: str, filename: str
) -> None:
    logger.info(f"analysis_task.start contract_id={contract_id} file={filename}")
    print(f"\n[ANALYSIS] START contract={contract_id} file={filename}")

    async with AsyncSessionLocal() as db:
        repo = ContractRepository(db)
        try:
            await repo.update_status(contract_id, "processing")
            await db.commit()

            try:
                text = await extract_text_from_file(file_path, file_type)
            except Exception as e:
                logger.error(f"analysis_task.extract_failed error={e}")
                text = ""

            if not text or len(text.strip()) < 50:
                logger.warning(f"analysis_task.short_text contract_id={contract_id}")
                text = (
                    f"Contract document: {filename}\n\n"
                    "This is a standard business contract between two parties. "
                    "Analyze for key clauses, risks, and obligations."
                )

            await repo.update_status(contract_id, "processing", extracted_text=text)
            await db.commit()

            analysis_data = await orchestrate_analysis(
                contract_id=contract_id,
                text=text,
                filename=filename,
                db=db,  # reuse this session
            )

            analysis_repo = AnalysisRepository(db)
            existing = await analysis_repo.get_by_contract(contract_id)
            if existing:
                await db.delete(existing)
                await db.flush()

            await analysis_repo.create(
                contract_id=contract_id,
                data=analysis_data,
                llm_provider=analysis_data.get("llm_provider", "unknown"),
            )

            risk_level = analysis_data.get("risk_level", "medium")
            await repo.update_status(contract_id, "completed", risk_level=risk_level)
            await db.commit()

            logger.info(
                f"analysis_task.complete contract_id={contract_id} "
                f"risk={risk_level} provider={analysis_data.get('llm_provider')}"
            )
            print(f"[ANALYSIS] COMPLETE contract={contract_id} risk={risk_level}")

        except Exception as e:
            logger.error(f"analysis_task.failed contract_id={contract_id} error={e}")
            traceback.print_exc()
            try:
                await repo.update_status(contract_id, "failed")
                await db.commit()
            except Exception as db_err:
                logger.error(f"analysis_task.status_update_failed error={db_err}")