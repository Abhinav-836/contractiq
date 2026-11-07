"""Approval workflow: request → every reviewer approves, or one rejects."""
import pytest
from sqlalchemy import select, update

from modules.approvals.models import ApprovalRequest
from modules.contracts.models import Contract
from test_workspaces import API, add_contract, team_with

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def setup_team(make_user, db, *extra_roles):
    """Owner Alice, member Bob, viewer Vic (+ any extra (name, role)), and one finished contract."""
    alice, bob, vic = [await make_user(n) for n in ("Alice", "Bob", "Vic")]
    extras = [(await make_user(name), role) for name, role in extra_roles]
    team = await team_with(alice, (bob, "member"), (vic, "viewer"), *extras)
    ids = await add_contract(db, team, alice.id)
    return team, ids["contract"], alice, bob, vic, [u for u, _ in extras]


async def request(user, team, contract_id, reviewers, note="Please check clause 7"):
    return await user.post(
        f"{API}/approvals/contract/{contract_id}", ws=team,
        json={"reviewer_ids": [r.id for r in reviewers], "note": note},
    )


async def contract_status(db, contract_id):
    db.expire_all()
    return (await db.execute(select(Contract.approval_status).where(Contract.id == contract_id))).scalar()


async def test_everyone_must_approve(make_user, db):
    team, cid, alice, bob, vic, _ = await setup_team(make_user, db)
    r = await request(alice, team, cid, [bob, vic])
    assert r.status_code == 201, r.text
    req = r.json()
    assert req["status"] == "pending" and req["requested_by_name"] == "Alice" and req["note"] == "Please check clause 7"
    assert {v["name"] for v in req["reviewers"]} == {"Bob", "Vic"}
    assert await contract_status(db, cid) == "pending"
    listed = (await alice.get(f"{API}/contracts", ws=team)).json()
    assert listed[0]["approval_status"] == "pending"

    assert (await bob.get(f"{API}/approvals/stats", ws=team)).json()["waiting_for_me"] == 1
    r = await bob.post(f"{API}/approvals/{req['id']}/decision", ws=team, json={"decision": "approved"})
    assert r.json()["status"] == "pending" and r.json()["approved_count"] == 1
    assert (await bob.get(f"{API}/approvals/stats", ws=team)).json()["waiting_for_me"] == 0

    # A viewer can be a reviewer and decide
    r = await vic.post(f"{API}/approvals/{req['id']}/decision", ws=team, json={"decision": "approved", "comment": "Fine by finance"})
    assert r.status_code == 200
    assert r.json()["status"] == "approved" and r.json()["closed_at"] and r.json()["closed_by_name"] == "Vic"
    assert await contract_status(db, cid) == "approved"


async def test_one_rejection_rejects_and_needs_a_comment(make_user, db):
    team, cid, alice, bob, vic, _ = await setup_team(make_user, db)
    req = (await request(alice, team, cid, [bob, vic])).json()

    r = await bob.post(f"{API}/approvals/{req['id']}/decision", ws=team, json={"decision": "rejected"})
    assert r.status_code == 422 and "why" in r.json()["detail"]
    r = await bob.post(f"{API}/approvals/{req['id']}/decision", ws=team, json={"decision": "rejected", "comment": "Liability is uncapped"})
    assert r.json()["status"] == "rejected"
    assert await contract_status(db, cid) == "rejected"

    # Closed: nobody else can decide, and it can't be cancelled
    assert (await vic.post(f"{API}/approvals/{req['id']}/decision", ws=team, json={"decision": "approved"})).status_code == 409
    assert (await alice.post(f"{API}/approvals/{req['id']}/cancel", ws=team)).status_code == 409
    history = (await alice.get(f"{API}/approvals/contract/{cid}", ws=team)).json()
    bob_row = next(v for v in history[0]["reviewers"] if v["name"] == "Bob")
    assert bob_row["decision"] == "rejected" and bob_row["comment"] == "Liability is uncapped"


async def test_reviewer_cannot_decide_twice_and_outsiders_cannot_decide(make_user, db):
    team, cid, alice, bob, vic, _ = await setup_team(make_user, db)
    req = (await request(alice, team, cid, [bob, vic])).json()
    await bob.post(f"{API}/approvals/{req['id']}/decision", ws=team, json={"decision": "approved"})
    r = await bob.post(f"{API}/approvals/{req['id']}/decision", ws=team, json={"decision": "approved"})
    assert r.status_code == 409 and "already approved" in r.json()["detail"]
    # Alice is in the workspace but isn't a reviewer
    r = await alice.post(f"{API}/approvals/{req['id']}/decision", ws=team, json={"decision": "approved"})
    assert r.status_code == 403


async def test_request_validation(make_user, db):
    team, cid, alice, bob, vic, _ = await setup_team(make_user, db)
    stranger = await make_user("Stranger")

    r = await request(alice, team, cid, [alice])
    assert r.status_code == 422 and "your own" in r.json()["detail"]
    r = await request(alice, team, cid, [bob, stranger])
    assert r.status_code == 422 and "in this workspace" in r.json()["detail"]
    assert (await alice.post(f"{API}/approvals/contract/{cid}", ws=team, json={"reviewer_ids": []})).status_code == 422
    r = await request(vic, team, cid, [bob])  # viewers can review, not request
    assert r.status_code == 403

    await db.execute(update(Contract).where(Contract.id == cid).values(status="processing"))
    await db.commit()
    r = await request(alice, team, cid, [bob])
    assert r.status_code == 409 and "review to finish" in r.json()["detail"]


async def test_one_open_request_per_contract_and_cancel_rules(make_user, db):
    team, cid, alice, bob, vic, (admin,) = await setup_team(make_user, db, ("Ada", "admin"))

    first = (await request(alice, team, cid, [bob])).json()
    assert (await request(alice, team, cid, [vic])).status_code == 409
    # Bob (a member, not the requester) can't cancel; an admin can
    assert (await bob.post(f"{API}/approvals/{first['id']}/cancel", ws=team)).status_code == 403
    r = await admin.post(f"{API}/approvals/{first['id']}/cancel", ws=team)
    assert r.json()["status"] == "cancelled" and r.json()["closed_by_name"] == "Ada"
    assert await contract_status(db, cid) is None  # nothing else was ever decided

    # Approve a second request, then cancel a third: status falls back to "approved"
    second = (await request(bob, team, cid, [alice])).json()
    await alice.post(f"{API}/approvals/{second['id']}/decision", ws=team, json={"decision": "approved"})
    third = (await request(alice, team, cid, [vic])).json()
    assert await contract_status(db, cid) == "pending"
    assert (await alice.post(f"{API}/approvals/{third['id']}/cancel", ws=team)).status_code == 200
    assert await contract_status(db, cid) == "approved"

    history = (await alice.get(f"{API}/approvals/contract/{cid}", ws=team)).json()
    assert [h["status"] for h in history] == ["cancelled", "approved", "cancelled"]


async def test_removed_reviewer_does_not_block_a_request(make_user, db):
    team, cid, alice, bob, vic, _ = await setup_team(make_user, db)
    req = (await request(alice, team, cid, [bob, vic])).json()
    await vic.post(f"{API}/approvals/{req['id']}/decision", ws=team, json={"decision": "approved"})
    await alice.delete(f"{API}/workspaces/{team}/members/{bob.id}")
    history = (await alice.get(f"{API}/approvals/contract/{cid}", ws=team)).json()
    assert history[0]["status"] == "approved" and [v["name"] for v in history[0]["reviewers"]] == ["Vic"]
    assert await contract_status(db, cid) == "approved"


async def test_only_reviewer_leaving_cancels_the_request(make_user, db):
    team, cid, alice, bob, vic, _ = await setup_team(make_user, db)
    await request(alice, team, cid, [bob])
    assert (await bob.delete(f"{API}/workspaces/{team}/members/{bob.id}")).status_code == 200  # Bob leaves
    history = (await alice.get(f"{API}/approvals/contract/{cid}", ws=team)).json()
    assert history[0]["status"] == "cancelled"
    assert await contract_status(db, cid) is None


async def test_inbox_scopes_and_isolation(make_user, db):
    team, cid, alice, bob, vic, _ = await setup_team(make_user, db)
    req = (await request(alice, team, cid, [bob])).json()

    waiting = (await bob.get(f"{API}/approvals?scope=waiting", ws=team)).json()
    assert [w["id"] for w in waiting] == [req["id"]] and waiting[0]["awaiting_my_decision"]
    assert waiting[0]["contract_filename"] == "c.pdf"
    assert (await alice.get(f"{API}/approvals?scope=waiting", ws=team)).json() == []
    assert [r["id"] for r in (await alice.get(f"{API}/approvals?scope=requested", ws=team)).json()] == [req["id"]]
    assert len((await vic.get(f"{API}/approvals?status=pending", ws=team)).json()) == 1

    mallory = await make_user("Mallory")
    assert (await mallory.get(f"{API}/approvals/contract/{cid}")).status_code == 404
    assert (await mallory.post(f"{API}/approvals/{req['id']}/decision", json={"decision": "approved"})).status_code == 404
    assert (await mallory.post(f"{API}/approvals/{req['id']}/cancel")).status_code == 404
    assert (await mallory.get(f"{API}/approvals")).json() == []
    # Other workspaces of the same user don't leak either
    bob_personal = await bob.personal_workspace_id()
    assert (await bob.get(f"{API}/approvals?scope=waiting", ws=bob_personal)).json() == []


async def test_deleting_a_contract_deletes_its_approvals(make_user, db):
    team, cid, alice, bob, vic, _ = await setup_team(make_user, db)
    req = (await request(alice, team, cid, [bob, vic])).json()
    await bob.post(f"{API}/approvals/{req['id']}/decision", ws=team, json={"decision": "approved"})
    assert (await alice.delete(f"{API}/contracts/{cid}", ws=team)).status_code == 200
    db.expire_all()
    assert (await db.execute(select(ApprovalRequest).where(ApprovalRequest.contract_id == cid))).first() is None
    assert (await bob.get(f"{API}/approvals/stats", ws=team)).json() == {"waiting_for_me": 0, "pending": 0}
