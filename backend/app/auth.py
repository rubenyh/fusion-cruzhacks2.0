import os
from functools import lru_cache
from typing import Any, Dict, Optional
from dotenv import load_dotenv
import httpx
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt
from jose.exceptions import ExpiredSignatureError, JWTClaimsError, JWTError

load_dotenv()
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE")
AUTH0_ISSUER = os.getenv("AUTH0_ISSUER", f"https://{AUTH0_DOMAIN}/")

if not AUTH0_DOMAIN or not AUTH0_AUDIENCE:
    raise RuntimeError("Missing AUTH0_DOMAIN or AUTH0_AUDIENCE env vars")

bearer_scheme = HTTPBearer(auto_error=False)


@lru_cache(maxsize=1)
def _jwks_url() -> str:
    return f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"


@lru_cache(maxsize=1)
def _algorithms() -> list[str]:
    # Auth0 access tokens are typically RS256
    return ["RS256"]


async def _fetch_jwks() -> Dict[str, Any]:
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(_jwks_url())
        resp.raise_for_status()
        return resp.json()


async def _get_signing_key(token: str) -> Dict[str, Any]:
    unverified_header = jwt.get_unverified_header(token)
    kid = unverified_header.get("kid")
    if not kid:
        raise HTTPException(status_code=401, detail="Invalid token header (missing kid)")

    jwks = await _fetch_jwks()
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return key

    # If keys rotated, clear cache and retry once
    _fetch_jwks.cache_clear()  # type: ignore[attr-defined]
    jwks = await _fetch_jwks()
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return key

    raise HTTPException(status_code=401, detail="Signing key not found")


async def verify_jwt(
    creds: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> Dict[str, Any]:
    if creds is None or not creds.credentials:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    token = creds.credentials
    try:
        key = await _get_signing_key(token)

        payload = jwt.decode(
            token,
            key,
            algorithms=_algorithms(),
            audience=AUTH0_AUDIENCE,
            issuer=AUTH0_ISSUER,
        )
        return payload

    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except JWTClaimsError as e:
        raise HTTPException(status_code=401, detail=f"Invalid claims: {str(e)}")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except httpx.HTTPError:
        raise HTTPException(status_code=503, detail="Auth service unavailable")


def require_scopes(required: list[str]):
    async def _dep(payload: Dict[str, Any] = Depends(verify_jwt)) -> Dict[str, Any]:
        token_scopes = set((payload.get("scope") or "").split())
        if not set(required).issubset(token_scopes):
            raise HTTPException(status_code=403, detail="Insufficient scope")
        return payload

    return _dep
