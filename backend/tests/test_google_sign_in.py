"""
"Sign in with Google": new accounts, linking to existing ones, and every
way a bad token is refused. Google is never called: the tests sign their
own ID tokens with a throwaway RSA key and put its public half where the
verifier caches Google's keys.
"""
import time

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from jose import jwk, jwt
from sqlalchemy import update

from core.config import settings
from modules.users import google
from modules.users.models import User as UserRow
from test_workspaces import API

pytestmark = pytest.mark.asyncio(loop_scope="session")

CLIENT_ID = "test-client.apps.googleusercontent.com"
KID = "test-key-1"

_private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
PRIVATE_PEM = _private.private_bytes(
    serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()
).decode()
PUBLIC_JWK = {
    **jwk.construct(
        _private.public_key().public_bytes(
            serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode(),
        "RS256",
    ).to_dict(),
    "kid": KID, "use": "sig", "alg": "RS256",
}
_n = {"i": 0}


@pytest.fixture(autouse=True)
def google_configured(monkeypatch):
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", CLIENT_ID)
    monkeypatch.setitem(google._cache, "keys", [PUBLIC_JWK])
    monkeypatch.setitem(google._cache, "expires", time.time() + 3600)

    async def no_network():
        raise AssertionError("tests must not fetch Google's keys")

    monkeypatch.setattr(google, "_fetch_keys", no_network)


def id_token(email, sub=None, *, aud=CLIENT_ID, iss="https://accounts.google.com",
             verified=True, exp_in=600, name="Gita Rao", key=PRIVATE_PEM, kid=KID):
    now = int(time.time())
    claims = {"iss": iss, "aud": aud, "sub": sub or f"g-{email}", "email": email,
              "email_verified": verified, "name": name, "iat": now, "exp": now + exp_in}
    return jwt.encode(claims, key, algorithm="RS256", headers={"kid": kid})


def new_email():
    _n["i"] += 1
    return f"google{_n['i']}@example.com"


async def sign_in(client, token):
    return await client.post(f"{API}/auth/google", json={"credential": token})


# ── Happy paths ────────────────────────────────────────────────────────────

async def test_features_tell_the_frontend_the_client_id(client):
    r = await client.get(f"{API}/features")
    assert r.json()["google_client_id"] == CLIENT_ID


async def test_first_google_sign_in_creates_a_confirmed_account_with_a_workspace(client):
    email = new_email()
    r = await sign_in(client, id_token(email))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["created"] is True
    assert body["user"]["email"] == email
    assert body["user"]["name"] == "Gita Rao"
    assert body["user"]["email_verified"] is True
    assert body["user"]["has_password"] is False

    headers = {"Authorization": f"Bearer {body['access_token']}"}
    workspaces = (await client.get(f"{API}/workspaces", headers=headers)).json()
    assert [w["is_personal"] for w in workspaces] == [True]

    again = await sign_in(client, id_token(email))
    assert again.json()["created"] is False
    assert again.json()["user"]["id"] == body["user"]["id"]


async def test_google_links_to_an_existing_confirmed_account_and_keeps_its_password(client, make_user):
    u = await make_user("Linked")
    email = (await u.get(f"{API}/auth/me")).json()["email"]

    r = await sign_in(client, id_token(email.upper()))
    assert r.status_code == 200, r.text
    assert r.json()["created"] is False
    assert r.json()["user"]["id"] == u.id
    assert r.json()["user"]["has_password"] is True

    pw = await client.post(f"{API}/auth/login", json={"email": email, "password": "password123"})
    assert pw.status_code == 200


async def test_linking_an_unconfirmed_account_cancels_a_password_someone_else_may_have_set(client, make_user):
    # Someone registers an address they don't own and sets a password.
    squatter = await make_user("Squat", verified=False)
    email = (await squatter.get(f"{API}/auth/me")).json()["email"]

    # The real owner then signs in with Google: Google proves the address is theirs.
    r = await sign_in(client, id_token(email))
    assert r.status_code == 200
    assert r.json()["user"]["email_verified"] is True
    assert r.json()["user"]["has_password"] is False

    old = await client.post(f"{API}/auth/login", json={"email": email, "password": "password123"})
    assert old.status_code == 401
    assert "Google" in old.json()["detail"]


async def test_found_by_google_id_after_changing_email(client, db):
    email = new_email()
    body = (await sign_in(client, id_token(email, sub="sub-moves"))).json()
    await db.execute(update(UserRow).where(UserRow.id == body["user"]["id"]).values(email="moved@example.com"))
    await db.commit()

    r = await sign_in(client, id_token(email, sub="sub-moves"))
    assert r.json()["user"]["id"] == body["user"]["id"]
    assert r.json()["user"]["email"] == "moved@example.com"


# ── Google-only accounts and passwords ─────────────────────────────────────

async def test_google_only_account_can_set_a_password_without_a_current_one(client):
    email = new_email()
    token = (await sign_in(client, id_token(email))).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    no_pw = await client.post(f"{API}/auth/login", json={"email": email, "password": "whatever123"})
    assert no_pw.status_code == 401

    change_email = await client.patch(f"{API}/auth/me", headers=headers, json={"email": "elsewhere@example.com"})
    assert change_email.status_code == 400

    r = await client.patch(f"{API}/auth/me", headers=headers, json={"new_password": "brand-new-pass"})
    assert r.status_code == 200, r.text
    assert r.json()["user"]["has_password"] is True

    ok = await client.post(f"{API}/auth/login", json={"email": email, "password": "brand-new-pass"})
    assert ok.status_code == 200

    # From now on, changing it needs the current password like any account.
    headers = {"Authorization": f"Bearer {ok.json()['access_token']}"}
    again = await client.patch(f"{API}/auth/me", headers=headers, json={"new_password": "another-pass1"})
    assert again.status_code == 403


# ── Refused tokens ─────────────────────────────────────────────────────────

@pytest.mark.parametrize("kwargs", [
    {"aud": "someone-elses-app.apps.googleusercontent.com"},
    {"iss": "https://evil.example.com"},
    {"exp_in": -60},
    {"key": rsa.generate_private_key(public_exponent=65537, key_size=2048).private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()).decode()},
], ids=["other-app", "not-google", "expired", "forged-signature"])
async def test_bad_tokens_are_refused(client, kwargs):
    r = await sign_in(client, id_token(new_email(), **kwargs))
    assert r.status_code == 401, r.text


async def test_unverified_google_email_is_refused(client):
    r = await sign_in(client, id_token(new_email(), verified=False))
    assert r.status_code == 401
    assert "verified" in r.json()["detail"]


async def test_hs256_token_signed_with_a_guessable_secret_is_refused(client):
    now = int(time.time())
    fake = jwt.encode({"iss": "accounts.google.com", "aud": CLIENT_ID, "sub": "x", "email": new_email(),
                       "email_verified": True, "exp": now + 600}, "secret", algorithm="HS256")
    assert (await sign_in(client, fake)).status_code == 401


async def test_garbage_is_refused(client):
    assert (await sign_in(client, "not-a-jwt-at-all-really")).status_code == 401


async def test_other_google_account_cannot_take_over_a_linked_email(client):
    email = new_email()
    await sign_in(client, id_token(email, sub="owner-sub"))
    r = await sign_in(client, id_token(email, sub="intruder-sub"))
    assert r.status_code == 409


async def test_disabled_account_cannot_sign_in(client, db):
    email = new_email()
    body = (await sign_in(client, id_token(email))).json()
    await db.execute(update(UserRow).where(UserRow.id == body["user"]["id"]).values(is_active=False))
    await db.commit()
    assert (await sign_in(client, id_token(email))).status_code == 403


async def test_switched_off_without_a_client_id(client, monkeypatch):
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", None)
    assert (await sign_in(client, id_token(new_email()))).status_code == 404
    assert (await client.get(f"{API}/features")).json()["google_client_id"] is None

