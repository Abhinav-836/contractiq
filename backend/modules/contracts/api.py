from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from core.dependencies import get_db
from core.security import get_current_user_id
from .service import ContractService
from .schemas import ContractOut, ContractStatsOut, ContractUploadResponse
from typing import List, Optional
import os

router = APIRouter()


@router.get("", response_model=List[ContractOut])
async def list_contracts(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = None,
    user_id: Optional[str] = Depends(get_current_user_id),
):
    """List all contracts with optional filters"""
    service = ContractService(db)
    return await service.get_all(user_id, skip, limit, status)


@router.get("/stats", response_model=ContractStatsOut)
async def get_contract_stats(db: AsyncSession = Depends(get_db)):
    """Get contract statistics"""
    service = ContractService(db)
    return await service.get_stats()


@router.post("/upload", response_model=ContractUploadResponse)
async def upload_contract(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user_id: Optional[str] = Depends(get_current_user_id),
):
    """Upload a contract for AI analysis"""
    service = ContractService(db)
    return await service.upload(file, background_tasks, user_id)


@router.get("/{contract_id}", response_model=ContractOut)
async def get_contract(
    contract_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get contract by ID"""
    service = ContractService(db)
    return await service.get_one(contract_id)


@router.post("/{contract_id}/analyze", tags=["Contracts"])
async def manually_trigger_analysis(
    contract_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger analysis for a contract (useful for testing)"""
    service = ContractService(db)
    contract = await service.get_one(contract_id)
    
    background_tasks.add_task(
        service._run_analysis,
        contract.id,
        contract.file_path,
        contract.file_type,
        contract.filename
    )
    
    return {
        "message": "Analysis triggered successfully",
        "contract_id": contract_id,
        "status": "processing"
    }


# TEST ENDPOINTS - Remove in production
@router.post("/test-analysis/{contract_id}")
async def test_analysis(
    contract_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """TEST: Manually trigger analysis in background"""
    service = ContractService(db)
    contract = await service.get_one(contract_id)
    
    print(f"\n🔧 TEST: Adding background task for contract {contract_id}")
    background_tasks.add_task(
        service._run_analysis,
        contract.id,
        contract.file_path,
        contract.file_type,
        contract.filename
    )
    
    return {
        "message": "Test analysis triggered in background",
        "contract_id": contract_id,
        "status": "processing"
    }


@router.post("/test-analysis-sync/{contract_id}")
async def test_analysis_sync(
    contract_id: str,
    db: AsyncSession = Depends(get_db),
):
    """TEST: Manually trigger analysis synchronously (waits for completion)"""
    service = ContractService(db)
    contract = await service.get_one(contract_id)
    
    print(f"\n🔧 TEST SYNC: Starting analysis for contract {contract_id}")
    await service._run_analysis(
        contract.id,
        contract.file_path,
        contract.file_type,
        contract.filename
    )
    
    return {
        "message": "Test analysis completed synchronously",
        "contract_id": contract_id
    }


@router.get("/test-check/{contract_id}")
async def test_check_contract(
    contract_id: str,
    db: AsyncSession = Depends(get_db),
):
    """TEST: Check contract details"""
    service = ContractService(db)
    contract = await service.get_one(contract_id)
    
    return {
        "id": contract.id,
        "filename": contract.filename,
        "file_path": contract.file_path,
        "file_type": contract.file_type,
        "status": contract.status,
        "file_exists": os.path.exists(contract.file_path) if hasattr(contract, 'file_path') else False
    }