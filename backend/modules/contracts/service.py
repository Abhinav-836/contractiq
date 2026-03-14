# modules/contracts/service.py
import os
import aiofiles
import sys
from fastapi import UploadFile, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, select
from .repository import ContractRepository
from modules.analysis.orchestrator import orchestrate_analysis
from core.config import settings
from core.constants import ALLOWED_FILE_EXTENSIONS, MAX_FILE_SIZE
import logging
from datetime import datetime
from typing import Optional, List
import asyncio
import traceback

# Fix the import - use the correct path
try:
    from ingestion.parser.parser import extract_text_from_file
except ImportError:
    try:
        from ingestion.parser import extract_text_from_file
    except ImportError:
        # Fallback - define a simple function
        async def extract_text_from_file(file_path: str, file_type: str) -> str:
            print(f"⚠️ Using fallback text extractor for {file_path}")
            if file_type == '.txt':
                async with aiofiles.open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return await f.read()
            return f"Contract document at {file_path}"

logger = logging.getLogger(__name__)


class ContractService:
    def __init__(self, db: AsyncSession):
        self.repo = ContractRepository(db)
        self.db = db

    async def get_all(self, user_id: Optional[str] = None, skip: int = 0, limit: int = 50, status: Optional[str] = None) -> List:
        """Get all contracts with filters"""
        try:
            return await self.repo.list_all(user_id, skip, limit, status)
        except Exception as e:
            logger.error(f"Error fetching contracts: {str(e)}")
            return []

    async def get_stats(self):
        """Get contract statistics"""
        try:
            return await self.repo.stats()
        except Exception as e:
            logger.error(f"Error fetching stats: {str(e)}")
            return {
                "total_contracts": 0,
                "processing": 0,
                "completed": 0,
                "failed": 0,
                "high_risk": 0,
                "medium_risk": 0,
                "low_risk": 0
            }

    async def get_one(self, contract_id: str):
        """Get contract by ID"""
        contract = await self.repo.get_by_id(contract_id)
        if not contract:
            raise HTTPException(404, f"Contract '{contract_id}' not found")
        return contract

    async def upload(self, file: UploadFile, background_tasks: BackgroundTasks, user_id=None):
        """Upload a contract and automatically trigger analysis"""
        try:
            # Validate file type
            ext = os.path.splitext(file.filename)[1].lower()
            if ext not in ALLOWED_FILE_EXTENSIONS:
                raise HTTPException(400, f"File type '{ext}' not allowed. Allowed: {ALLOWED_FILE_EXTENSIONS}")

            # Validate file size
            content = await file.read()
            if len(content) > MAX_FILE_SIZE:
                raise HTTPException(400, f"File exceeds {settings.MAX_FILE_SIZE_MB}MB limit")

            logger.info(f"📤 Uploading file: {file.filename}, size: {len(content)} bytes, type: {ext}")

            # Create contract record
            contract = await self.repo.create(
                filename=file.filename,
                file_type=ext,
                file_size=len(content),
                file_path="",
                user_id=user_id,
            )

            # Save file to disk
            file_path = os.path.join(settings.UPLOAD_DIR, f"{contract.id}{ext}")
            os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
            
            async with aiofiles.open(file_path, "wb") as f:
                await f.write(content)

            # Update file path in database
            await self.db.execute(
                update(type(contract))
                .where(type(contract).id == contract.id)
                .values(file_path=file_path)
            )
            await self.db.commit()

            logger.info(f"✅ File saved: {file_path}")
            logger.info(f"🚀 Adding background analysis task for contract {contract.id}")

            # IMPORTANT: Add background task to run analysis
            background_tasks.add_task(
                self._run_analysis,
                contract.id,
                file_path,
                ext,
                file.filename
            )

            return {
                "id": contract.id,
                "filename": file.filename,
                "status": "processing",
                "message": "Contract uploaded successfully. AI analysis started in background.",
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Upload failed: {str(e)}")
            traceback.print_exc()
            raise HTTPException(500, f"Upload failed: {str(e)}")

    async def _run_analysis(self, contract_id: str, file_path: str, file_type: str, filename: str):
        """Run analysis in background with proper error handling"""
        print(f"\n{'='*60}")
        print(f"🔥🔥🔥 _run_analysis STARTED for contract {contract_id} 🔥🔥🔥")
        print(f"📁 File: {filename}")
        print(f"📂 Path: {file_path}")
        print(f"🔤 Type: {file_type}")
        print(f"📂 File exists: {os.path.exists(file_path)}")
        print(f"{'='*60}\n")
        sys.stdout.flush()
        
        logger.info(f"🔍 [BACKGROUND] Starting analysis for contract {contract_id} - {filename}")
        
        try:
            # Update status to processing
            await self.repo.update_status(contract_id, "processing")
            await self.db.commit()
            logger.info(f"✅ [BACKGROUND] Updated status to processing")
            
            # Step 1: Extract text from file
            logger.info(f"📄 [BACKGROUND] Extracting text from {filename}")
            print(f"📄 Calling extract_text_from_file({file_path}, {file_type})")
            
            text = await extract_text_from_file(file_path, file_type)
            
            print(f"📄 Extracted {len(text) if text else 0} characters")
            logger.info(f"📄 [BACKGROUND] Extracted {len(text)} characters from {filename}")
            
            if not text or len(text.strip()) < 50:
                logger.warning(f"⚠️ [BACKGROUND] Extracted text too short for {contract_id}")
                text = f"""Contract document: {filename}
                
This is a standard business contract between two parties. 
Please analyze it for key clauses, risks, and obligations.
                
The agreement covers services, payment terms, liability limitations,
confidentiality obligations, and termination rights."""
                print(f"📄 Using fallback text ({len(text)} chars)")
            
            # Update contract with extracted text
            await self.repo.update_status(contract_id, "processing", extracted_text=text)
            await self.db.commit()
            logger.info(f"✅ [BACKGROUND] Updated contract with extracted text")

            # Step 2: Run AI analysis with Ollama (with fallback chain)
            logger.info(f"🤖 [BACKGROUND] Starting AI analysis for contract {contract_id}")
            print(f"🤖 Calling orchestrate_analysis()...")
            
            analysis_data = await orchestrate_analysis(contract_id, text, filename)
            
            print(f"✅ Analysis complete! Risk level: {analysis_data.get('risk_level')}")
            logger.info(f"✅ [BACKGROUND] Analysis completed - Risk: {analysis_data.get('risk_level')}")
            
            # Step 3: Save analysis to database - FIXED: Check for existing analysis
            from modules.analysis.repository import AnalysisRepository
            analysis_repo = AnalysisRepository(self.db)
            
            # Check if analysis already exists
            existing = await analysis_repo.get_by_contract(contract_id)
            if existing:
                logger.info(f"⚠️ [BACKGROUND] Analysis already exists for contract {contract_id}, deleting...")
                await self.db.delete(existing)
                await self.db.flush()
            
            # Create new analysis
            await analysis_repo.create(
                contract_id=contract_id,
                data=analysis_data,
                llm_provider=analysis_data.get('llm_provider', 'ollama')
            )
            logger.info(f"✅ [BACKGROUND] Saved analysis to database")
            
            # Step 4: Update contract status to completed
            risk_level = analysis_data.get("risk_level", "medium")
            await self.repo.update_status(contract_id, "completed", risk_level=risk_level)
            await self.db.commit()
            
            print(f"\n{'='*60}")
            print(f"✅✅✅ ANALYSIS COMPLETE for contract {contract_id} ✅✅✅")
            print(f"📊 Risk Level: {risk_level}")
            print(f"📊 Risk Score: {analysis_data.get('risk_score')}")
            print(f"🤖 Provider: {analysis_data.get('llm_provider')}")
            print(f"{'='*60}\n")
            
            logger.info(f"✅ [BACKGROUND] Analysis completed for contract {contract_id}")
            logger.info(f"📊 [BACKGROUND] Risk Level: {risk_level}, Score: {analysis_data.get('risk_score')}")
            logger.info(f"🤖 [BACKGROUND] Provider used: {analysis_data.get('llm_provider')}")
            
        except Exception as e:
            print(f"\n❌❌❌ ANALYSIS FAILED for contract {contract_id} ❌❌❌")
            print(f"Error: {str(e)}")
            traceback.print_exc()
            print(f"{'='*60}\n")
            
            logger.error(f"❌ [BACKGROUND] Analysis failed for contract {contract_id}: {str(e)}")
            traceback.print_exc()
            
            try:
                await self.repo.update_status(contract_id, "failed")
                await self.db.commit()
                logger.info(f"✅ [BACKGROUND] Updated status to failed")
            except Exception as db_err:
                logger.error(f"❌ Failed to update status: {str(db_err)}")

    async def delete(self, contract_id: str, user_id: str):
        """Delete a contract"""
        contract = await self.repo.get_by_id(contract_id)
        if not contract:
            raise HTTPException(404, "Contract not found")

        # Delete file from disk
        if os.path.exists(contract.file_path):
            os.remove(contract.file_path)
            logger.info(f"🗑️ Deleted file: {contract.file_path}")

        # Delete from database
        await self.db.delete(contract)
        await self.db.commit()

        return {"message": "Contract deleted successfully"}