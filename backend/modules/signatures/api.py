from typing import List
from urllib.parse import quote

from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_db
from modules.signatures import service
from modules.signatures.schemas import DeclineBody, EnvelopeCreate, EnvelopeOut, PublicSigningOut, SignBody
from modules.workspaces.deps import current_workspace
from modules.workspaces.permissions import WorkspaceContext

# Workspace side (login + X-Workspace-Id)
router = APIRouter()
# Signer side (no login; the token in the link is the credential)
public_router = APIRouter()


@router.get("/contract/{contract_id}", response_model=List[EnvelopeOut])
async def contract_envelopes(
    contract_id: str, ctx: WorkspaceContext = Depends(current_workspace), db: AsyncSession = Depends(get_db)
):
    """Every signature request for a contract, newest first."""
    return await service.list_for_contract(db, ctx, contract_id)


@router.post("/contract/{contract_id}", response_model=EnvelopeOut, status_code=201)
async def send_for_signing(
    contract_id: str,
    body: EnvelopeCreate,
    request: Request,
    ctx: WorkspaceContext = Depends(current_workspace),
    db: AsyncSession = Depends(get_db),
):
    """Members and above. The response carries each signer's link token once."""
    signers = [s.model_dump() for s in body.signers]
    return await service.create_envelope(db, ctx, contract_id, signers, body.message, request)


@router.get("/{envelope_id}", response_model=EnvelopeOut)
async def certificate(
    envelope_id: str, ctx: WorkspaceContext = Depends(current_workspace), db: AsyncSession = Depends(get_db)
):
    """Full record with the audit trail, for the signature certificate."""
    return await service.get_certificate(db, ctx, envelope_id)


def _pdf(data: bytes, filename: str) -> Response:
    return Response(
        content=data,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}",
            "Cache-Control": "no-store",
        },
    )


@router.get("/{envelope_id}/signed-pdf")
async def signed_pdf(
    envelope_id: str, ctx: WorkspaceContext = Depends(current_workspace), db: AsyncSession = Depends(get_db)
):
    """Original pages + signature certificate, with the original file attached."""
    return _pdf(*await service.signed_copy(db, ctx, envelope_id))


@router.post("/{envelope_id}/signers/{signer_id}/link", response_model=EnvelopeOut)
async def new_link(
    envelope_id: str,
    signer_id: str,
    request: Request,
    ctx: WorkspaceContext = Depends(current_workspace),
    db: AsyncSession = Depends(get_db),
):
    """Replace a signer's link (e.g. it was lost or sent to the wrong person)."""
    return await service.reissue_link(db, ctx, envelope_id, signer_id, request)


@router.post("/{envelope_id}/cancel", response_model=EnvelopeOut)
async def cancel(
    envelope_id: str,
    request: Request,
    ctx: WorkspaceContext = Depends(current_workspace),
    db: AsyncSession = Depends(get_db),
):
    return await service.cancel(db, ctx, envelope_id, request)


@public_router.get("/{token}", response_model=PublicSigningOut)
async def signing_page(token: str, request: Request, db: AsyncSession = Depends(get_db)):
    return await service.public_summary(db, token, request)


@public_router.get("/{token}/document")
async def signing_document(token: str, db: AsyncSession = Depends(get_db)):
    data, content_type, filename = await service.public_document(db, token)
    return Response(
        content=data,
        media_type=content_type,
        headers={
            "Content-Disposition": f"inline; filename*=UTF-8''{quote(filename)}",
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )


@public_router.get("/{token}/signed-pdf")
async def signer_signed_pdf(token: str, db: AsyncSession = Depends(get_db)):
    return _pdf(*await service.public_signed_copy(db, token))


@public_router.post("/{token}/sign", response_model=PublicSigningOut)
async def sign(token: str, body: SignBody, request: Request, db: AsyncSession = Depends(get_db)):
    return await service.sign(db, token, body.typed_name, body.consent, request)


@public_router.post("/{token}/decline", response_model=PublicSigningOut)
async def decline(token: str, body: DeclineBody, request: Request, db: AsyncSession = Depends(get_db)):
    return await service.decline(db, token, body.reason, request)
