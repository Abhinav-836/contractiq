"""Built-in e-signature: send → every signer signs via their link, or one declines."""
import hashlib

import pytest
from sqlalchemy import select, update

from modules.contracts.models import Contract, ContractFile
from modules.signatures.models import SignatureEnvelope, SignatureEvent, SignatureSigner
from test_workspaces import API, add_contract, team_with

pytestmark = pytest.mark.asyncio(loop_scope="session")

PDF = b"%PDF-1.4 fake contract body"


async def setup_team(make_user, db):
    """Owner Alice, member Bob, viewer Vic, admin Ada, and one finished contract with its file."""
    alice, bob, vic, ada = [await make_user(n) for n in ("Alice", "Bob", "Vic", "Ada")]
    team = await team_with(alice, (bob, "member"), (vic, "viewer"), (ada, "admin"))
    cid = (await add_contract(db, team, alice.id, name="Supply agreement.pdf"))["contract"]
    db.add(ContractFile(contract_id=cid, data=PDF))
    await db.commit()
    return team, cid, alice, bob, vic, ada


SIGNERS = [
    {"name": "Priya  Sharma", "email": "Priya@Example.com"},
    {"name": "Bob", "email": "bob@example.com"},
]


async def send(user, team, cid, signers=SIGNERS, message="Please sign by Friday"):
    return await user.post(f"{API}/signatures/contract/{cid}", ws=team, json={"signers": signers, "message": message})


async def contract_status(db, cid):
    db.expire_all()
    return (await db.execute(select(Contract.signature_status).where(Contract.id == cid))).scalar()


def link_for(env, name):
    signer = next(s for s in env["signers"] if s["name"] == name)
    return env["links"][signer["id"]]


async def test_everyone_signs_and_certificate_has_audit_trail(make_user, db, client):
    team, cid, alice, bob, vic, _ = await setup_team(make_user, db)
    r = await send(alice, team, cid)
    assert r.status_code == 201, r.text
    env = r.json()
    assert env["status"] == "pending" and env["requested_by_name"] == "Alice"
    assert env["document_sha256"] == hashlib.sha256(PDF).hexdigest()
    assert env["document_filename"] == "Supply agreement.pdf"
    # Names are tidied, emails lower-cased; one link per signer, returned only now
    assert [s["name"] for s in env["signers"]] == ["Priya Sharma", "Bob"]
    assert env["signers"][0]["email"] == "priya@example.com"
    assert set(env["links"]) == {s["id"] for s in env["signers"]}
    assert await contract_status(db, cid) == "pending"
    assert (await alice.get(f"{API}/contracts", ws=team)).json()[0]["signature_status"] == "pending"
    listed = (await vic.get(f"{API}/signatures/contract/{cid}", ws=team)).json()
    assert listed[0]["links"] is None and listed[0]["can_manage"] is False

    # Token is only stored hashed
    db.expire_all()
    stored = (await db.execute(select(SignatureSigner.token_hash))).scalars().all()
    assert link_for(env, "Bob") not in stored

    priya = link_for(env, "Priya Sharma")
    hdrs = {"X-Forwarded-For": "1.2.3.4, 8.8.4.4, 10.0.0.1", "User-Agent": "TestBrowser/1.0"}
    # Public page, no login needed
    page = (await client.get(f"{API}/sign/{priya}", headers=hdrs)).json()
    assert page["signer"]["name"] == "Priya Sharma" and page["envelope_status"] == "pending"
    assert page["message"] == "Please sign by Friday" and page["requested_by_name"] == "Alice"
    assert [s["is_you"] for s in page["signers"]] == [True, False]
    assert "email" not in page["signers"][1]
    doc = await client.get(f"{API}/sign/{priya}/document")
    assert doc.status_code == 200 and doc.content == PDF and doc.headers["content-type"] == "application/pdf"

    # Must tick consent and type the exact name (case / spacing don't matter)
    r = await client.post(f"{API}/sign/{priya}/sign", json={"typed_name": "Priya Sharma", "consent": False})
    assert r.status_code == 422
    r = await client.post(f"{API}/sign/{priya}/sign", json={"typed_name": "P. Sharma", "consent": True})
    assert r.status_code == 422 and "Priya Sharma" in r.json()["detail"]
    r = await client.post(f"{API}/sign/{priya}/sign", headers=hdrs, json={"typed_name": " priya   SHARMA ", "consent": True})
    assert r.status_code == 200, r.text
    assert r.json()["signer"]["status"] == "signed" and r.json()["envelope_status"] == "pending"
    # Can't sign twice
    assert (await client.post(f"{API}/sign/{priya}/sign", json={"typed_name": "Priya Sharma", "consent": True})).status_code == 409

    r = await client.post(f"{API}/sign/{link_for(env, 'Bob')}/sign", json={"typed_name": "bob", "consent": True})
    assert r.json()["envelope_status"] == "completed"
    assert await contract_status(db, cid) == "completed"

    # Any workspace member, viewers included, can open the certificate
    cert = (await vic.get(f"{API}/signatures/{env['id']}", ws=team)).json()
    assert cert["status"] == "completed" and cert["signed_count"] == 2 and cert["closed_at"]
    p = cert["signers"][0]
    # Rightmost public address in X-Forwarded-For (private proxy hops skipped, spoofed left entry ignored)
    assert p["ip_address"] == "8.8.4.4" and p["user_agent"] == "TestBrowser/1.0"
    assert p["typed_signature"] == "priya SHARMA" and "electronic signature" in p["consent_text"]
    assert p["viewed_at"] and p["acted_at"]
    assert [e["type"] for e in cert["events"]] == ["created", "viewed", "signed", "signed", "completed"]

    # Closed: the link still shows the outcome but can't act
    page = (await client.get(f"{API}/sign/{priya}")).json()
    assert page["envelope_status"] == "completed"
    assert (await alice.post(f"{API}/signatures/{env['id']}/cancel", ws=team)).status_code == 409


async def test_decline_closes_request_and_needs_reason(make_user, db, client):
    team, cid, alice, *_ = await setup_team(make_user, db)
    env = (await send(alice, team, cid)).json()
    priya, bob = link_for(env, "Priya Sharma"), link_for(env, "Bob")
    assert (await client.post(f"{API}/sign/{priya}/decline", json={"reason": "  "})).status_code == 422
    r = await client.post(f"{API}/sign/{priya}/decline", json={"reason": "Payment terms are wrong"})
    assert r.status_code == 200 and r.json()["envelope_status"] == "declined"
    assert await contract_status(db, cid) == "declined"
    # Others can no longer sign
    r = await client.post(f"{API}/sign/{bob}/sign", json={"typed_name": "Bob", "consent": True})
    assert r.status_code == 409 and "declined" in r.json()["detail"]
    cert = (await alice.get(f"{API}/signatures/{env['id']}", ws=team)).json()
    assert cert["signers"][0]["decline_reason"] == "Payment terms are wrong"
    # A new request can be sent after a decline
    assert (await send(alice, team, cid)).status_code == 201


async def test_permissions_and_validation(make_user, db):
    team, cid, alice, bob, vic, ada = await setup_team(make_user, db)
    outsider = await make_user("Mallory")

    # Viewers can't send; outsiders can't see the contract
    assert (await send(vic, team, cid)).status_code == 403
    assert (await send(outsider, team, cid)).status_code in (403, 404)
    assert (await outsider.get(f"{API}/signatures/contract/{cid}", ws=team)).status_code in (403, 404)

    # Validation
    r = await send(bob, team, cid, signers=[{"name": "A", "email": "a@x.com"}, {"name": "B", "email": "A@x.com"}])
    assert r.status_code == 422 and "twice" in r.json()["detail"]
    assert (await send(bob, team, cid, signers=[])).status_code == 422
    assert (await send(bob, team, cid, signers=[{"name": "A", "email": "not-an-email"}])).status_code == 422
    many = [{"name": f"P{i}", "email": f"p{i}@x.com"} for i in range(11)]
    assert (await send(bob, team, cid, signers=many)).status_code == 422

    # Contract must be reviewed and must have its file
    await db.execute(update(Contract).where(Contract.id == cid).values(status="processing"))
    await db.commit()
    r = await send(bob, team, cid)
    assert r.status_code == 409 and "review" in r.json()["detail"]
    await db.execute(update(Contract).where(Contract.id == cid).values(status="completed"))
    await db.commit()
    other = (await add_contract(db, team, alice.id, name="nofile.pdf"))["contract"]
    r = await send(bob, team, other)
    assert r.status_code == 409 and "missing" in r.json()["detail"]

    # A member sends; only one open request per contract
    env = (await send(bob, team, cid)).json()
    assert env["can_manage"] is True
    r = await send(alice, team, cid)
    assert r.status_code == 409 and "already out for signing" in r.json()["detail"]

    # Another member who isn't the sender can't cancel; an admin can
    carol = await make_user("Carol")
    team_inv = (await alice.post(f"{API}/workspaces/{team}/invites", json={"role": "member"})).json()["token"]
    await carol.post(f"{API}/invites/{team_inv}/accept")
    assert (await carol.post(f"{API}/signatures/{env['id']}/cancel", ws=team)).status_code == 403
    r = await ada.post(f"{API}/signatures/{env['id']}/cancel", ws=team)
    assert r.status_code == 200 and r.json()["status"] == "cancelled"
    # Cancelled requests don't count toward the contract's status
    assert await contract_status(db, cid) is None


async def test_new_link_replaces_old_and_cancel_kills_links(make_user, db, client):
    team, cid, alice, bob, *_ = await setup_team(make_user, db)
    env = (await send(bob, team, cid)).json()
    old = link_for(env, "Priya Sharma")
    signer_id = next(s["id"] for s in env["signers"] if s["name"] == "Priya Sharma")

    r = await bob.post(f"{API}/signatures/{env['id']}/signers/{signer_id}/link", ws=team)
    assert r.status_code == 200
    new = r.json()["links"][signer_id]
    assert new != old
    assert (await client.get(f"{API}/sign/{old}")).status_code == 404
    assert (await client.get(f"{API}/sign/{new}")).status_code == 200
    assert (await client.get(f"{API}/sign/not-a-real-token")).status_code == 404

    # Can't reissue for someone who already signed
    await client.post(f"{API}/sign/{new}/sign", json={"typed_name": "Priya Sharma", "consent": True})
    assert (await bob.post(f"{API}/signatures/{env['id']}/signers/{signer_id}/link", ws=team)).status_code == 409

    await bob.post(f"{API}/signatures/{env['id']}/cancel", ws=team)
    bob_link = link_for(env, "Bob")
    assert (await client.get(f"{API}/sign/{bob_link}")).json()["envelope_status"] == "cancelled"
    assert (await client.get(f"{API}/sign/{bob_link}/document")).status_code == 410
    assert (await client.post(f"{API}/sign/{bob_link}/sign", json={"typed_name": "Bob", "consent": True})).status_code == 409
    events = (await alice.get(f"{API}/signatures/{env['id']}", ws=team)).json()["events"]
    assert [e["type"] for e in events] == ["created", "link_reissued", "viewed", "signed", "cancelled"]


async def test_changed_document_cannot_be_signed(make_user, db, client):
    team, cid, alice, *_ = await setup_team(make_user, db)
    env = (await send(alice, team, cid)).json()
    await db.execute(update(ContractFile).where(ContractFile.contract_id == cid).values(data=b"tampered"))
    await db.commit()
    r = await client.post(f"{API}/sign/{link_for(env, 'Bob')}/sign", json={"typed_name": "Bob", "consent": True})
    assert r.status_code == 409 and "changed" in r.json()["detail"]


async def test_deleting_contract_removes_signatures(make_user, db, client):
    team, cid, alice, *_ = await setup_team(make_user, db)
    env = (await send(alice, team, cid)).json()
    assert (await alice.delete(f"{API}/contracts/{cid}", ws=team)).status_code in (200, 204)
    db.expire_all()
    assert (await db.execute(select(SignatureEnvelope).where(SignatureEnvelope.id == env["id"]))).first() is None
    for model in (SignatureSigner, SignatureEvent):
        assert (await db.execute(select(model).where(model.envelope_id == env["id"]))).first() is None
    assert (await client.get(f"{API}/sign/{link_for(env, 'Bob')}")).status_code == 404


async def test_other_workspace_cannot_reach_envelope(make_user, db):
    team, cid, alice, *_ = await setup_team(make_user, db)
    env = (await send(alice, team, cid)).json()
    mallory = await make_user("Mallory")
    # Mallory's personal workspace
    assert (await mallory.get(f"{API}/signatures/{env['id']}")).status_code == 404
    assert (await mallory.post(f"{API}/signatures/{env['id']}/cancel")).status_code == 404


def test_client_ip_skips_cloudflare_and_private_hops():
    from types import SimpleNamespace
    from modules.signatures.service import client_info

    def req(headers):
        return SimpleNamespace(headers={k.lower(): v for k, v in headers.items()}, client=SimpleNamespace(host="10.0.0.9"))

    # What Render produced live: visitor, then a Cloudflare edge, then an internal hop
    xff = {"X-Forwarded-For": "1.2.3.4, 49.36.10.20, 104.23.160.38, 10.0.0.1"}
    assert client_info(req(xff))[0] == "49.36.10.20"
    # Cloudflare's own header wins when present
    assert client_info(req({**xff, "CF-Connecting-IP": "49.36.99.1"}))[0] == "49.36.99.1"
    assert client_info(req({"X-Forwarded-For": "172.69.94.197"}))[0] == "172.69.94.197"  # nothing better available
    assert client_info(req({}))[0] == "10.0.0.9"


def _real_pdf(pages=2) -> bytes:
    import io
    from reportlab.pdfgen import canvas
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    for i in range(pages):
        c.drawString(72, 720, f"Contract page {i + 1}")
        c.showPage()
    c.save()
    return buf.getvalue()


async def _complete(client, env):
    for s in env["signers"]:
        r = await client.post(f"{API}/sign/{env['links'][s['id']]}/sign", json={"typed_name": s["name"], "consent": True})
        assert r.status_code == 200, r.text


@pytest.mark.parametrize("name,body,original_pages", [
    ("Supply agreement.pdf", None, 2),                      # real PDF: pages kept + stamped
    ("Notes.txt", "Line one\nLine two " + "x" * 200, 1),   # text typeset onto a page
    ("Broken.pdf", b"%PDF-1.4 not really a pdf", 0),       # unreadable: certificate + attachment only
    ("Offer.docx", b"PK\x03\x04 fake docx", 0),            # docx: certificate + attachment only
])
async def test_signed_pdf_download(make_user, db, client, name, body, original_pages):
    import io
    from pypdf import PdfReader

    team, cid, alice, bob, vic, _ = await setup_team(make_user, db)
    data = _real_pdf() if body is None else (body.encode() if isinstance(body, str) else body)
    await db.execute(update(Contract).where(Contract.id == cid).values(filename=name))
    await db.execute(update(ContractFile).where(ContractFile.contract_id == cid).values(data=data))
    await db.commit()
    env = (await send(alice, team, cid)).json()

    # Not available until everyone has signed
    r = await alice.get(f"{API}/signatures/{env['id']}/signed-pdf", ws=team)
    assert r.status_code == 409
    assert (await client.get(f"{API}/sign/{link_for(env, 'Bob')}/signed-pdf")).status_code == 409

    await _complete(client, env)
    r = await vic.get(f"{API}/signatures/{env['id']}/signed-pdf", ws=team)  # viewers can download
    assert r.status_code == 200, r.text
    assert r.headers["content-type"] == "application/pdf"
    assert "%28signed%29.pdf" in r.headers["content-disposition"]
    pdf = PdfReader(io.BytesIO(r.content))
    text = "\n".join(p.extract_text() or "" for p in pdf.pages)
    assert "SIGNATURE CERTIFICATE" in text and env["id"] in text and env["document_sha256"] in text
    assert "Priya Sharma" in text and "Audit trail" in text
    assert len(pdf.pages) >= original_pages + 1
    if original_pages:
        first = pdf.pages[0].extract_text()
        assert "Signed electronically with ContractIQ" in first
    if name == "Supply agreement.pdf":
        assert "Contract page 1" in pdf.pages[0].extract_text() and "Contract page 2" in pdf.pages[1].extract_text()
    # The original is attached byte for byte
    assert pdf.attachments[name] == [data]

    # Each signer can download it from their link too
    r = await client.get(f"{API}/sign/{link_for(env, 'Priya Sharma')}/signed-pdf")
    assert r.status_code == 200 and r.content[:4] == b"%PDF"


async def test_signed_pdf_needs_workspace_access(make_user, db, client):
    team, cid, alice, *_ = await setup_team(make_user, db)
    env = (await send(alice, team, cid)).json()
    await _complete(client, env)
    mallory = await make_user("Mallory")
    assert (await mallory.get(f"{API}/signatures/{env['id']}/signed-pdf")).status_code == 404
    assert (await client.get(f"{API}/sign/not-a-token/signed-pdf")).status_code == 404
