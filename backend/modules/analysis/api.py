from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .models import Analysis
from core.dependencies import get_db
from core.security import get_current_user_id
from .repository import AnalysisRepository
from .schemas import AnalysisOut
from typing import Optional

router = APIRouter()


@router.get("/contract/{contract_id}", response_model=AnalysisOut)
async def get_analysis_by_contract(
    contract_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: Optional[str] = Depends(get_current_user_id),
):
    """Get analysis for a specific contract"""
    repo = AnalysisRepository(db)
    analysis = await repo.get_by_contract(contract_id)
    
    if not analysis:
        raise HTTPException(404, "Analysis not found for this contract")
    
    return repo.serialize(analysis)


@router.get("/{analysis_id}", response_model=AnalysisOut)
async def get_analysis(
    analysis_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get analysis by ID"""
    result = await db.execute(
        select(Analysis).where(Analysis.id == analysis_id)
    )
    analysis = result.scalar_one_or_none()
    
    if not analysis:
        raise HTTPException(404, "Analysis not found")
    
    repo = AnalysisRepository(db)
    return repo.serialize(analysis)