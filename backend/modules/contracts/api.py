from typing import Optional, List

from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_db
from core.security import require_auth
from .service import ContractService
from .schemas import ContractOut, ContractListItem, ContractStatsOut, ContractUploadResponse

router = APIRouter()


@router.get("", response_model=List[ContractListItem])
async def list_contracts(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(require_auth),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = None,
):
    # List items omit extracted_text — returning full contract text for every row
    # made this endpoint (polled every 5s by the UI) very heavy.
    return await ContractService(db).get_all(user_id, skip, limit, status)


@router.get("/stats", response_model=ContractStatsOut)
async def get_contract_stats(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(require_auth),
):
    return await ContractService(db).get_stats(user_id)


@router.post("/upload", response_model=ContractUploadResponse)
async def upload_contract(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(require_auth),
):
    return await ContractService(db).upload(file, background_tasks, user_id)


@router.get("/{contract_id}", response_model=ContractOut)
async def get_contract(
    contract_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(require_auth),
):
    return await ContractService(db).get_owned(contract_id, user_id)


@router.post("/{contract_id}/analyze")
async def trigger_analysis(
    contract_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(require_auth),
):
    service = ContractService(db)
    contract = await service.get_owned(contract_id, user_id)
    return await service.reanalyze(contract, background_tasks)


@router.delete("/{contract_id}")
async def delete_contract(
    contract_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(require_auth),
):
    service = ContractService(db)
    contract = await service.get_owned(contract_id, user_id)
    return await service.delete(contract)