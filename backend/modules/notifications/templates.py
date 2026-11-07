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

def signature_request(signer_name, requester_name, filename, message, url, reissued=False):
    e = escape
    subject = f"{'New signing link' if reissued else 'Please sign'}: {filename}"
    heading = e(f"{requester_name} asked you to sign {filename}")
    paras = [f"Hi {e(signer_name)},"]
    if reissued:
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
