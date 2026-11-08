from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_db
from core.security import create_access_token, hash_password, require_auth, verify_password
from modules.notifications import templates
from modules.notifications.mailer import is_enabled as email_enabled
from modules.notifications.service import Outbox, deliver
from modules.users import account
from modules.users.repository import UserRepository
from modules.users.schemas import (
    ForgotPassword, ResetPassword, TokenOut, UserLogin, UserOut, UserRegister, UserUpdate, VerifyEmail,
)
from modules.workspaces.service import create_personal_workspace

# Remove the prefix from here - let routes.py handle it
router = APIRouter(tags=["auth"])


def _token_out(user) -> TokenOut:
    token = create_access_token(user.id, {"email": user.email, "name": user.name})
    return TokenOut(access_token=token, user=UserOut.model_validate(user))


async def _send(db: AsyncSession, background: BackgroundTasks, outbox: Outbox) -> None:
    """Commit first so the rows the emails refer to exist, then send after the response."""
    if outbox:
        await db.commit()
        background.add_task(deliver, outbox)


@router.post("/register", response_model=TokenOut, status_code=201)
async def register(body: UserRegister, background: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    repo = UserRepository(db)
    if await repo.exists(body.email):
        raise HTTPException(400, "Email already registered")
    user = await repo.create(body.email, body.name, body.password)
    await create_personal_workspace(db, user)
    outbox = Outbox()
    await account.queue_verification(db, user, outbox)
    out = _token_out(user)
    await _send(db, background, outbox)
    return out


@router.post("/login", response_model=TokenOut)
async def login(body: UserLogin, db: AsyncSession = Depends(get_db)):
    repo = UserRepository(db)
    user = await repo.get_by_email(body.email)
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(401, "Invalid email or password")
    if not user.is_active:
        raise HTTPException(403, "Account is disabled")
    return _token_out(user)


@router.get("/me", response_model=UserOut)
async def me(user_id: str = Depends(require_auth), db: AsyncSession = Depends(get_db)):
    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if not user:
        raise HTTPException(404, "User not found")
    return UserOut.model_validate(user)


@router.patch("/me", response_model=TokenOut)
async def update_me(
    body: UserUpdate, background: BackgroundTasks,
    user_id: str = Depends(require_auth), db: AsyncSession = Depends(get_db),
):
    """
    Change your name, email or password. Changing the email or password needs
    the current password. Returns a fresh token, since the token carries the
    email and name. A new email has to be confirmed again, and the old
    address is told about the change.
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

    outbox = Outbox()
    if changing_email:
        old_email = user.email
        user.email = new_email
        user.email_verified_at = None
        await db.flush()
        subject, html, text = templates.email_changed(user.name, old_email, new_email)
        account.queue_notice(outbox, "email_changed", old_email, user.name, subject, html, text, user.id)
        await account.queue_verification(db, user, outbox)
    if body.new_password:
        user.hashed_password = hash_password(body.new_password)
        subject, html, text = templates.password_changed(user.name)
        account.queue_notice(outbox, "password_changed", user.email, user.name, subject, html, text, user.id)
    await db.flush()
    out = _token_out(user)
    await _send(db, background, outbox)
    return out


# ── Email verification ─────────────────────────────────────────────────────

@router.post("/verify-email", response_model=UserOut)
async def verify_email(body: VerifyEmail, db: AsyncSession = Depends(get_db)):
    """Public: the link in the email is the proof, so no sign-in is needed."""
    row, user = await account.consume(db, body.token, account.VERIFY)
    if row.email != user.email:
        raise HTTPException(400, "This link was for an email address you've since changed. Ask for a new one.")
    if user.email_verified_at is None:
        user.email_verified_at = account.utcnow()
    await db.flush()
    return UserOut.model_validate(user)


@router.post("/resend-verification")
async def resend_verification(
    background: BackgroundTasks, user_id: str = Depends(require_auth), db: AsyncSession = Depends(get_db),
):
    user = await UserRepository(db).get_by_id(user_id)
    if not user:
        raise HTTPException(404, "User not found")
    if user.email_verified_at is not None:
        raise HTTPException(409, "Your email is already confirmed.")
    if not email_enabled():
        raise HTTPException(503, "Email isn't set up on this server, so there's nothing to confirm.")
    outbox = Outbox()
    if not await account.queue_verification(db, user, outbox):
        raise HTTPException(429, "We just sent one. Check your inbox and spam folder, or try again in a minute.")
    await _send(db, background, outbox)
    return {"sent_to": user.email}


# ── Password reset ─────────────────────────────────────────────────────────

@router.post("/forgot-password", status_code=202)
async def forgot_password(body: ForgotPassword, background: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """
    Always answers the same way, whether or not the address has an account,
    so this can't be used to find out who uses ContractIQ.
    """
    if not email_enabled():
        raise HTTPException(503, "Password reset by email isn't set up on this server. Ask the workspace owner for help.")
    user = await UserRepository(db).get_by_email(body.email)
    outbox = Outbox()
    if user:
        await account.queue_reset(db, user, outbox)
    await _send(db, background, outbox)
    return {"message": "If an account uses that email, a reset link is on its way. It works for 30 minutes."}


@router.get("/reset-password/{token}")
async def check_reset_link(token: str, db: AsyncSession = Depends(get_db)):
    """Lets the page say up front whether the link still works."""
    user = await account.check_link(db, token, account.RESET)
    if not user or not user.is_active:
        raise HTTPException(400, account.INVALID_LINK)
    return {"email": user.email}


@router.post("/reset-password", response_model=TokenOut)
async def reset_password(body: ResetPassword, background: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """Sets the new password and signs the person in."""
    row, user = await account.consume(db, body.token, account.RESET)
    user.hashed_password = hash_password(body.new_password)
    # Getting the email proves they own the address it went to.
    if user.email_verified_at is None and row.email == user.email:
        user.email_verified_at = account.utcnow()
    await db.flush()
    outbox = Outbox()
    subject, html, text = templates.password_changed(user.name)
    account.queue_notice(outbox, "password_changed", user.email, user.name, subject, html, text, user.id)
    out = _token_out(user)
    await _send(db, background, outbox)
    return out
