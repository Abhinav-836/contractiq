from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from core.dependencies import get_db
from core.security import verify_password, create_access_token, require_auth
from modules.users.repository import UserRepository
from modules.users.schemas import UserRegister, UserLogin, UserOut, TokenOut

# Remove the prefix from here - let routes.py handle it
router = APIRouter(tags=["auth"])


@router.post("/register", response_model=TokenOut, status_code=201)
async def register(body: UserRegister, db: AsyncSession = Depends(get_db)):
    repo = UserRepository(db)
    if await repo.exists(body.email):
        raise HTTPException(400, "Email already registered")
    user = await repo.create(body.email, body.name, body.password)
    token = create_access_token(user.id, {"email": user.email, "name": user.name})
    return TokenOut(access_token=token, user=UserOut.model_validate(user))


@router.post("/login", response_model=TokenOut)
async def login(body: UserLogin, db: AsyncSession = Depends(get_db)):
    repo = UserRepository(db)
    user = await repo.get_by_email(body.email)
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(401, "Invalid email or password")
    if not user.is_active:
        raise HTTPException(403, "Account is disabled")
    token = create_access_token(user.id, {"email": user.email, "name": user.name})
    return TokenOut(access_token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
async def me(user_id: str = Depends(require_auth), db: AsyncSession = Depends(get_db)):
    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if not user:
        raise HTTPException(404, "User not found")
    return UserOut.model_validate(user)