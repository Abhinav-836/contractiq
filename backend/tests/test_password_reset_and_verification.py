"""Forgot password, email verification, and what an unverified account can't do."""
import re
from datetime import timedelta

import pytest
from sqlalchemy import update

from modules.users.models import AuthToken, User as UserRow
from modules.users.account import utcnow
from test_notifications import SIGNERS, email_of, outbox, send, to  # noqa: F401  (fixture)
from test_signatures import setup_team as signing_team
from test_workspaces import API

pytestmark = pytest.mark.asyncio(loop_scope="session")

RESET_LINK = re.compile(r"https://app\.example\.com/reset-password/([A-Za-z0-9_\-]+)")
VERIFY_LINK = re.compile(r"https://app\.example\.com/verify-email/([A-Za-z0-9_\-]+)")


def link(outbox, address, pattern):
    found = [pattern.search(m["text"]) for m in to(outbox, address)]
    found = [f.group(1) for f in found if f]
    assert found, f"no matching email to {address}"
    return found[-1]


async def age_tokens(db, user_id, by=timedelta(minutes=5)):
    """Pretend the user's links were issued a while ago, to get past the one-a-minute limit."""
    await db.execute(update(AuthToken).where(AuthToken.user_id == user_id)
                     .values(created_at=utcnow() - by))
    await db.commit()


# ── Forgot password ────────────────────────────────────────────────────────

async def test_password_reset_flow(make_user, client, outbox, db):
    u = await make_user("Rita")
    email = await email_of(u)

    r = await client.post(f"{API}/auth/forgot-password", json={"email": email.upper()})
    assert r.status_code == 202
    mail = to(outbox, email)[-1]
    assert mail["subject"] == "Reset your ContractIQ password"
    token = link(outbox, email, RESET_LINK)

    # The page can check the link first
    r = await client.get(f"{API}/auth/reset-password/{token}")
    assert r.status_code == 200 and r.json()["email"] == email

    # Too-short password is rejected without using up the link
    assert (await client.post(f"{API}/auth/reset-password", json={"token": token, "new_password": "short"})).status_code == 422
    r = await client.post(f"{API}/auth/reset-password", json={"token": token, "new_password": "fresh-password-1"})
    assert r.status_code == 200, r.text
    assert r.json()["access_token"] and r.json()["user"]["email"] == email

    # Old password no longer works, new one does, and they're told about the change
    assert (await client.post(f"{API}/auth/login", json={"email": email, "password": "password123"})).status_code == 401
    assert (await client.post(f"{API}/auth/login", json={"email": email, "password": "fresh-password-1"})).status_code == 200
    assert to(outbox, email)[-1]["subject"] == "Your ContractIQ password was changed"

    # The link only works once
    r = await client.post(f"{API}/auth/reset-password", json={"token": token, "new_password": "another-pass-2"})
    assert r.status_code == 400 and "already used" in r.json()["detail"]
    assert (await client.get(f"{API}/auth/reset-password/{token}")).status_code == 400


async def test_forgot_password_does_not_reveal_accounts(client, outbox):
    r = await client.post(f"{API}/auth/forgot-password", json={"email": "nobody-here@example.com"})
    assert r.status_code == 202 and "If an account uses that email" in r.json()["message"]
    assert outbox == []


async def test_reset_links_expire_and_newer_link_cancels_older(make_user, client, outbox, db):
    u = await make_user("Sam")
    email = await email_of(u)
    await client.post(f"{API}/auth/forgot-password", json={"email": email})
    first = link(outbox, email, RESET_LINK)

    # Asking again within a minute sends nothing new (but answers the same)
    r = await client.post(f"{API}/auth/forgot-password", json={"email": email})
    assert r.status_code == 202 and len(to(outbox, email)) == 1

    await age_tokens(db, u.id)
    await client.post(f"{API}/auth/forgot-password", json={"email": email})
    second = link(outbox, email, RESET_LINK)
    assert second != first
    assert (await client.post(f"{API}/auth/reset-password", json={"token": first, "new_password": "x-password-9"})).status_code == 400

    # Expired
    await db.execute(update(AuthToken).where(AuthToken.user_id == u.id).values(expires_at=utcnow() - timedelta(seconds=1)))
    await db.commit()
    assert (await client.post(f"{API}/auth/reset-password", json={"token": second, "new_password": "x-password-9"})).status_code == 400
    assert (await client.post(f"{API}/auth/reset-password", json={"token": "made-up-token-123", "new_password": "x-password-9"})).status_code == 400


async def test_forgot_password_daily_limit(make_user, client, outbox, db):
    u = await make_user("Lim")
    email = await email_of(u)
    for _ in range(8):
        await client.post(f"{API}/auth/forgot-password", json={"email": email})
        await age_tokens(db, u.id)
    assert len(to(outbox, email)) == 6


async def test_forgot_password_when_email_is_off(make_user, client, monkeypatch):
    from core.config import settings
    monkeypatch.setattr(settings, "EMAIL_PROVIDER", "none")
    r = await client.post(f"{API}/auth/forgot-password", json={"email": "a@example.com"})
    assert r.status_code == 503


# ── Email verification ─────────────────────────────────────────────────────

async def test_signup_sends_confirmation_and_link_verifies(make_user, client, outbox):
    u = await make_user("Nina", verified=False)
    email = await email_of(u)
    me = (await u.get(f"{API}/auth/me")).json()
    assert me["email_verified"] is False
    mail = to(outbox, email)[-1]
    assert mail["subject"] == "Confirm your email for ContractIQ"

    token = link(outbox, email, VERIFY_LINK)
    r = await client.post(f"{API}/auth/verify-email", json={"token": token})  # no sign-in needed
    assert r.status_code == 200 and r.json()["email_verified"] is True
    assert (await u.get(f"{API}/auth/me")).json()["email_verified"] is True
    # Used up
    assert (await client.post(f"{API}/auth/verify-email", json={"token": token})).status_code == 400
    # Nothing left to resend
    assert (await u.post(f"{API}/auth/resend-verification")).status_code == 409


async def test_resend_verification_is_limited(make_user, outbox, db):
    u = await make_user("Omar", verified=False)
    email = await email_of(u)
    assert (await u.post(f"{API}/auth/resend-verification")).status_code == 429  # signup email just went
    await age_tokens(db, u.id)
    r = await u.post(f"{API}/auth/resend-verification")
    assert r.status_code == 200 and r.json()["sent_to"] == email
    assert len(to(outbox, email)) == 2


async def test_changing_email_needs_new_confirmation_and_tells_old_address(make_user, client, outbox):
    u = await make_user("Pia")
    old = await email_of(u)
    new = f"pia-new-{u.id[:6]}@example.com"
    r = await u.patch(f"{API}/auth/me", json={"email": new, "current_password": "password123"})
    assert r.status_code == 200 and r.json()["user"]["email_verified"] is False

    assert to(outbox, old)[-1]["subject"] == "Your ContractIQ email was changed"
    assert new in to(outbox, old)[-1]["text"]
    token = link(outbox, new, VERIFY_LINK)
    assert (await client.post(f"{API}/auth/verify-email", json={"token": token})).status_code == 200
    assert (await u.get(f"{API}/auth/me")).json()["email_verified"] is True


async def test_verify_link_for_an_old_address_does_not_count(make_user, client, outbox, db):
    u = await make_user("Quinn", verified=False)
    first_email = await email_of(u)
    old_link = link(outbox, first_email, VERIFY_LINK)
    await age_tokens(db, u.id)
    r = await u.patch(f"{API}/auth/me", json={"email": f"q2-{u.id[:6]}@example.com", "current_password": "password123"})
    assert r.status_code == 200
    # Issuing the new link cancelled the old one
    assert (await client.post(f"{API}/auth/verify-email", json={"token": old_link})).status_code == 400


async def test_password_change_in_settings_sends_notice(make_user, outbox):
    u = await make_user("Ravi")
    email = await email_of(u)
    r = await u.patch(f"{API}/auth/me", json={"new_password": "brand-new-pass", "current_password": "password123"})
    assert r.status_code == 200
    assert to(outbox, email)[-1]["subject"] == "Your ContractIQ password was changed"


# ── What an unverified account can't do ────────────────────────────────────

async def test_unverified_cannot_email_outsiders(make_user, db, outbox):
    team, cid, alice, *_ = await signing_team(make_user, db)
    await db.execute(update(UserRow).where(UserRow.id == alice.id).values(email_verified_at=None))
    await db.commit()

    # Sending for signing by email is blocked with a clear reason…
    r = await alice.post(f"{API}/signatures/contract/{cid}", ws=team,
                         json={"signers": SIGNERS, "message": None, "send_email": True})
    assert r.status_code == 403 and "Confirm your email" in r.json()["detail"]
    # …but sharing links yourself still works
    env = await send(alice, team, cid, SIGNERS, send_email=False)
    priya = next(s["id"] for s in env["signers"] if s["name"] == "Priya Sharma")
    outbox.clear()
    # New link: made, just not emailed
    r = await alice.post(f"{API}/signatures/{env['id']}/signers/{priya}/link", ws=team)
    assert r.status_code == 200 and outbox == []
    # Reminders and emailed invites are blocked
    assert (await alice.post(f"{API}/signatures/{env['id']}/signers/{priya}/link?reminder=true", ws=team)).status_code == 403
    assert (await alice.post(f"{API}/workspaces/{team}/invites", json={"email": "x@corp.in"})).status_code == 403
    # Invite links without email still work
    assert (await alice.post(f"{API}/workspaces/{team}/invites", json={"role": "member"})).status_code == 201


async def test_email_off_means_nothing_is_blocked(make_user, monkeypatch):
    from core.config import settings
    monkeypatch.setattr(settings, "EMAIL_PROVIDER", "none")
    u = await make_user("Off", verified=False)
    team = (await u.post(f"{API}/workspaces", json={"name": "T"})).json()["id"]
    assert (await u.post(f"{API}/workspaces/{team}/invites", json={"email": "x@corp.in"})).status_code == 201
    assert (await u.post(f"{API}/auth/resend-verification")).status_code == 503
