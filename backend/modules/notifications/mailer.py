"""
Sends one email through the configured provider.

Render's free plan blocks outbound SMTP (ports 25/465/587), so real
providers are called over HTTPS:
  brevo   POST https://api.brevo.com/v3/smtp/email   (free: 300/day, a single verified sender is enough)
  resend  POST https://api.resend.com/emails          (needs a verified domain to email other people)
  console logs the email instead of sending it (local development)
  memory  keeps it in OUTBOX (tests)
  none    sends nothing (default)
"""
import base64
import logging
from dataclasses import dataclass
from typing import List, Optional

import httpx

from core.config import settings

logger = logging.getLogger("notifications.mailer")

BREVO_URL = "https://api.brevo.com/v3/smtp/email"
RESEND_URL = "https://api.resend.com/emails"
TIMEOUT = httpx.Timeout(15.0, connect=10.0)

# Used by the "memory" provider in tests.
OUTBOX: List[dict] = []


@dataclass
class SendResult:
    ok: bool
    provider: str
    message_id: Optional[str] = None
    error: Optional[str] = None


def provider_name() -> str:
    return (settings.EMAIL_PROVIDER or "none").strip().lower()


def is_enabled() -> bool:
    return provider_name() == "memory" or settings.email_enabled


def _sender() -> tuple[str, str]:
    return settings.EMAIL_FROM_NAME or "ContractIQ", settings.EMAIL_FROM or "noreply@contractiq.local"


def _error_text(resp: httpx.Response) -> str:
    try:
        body = resp.json()
        detail = body.get("message") or body.get("error") or body
    except ValueError:
        detail = resp.text
    return f"HTTP {resp.status_code}: {str(detail)[:300]}"


async def send_email(
    to_email: str, to_name: Optional[str], subject: str, html: str, text: str,
    reply_to: Optional[str] = None, client: Optional[httpx.AsyncClient] = None,
    attachments: Optional[List[tuple[str, bytes]]] = None,
) -> SendResult:
    attachments = attachments or []
    provider = provider_name()
    from_name, from_email = _sender()

    if provider == "memory":
        OUTBOX.append({"to": to_email, "to_name": to_name, "subject": subject, "html": html,
                       "text": text, "reply_to": reply_to,
                       "attachments": [(name, len(data)) for name, data in attachments]})
        return SendResult(True, provider, message_id=f"memory-{len(OUTBOX)}")
    if provider == "console":
        logger.info("EMAIL (console) to=%s subject=%s\n%s", to_email, subject, text)
        return SendResult(True, provider, message_id="console")
    if not settings.email_enabled:
        return SendResult(False, provider, error="Email isn't set up on this server")

    own_client = client is None
    client = client or httpx.AsyncClient(timeout=TIMEOUT)
    try:
        if provider == "brevo":
            payload = {
                "sender": {"name": from_name, "email": from_email},
                "to": [{"email": to_email, **({"name": to_name} if to_name else {})}],
                "subject": subject,
                "htmlContent": html,
                "textContent": text,
            }
            if reply_to:
                payload["replyTo"] = {"email": reply_to}
            if attachments:
                payload["attachment"] = [
                    {"name": name, "content": base64.b64encode(data).decode()} for name, data in attachments
                ]
            resp = await client.post(
                BREVO_URL, json=payload,
                headers={"api-key": settings.BREVO_API_KEY, "accept": "application/json"},
            )
            if resp.status_code in (200, 201, 202):
                return SendResult(True, provider, message_id=(resp.json() or {}).get("messageId"))
            return SendResult(False, provider, error=_error_text(resp))

        if provider == "resend":
            payload = {
                "from": f"{from_name} <{from_email}>",
                "to": [to_email],
                "subject": subject,
                "html": html,
                "text": text,
            }
            if reply_to:
                payload["reply_to"] = reply_to
            if attachments:
                payload["attachments"] = [
                    {"filename": name, "content": base64.b64encode(data).decode()} for name, data in attachments
                ]
            resp = await client.post(
                RESEND_URL, json=payload, headers={"Authorization": f"Bearer {settings.RESEND_API_KEY}"}
            )
            if resp.status_code in (200, 201, 202):
                return SendResult(True, provider, message_id=(resp.json() or {}).get("id"))
            return SendResult(False, provider, error=_error_text(resp))

        return SendResult(False, provider, error=f"Unknown EMAIL_PROVIDER '{provider}'")
    except httpx.HTTPError as e:
        return SendResult(False, provider, error=f"{type(e).__name__}: {e}"[:300])
    finally:
        if own_client:
            await client.aclose()

