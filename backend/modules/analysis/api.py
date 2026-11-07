from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_db
from modules.contracts.repository import workspace_contract_ids
from modules.workspaces.deps import current_workspace
from modules.workspaces.permissions import WorkspaceContext
from .models import Analysis
from .repository import AnalysisRepository
from .schemas import AnalysisOut

router = APIRouter()


@router.get("/contract/{contract_id}", response_model=AnalysisOut)
async def get_analysis_by_contract(
    contract_id: str,
    db: AsyncSession = Depends(get_db),
    ctx: WorkspaceContext = Depends(current_workspace),
):
    result = await db.execute(
        select(Analysis).where(
            Analysis.contract_id == contract_id,
            Analysis.contract_id.in_(workspace_contract_ids(ctx.workspace_id)),
        )
    )
    analysis = result.scalar_one_or_none()
    if not analysis:
        raise HTTPException(404, "Analysis not found for this contract")
    return AnalysisRepository(db).serialize(analysis)


@router.get("/{analysis_id}", response_model=AnalysisOut)
async def get_analysis(
    analysis_id: str,
    db: AsyncSession = Depends(get_db),
    ctx: WorkspaceContext = Depends(current_workspace),
):
    result = await db.execute(
        select(Analysis).where(
            Analysis.id == analysis_id,
            Analysis.contract_id.in_(workspace_contract_ids(ctx.workspace_id)),
        )
    )
    analysis = result.scalar_one_or_none()
    if not analysis:
        raise HTTPException(404, "Analysis not found")
    return AnalysisRepository(db).serialize(analysis)