"""
Password reset and email verification.

Both work by emailing a one-time link. Only a hash of each token is stored,
links expire, using one marks it used, and issuing a new one cancels the
older unused ones of the same kind.
"""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from modules.notifications import templates
from modules.notifications.mailer import is_enabled as email_enabled
from modules.notifications.service import Email, Outbox, app_link
from modules.users.models import AuthToken, User

RESET = "reset_password"
VERIFY = "verify_email"
TTL = {RESET: timedelta(minutes=30), VERIFY: timedelta(hours=48)}
RESEND_GAP = timedelta(seconds=60)   # at most one link a minute per person and kind
DAILY_MAX = 6                        # and a handful a day, so the endpoint can't be used to spam an inbox

INVALID_LINK = "This link is invalid, has expired or was already used. Ask for a new one."


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


async def _can_issue(db: AsyncSession, user: User, purpose: str) -> bool:
    """The one-a-minute gap is per address, so a just-changed email still gets its link."""
    now = utcnow()
    rows = (
        await db.execute(
            select(AuthToken.created_at, AuthToken.email).where(
                AuthToken.user_id == user.id, AuthToken.purpose == purpose,
                AuthToken.created_at >= now - timedelta(days=1),
            )
        )
    ).all()
    if len(rows) >= DAILY_MAX:
        return False
    return not any(email == user.email and _aware(t) > now - RESEND_GAP for t, email in rows)


async def _issue(db: AsyncSession, user: User, purpose: str) -> str:
    now = utcnow()
    await db.execute(
        update(AuthToken)
        .where(AuthToken.user_id == user.id, AuthToken.purpose == purpose, AuthToken.used_at.is_(None))
        .values(used_at=now)
    )
    token = secrets.token_urlsafe(32)
    db.add(AuthToken(user_id=user.id, purpose=purpose, token_hash=_hash(token), email=user.email,
                     expires_at=now + TTL[purpose], created_at=now))
    await db.flush()
    return token


async def queue_verification(db: AsyncSession, user: User, outbox: Outbox) -> bool:
    """Email a confirm-your-address link. False when email is off or it's too soon."""
    if not email_enabled() or not await _can_issue(db, user, VERIFY):
        return False
    token = await _issue(db, user, VERIFY)
    subject, html, text = templates.verify_email(user.name, app_link(f"/verify-email/{token}"))
    outbox.add(Email(kind="verify_email", to_email=user.email, to_name=user.name, subject=subject,
                     html=html, text=text, ref_type="user", ref_id=user.id))
    return True


async def queue_reset(db: AsyncSession, user: User, outbox: Outbox) -> bool:
    if not email_enabled() or not user.is_active or not await _can_issue(db, user, RESET):
        return False
    token = await _issue(db, user, RESET)
    subject, html, text = templates.password_reset(user.name, app_link(f"/reset-password/{token}"))
    outbox.add(Email(kind="password_reset", to_email=user.email, to_name=user.name, subject=subject,
                     html=html, text=text, ref_type="user", ref_id=user.id))
    return True


def queue_notice(outbox: Outbox, kind: str, to_email: str, name: str, subject: str, html: str, text: str,
                 user_id: str) -> None:
    outbox.add(Email(kind=kind, to_email=to_email, to_name=name, subject=subject, html=html, text=text,
                     ref_type="user", ref_id=user_id))


async def consume(db: AsyncSession, token: str, purpose: str) -> tuple[AuthToken, User]:
    """Check a link and mark it used. Raises 400 for anything not usable."""
    if not token or len(token) > 200:
        raise HTTPException(400, INVALID_LINK)
    row = (
        await db.execute(select(AuthToken).where(AuthToken.token_hash == _hash(token), AuthToken.purpose == purpose))
    ).scalar_one_or_none()
    if not row or row.used_at is not None or _aware(row.expires_at) <= utcnow():
        raise HTTPException(400, INVALID_LINK)
    user = await db.get(User, row.user_id)
    if not user or not user.is_active:
        raise HTTPException(400, INVALID_LINK)
    row.used_at = utcnow()
    return row, user


async def check_link(db: AsyncSession, token: str, purpose: str) -> Optional[User]:
    """Look a link up without using it (for showing the reset form)."""
    if not token or len(token) > 200:
        return None
    row = (
        await db.execute(select(AuthToken).where(AuthToken.token_hash == _hash(token), AuthToken.purpose == purpose))
    ).scalar_one_or_none()
    if not row or row.used_at is not None or _aware(row.expires_at) <= utcnow():
        return None
    return await db.get(User, row.user_id)


async def email_verified(db: AsyncSession, user_id: str) -> bool:
    if not email_enabled():
        return True
    at = (await db.execute(select(User.email_verified_at).where(User.id == user_id))).scalar_one_or_none()
    return at is not None


async def require_verified_email(db: AsyncSession, user_id: str) -> None:
    """
    Emails sent on someone's behalf (signing requests, invites) use their
    address as the reply-to, so the address has to be really theirs.
    Only enforced when the server can send email, since otherwise there is
    no way to verify.
    """
    if not await email_verified(db, user_id):
        raise HTTPException(
            403, "Confirm your email address first — we sent you a link. You can resend it from the banner at the top."
        )


async def pending_count(db: AsyncSession, user_id: str, purpose: str) -> int:  # used in tests
    return (
        await db.execute(
            select(func.count()).select_from(AuthToken).where(
                AuthToken.user_id == user_id, AuthToken.purpose == purpose, AuthToken.used_at.is_(None)
            )
        )
    ).scalar_one()
