"""
Daily limits on AI contract reviews.

Every review is one paid call to the AI provider (Ollama Cloud bills per
token), so two limits apply over a rolling 24 hours:
  - AI_REVIEWS_PER_USER_DAILY: reviews one account can start
  - AI_REVIEWS_DAILY_TOTAL:    reviews the whole server will start
Set either to 0 to switch that limit off. Both are read from the environment
(Render) so they can be changed without a code change.
"""
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.logger import get_logger
from modules.usage.models import AIRun

logger = get_logger(__name__)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


async def _count_since(db: AsyncSession, since: datetime, user_id: str | None = None) -> int:
    q = select(func.count()).select_from(AIRun).where(AIRun.created_at >= since)
    if user_id:
        q = q.where(AIRun.user_id == user_id)
    return (await db.execute(q)).scalar_one()


async def reviews_left_today(db: AsyncSession, user_id: str) -> int | None:
    """How many more reviews this user can start now; None means no per-user limit."""
    limit = settings.AI_REVIEWS_PER_USER_DAILY
    if limit <= 0:
        return None
    used = await _count_since(db, utcnow() - timedelta(days=1), user_id)
    return max(0, limit - used)


async def claim_ai_review(db: AsyncSession, user_id: str, contract_id: str | None = None) -> None:
    """
    Check both limits and record the review. Raises 429 when a limit is hit.
    Call BEFORE storing anything or starting the background task. The caller
    commits (the row is added to the caller's session).
    """
    since = utcnow() - timedelta(days=1)

    total_limit = settings.AI_REVIEWS_DAILY_TOTAL
    if total_limit > 0 and await _count_since(db, since) >= total_limit:
        logger.warning(f"usage.daily_total_reached limit={total_limit}")
        raise HTTPException(
            429,
            "ContractIQ has reached its daily review limit. Please try again in a few hours.",
        )

    user_limit = settings.AI_REVIEWS_PER_USER_DAILY
    if user_limit > 0 and await _count_since(db, since, user_id) >= user_limit:
        raise HTTPException(
            429,
            f"You've used your {user_limit} contract reviews for today. "
            "You can review more 24 hours after your earliest one.",
        )

    db.add(AIRun(user_id=user_id, contract_id=contract_id, created_at=utcnow()))
