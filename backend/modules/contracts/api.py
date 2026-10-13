import os
from typing import Optional, List

from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_db
from core.security import require_auth, get_current_user_id
from .service import ContractService
from .schemas import ContractOut, ContractStatsOut, ContractUploadResponse

router = APIRouter()


@router.get("", response_model=List[ContractOut])
async def list_contracts(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(require_auth),   # auth REQUIRED
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = None,
):
    service = ContractService(db)
    return await service.get_all(user_id, skip, limit, status)


@router.get("/stats", response_model=ContractStatsOut)
async def get_contract_stats(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(require_auth),
):
    service = ContractService(db)
    return await service.get_stats()


@router.post("/upload", response_model=ContractUploadResponse)
async def upload_contract(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(require_auth),
):
    service = ContractService(db)
    return await service.upload(file, background_tasks, user_id)


@router.get("/{contract_id}", response_model=ContractOut)
async def get_contract(
    contract_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(require_auth),
):
    service = ContractService(db)
    contract = await service.get_one(contract_id)
    if contract.user_id and contract.user_id != user_id:
        raise HTTPException(403, "Not authorized to view this contract")
    return contract


@router.post("/{contract_id}/analyze")
async def manually_trigger_analysis(
    contract_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(require_auth),
):
    service = ContractService(db)
    contract = await service.get_one(contract_id)
    if contract.user_id and contract.user_id != user_id:
        raise HTTPException(403, "Not authorized")

    from modules.contracts.service import _run_analysis_task
    background_tasks.add_task(
        _run_analysis_task,
        contract.id,
        contract.file_path,
        contract.file_type,
        contract.filename,
    )
    return {"message": "Analysis triggered", "contract_id": contract_id, "status": "processing"}


@router.delete("/{contract_id}")
async def delete_contract(
    contract_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(require_auth),
):
    service = ContractService(db)
    contract = await service.get_one(contract_id)
    if contract.user_id and contract.user_id != user_id:
        raise HTTPException(403, "Not authorized")
    return await service.delete(contract_id, user_id)