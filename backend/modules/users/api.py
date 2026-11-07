from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from core.dependencies import get_db
from core.security import verify_password, hash_password, create_access_token, require_auth
from modules.users.repository import UserRepository
from modules.users.schemas import UserRegister, UserLogin, UserOut, UserUpdate, TokenOut
from modules.workspaces.service import create_personal_workspace

# Remove the prefix from here - let routes.py handle it
router = APIRouter(tags=["auth"])


@router.post("/register", response_model=TokenOut, status_code=201)
async def register(body: UserRegister, db: AsyncSession = Depends(get_db)):
    repo = UserRepository(db)
    if await repo.exists(body.email):
        raise HTTPException(400, "Email already registered")
    user = await repo.create(body.email, body.name, body.password)
    await create_personal_workspace(db, user)
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


@router.patch("/me", response_model=TokenOut)
async def update_me(body: UserUpdate, user_id: str = Depends(require_auth), db: AsyncSession = Depends(get_db)):
    """
    Change your name, email or password. Changing the email or password needs
    the current password. Returns a fresh token, since the token carries the
    email and name.
    """
    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if not user:
        raise HTTPException(404, "User not found")

    new_email = body.email.lower().strip() if body.email else None
    changing_email = bool(new_email and new_email != user.email)
    if (changing_email or body.new_password) and not (
        body.current_password and verify_password(body.current_password, user.hashed_password)
    ):
        raise HTTPException(403, "Your current password is wrong")
    if changing_email and await repo.exists(new_email):
        raise HTTPException(400, "That email is already used by another account")

    if body.name is not None:
        name = " ".join(body.name.split())
        if not name:
            raise HTTPException(422, "Name can't be empty")
        user.name = name
    if changing_email:
        user.email = new_email
    if body.new_password:
        user.hashed_password = hash_password(body.new_password)
    await db.flush()
    token = create_access_token(user.id, {"email": user.email, "name": user.name})
    return TokenOut(access_token=token, user=UserOut.model_validate(user))
