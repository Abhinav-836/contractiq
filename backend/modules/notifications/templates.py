"""
Email bodies. Every value that came from a user (names, file names,
messages, reasons) is HTML-escaped here; plain-text versions go alongside.
"""
from html import escape
from typing import Optional

BRAND = "#4338ca"


def _layout(heading: str, paragraphs: list[str], button: Optional[tuple[str, str]], footer: str) -> str:
    body = "".join(f'<p style="margin:0 0 14px;line-height:1.55;">{p}</p>' for p in paragraphs)
    btn = ""
    if button:
        label, url = button
        btn = (
            f'<p style="margin:22px 0;"><a href="{escape(url, quote=True)}" '
            f'style="background:{BRAND};color:#ffffff;text-decoration:none;padding:12px 20px;'
            f'border-radius:8px;font-weight:600;display:inline-block;">{escape(label)}</a></p>'
            f'<p style="margin:0 0 14px;font-size:12px;color:#6b7280;line-height:1.5;">'
            f'Or open this link: <a href="{escape(url, quote=True)}" style="color:{BRAND};word-break:break-all;">'
            f'{escape(url)}</a></p>'
        )
    return (
        '<!doctype html><html><body style="margin:0;background:#f4f4f5;">'
        '<div style="max-width:560px;margin:0 auto;padding:28px 16px;font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif;color:#18181b;">'
        f'<p style="margin:0 0 18px;font-weight:700;font-size:15px;color:{BRAND};">ContractIQ</p>'
        '<div style="background:#ffffff;border:1px solid #e4e4e7;border-radius:12px;padding:24px;">'
        f'<h1 style="margin:0 0 16px;font-size:20px;line-height:1.3;">{heading}</h1>{body}{btn}</div>'
        f'<p style="margin:16px 4px 0;font-size:12px;color:#71717a;line-height:1.5;">{footer}</p>'
        '</div></body></html>'
    )


def _text(lines: list[str]) -> str:
    return "\n\n".join(line for line in lines if line) + "\n"


# ── Signatures ────────────────────────────────────────────────────────────

def signature_request(signer_name, requester_name, filename, message, url, reissued=False, reminder=False):
    e = escape
    subject = f"{'Reminder: please sign' if reminder else 'New signing link' if reissued else 'Please sign'}: {filename}"
    heading = e(f"{requester_name} asked you to sign {filename}")
    paras = [f"Hi {e(signer_name)},"]
    if reminder:
        paras.append(f"A reminder that <strong>{e(requester_name)}</strong> is waiting for your signature on "
                     f"<strong>{e(filename)}</strong>. Here is a fresh link — any earlier link no longer works.")
    elif reissued:
        paras.append("Here is a new signing link. Any earlier link for this document no longer works.")
    else:
        paras.append(f"<strong>{e(requester_name)}</strong> has asked you to review and sign "
                     f"<strong>{e(filename)}</strong>. You don't need an account.")
    if message:
        paras.append(f'<span style="display:block;border-left:3px solid #e4e4e7;padding-left:12px;color:#3f3f46;">'
                     f'{e(message)}</span>')
    paras.append("Open the link, read the document, then type your name to sign — or decline with a reason.")
    footer = ("This link is private to you, so please don't forward it. "
              "If you weren't expecting this email, you can ignore it.")
    html = _layout(heading, paras, ("Review and sign", url), footer)
    text = _text([
        f"Hi {signer_name},",
        f"A reminder that {requester_name} is waiting for your signature on \"{filename}\". "
        "Here is a fresh link; any earlier link no longer works." if reminder else
        "Here is a new signing link. Any earlier link no longer works." if reissued
        else f"{requester_name} has asked you to review and sign \"{filename}\". You don't need an account.",
        f"Message: {message}" if message else "",
        f"Open this private link to read and sign it:\n{url}",
        "Please don't forward this link. If you weren't expecting this email, you can ignore it.",
    ])
    return subject, html, text


def signature_completed(recipient_name, filename, url, is_requester, attached):
    """url is the certificate page for the requester, None for outside signers."""
    e = escape
    subject = f"Signed by everyone: {filename}"
    paras = [f"Hi {e(recipient_name)},", f"Everyone has signed <strong>{e(filename)}</strong>."]
    if attached:
        paras.append("Your signed copy is attached: the original document, then the signature certificate "
                     "with every signature and the full audit trail.")
    elif is_requester:
        paras.append("The signed PDF and the signature certificate are ready in ContractIQ.")
    else:
        paras.append("Ask the sender for the signed copy.")
    button = ("View certificate", url) if (is_requester and url) else None
    html = _layout(e(f"{filename} is fully signed"), paras, button,
                   "Keep this email as your record of the signed document.")
    text = _text([f"Hi {recipient_name},", f"Everyone has signed \"{filename}\".",
                  "Your signed copy is attached." if attached else "",
                  f"View the certificate: {url}" if (is_requester and url) else ""])
    return subject, html, text


def signature_declined(requester_name, signer_name, filename, reason, url):
    e = escape
    subject = f"Declined: {filename}"
    paras = [f"Hi {e(requester_name)},",
             f"<strong>{e(signer_name)}</strong> declined to sign <strong>{e(filename)}</strong>, "
             "so the signing request is closed.",
             f'Their reason: <span style="display:block;border-left:3px solid #fecaca;padding-left:12px;'
             f'margin-top:6px;color:#3f3f46;">{e(reason)}</span>',
             "You can update the contract and send it for signing again."]
    html = _layout(e(f"{signer_name} declined to sign"), paras, ("Open the contract", url),
                   "You're receiving this because you sent this document for signing.")
    text = _text([f"Hi {requester_name},", f"{signer_name} declined to sign \"{filename}\".",
                  f"Reason: {reason}", f"Open the contract: {url}"])
    return subject, html, text


# ── Approvals ─────────────────────────────────────────────────────────────

def approval_requested(reviewer_name, requester_name, filename, note, url):
    e = escape
    subject = f"Approval needed: {filename}"
    paras = [f"Hi {e(reviewer_name)},",
             f"<strong>{e(requester_name)}</strong> asked you to approve <strong>{e(filename)}</strong>."]
    if note:
        paras.append(f'<span style="display:block;border-left:3px solid #e4e4e7;padding-left:12px;color:#3f3f46;">'
                     f'{e(note)}</span>')
    paras.append("Open the contract to read the review, then approve or reject it.")
    html = _layout(e(f"Approval needed: {filename}"), paras, ("Review and decide", url),
                   "You're receiving this because you were picked as a reviewer in ContractIQ.")
    text = _text([f"Hi {reviewer_name},", f"{requester_name} asked you to approve \"{filename}\".",
                  f"Note: {note}" if note else "", f"Review and decide: {url}"])
    return subject, html, text


def approval_decided(requester_name, filename, status, decided_by, comment, url):
    e = escape
    approved = status == "approved"
    subject = f"{'Approved' if approved else 'Rejected'}: {filename}"
    paras = [f"Hi {e(requester_name)},"]
    if approved:
        paras.append(f"Every reviewer approved <strong>{e(filename)}</strong>.")
    else:
        paras.append(f"<strong>{e(decided_by)}</strong> rejected <strong>{e(filename)}</strong>.")
        if comment:
            paras.append(f'Their reason: <span style="display:block;border-left:3px solid #fecaca;'
                         f'padding-left:12px;margin-top:6px;color:#3f3f46;">{e(comment)}</span>')
    html = _layout(e(subject), paras, ("Open the contract", url),
                   "You're receiving this because you asked for this approval in ContractIQ.")
    text = _text([f"Hi {requester_name},",
                  f"Every reviewer approved \"{filename}\"." if approved
                  else f"{decided_by} rejected \"{filename}\".",
                  f"Reason: {comment}" if (comment and not approved) else "",
                  f"Open the contract: {url}"])
    return subject, html, text


# ── Team invites ──────────────────────────────────────────────────────────

def workspace_invite(inviter_name, workspace_name, role, url, expires_label):
    e = escape
    role_label = {"admin": "an admin", "member": "a member", "viewer": "a viewer"}.get(role, role)
    subject = f"{inviter_name} invited you to {workspace_name} on ContractIQ"
    paras = [f"<strong>{e(inviter_name)}</strong> invited you to join <strong>{e(workspace_name)}</strong> "
             f"on ContractIQ as {e(role_label)}.",
             "ContractIQ reviews contracts with AI and lets a team approve and sign them together. "
             "Accept the invite to create an account (or sign in) and join.",
             f"The invite expires {e(expires_label)}."]
    html = _layout(e(f"Join {workspace_name} on ContractIQ"), paras, ("Accept invite", url),
                   "If you weren't expecting this, you can ignore it — nothing happens unless you accept.")
    text = _text([f"{inviter_name} invited you to join \"{workspace_name}\" on ContractIQ as {role_label}.",
                  f"Accept the invite: {url}", f"The invite expires {expires_label}."])
    return subject, html, text


# ── Account ───────────────────────────────────────────────────────────────

def verify_email(name, url):
    e = escape
    subject = "Confirm your email for ContractIQ"
    paras = [f"Hi {e(name)},",
             "Confirm this is your email address so you can send signing requests and invites from ContractIQ.",
             "The link works for 48 hours."]
    html = _layout("Confirm your email", paras, ("Confirm email", url),
                   "If you didn't create a ContractIQ account or change your email, you can ignore this.")
    text = _text([f"Hi {name},", "Confirm this is your email address for ContractIQ:", url,
                  "The link works for 48 hours. If this wasn't you, ignore this email."])
    return subject, html, text


def password_reset(name, url):
    e = escape
    subject = "Reset your ContractIQ password"
    paras = [f"Hi {e(name)},",
             "Someone (hopefully you) asked to reset the password for your ContractIQ account.",
             "The link works for 30 minutes and only once."]
    html = _layout("Reset your password", paras, ("Choose a new password", url),
                   "If you didn't ask for this, ignore this email — your password stays the same.")
    text = _text([f"Hi {name},", "Reset your ContractIQ password with this link (works for 30 minutes, once):", url,
                  "If you didn't ask for this, ignore this email — your password stays the same."])
    return subject, html, text


def email_changed(name, old_email, new_email):
    e = escape
    subject = "Your ContractIQ email was changed"
    paras = [f"Hi {e(name)},",
             f"The sign-in email for your ContractIQ account was changed from <strong>{e(old_email)}</strong> "
             f"to <strong>{e(new_email)}</strong>.",
             "If you did this, there's nothing to do. If you didn't, someone may have your password — "
             "reply to this email or contact the workspace owner straight away."]
    html = _layout("Your sign-in email changed", paras, None,
                   "This was sent to your old address so you know about the change.")
    text = _text([f"Hi {name},", f"Your ContractIQ sign-in email was changed from {old_email} to {new_email}.",
                  "If this wasn't you, someone may have your password. Act straight away."])
    return subject, html, text


def password_changed(name):
    e = escape
    subject = "Your ContractIQ password was changed"
    paras = [f"Hi {e(name)},", "The password for your ContractIQ account was just changed.",
             "If this wasn't you, reset it straight away with “Forgot password” on the sign-in page."]
    html = _layout("Your password changed", paras, None, "Sent so you know about changes to your account.")
    text = _text([f"Hi {name},", "Your ContractIQ password was just changed.",
                  "If this wasn't you, reset it with “Forgot password” on the sign-in page."])
    return subject, html, text
