"""
Checks the ID token that "Sign in with Google" gives the browser.

The browser gets a signed JWT from Google and posts it here. We only trust
it after checking, ourselves:
  - the signature, against Google's published public keys (RS256);
  - "aud" is our own client ID, so a token made for another site is refused;
  - "iss" is Google and the token hasn't expired;
  - Google has verified the email address.

Google's keys rotate, so they're fetched from Google and cached for as long
as Google's Cache-Control header allows. No extra library is needed:
python-jose (already used for our own tokens) does the RS256 check.
"""
import re
import time
from typing import Any, Dict, List, Optional

import httpx
from fastapi import HTTPException
from jose import JWTError, jwt

GOOGLE_CERTS_URL = "https://www.googleapis.com/oauth2/v3/certs"
GOOGLE_ISSUERS = {"accounts.google.com", "https://accounts.google.com"}

_cache: Dict[str, Any] = {"keys": [], "expires": 0.0}

INVALID = "Google sign-in didn't work. Try again."


async def _fetch_keys() -> List[dict]:
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(GOOGLE_CERTS_URL)
        r.raise_for_status()
    match = re.search(r"max-age=(\d+)", r.headers.get("cache-control", ""))
    _cache["keys"] = r.json().get("keys", [])
    _cache["expires"] = time.time() + (int(match.group(1)) if match else 3600)
    return _cache["keys"]


async def _key_for(kid: Optional[str]) -> Optional[dict]:
    keys = _cache["keys"] if time.time() < _cache["expires"] else await _fetch_keys()
    found = next((k for k in keys if k.get("kid") == kid), None)
    if found is None:
        # Google may have just rotated its keys: fetch once more before giving up.
        keys = await _fetch_keys()
        found = next((k for k in keys if k.get("kid") == kid), None)
    return found


async def verify_id_token(token: str, client_id: str) -> dict:
    """The token's claims if every check passes, otherwise HTTP 401."""
    try:
        header = jwt.get_unverified_header(token)
    except JWTError:
        raise HTTPException(401, INVALID)
    if header.get("alg") != "RS256":
        raise HTTPException(401, INVALID)

    try:
        key = await _key_for(header.get("kid"))
    except httpx.HTTPError:
        raise HTTPException(503, "Couldn't reach Google to check the sign-in. Try again in a moment.")
    if key is None:
        raise HTTPException(401, INVALID)

    try:
        claims = jwt.decode(
            token, key, algorithms=["RS256"], audience=client_id,
            options={"verify_at_hash": False},
        )
    except JWTError:
        raise HTTPException(401, INVALID)

    if claims.get("iss") not in GOOGLE_ISSUERS or not claims.get("sub"):
        raise HTTPException(401, INVALID)
    if not claims.get("email") or claims.get("email_verified") not in (True, "true"):
        raise HTTPException(401, "Your Google account's email isn't verified, so it can't be used to sign in.")
    return claims
