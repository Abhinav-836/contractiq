"""Team workspaces: isolation, roles, invite links."""
from datetime import timedelta

import pytest
from sqlalchemy import update

from db.base import gen_uuid
from modules.alerts.models import Alert
from modules.contracts.models import Contract
from modules.obligations.models import Obligation
from modules.workspaces.models import WorkspaceInvite
from modules.workspaces.service import utcnow

pytestmark = pytest.mark.asyncio(loop_scope="session")

API = "/api/v1"
SAMPLE_TXT = ("This Services Agreement is made between Acme Ltd and Beta LLC. " * 5).encode()


async def add_contract(db, workspace_id: str, uploader_id: str, name: str = "c.pdf") -> dict:
    """A finished contract with one obligation and one alert, inserted directly."""
    contract = Contract(
        id=gen_uuid(), filename=name, file_type=".pdf", file_size=1, file_path="db",
        status="completed", risk_level="high", user_id=uploader_id, workspace_id=workspace_id,
    )
    db.add(contract)
    await db.flush()
    obligation = Obligation(id=gen_uuid(), contract_id=contract.id, title="Pay invoice")
    alert = Alert(id=gen_uuid(), contract_id=contract.id, type="risk", title="High risk", message="m")
    db.add_all([obligation, alert])
    await db.commit()
    return {"contract": contract.id, "obligation": obligation.id, "alert": alert.id}


async def team_with(owner, *people_and_roles):
    """Owner creates a team workspace and invites each (user, role) via a link."""
    r = await owner.post(f"{API}/workspaces", json={"name": "Legal team"})
    assert r.status_code == 201, r.text
    ws = r.json()["id"]
    for user, role in people_and_roles:
        r = await owner.post(f"{API}/workspaces/{ws}/invites", json={"role": role})
        assert r.status_code == 201, r.text
        r = await user.post(f"{API}/invites/{r.json()['token']}/accept")
        assert r.status_code == 200, r.text
    return ws


# ── Personal workspaces & backward compatibility ─────────────────────────────

async def test_signup_creates_personal_workspace(make_user):
    alice = await make_user("Alice")
    r = await alice.get(f"{API}/workspaces")
    assert r.status_code == 200
    [ws] = r.json()
    assert ws["is_personal"] and ws["role"] == "owner" and ws["name"] == "Alice's workspace"


async def test_no_header_means_personal_workspace(make_user, db):
    alice = await make_user("Alice")
    ws = await alice.personal_workspace_id()
    ids = await add_contract(db, ws, alice.id)
    r = await alice.get(f"{API}/contracts")  # no X-Workspace-Id, like old clients
    assert [c["id"] for c in r.json()] == [ids["contract"]]


async def test_upload_goes_into_active_workspace(make_user, db):
    alice = await make_user("Alice")
    team = await team_with(alice)
    r = await alice.post(f"{API}/contracts/upload", ws=team, files={"file": ("a.txt", SAMPLE_TXT, "text/plain")})
    assert r.status_code == 200, r.text
    contract = await db.get(Contract, r.json()["id"])
    assert contract.workspace_id == team and contract.user_id == alice.id
    personal = await alice.get(f"{API}/contracts")
    assert all(c["id"] != contract.id for c in personal.json())


# ── Isolation ────────────────────────────────────────────────────────────────

async def test_outsiders_see_nothing(make_user, db):
    alice, mallory = await make_user("Alice"), await make_user("Mallory")
    ws = await alice.personal_workspace_id()
    ids = await add_contract(db, ws, alice.id)

    for url in (
        f"{API}/contracts/{ids['contract']}",
        f"{API}/analysis/contract/{ids['contract']}",
        f"{API}/obligations/{ids['obligation']}",
    ):
        assert (await mallory.get(url)).status_code == 404, url
    assert (await mallory.get(f"{API}/contracts")).json() == []
    assert (await mallory.get(f"{API}/obligations")).json() == []
    assert (await mallory.get(f"{API}/alerts")).json() == []
    assert (await mallory.get(f"{API}/contracts/stats")).json()["total_contracts"] == 0
    assert (await mallory.patch(f"{API}/obligations/{ids['obligation']}/complete")).status_code == 404
    assert (await mallory.delete(f"{API}/contracts/{ids['contract']}")).status_code == 404

    # Naming someone else's workspace in the header doesn't help
    assert (await mallory.get(f"{API}/contracts", ws=ws)).status_code == 404
    assert (await mallory.get(f"{API}/workspaces/{ws}/members")).status_code == 404
    assert (await mallory.post(f"{API}/workspaces/{ws}/invites", json={"role": "admin"})).status_code == 404


async def test_contract_id_from_another_workspace_is_404_even_for_a_member_of_both(make_user, db):
    alice, bob = await make_user("Alice"), await make_user("Bob")
    team = await team_with(alice, (bob, "member"))
    ids = await add_contract(db, team, alice.id)
    bob_personal = await bob.personal_workspace_id()
    assert (await bob.get(f"{API}/contracts/{ids['contract']}", ws=team)).status_code == 200
    assert (await bob.get(f"{API}/contracts/{ids['contract']}", ws=bob_personal)).status_code == 404


# ── Roles ────────────────────────────────────────────────────────────────────

async def test_viewer_is_read_only(make_user, db):
    alice, vic = await make_user("Alice"), await make_user("Vic")
    team = await team_with(alice, (vic, "viewer"))
    ids = await add_contract(db, team, alice.id)

    assert (await vic.get(f"{API}/contracts", ws=team)).json()[0]["id"] == ids["contract"]
    assert (await vic.get(f"{API}/obligations", ws=team)).status_code == 200
    assert (await vic.get(f"{API}/alerts", ws=team)).status_code == 200

    blocked = [
        await vic.post(f"{API}/contracts/upload", ws=team, files={"file": ("a.txt", SAMPLE_TXT, "text/plain")}),
        await vic.post(f"{API}/contracts/{ids['contract']}/analyze", ws=team),
        await vic.delete(f"{API}/contracts/{ids['contract']}", ws=team),
        await vic.patch(f"{API}/obligations/{ids['obligation']}/complete", ws=team),
        await vic.patch(f"{API}/obligations/{ids['obligation']}", ws=team, json={"title": "x"}),
        await vic.delete(f"{API}/obligations/{ids['obligation']}", ws=team),
        await vic.patch(f"{API}/alerts/{ids['alert']}/read", ws=team),
        await vic.post(f"{API}/alerts/mark-all-read", ws=team),
        await vic.delete(f"{API}/alerts/{ids['alert']}", ws=team),
    ]
    assert [r.status_code for r in blocked] == [403] * len(blocked)
    assert "view-only" in blocked[0].json()["detail"]


async def test_member_can_edit_but_only_delete_own_contracts(make_user, db):
    alice, bob = await make_user("Alice"), await make_user("Bob")
    team = await team_with(alice, (bob, "member"))
    alices = await add_contract(db, team, alice.id, "alice.pdf")
    bobs = await add_contract(db, team, bob.id, "bob.pdf")

    assert (await bob.patch(f"{API}/obligations/{alices['obligation']}/complete", ws=team)).status_code == 200
    assert (await bob.patch(f"{API}/alerts/{alices['alert']}/read", ws=team)).status_code == 200
    r = await bob.delete(f"{API}/contracts/{alices['contract']}", ws=team)
    assert r.status_code == 403 and "admins" in r.json()["detail"]
    assert (await bob.delete(f"{API}/contracts/{bobs['contract']}", ws=team)).status_code == 200
    # Admins and owners can delete anyone's
    assert (await alice.delete(f"{API}/contracts/{alices['contract']}", ws=team)).status_code == 200


async def test_role_management_rules(make_user):
    owner, admin, member, viewer = [await make_user(n) for n in ("Owner", "Admin", "Member", "Viewer")]
    team = await team_with(owner, (admin, "admin"), (member, "member"), (viewer, "viewer"))
    members_url = f"{API}/workspaces/{team}/members"

    # Admins manage members/viewers, but can't create admins or touch admins/the owner
    assert (await admin.patch(f"{members_url}/{viewer.id}", json={"role": "member"})).status_code == 200
    assert (await admin.patch(f"{members_url}/{member.id}", json={"role": "admin"})).status_code == 403
    assert (await admin.patch(f"{members_url}/{owner.id}", json={"role": "viewer"})).status_code == 403
    assert (await admin.post(f"{API}/workspaces/{team}/invites", json={"role": "admin"})).status_code == 403
    # Members can't manage anyone
    assert (await member.patch(f"{members_url}/{viewer.id}", json={"role": "viewer"})).status_code == 403
    assert (await member.post(f"{API}/workspaces/{team}/invites", json={"role": "viewer"})).status_code == 403
    assert (await member.patch(f"{API}/workspaces/{team}", json={"name": "Mine now"})).status_code == 403
    # "owner" can't be handed out through the API
    assert (await owner.patch(f"{members_url}/{admin.id}", json={"role": "owner"})).status_code == 422
    # Owner can do all of it
    assert (await owner.patch(f"{members_url}/{member.id}", json={"role": "admin"})).status_code == 200
    assert (await owner.delete(f"{members_url}/{admin.id}")).status_code == 200

    roles = {m["user_id"]: m["role"] for m in (await viewer.get(members_url)).json()}
    assert roles == {owner.id: "owner", member.id: "admin", viewer.id: "member"}


async def test_leaving(make_user):
    alice, bob = await make_user("Alice"), await make_user("Bob")
    team = await team_with(alice, (bob, "member"))
    r = await alice.delete(f"{API}/workspaces/{team}/members/{alice.id}")
    assert r.status_code == 400 and "Owners can't leave" in r.json()["detail"]
    assert (await bob.delete(f"{API}/workspaces/{team}/members/{bob.id}")).status_code == 200
    assert (await bob.get(f"{API}/contracts", ws=team)).status_code == 404


# ── Invite links ─────────────────────────────────────────────────────────────

async def test_invite_preview_is_public_and_token_is_not_stored(make_user, client, db):
    alice = await make_user("Alice")
    team = await team_with(alice)
    created = (await alice.post(f"{API}/workspaces/{team}/invites", json={"role": "viewer"})).json()

    r = await client.get(f"{API}/invites/{created['token']}")  # no auth header
    assert r.status_code == 200
    assert r.json()["workspace_name"] == "Legal team" and r.json()["role"] == "viewer"
    assert r.json()["invited_by"] == "Alice"

    invite = await db.get(WorkspaceInvite, created["id"])
    assert invite.token_hash != created["token"] and len(invite.token_hash) == 64
    listed = (await alice.get(f"{API}/workspaces/{team}/invites")).json()
    assert all("token" not in i for i in listed)


async def test_invite_max_uses_revoke_and_expiry(make_user, db):
    alice, b, c, d = [await make_user(n) for n in ("Alice", "B", "C", "D")]
    team = await team_with(alice)

    single = (await alice.post(f"{API}/workspaces/{team}/invites", json={"role": "member", "max_uses": 1})).json()
    assert (await b.post(f"{API}/invites/{single['token']}/accept")).status_code == 200
    assert (await c.post(f"{API}/invites/{single['token']}/accept")).status_code == 404

    revoked = (await alice.post(f"{API}/workspaces/{team}/invites", json={})).json()
    assert (await alice.delete(f"{API}/workspaces/{team}/invites/{revoked['id']}")).status_code == 200
    assert (await c.post(f"{API}/invites/{revoked['token']}/accept")).status_code == 404

    expired = (await alice.post(f"{API}/workspaces/{team}/invites", json={})).json()
    await db.execute(
        update(WorkspaceInvite).where(WorkspaceInvite.id == expired["id"]).values(expires_at=utcnow() - timedelta(minutes=1))
    )
    await db.commit()
    assert (await d.post(f"{API}/invites/{expired['token']}/accept")).status_code == 404
    assert (await d.get(f"{API}/invites/{expired['token']}")).status_code == 404

    # Used-up / revoked / expired links aren't listed
    assert (await alice.get(f"{API}/workspaces/{team}/invites")).json() == []


async def test_existing_member_accepting_keeps_role_and_does_not_use_up_link(make_user, db):
    alice, bob = await make_user("Alice"), await make_user("Bob")
    team = await team_with(alice, (bob, "admin"))
    link = (await alice.post(f"{API}/workspaces/{team}/invites", json={"role": "viewer", "max_uses": 1})).json()
    r = await bob.post(f"{API}/invites/{link['token']}/accept")
    assert r.json() == {"workspace_id": team, "role": "admin", "already_member": True}
    assert (await db.get(WorkspaceInvite, link["id"])).use_count == 0


# ── Workspace lifecycle ──────────────────────────────────────────────────────

async def test_workspace_delete_rules(make_user, db):
    alice, bob = await make_user("Alice"), await make_user("Bob")
    personal = await alice.personal_workspace_id()
    assert (await alice.delete(f"{API}/workspaces/{personal}")).status_code == 400

    team = await team_with(alice, (bob, "admin"))
    ids = await add_contract(db, team, alice.id)
    assert (await bob.delete(f"{API}/workspaces/{team}")).status_code == 403
    r = await alice.delete(f"{API}/workspaces/{team}")
    assert r.status_code == 409 and "1 contract" in r.json()["detail"]
    await alice.delete(f"{API}/contracts/{ids['contract']}", ws=team)
    assert (await alice.delete(f"{API}/workspaces/{team}")).status_code == 200
    assert team not in [w["id"] for w in (await bob.get(f"{API}/workspaces")).json()]


async def test_workspace_list_counts(make_user, db):
    alice, bob = await make_user("Alice"), await make_user("Bob")
    team = await team_with(alice, (bob, "viewer"))
    await add_contract(db, team, alice.id)
    listed = {w["id"]: w for w in (await bob.get(f"{API}/workspaces")).json()}
    assert listed[team]["role"] == "viewer"
    assert listed[team]["member_count"] == 2 and listed[team]["contract_count"] == 1


async def test_every_read_route_works_for_every_role(make_user, db):
    """Smoke test: each list/stats/detail route answers 200 in a shared workspace, for every role."""
    owner, admin, member, viewer = [await make_user(n) for n in ("Owner", "Admin", "Member", "Viewer")]
    team = await team_with(owner, (admin, "admin"), (member, "member"), (viewer, "viewer"))
    ids = await add_contract(db, team, owner.id)
    from modules.analysis.models import Analysis
    db.add(Analysis(id=gen_uuid(), contract_id=ids["contract"], summary="s", risk_score=50, risk_level="medium"))
    await db.commit()

    routes = [
        "/contracts", "/contracts/stats", f"/contracts/{ids['contract']}",
        f"/analysis/contract/{ids['contract']}",
        "/obligations", "/obligations/stats", f"/obligations/{ids['obligation']}",
        "/alerts", "/alerts/stats",
        "/workspaces", f"/workspaces/{team}/members",
    ]
    for user in (owner, admin, member, viewer):
        for route in routes:
            r = await user.get(f"{API}{route}", ws=team)
            assert r.status_code == 200, f"{user.name} GET {route} -> {r.status_code} {r.text}"
        # and without the header (personal workspace)
        for route in ("/contracts/stats", "/obligations/stats", "/alerts/stats"):
            assert (await user.get(f"{API}{route}")).status_code == 200
