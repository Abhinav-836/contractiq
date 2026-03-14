from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from db.session import get_session
from core.security import get_current_user_id


# Re-export DB session dependency
async def get_db(session: AsyncSession = Depends(get_session)) -> AsyncSession:
    return session


# Optional auth (returns None if no token)
OptionalUser = Depends(get_current_user_id)
