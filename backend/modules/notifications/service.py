"""
Queue emails during a request, send them after the database has committed.

Routes create an Outbox, pass it to the service, then hand it to
BackgroundTasks. FastAPI runs background tasks after the response — and
after the get_db dependency has committed — so the rows the emails refer to
already exist, and a slow or failing email provider never breaks or slows
the action itself.
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from sqlalchemy import func, select

from core.config import settings
from modules.notifications import mailer
from modules.notifications.models import EmailLog

logger = logging.getLogger("notifications")


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def app_link(path: str) -> str:
    return f"{settings.app_url}{path}"


@dataclass
class Email:
    kind: str
    to_email: str
    to_name: Optional[str]
    subject: str
    html: str
    text: str
    workspace_id: Optional[str] = None
    reply_to: Optional[str] = None
    ref_type: Optional[str] = None
    ref_id: Optional[str] = None
    # When set, a successful send is also written to this envelope's audit trail.
    signature_envelope_id: Optional[str] = None
    # When set, the signed PDF of this envelope is attached (built once per batch).
    attach_signed_pdf: Optional[str] = None


@dataclass
class Outbox:
    emails: List[Email] = field(default_factory=list)

    def add(self, email: Email) -> None:
        if mailer.is_enabled() and email.to_email:
            self.emails.append(email)

    def __len__(self) -> int:
        return len(self.emails)


async def _sent_since(db, since: datetime, workspace_id: Optional[str] = None) -> int:
    q = select(func.count()).select_from(EmailLog).where(EmailLog.status == "sent", EmailLog.created_at >= since)
    if workspace_id:
        q = q.where(EmailLog.workspace_id == workspace_id)
    return (await db.execute(q)).scalar_one()


async def deliver(outbox: Outbox) -> None:
    """Background task: send everything in the outbox and record the outcome."""
    if not outbox.emails:
        return
    from db.session import AsyncSessionLocal
    from modules.signatures.models import SignatureEvent

    pdf_cache: dict[str, Optional[tuple[str, bytes]]] = {}

    async def signed_pdf(db, envelope_id: str):
        if envelope_id not in pdf_cache:
            try:
                from modules.signatures.service import signed_copy_for_email
                pdf_cache[envelope_id] = await signed_copy_for_email(db, envelope_id)
            except Exception:
                logger.exception("email.signed_pdf_failed envelope=%s", envelope_id)
                pdf_cache[envelope_id] = None
        return pdf_cache[envelope_id]

    async with AsyncSessionLocal() as db:
        for email in outbox.emails:
            since = utcnow() - timedelta(days=1)
            status, error, result = "sent", None, None
            try:
                if await _sent_since(db, since) >= settings.EMAIL_DAILY_LIMIT:
                    status, error = "skipped", "Daily email limit reached for this server"
                elif email.workspace_id and await _sent_since(db, since, email.workspace_id) >= settings.EMAIL_DAILY_LIMIT_PER_WORKSPACE:
                    status, error = "skipped", "Daily email limit reached for this workspace"
                else:
                    attachments = []
                    pdf = await signed_pdf(db, email.attach_signed_pdf) if email.attach_signed_pdf else None
                    if email.attach_signed_pdf and not pdf:
                        # The email says the copy is attached; don't send it without one.
                        status, error = "failed", "Couldn't build the signed PDF to attach"
                    else:
                        if pdf:
                            data, name = pdf
                            attachments.append((name, data))
                        result = await mailer.send_email(
                            email.to_email, email.to_name, email.subject, email.html, email.text, email.reply_to,
                            attachments=attachments,
                        )
                        if not result.ok:
                            status, error = "failed", result.error
            except Exception as e:  # never let one email stop the rest
                status, error = "failed", f"{type(e).__name__}: {e}"[:300]

            if status != "sent":
                logger.warning("email.%s kind=%s to=%s error=%s", status, email.kind, email.to_email, error)
            db.add(EmailLog(
                workspace_id=email.workspace_id, kind=email.kind, to_email=email.to_email,
                subject=email.subject[:300], status=status, error=error,
                provider=mailer.provider_name(), provider_message_id=(result.message_id if result else None),
                ref_type=email.ref_type, ref_id=email.ref_id, created_at=utcnow(),
            ))
            if status == "sent" and email.signature_envelope_id:
                db.add(SignatureEvent(
                    envelope_id=email.signature_envelope_id, type="emailed", actor=email.to_name,
                    detail=f"Email sent to {email.to_email}: {email.subject}", created_at=utcnow(),
                ))
            try:
                await db.commit()
            except Exception:
                # e.g. the envelope was deleted in the meantime; keep going
                await db.rollback()
                logger.exception("email.log_failed kind=%s", email.kind)


async def latest_status(db, ref_type: str, ref_ids: list[str]) -> dict[str, dict]:
    """Most recent email outcome per referenced row, e.g. per signer."""
    if not ref_ids:
        return {}
    rows = (
        await db.execute(
            select(EmailLog)
            .where(EmailLog.ref_type == ref_type, EmailLog.ref_id.in_(ref_ids))
            .order_by(EmailLog.created_at)
        )
    ).scalars().all()
    out: dict[str, dict] = {}
    for r in rows:  # later rows overwrite earlier ones
        out[r.ref_id] = {"status": r.status, "at": r.created_at, "error": r.error}
    return out

