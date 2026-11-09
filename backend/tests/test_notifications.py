"""Email notifications: signing links, completion/decline, approvals, caps, providers."""
import base64
import json
import re

import httpx
import pytest
from sqlalchemy import select, update

from core.config import settings
from modules.contracts.models import Contract, ContractFile
from modules.notifications import mailer, templates
from modules.notifications.models import EmailLog
from test_signatures import PDF, _real_pdf
from test_signatures import setup_team as signing_team
from test_workspaces import API

pytestmark = pytest.mark.asyncio(loop_scope="session")

TOKEN_IN_URL = re.compile(r"/sign/([A-Za-z0-9_\-]+)")


@pytest.fixture
def outbox(monkeypatch):
    """Send email through the in-memory provider and give the test its outbox."""
    monkeypatch.setattr(settings, "EMAIL_PROVIDER", "memory")
    monkeypatch.setattr(settings, "APP_URL", "https://app.example.com")
    mailer.OUTBOX.clear()
    yield mailer.OUTBOX
    mailer.OUTBOX.clear()


async def email_of(user) -> str:
    return (await user.get(f"{API}/auth/me")).json()["email"]


def to(outbox, address):
    return [m for m in outbox if m["to"] == address]


async def send(user, team, cid, signers, **extra):
    r = await user.post(f"{API}/signatures/contract/{cid}", ws=team, json={"signers": signers, **extra})
    assert r.status_code == 201, r.text
    return r.json()


SIGNERS = [{"name": "Priya Sharma", "email": "priya@vendor.in"}, {"name": "Ravi Kumar", "email": "ravi@vendor.in"}]


async def test_features_endpoint(client, monkeypatch):
    monkeypatch.setattr(settings, "EMAIL_PROVIDER", "none")
    assert (await client.get(f"{API}/features")).json()["email"] is False
    monkeypatch.setattr(settings, "EMAIL_PROVIDER", "brevo")
    monkeypatch.setattr(settings, "BREVO_API_KEY", None)
    assert (await client.get(f"{API}/features")).json()["email"] is False  # half set up = off
    monkeypatch.setattr(settings, "BREVO_API_KEY", "key")
    monkeypatch.setattr(settings, "EMAIL_FROM", "me@example.com")
    assert (await client.get(f"{API}/features")).json()["email"] is True


async def test_signing_links_are_emailed(make_user, db, client, outbox):
    team, cid, alice, *_ = await signing_team(make_user, db)
    env = await send(alice, team, cid, SIGNERS, message="Please sign <b>by Friday</b>")
    assert env["emailed"] is True and set(env["links"])  # links are still returned as a backup

    priya = to(outbox, "priya@vendor.in")
    assert len(priya) == 1 and len(outbox) == 2
    mail = priya[0]
    assert mail["subject"] == "Please sign: Supply agreement.pdf"
    assert mail["reply_to"] == await email_of(alice)
    # The emailed link is the signer's own working link
    token = TOKEN_IN_URL.search(mail["text"]).group(1)
    page = (await client.get(f"{API}/sign/{token}")).json()
    assert page["signer"]["name"] == "Priya Sharma"
    assert mail["html"].count("https://app.example.com/sign/") >= 1
    # User text is escaped in HTML
    assert "<b>by Friday</b>" not in mail["html"] and "&lt;b&gt;by Friday&lt;/b&gt;" in mail["html"]

    # Status shows per signer, and the audit trail records the email
    cert = (await alice.get(f"{API}/signatures/{env['id']}", ws=team)).json()
    assert [s["email_status"] for s in cert["signers"]] == ["sent", "sent"]
    emailed = [e for e in cert["events"] if e["type"] == "emailed"]
    assert len(emailed) == 2 and "priya@vendor.in" in emailed[0]["detail"] + emailed[1]["detail"]


async def test_send_email_false_and_email_off(make_user, db, outbox, monkeypatch):
    team, cid, alice, *_ = await signing_team(make_user, db)
    env = await send(alice, team, cid, SIGNERS, send_email=False)
    assert env["emailed"] is False and outbox == []
    await alice.post(f"{API}/signatures/{env['id']}/cancel", ws=team)

    monkeypatch.setattr(settings, "EMAIL_PROVIDER", "none")
    env = await send(alice, team, cid, SIGNERS)
    assert env["emailed"] is False and outbox == [] and len(env["links"]) == 2
    cert = (await alice.get(f"{API}/signatures/{env['id']}", ws=team)).json()
    assert [s["email_status"] for s in cert["signers"]] == [None, None]


async def test_new_link_is_emailed(make_user, db, client, outbox):
    team, cid, alice, *_ = await signing_team(make_user, db)
    env = await send(alice, team, cid, SIGNERS)
    priya_id = next(s["id"] for s in env["signers"] if s["name"] == "Priya Sharma")
    outbox.clear()
    r = await alice.post(f"{API}/signatures/{env['id']}/signers/{priya_id}/link", ws=team)
    assert r.json()["emailed"] is True
    assert len(outbox) == 1 and outbox[0]["subject"].startswith("New signing link")
    new_token = TOKEN_IN_URL.search(outbox[0]["text"]).group(1)
    assert new_token == r.json()["links"][priya_id]
    # Not emailed when asked not to
    outbox.clear()
    r = await alice.post(f"{API}/signatures/{env['id']}/signers/{priya_id}/link?send_email=false", ws=team)
    assert r.json()["emailed"] is False and outbox == []


async def test_completion_emails_attach_the_signed_pdf(make_user, db, client, outbox):
    team, cid, alice, *_ = await signing_team(make_user, db)
    await db.execute(update(ContractFile).where(ContractFile.contract_id == cid).values(data=_real_pdf()))
    await db.commit()
    env = await send(alice, team, cid, SIGNERS)
    tokens = {m["to"]: TOKEN_IN_URL.search(m["text"]).group(1) for m in outbox}
    outbox.clear()

    await client.post(f"{API}/sign/{tokens['priya@vendor.in']}/sign", json={"typed_name": "Priya Sharma", "consent": True})
    assert outbox == []  # nothing until everyone has signed
    await client.post(f"{API}/sign/{tokens['ravi@vendor.in']}/sign", json={"typed_name": "Ravi Kumar", "consent": True})

    alice_email = await email_of(alice)
    assert {m["to"] for m in outbox} == {alice_email, "priya@vendor.in", "ravi@vendor.in"}
    for m in outbox:
        assert m["subject"] == "Signed by everyone: Supply agreement.pdf"
        assert m["attachments"] and m["attachments"][0][0] == "Supply agreement (signed).pdf"
        assert m["attachments"][0][1] > 1000
    # Only the sender gets a link to the certificate page
    assert f"https://app.example.com/signatures/{env['id']}" in to(outbox, alice_email)[0]["text"]
    assert "/signatures/" not in to(outbox, "priya@vendor.in")[0]["text"]


async def test_decline_emails_the_sender(make_user, db, client, outbox):
    team, cid, alice, *_ = await signing_team(make_user, db)
    await send(alice, team, cid, SIGNERS)
    token = TOKEN_IN_URL.search(to(outbox, "ravi@vendor.in")[0]["text"]).group(1)
    outbox.clear()
    await client.post(f"{API}/sign/{token}/decline", json={"reason": "Clause 7 caps liability too low"})
    assert len(outbox) == 1
    m = outbox[0]
    assert m["to"] == await email_of(alice) and m["subject"] == "Declined: Supply agreement.pdf"
    assert "Clause 7 caps liability too low" in m["text"] and m["reply_to"] == "ravi@vendor.in"
    assert f"https://app.example.com/contracts/{cid}" in m["text"]


async def test_failed_send_never_breaks_the_action(make_user, db, outbox, monkeypatch):
    async def broken(*args, **kwargs):
        return mailer.SendResult(False, "brevo", error="HTTP 401: Key not found")

    monkeypatch.setattr(mailer, "send_email", broken)
    team, cid, alice, *_ = await signing_team(make_user, db)
    env = await send(alice, team, cid, SIGNERS)  # still 201
    cert = (await alice.get(f"{API}/signatures/{env['id']}", ws=team)).json()
    assert [s["email_status"] for s in cert["signers"]] == ["failed", "failed"]
    assert cert["signers"][0]["email_error"] == "HTTP 401: Key not found"
    assert not [e for e in cert["events"] if e["type"] == "emailed"]


async def test_daily_cap_per_workspace(make_user, db, outbox, monkeypatch):
    monkeypatch.setattr(settings, "EMAIL_DAILY_LIMIT_PER_WORKSPACE", 1)
    team, cid, alice, *_ = await signing_team(make_user, db)
    env = await send(alice, team, cid, SIGNERS)
    assert len(outbox) == 1  # second email held back
    cert = (await alice.get(f"{API}/signatures/{env['id']}", ws=team)).json()
    assert sorted(s["email_status"] for s in cert["signers"]) == ["sent", "skipped"]
    db.expire_all()
    skipped = (await db.execute(select(EmailLog).where(EmailLog.status == "skipped"))).scalars().all()
    assert any("workspace" in (s.error or "") for s in skipped)


# ── Approvals ─────────────────────────────────────────────────────────────

async def test_approval_emails(make_user, db, outbox):
    from test_approvals import request as ask, setup_team as approval_team

    team, cid, alice, bob, vic, (carol,) = await approval_team(make_user, db, ("Carol", "admin"))
    r = await ask(alice, team, cid, [bob, carol], note="Check the <indemnity> clause")
    assert r.status_code == 201
    req_id = r.json()["id"]
    bob_email, carol_email, alice_email = await email_of(bob), await email_of(carol), await email_of(alice)
    assert {m["to"] for m in outbox} == {bob_email, carol_email}
    m = to(outbox, bob_email)[0]
    assert m["subject"].startswith("Approval needed:") and m["reply_to"] == alice_email
    assert f"https://app.example.com/contracts/{cid}" in m["text"]
    assert "&lt;indemnity&gt;" in m["html"]

    outbox.clear()
    await bob.post(f"{API}/approvals/{req_id}/decision", ws=team, json={"decision": "approved"})
    assert outbox == []  # still waiting for Carol
    await carol.post(f"{API}/approvals/{req_id}/decision", ws=team,
                     json={"decision": "rejected", "comment": "Liability cap missing"})
    assert len(outbox) == 1 and outbox[0]["to"] == alice_email
    assert outbox[0]["subject"].startswith("Rejected:") and "Liability cap missing" in outbox[0]["text"]

    # A fully approved request
    await db.execute(update(Contract).where(Contract.id == cid).values(approval_status=None))
    await db.commit()
    outbox.clear()
    req_id = (await ask(alice, team, cid, [bob])).json()["id"]
    outbox.clear()
    await bob.post(f"{API}/approvals/{req_id}/decision", ws=team, json={"decision": "approved"})
    assert [m["subject"] for m in outbox] == [f"Approved: {(await db.get(Contract, cid)).filename}"]


# ── Providers ─────────────────────────────────────────────────────────────

def _client(handler):
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


async def test_brevo_request(monkeypatch):
    monkeypatch.setattr(settings, "EMAIL_PROVIDER", "brevo")
    monkeypatch.setattr(settings, "BREVO_API_KEY", "xkeysib-test")
    monkeypatch.setattr(settings, "EMAIL_FROM", "abhinav@example.com")
    seen = {}

    def handler(req: httpx.Request):
        seen["url"], seen["key"], seen["body"] = str(req.url), req.headers["api-key"], json.loads(req.content)
        return httpx.Response(201, json={"messageId": "<abc@smtp-relay>"})

    async with _client(handler) as c:
        res = await mailer.send_email("p@x.com", "Priya", "Hi", "<p>Hi</p>", "Hi", reply_to="a@x.com",
                                      client=c, attachments=[("doc.pdf", PDF)])
    assert res.ok and res.message_id == "<abc@smtp-relay>"
    assert seen["url"] == mailer.BREVO_URL and seen["key"] == "xkeysib-test"
    body = seen["body"]
    assert body["sender"] == {"name": "ContractIQ", "email": "abhinav@example.com"}
    assert body["to"] == [{"email": "p@x.com", "name": "Priya"}] and body["replyTo"] == {"email": "a@x.com"}
    assert base64.b64decode(body["attachment"][0]["content"]) == PDF and body["attachment"][0]["name"] == "doc.pdf"

    async with _client(lambda req: httpx.Response(401, json={"code": "unauthorized", "message": "Key not found"})) as c:
        res = await mailer.send_email("p@x.com", None, "Hi", "<p>Hi</p>", "Hi", client=c)
    assert not res.ok and res.error == "HTTP 401: Key not found"


async def test_resend_request(monkeypatch):
    monkeypatch.setattr(settings, "EMAIL_PROVIDER", "resend")
    monkeypatch.setattr(settings, "RESEND_API_KEY", "re_test")
    monkeypatch.setattr(settings, "EMAIL_FROM", "noreply@contractiq.app")
    seen = {}

    def handler(req: httpx.Request):
        seen["auth"], seen["body"] = req.headers["authorization"], json.loads(req.content)
        return httpx.Response(200, json={"id": "re_123"})

    async with _client(handler) as c:
        res = await mailer.send_email("p@x.com", "Priya", "Hi", "<p>Hi</p>", "Hi", client=c,
                                      attachments=[("doc.pdf", PDF)])
    assert res.ok and res.message_id == "re_123" and seen["auth"] == "Bearer re_test"
    assert seen["body"]["from"] == "ContractIQ <noreply@contractiq.app>" and seen["body"]["to"] == ["p@x.com"]
    assert seen["body"]["attachments"][0]["filename"] == "doc.pdf"

    def boom(req):
        raise httpx.ConnectError("no route")

    async with _client(boom) as c:
        res = await mailer.send_email("p@x.com", None, "Hi", "<p>Hi</p>", "Hi", client=c)
    assert not res.ok and "ConnectError" in res.error


async def test_not_configured_sends_nothing(monkeypatch):
    monkeypatch.setattr(settings, "EMAIL_PROVIDER", "brevo")
    monkeypatch.setattr(settings, "BREVO_API_KEY", None)
    res = await mailer.send_email("p@x.com", None, "Hi", "<p>Hi</p>", "Hi")
    assert not res.ok and "isn't set up" in res.error


async def test_templates_escape_user_text():
    _, html, text = templates.signature_request(
        "<img src=x onerror=alert(1)>", "Eve <script>", "a<b>.pdf", "</p><a href='evil'>", "https://app/sign/t"
    )
    assert "<script>" not in html and "<img" not in html and "href='evil'" not in html
    assert "https://app/sign/t" in html and "https://app/sign/t" in text
