"""
FastAPI dependencies that resolve the active workspace for a request.

The frontend sends the selected workspace in the X-Workspace-Id header. With no
header, the user's personal workspace is used — so old clients and API calls
without the header keep working exactly as before.
"""
from typing import Optional

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_db
from core.security import require_auth
from modules.workspaces.permissions import WorkspaceContext
from modules.workspaces.service import context_for, default_context

VIEWER_READ_ONLY = "You have view-only access to this workspace"


async def current_workspace(
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    user_id: str = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
) -> WorkspaceContext:
    workspace_id = (x_workspace_id or "").strip()
    if workspace_id:
        return await context_for(db, workspace_id, user_id)
    return await default_context(db, user_id)


async def editable_workspace(ctx: WorkspaceContext = Depends(current_workspace)) -> WorkspaceContext:
    """Members and above. Viewers get a 403."""
    ctx.require("member", VIEWER_READ_ONLY)
    return ctx


async def workspace_from_path(
    workspace_id: str,
    user_id: str = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
) -> WorkspaceContext:
    """For /workspaces/{workspace_id}/... routes."""
    return await context_for(db, workspace_id, user_id)
