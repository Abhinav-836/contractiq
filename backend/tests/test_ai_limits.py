"""Daily AI review limits: per account and for the whole server."""
import pytest
from sqlalchemy import func, select

from core.config import settings
from modules.contracts.models import Contract
from modules.usage.models import AIRun

pytestmark = pytest.mark.asyncio(loop_scope="session")

API = "/api/v1"
SAMPLE_TXT = ("This Services Agreement is made between Acme Ltd and Beta LLC. " * 5).encode()


async def upload(user):
    return await user.post(f"{API}/contracts/upload", files={"file": ("a.txt", SAMPLE_TXT, "text/plain")})


async def test_each_account_gets_its_daily_reviews_then_429(make_user, db, monkeypatch):
    monkeypatch.setattr(settings, "AI_REVIEWS_PER_USER_DAILY", 2)
    alice, bob = await make_user("Alice"), await make_user("Bob")

    assert (await upload(alice)).status_code == 200
    assert (await upload(alice)).status_code == 200
    r = await upload(alice)
    assert r.status_code == 429
    assert "2 contract reviews" in r.json()["detail"]

    # The refused upload left nothing behind
    n = (await db.execute(select(func.count()).select_from(Contract).where(Contract.user_id == alice.id))).scalar_one()
    assert n == 2
    # Someone else still has their own allowance
    assert (await upload(bob)).status_code == 200


async def test_review_again_counts_too(make_user, db, monkeypatch):
    monkeypatch.setattr(settings, "AI_REVIEWS_PER_USER_DAILY", 1)
    carol = await make_user("Carol")
    r = await upload(carol)
    assert r.status_code == 200
    contract = await db.get(Contract, r.json()["id"])
    await db.refresh(contract)
    if contract.status == "processing":  # the mock review normally finishes straight away
        contract.status = "completed"
        await db.commit()
    r = await carol.post(f"{API}/contracts/{contract.id}/analyze")
    assert r.status_code == 429


async def test_server_wide_daily_total(make_user, db, monkeypatch):
    monkeypatch.setattr(settings, "AI_REVIEWS_PER_USER_DAILY", 0)  # off
    used = (await db.execute(select(func.count()).select_from(AIRun))).scalar_one()
    monkeypatch.setattr(settings, "AI_REVIEWS_DAILY_TOTAL", used + 1)
    dave, erin = await make_user("Dave"), await make_user("Erin")
    assert (await upload(dave)).status_code == 200
    r = await upload(erin)
    assert r.status_code == 429
    assert "daily review limit" in r.json()["detail"]
