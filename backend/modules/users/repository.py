from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import hash_password
from db.base import gen_uuid
from modules.users.models import User


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, email: str, name: str, password: str, role: str = "user") -> User:
        user = User(
            id=gen_uuid(),
            email=email.lower().strip(),
            name=name.strip(),
            hashed_password=hash_password(password),
            role=role,
            is_active=True,
        )
        self.db.add(user)
        await self.db.flush()
        return user

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(
            select(User).where(User.email == email.lower().strip())
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def exists(self, email: str) -> bool:
        result = await self.db.execute(
            select(User.id).where(User.email == email.lower().strip())
        )
        return result.scalar_one_or_none() is not None

    async def update_last_login(self, user_id: str):
        await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(updated_at=datetime.now(timezone.utc))
        )
        await self.db.flush()