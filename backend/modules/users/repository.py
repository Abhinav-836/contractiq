# modules/users/repository.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from modules.users.models import User
from core.security import hash_password
from db.base import gen_uuid
from typing import Optional


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, email: str, name: str, password: str, role: str = "user") -> User:
        """Create a new user with hashed password"""
        user = User(
            id=gen_uuid(),
            email=email.lower().strip(),  # Normalize email
            name=name.strip(),
            hashed_password=hash_password(password),
            role=role,
            is_active=True
        )
        self.db.add(user)
        await self.db.flush()
        return user

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email (case-insensitive)"""
        result = await self.db.execute(
            select(User).where(User.email == email.lower().strip())
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def exists(self, email: str) -> bool:
        """Check if user exists"""
        result = await self.db.execute(
            select(User.id).where(User.email == email.lower().strip())
        )
        return result.scalar_one_or_none() is not None

    async def update_last_login(self, user_id: str):
        """Update user's last login timestamp"""
        from datetime import datetime
        await self.db.execute(
            User.__table__.update()
            .where(User.id == user_id)
            .values(updated_at=datetime.utcnow())
        )
        await self.db.flush()