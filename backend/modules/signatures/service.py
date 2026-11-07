"""
Built-in e-signature.

  * A member or above sends a reviewed contract out for signing to 1–10 people,
    who can be teammates or outsiders. Each signer gets a private link; the raw
    token is returned once and only its SHA-256 is stored.
  * A signer opens the link (no account needed), reads the document, types
    their full name and ticks the consent box. That is the signature.
  * Every signer must sign; one decline (with a reason) closes the request.
  * The SHA-256 of the file is fixed when the request is sent and checked
    again at every signature, so the certificate proves which bytes were signed.
  * Every step is logged with time, IP address and browser in signature_events.
  * One open request per contract. The requester or an admin can cancel it or
    issue a fresh link for a signer (the old link stops working).
  * contracts.signature_status mirrors the newest request that wasn't cancelled.

This is a simple electronic signature with an audit trail. It is not an
Aadhaar eSign or a certificate-based digital signature.
"""
import hashlib
import ipaddress
import re
import secrets
from datetime import datetime, timedelta, timezone
from typing import Iterable, Optional

from fastapi import HTTPException, Request
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from modules.contracts.models import Contract
from modules.contracts.service import load_file_bytes
from modules.notifications import templates
from modules.notifications.mailer import is_enabled as is_email_enabled
from modules.notifications.service import Email, Outbox, app_link, latest_status
from modules.signatures.models import SignatureEnvelope, SignatureEvent, SignatureSigner
from modules.users.models import User
from modules.workspaces.permissions import WorkspaceContext

MAX_SIGNERS = 10
NOT_FOUND = "Signature request not found"
LINK_NOT_FOUND = "This signing link is not valid. It may have been replaced by a newer link."
CONSENT_TEXT = (
    "I agree that typing my name here is my electronic signature on this document, "
    "that I have read it, and that I intend to be bound by it."
)
CONTENT_TYPES = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".txt": "text/plain; charset=utf-8",
}


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _aware(dt: datetime) -> datetime:
    # SQLite returns naive datetimes; treat them as UTC.
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def normalize_name(name: str) -> str:
    return re.sub(r"\s+", " ", (name or "").strip()).casefold()


# Cloudflare's edge ranges (https://www.cloudflare.com/ips/). Render sits behind
# Cloudflare, so these show up in X-Forwarded-For and must be skipped.
CLOUDFLARE_NETWORKS = [ipaddress.ip_network(n) for n in (
    "173.245.48.0/20", "103.21.244.0/22", "103.22.200.0/22", "103.31.4.0/22", "141.101.64.0/18",
    "108.162.192.0/18", "190.93.240.0/20", "188.114.96.0/20", "197.234.240.0/22", "198.41.128.0/17",
    "162.158.0.0/15", "104.16.0.0/13", "104.24.0.0/14", "172.64.0.0/13", "131.0.72.0/22",
    "2400:cb00::/32", "2606:4700::/32", "2803:f800::/32", "2405:b500::/32", "2405:8100::/32",
    "2a06:98c0::/29", "2c0f:f248::/32",
)]


def _is_proxy(ip) -> bool:
    return not ip.is_global or any(ip.version == n.version and ip in n for n in CLOUDFLARE_NETWORKS)


def client_info(request: Optional[Request]) -> tuple[Optional[str], Optional[str]]:
    """
    Caller's IP and browser.

    Render is behind Cloudflare, which puts the visitor's address in
    CF-Connecting-IP (overwriting anything the visitor sends). Otherwise walk
    X-Forwarded-For from the right, skipping private and Cloudflare addresses
    (added by the proxies), so a client can't simply prepend a fake one.
    """
    if request is None:
        return None, None
    ua = (request.headers.get("user-agent") or "")[:400] or None
    chain = [p.strip() for p in (request.headers.get("x-forwarded-for") or "").split(",") if p.strip()]
    cf = (request.headers.get("cf-connecting-ip") or "").strip()
    if cf:
        try:
            return str(ipaddress.ip_address(cf)), ua
        except ValueError:
            pass
    for candidate in reversed(chain):
        try:
            ip = ipaddress.ip_address(candidate)
        except ValueError:
            continue
        if not _is_proxy(ip):
            return str(ip), ua
    host = request.client.host if request.client else None
    return (chain[-1] if chain else host), ua


def _event(db: AsyncSession, envelope_id: str, type_: str, actor: Optional[str] = None,
           detail: Optional[str] = None, ip: Optional[str] = None, ua: Optional[str] = None) -> None:
    db.add(SignatureEvent(
        envelope_id=envelope_id, type=type_, actor=actor, detail=detail,
        ip_address=ip, user_agent=ua, created_at=utcnow(),
    ))


# ─────────────────────────────────────────────────────────────────────────────
# Reading (workspace side)
# ─────────────────────────────────────────────────────────────────────────────

async def _serialize(db: AsyncSession, envelopes: list[SignatureEnvelope], ctx: Optional[WorkspaceContext],
                     with_events: bool = False) -> list[dict]:
    if not envelopes:
        return []
    ids = [e.id for e in envelopes]
    signers = (
        await db.execute(
            select(SignatureSigner).where(SignatureSigner.envelope_id.in_(ids)).order_by(SignatureSigner.position)
        )
    ).scalars().all()
    events = []
    if with_events:
        events = (
            await db.execute(
                select(SignatureEvent).where(SignatureEvent.envelope_id.in_(ids)).order_by(SignatureEvent.created_at)
            )
        ).scalars().all()
    user_ids = {e.requested_by for e in envelopes if e.requested_by}
    users = {
        u.id: u.name for u in (await db.execute(select(User).where(User.id.in_(user_ids)))).scalars().all()
    } if user_ids else {}

    email_status = await latest_status(db, "signature_signer", [s.id for s in signers])

    by_env: dict[str, list] = {}
    for s in signers:
        by_env.setdefault(s.envelope_id, []).append({
            "id": s.id, "name": s.name, "email": s.email, "status": s.status,
            "typed_signature": s.typed_signature, "consent_text": s.consent_text,
            "decline_reason": s.decline_reason, "viewed_at": s.viewed_at, "acted_at": s.acted_at,
            "ip_address": s.ip_address, "user_agent": s.user_agent,
            "email_status": (email_status.get(s.id) or {}).get("status"),
            "email_error": (email_status.get(s.id) or {}).get("error"),
        })
    events_by_env: dict[str, list] = {}
    for ev in events:
        events_by_env.setdefault(ev.envelope_id, []).append({
            "type": ev.type, "actor": ev.actor, "detail": ev.detail,
            "ip_address": ev.ip_address, "user_agent": ev.user_agent, "created_at": ev.created_at,
        })

    out = []
    for e in envelopes:
        rows = by_env.get(e.id, [])
        can_manage = bool(ctx) and e.status == "pending" and (
            e.requested_by == ctx.user_id or ctx.can("admin")
        )
        out.append({
            "id": e.id, "contract_id": e.contract_id, "status": e.status, "message": e.message,
            "document_filename": e.document_filename, "document_sha256": e.document_sha256,
            "requested_by": e.requested_by,
            "requested_by_name": users.get(e.requested_by) or "Former member",
            "created_at": e.created_at, "closed_at": e.closed_at,
            "signers": rows,
            "signed_count": sum(1 for r in rows if r["status"] == "signed"),
            "can_manage": can_manage,
            "events": events_by_env.get(e.id, []) if with_events else None,
        })
    return out


async def _contract_in_workspace(db: AsyncSession, ctx: WorkspaceContext, contract_id: str) -> Contract:
    contract = await db.get(Contract, contract_id)
    if not contract or contract.workspace_id != ctx.workspace_id:
        raise HTTPException(404, "Contract not found")
    return contract


async def _envelope_in_workspace(db: AsyncSession, ctx: WorkspaceContext, envelope_id: str,
                                 lock: bool = False) -> SignatureEnvelope:
    q = select(SignatureEnvelope).where(
        SignatureEnvelope.id == envelope_id, SignatureEnvelope.workspace_id == ctx.workspace_id
    )
    if lock:
        q = q.with_for_update()
    envelope = (await db.execute(q)).scalar_one_or_none()
    if not envelope:
        raise HTTPException(404, NOT_FOUND)
    return envelope


async def list_for_contract(db: AsyncSession, ctx: WorkspaceContext, contract_id: str) -> list[dict]:
    await _contract_in_workspace(db, ctx, contract_id)
    envelopes = (
        await db.execute(
            select(SignatureEnvelope)
            .where(SignatureEnvelope.contract_id == contract_id)
            .order_by(SignatureEnvelope.created_at.desc())
        )
    ).scalars().all()
    return await _serialize(db, list(envelopes), ctx)


async def get_certificate(db: AsyncSession, ctx: WorkspaceContext, envelope_id: str) -> dict:
    envelope = await _envelope_in_workspace(db, ctx, envelope_id)
    return (await _serialize(db, [envelope], ctx, with_events=True))[0]


async def _signed_copy(db: AsyncSession, envelope: SignatureEnvelope, ctx: Optional[WorkspaceContext]) -> tuple[bytes, str]:
    from modules.signatures.pdf import build_signed_pdf, signed_filename

    if envelope.status != "completed":
        raise HTTPException(409, "The signed copy is available once everyone has signed")
    contract = await db.get(Contract, envelope.contract_id)
    data = await load_file_bytes(db, contract.id, contract.file_path) if contract else None
    if data is None or hashlib.sha256(data).hexdigest() != envelope.document_sha256:
        raise HTTPException(409, "The original document is no longer available, so a signed copy can't be made")
    record = (await _serialize(db, [envelope], ctx, with_events=True))[0]
    return build_signed_pdf(record, data), signed_filename(envelope.document_filename)


async def signed_copy_for_email(db: AsyncSession, envelope_id: str) -> Optional[tuple[bytes, str]]:
    envelope = await db.get(SignatureEnvelope, envelope_id)
    if not envelope or envelope.status != "completed":
        return None
    return await _signed_copy(db, envelope, None)


async def signed_copy(db: AsyncSession, ctx: WorkspaceContext, envelope_id: str) -> tuple[bytes, str]:
    envelope = await _envelope_in_workspace(db, ctx, envelope_id)
    return await _signed_copy(db, envelope, ctx)


# ─────────────────────────────────────────────────────────────────────────────
# Changing (workspace side)
# ─────────────────────────────────────────────────────────────────────────────

async def _sync_contract_status(db: AsyncSession, contract_id: str) -> None:
    latest = (
        await db.execute(
            select(SignatureEnvelope.status)
            .where(SignatureEnvelope.contract_id == contract_id, SignatureEnvelope.status != "cancelled")
            .order_by(SignatureEnvelope.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    await db.execute(update(Contract).where(Contract.id == contract_id).values(signature_status=latest))


def _require_manager(ctx: WorkspaceContext, envelope: SignatureEnvelope) -> None:
    if envelope.requested_by != ctx.user_id and not ctx.can("admin"):
        raise HTTPException(403, "Only the person who sent this for signing or a workspace admin can change it")
    if envelope.status != "pending":
        raise HTTPException(409, f"This signature request is already {envelope.status}")


def _queue_link_email(outbox: Optional[Outbox], envelope: SignatureEnvelope, signer: SignatureSigner,
                      token: str, requester: Optional[User], reissued: bool = False, reminder: bool = False) -> None:
    if outbox is None:
        return
    requester_name = requester.name if requester else "Someone"
    subject, html, text = templates.signature_request(
        signer.name, requester_name, envelope.document_filename, envelope.message,
        app_link(f"/sign/{token}"), reissued=reissued, reminder=reminder,
    )
    outbox.add(Email(
        kind="signature_reminder" if reminder else "signature_link" if reissued else "signature_request",
        to_email=signer.email, to_name=signer.name,
        subject=subject, html=html, text=text, workspace_id=envelope.workspace_id,
        reply_to=requester.email if requester else None,
        ref_type="signature_signer", ref_id=signer.id, signature_envelope_id=envelope.id,
    ))


async def create_envelope(db: AsyncSession, ctx: WorkspaceContext, contract_id: str,
                          signers: Iterable[dict], message: Optional[str], request: Optional[Request],
                          outbox: Optional[Outbox] = None) -> dict:
    ctx.require("member", "You have view-only access to this workspace")
    contract = await _contract_in_workspace(db, ctx, contract_id)
    if contract.status != "completed":
        raise HTTPException(409, "Wait for the review to finish before sending this for signing")

    open_id = (
        await db.execute(
            select(SignatureEnvelope.id).where(
                SignatureEnvelope.contract_id == contract_id, SignatureEnvelope.status == "pending"
            )
        )
    ).scalar_one_or_none()
    if open_id:
        raise HTTPException(409, "This contract is already out for signing. Cancel that request first.")

    cleaned, seen = [], set()
    for s in signers:
        name = re.sub(r"\s+", " ", (s.get("name") or "").strip())
        email = (s.get("email") or "").strip().lower()
        if not name or not email:
            raise HTTPException(422, "Every signer needs a name and an email")
        if email in seen:
            raise HTTPException(422, f"{email} is listed twice")
        seen.add(email)
        cleaned.append((name, email))
    if not 1 <= len(cleaned) <= MAX_SIGNERS:
        raise HTTPException(422, f"Add between 1 and {MAX_SIGNERS} signers")

    data = await load_file_bytes(db, contract.id, contract.file_path)
    if data is None:
        raise HTTPException(409, "The original file for this contract is missing, so it can't be signed")

    requester = await db.get(User, ctx.user_id)
    envelope = SignatureEnvelope(
        contract_id=contract.id, workspace_id=ctx.workspace_id, requested_by=ctx.user_id,
        message=(message or "").strip() or None, status="pending",
        document_sha256=hashlib.sha256(data).hexdigest(), document_filename=contract.filename,
        created_at=utcnow(),
    )
    db.add(envelope)
    await db.flush()

    links = {}
    for i, (name, email) in enumerate(cleaned):
        token = secrets.token_urlsafe(32)
        signer = SignatureSigner(
            envelope_id=envelope.id, name=name, email=email, position=i,
            token_hash=hash_token(token), status="pending",
        )
        db.add(signer)
        await db.flush()
        links[signer.id] = token
        _queue_link_email(outbox, envelope, signer, token, requester)

    ip, ua = client_info(request)
    _event(db, envelope.id, "created", requester.name if requester else None,
           f"Sent to {', '.join(n for n, _ in cleaned)}", ip, ua)
    await db.flush()
    await _sync_contract_status(db, contract.id)

    out = (await _serialize(db, [envelope], ctx))[0]
    out["links"] = links
    out["emailed"] = bool(outbox)
    return out


REMINDER_GAP = timedelta(hours=1)


async def reissue_link(db: AsyncSession, ctx: WorkspaceContext, envelope_id: str, signer_id: str,
                       request: Optional[Request], outbox: Optional[Outbox] = None, reminder: bool = False) -> dict:
    envelope = await _envelope_in_workspace(db, ctx, envelope_id, lock=True)
    _require_manager(ctx, envelope)
    signer = await db.get(SignatureSigner, signer_id)
    if not signer or signer.envelope_id != envelope.id:
        raise HTTPException(404, "Signer not found")
    if signer.status != "pending":
        raise HTTPException(409, f"{signer.name} has already {signer.status}")
    if reminder:
        if outbox is None or not is_email_enabled():
            raise HTTPException(409, "Email isn't set up, so reminders can't be sent. Use New link and share it yourself.")
        last = (await latest_status(db, "signature_signer", [signer.id])).get(signer.id)
        if last and last["status"] == "sent" and last["at"] and _aware(last["at"]) > utcnow() - REMINDER_GAP:
            raise HTTPException(429, f"{signer.name} was emailed less than an hour ago. Try again later.")
    token = secrets.token_urlsafe(32)
    signer.token_hash = hash_token(token)
    actor = await db.get(User, ctx.user_id)
    ip, ua = client_info(request)
    _event(db, envelope.id, "link_reissued", actor.name if actor else None,
           f"{'Reminder with a new' if reminder else 'New'} signing link for {signer.name}; the old one no longer works",
           ip, ua)
    await db.flush()
    # The email names whoever originally sent the document (an admin may be reissuing it).
    sender = await db.get(User, envelope.requested_by) if envelope.requested_by else None
    _queue_link_email(outbox, envelope, signer, token, sender or actor, reissued=True, reminder=reminder)
    out = (await _serialize(db, [envelope], ctx))[0]
    out["links"] = {signer.id: token}
    out["emailed"] = bool(outbox)
    return out


async def cancel(db: AsyncSession, ctx: WorkspaceContext, envelope_id: str, request: Optional[Request]) -> dict:
    envelope = await _envelope_in_workspace(db, ctx, envelope_id, lock=True)
    _require_manager(ctx, envelope)
    envelope.status, envelope.closed_at = "cancelled", utcnow()
    actor = await db.get(User, ctx.user_id)
    ip, ua = client_info(request)
    _event(db, envelope.id, "cancelled", actor.name if actor else None, None, ip, ua)
    await db.flush()
    await _sync_contract_status(db, envelope.contract_id)
    return (await _serialize(db, [envelope], ctx))[0]


async def delete_for_contract(db: AsyncSession, contract_id: str) -> None:
    """Called when a contract is deleted (SQLite doesn't enforce cascades)."""
    ids = select(SignatureEnvelope.id).where(SignatureEnvelope.contract_id == contract_id)
    await db.execute(delete(SignatureEvent).where(SignatureEvent.envelope_id.in_(ids)))
    await db.execute(delete(SignatureSigner).where(SignatureSigner.envelope_id.in_(ids)))
    await db.execute(delete(SignatureEnvelope).where(SignatureEnvelope.contract_id == contract_id))


# ─────────────────────────────────────────────────────────────────────────────
# Public signing (no login; the link token is the credential)
# ─────────────────────────────────────────────────────────────────────────────

async def _signer_for_token(db: AsyncSession, token: str, lock: bool = False
                            ) -> tuple[SignatureSigner, SignatureEnvelope]:
    if not token or len(token) > 200:
        raise HTTPException(404, LINK_NOT_FOUND)
    signer = (
        await db.execute(select(SignatureSigner).where(SignatureSigner.token_hash == hash_token(token)))
    ).scalar_one_or_none()
    if not signer:
        raise HTTPException(404, LINK_NOT_FOUND)
    q = select(SignatureEnvelope).where(SignatureEnvelope.id == signer.envelope_id)
    if lock:
        q = q.with_for_update()
    envelope = (await db.execute(q)).scalar_one()
    if lock:
        await db.refresh(signer)
    return signer, envelope


async def _public_view(db: AsyncSession, signer: SignatureSigner, envelope: SignatureEnvelope) -> dict:
    others = (
        await db.execute(
            select(SignatureSigner).where(SignatureSigner.envelope_id == envelope.id).order_by(SignatureSigner.position)
        )
    ).scalars().all()
    requester = await db.get(User, envelope.requested_by) if envelope.requested_by else None
    return {
        "envelope_status": envelope.status,
        "document_filename": envelope.document_filename,
        "document_sha256": envelope.document_sha256,
        "message": envelope.message,
        "requested_by_name": requester.name if requester else None,
        "sent_at": envelope.created_at,
        "consent_text": CONSENT_TEXT,
        "signer": {
            "name": signer.name, "email": signer.email, "status": signer.status,
            "typed_signature": signer.typed_signature, "acted_at": signer.acted_at,
            "decline_reason": signer.decline_reason,
        },
        # Other signers' names and progress only — not their emails.
        "signers": [{"name": s.name, "status": s.status, "is_you": s.id == signer.id} for s in others],
    }


async def public_summary(db: AsyncSession, token: str, request: Optional[Request]) -> dict:
    signer, envelope = await _signer_for_token(db, token)
    if signer.viewed_at is None and envelope.status == "pending":
        signer.viewed_at = utcnow()
        ip, ua = client_info(request)
        _event(db, envelope.id, "viewed", signer.name, "Opened the signing link", ip, ua)
        await db.flush()
    return await _public_view(db, signer, envelope)


async def public_document(db: AsyncSession, token: str) -> tuple[bytes, str, str]:
    signer, envelope = await _signer_for_token(db, token)
    if envelope.status == "cancelled":
        raise HTTPException(410, "This signature request was cancelled")
    contract = await db.get(Contract, envelope.contract_id)
    data = await load_file_bytes(db, contract.id, contract.file_path) if contract else None
    if data is None:
        raise HTTPException(404, "The document is no longer available")
    ext = "." + envelope.document_filename.rsplit(".", 1)[-1].lower() if "." in envelope.document_filename else ""
    return data, CONTENT_TYPES.get(ext, "application/octet-stream"), envelope.document_filename


async def public_signed_copy(db: AsyncSession, token: str) -> tuple[bytes, str]:
    """Each signer can download the signed copy once everyone has signed."""
    signer, envelope = await _signer_for_token(db, token)
    return await _signed_copy(db, envelope, None)


def _require_open(signer: SignatureSigner, envelope: SignatureEnvelope) -> None:
    if envelope.status != "pending":
        raise HTTPException(409, f"This signature request is {envelope.status}")
    if signer.status != "pending":
        raise HTTPException(409, f"You have already {signer.status}")


async def _queue_completed_emails(db: AsyncSession, outbox: Optional[Outbox], envelope: SignatureEnvelope) -> None:
    if outbox is None:
        return
    requester = await db.get(User, envelope.requested_by) if envelope.requested_by else None
    signers = (
        await db.execute(select(SignatureSigner).where(SignatureSigner.envelope_id == envelope.id))
    ).scalars().all()
    recipients = [(s.name, s.email, False, s.id) for s in signers]
    if requester and requester.email.lower() not in {s.email.lower() for s in signers}:
        recipients.insert(0, (requester.name, requester.email, True, None))
    for name, email, is_requester, signer_id in recipients:
        is_req = is_requester or bool(requester and requester.email.lower() == email.lower())
        subject, html, text = templates.signature_completed(
            name, envelope.document_filename,
            app_link(f"/signatures/{envelope.id}") if is_req else None, is_req, attached=True,
        )
        outbox.add(Email(
            kind="signature_completed", to_email=email, to_name=name, subject=subject, html=html, text=text,
            workspace_id=envelope.workspace_id, ref_type="signature_envelope", ref_id=envelope.id,
            signature_envelope_id=envelope.id, attach_signed_pdf=envelope.id,
        ))


async def sign(db: AsyncSession, token: str, typed_name: str, consent: bool, request: Optional[Request],
               outbox: Optional[Outbox] = None) -> dict:
    signer, envelope = await _signer_for_token(db, token, lock=True)
    _require_open(signer, envelope)
    if not consent:
        raise HTTPException(422, "Tick the box to agree to sign electronically")
    if normalize_name(typed_name) != normalize_name(signer.name):
        raise HTTPException(422, f"Type your full name exactly as shown: {signer.name}")

    contract = await db.get(Contract, envelope.contract_id)
    data = await load_file_bytes(db, contract.id, contract.file_path) if contract else None
    if data is None or hashlib.sha256(data).hexdigest() != envelope.document_sha256:
        raise HTTPException(409, "The document changed after it was sent, so it can't be signed")

    ip, ua = client_info(request)
    now = utcnow()
    signer.status, signer.acted_at = "signed", now
    signer.typed_signature = re.sub(r"\s+", " ", typed_name.strip())
    signer.consent_text = CONSENT_TEXT
    signer.ip_address, signer.user_agent = ip, ua
    if signer.viewed_at is None:
        signer.viewed_at = now
    _event(db, envelope.id, "signed", signer.name, f"Signed as “{signer.typed_signature}”", ip, ua)
    await db.flush()

    statuses = (
        await db.execute(select(SignatureSigner.status).where(SignatureSigner.envelope_id == envelope.id))
    ).scalars().all()
    if all(s == "signed" for s in statuses):
        envelope.status, envelope.closed_at = "completed", now
        _event(db, envelope.id, "completed", None, "Everyone has signed", None, None)
        await db.flush()
        await _sync_contract_status(db, envelope.contract_id)
        await _queue_completed_emails(db, outbox, envelope)
    return await _public_view(db, signer, envelope)


async def decline(db: AsyncSession, token: str, reason: str, request: Optional[Request],
                  outbox: Optional[Outbox] = None) -> dict:
    signer, envelope = await _signer_for_token(db, token, lock=True)
    _require_open(signer, envelope)
    reason = (reason or "").strip()
    if not reason:
        raise HTTPException(422, "Say why you're declining so the sender knows what to change")
    ip, ua = client_info(request)
    now = utcnow()
    signer.status, signer.acted_at, signer.decline_reason = "declined", now, reason
    signer.ip_address, signer.user_agent = ip, ua
    envelope.status, envelope.closed_at = "declined", now
    _event(db, envelope.id, "declined", signer.name, reason, ip, ua)
    await db.flush()
    await _sync_contract_status(db, envelope.contract_id)
    requester = await db.get(User, envelope.requested_by) if envelope.requested_by else None
    if outbox is not None and requester:
        subject, html, text = templates.signature_declined(
            requester.name, signer.name, envelope.document_filename, reason,
            app_link(f"/contracts/{envelope.contract_id}"),
        )
        outbox.add(Email(
            kind="signature_declined", to_email=requester.email, to_name=requester.name, subject=subject,
            html=html, text=text, workspace_id=envelope.workspace_id, reply_to=signer.email,
            ref_type="signature_envelope", ref_id=envelope.id, signature_envelope_id=envelope.id,
        ))
    return await _public_view(db, signer, envelope)
