"""Account settings, emailed team invites and signing reminders."""
from datetime import timedelta

import pytest
from sqlalchemy import update

from modules.notifications.models import EmailLog
from modules.notifications.service import utcnow
from test_notifications import SIGNERS, TOKEN_IN_URL, email_of, outbox, send  # noqa: F401  (fixture)
from test_signatures import setup_team as signing_team
from test_workspaces import API

pytestmark = pytest.mark.asyncio(loop_scope="session")


# ── Account settings ───────────────────────────────────────────────────────

async def test_change_name_without_password(make_user):
    u = await make_user("Alex")
    r = await u.patch(f"{API}/auth/me", json={"name": "  Abhinav   Ashutosh "})
    assert r.status_code == 200, r.text
    assert r.json()["user"]["name"] == "Abhinav Ashutosh" and r.json()["access_token"]
    assert (await u.get(f"{API}/auth/me")).json()["name"] == "Abhinav Ashutosh"


async def test_change_email_needs_current_password(make_user, client):
    u = await make_user("Alex")
    other = await make_user("Other")
    new = f"new-{u.id[:8]}@example.com"
    assert (await u.patch(f"{API}/auth/me", json={"email": new})).status_code == 403
    assert (await u.patch(f"{API}/auth/me", json={"email": new, "current_password": "wrong-pass"})).status_code == 403
    taken = await email_of(other)
    r = await u.patch(f"{API}/auth/me", json={"email": taken.upper(), "current_password": "password123"})
    assert r.status_code == 400
    r = await u.patch(f"{API}/auth/me", json={"email": new.upper(), "current_password": "password123"})
    assert r.status_code == 200 and r.json()["user"]["email"] == new
    login = await client.post(f"{API}/auth/login", json={"email": new, "password": "password123"})
    assert login.status_code == 200


async def test_change_password(make_user, client):
    u = await make_user("Alex")
    email = await email_of(u)
    assert (await u.patch(f"{API}/auth/me", json={"new_password": "brand-new-pass"})).status_code == 403
    assert (await u.patch(f"{API}/auth/me", json={"new_password": "short", "current_password": "password123"})).status_code == 422
    r = await u.patch(f"{API}/auth/me", json={"new_password": "brand-new-pass", "current_password": "password123"})
    assert r.status_code == 200
    assert (await client.post(f"{API}/auth/login", json={"email": email, "password": "password123"})).status_code == 401
    assert (await client.post(f"{API}/auth/login", json={"email": email, "password": "brand-new-pass"})).status_code == 200


async def test_update_me_needs_auth(client):
    assert (await client.patch(f"{API}/auth/me", json={"name": "X"})).status_code == 401


# ── Emailed invites ────────────────────────────────────────────────────────

async def test_invite_can_be_emailed(make_user, outbox):
    alice = await make_user("Alice")
    team = (await alice.post(f"{API}/workspaces", json={"name": "Legal <Team>"})).json()["id"]
    r = await alice.post(f"{API}/workspaces/{team}/invites", json={"role": "member", "email": "newbie@corp.in"})
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["emailed_to"] == "newbie@corp.in" and body["token"]
    assert len(outbox) == 1
    mail = outbox[0]
    assert mail["to"] == "newbie@corp.in" and mail["reply_to"] == await email_of(alice)
    assert mail["subject"] == "Alice invited you to Legal <Team> on ContractIQ"
    assert f"https://app.example.com/invite/{body['token']}" in mail["text"]
    assert "Legal &lt;Team&gt;" in mail["html"] and "a member" in mail["text"]

    # The emailed link works
    newbie = await make_user("Newbie")
    assert (await newbie.post(f"{API}/invites/{body['token']}/accept")).status_code == 200

    # Without an email address, nothing is sent
    outbox.clear()
    r = await alice.post(f"{API}/workspaces/{team}/invites", json={"role": "viewer"})
    assert r.json()["emailed_to"] is None and outbox == []


async def test_invite_email_off(make_user, outbox, monkeypatch):
    from core.config import settings
    monkeypatch.setattr(settings, "EMAIL_PROVIDER", "none")
    alice = await make_user("Alice")
    team = (await alice.post(f"{API}/workspaces", json={"name": "T"})).json()["id"]
    r = await alice.post(f"{API}/workspaces/{team}/invites", json={"email": "x@corp.in"})
    assert r.status_code == 201 and r.json()["emailed_to"] is None and r.json()["token"]


async def test_invite_email_must_be_valid(make_user, outbox):
    alice = await make_user("Alice")
    team = (await alice.post(f"{API}/workspaces", json={"name": "T"})).json()["id"]
    assert (await alice.post(f"{API}/workspaces/{team}/invites", json={"email": "not-an-email"})).status_code == 422


# ── Signing reminders ──────────────────────────────────────────────────────

async def test_reminder_is_rate_limited(make_user, db, client, outbox):
    team, cid, alice, *_ = await signing_team(make_user, db)
    env = await send(alice, team, cid, SIGNERS)
    priya = next(s["id"] for s in env["signers"] if s["name"] == "Priya Sharma")
    url = f"{API}/signatures/{env['id']}/signers/{priya}/link?reminder=true"

    # Just emailed the original request: too soon
    r = await alice.post(url, ws=team)
    assert r.status_code == 429 and "less than an hour" in r.json()["detail"]

    # An hour later it goes out, with the reminder wording and a working fresh link
    await db.execute(update(EmailLog).where(EmailLog.ref_id == priya).values(created_at=utcnow() - timedelta(hours=2)))
    await db.commit()
    outbox.clear()
    r = await alice.post(url, ws=team)
    assert r.status_code == 200, r.text
    assert r.json()["emailed"] is True and len(outbox) == 1
    mail = outbox[0]
    assert mail["subject"] == "Reminder: please sign: Supply agreement.pdf"
    assert "reminder" in mail["text"].lower()
    token = TOKEN_IN_URL.search(mail["text"]).group(1)
    assert (await client.get(f"{API}/sign/{token}")).status_code == 200

    # …and the next one is limited again
    assert (await alice.post(url, ws=team)).status_code == 429
    cert = (await alice.get(f"{API}/signatures/{env['id']}", ws=team)).json()
    assert any(e["type"] == "link_reissued" and e["detail"].startswith("Reminder") for e in cert["events"])


async def test_reminder_needs_email_and_a_pending_signer(make_user, db, outbox, monkeypatch):
    from core.config import settings
    team, cid, alice, _bob, vic, _ada = await signing_team(make_user, db)
    env = await send(alice, team, cid, SIGNERS, send_email=False)
    priya = next(s["id"] for s in env["signers"] if s["name"] == "Priya Sharma")
    url = f"{API}/signatures/{env['id']}/signers/{priya}/link?reminder=true"
    # Viewers can't send reminders
    assert (await vic.post(url, ws=team)).status_code == 403
    # Never emailed before, so no wait
    assert (await alice.post(url, ws=team)).status_code == 200
    # Email turned off: clear error, no link changed
    monkeypatch.setattr(settings, "EMAIL_PROVIDER", "none")
    db.expire_all()
    await db.execute(update(EmailLog).where(EmailLog.ref_id == priya).values(created_at=utcnow() - timedelta(hours=2)))
    await db.commit()
    r = await alice.post(url, ws=team)
    assert r.status_code == 409 and "Email isn't set up" in r.json()["detail"]
