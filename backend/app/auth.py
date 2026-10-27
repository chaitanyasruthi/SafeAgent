import os
import hmac

from fastapi import Header, HTTPException


def require_api_token(
    authorization: str | None = Header(default=None),
) -> None:
    expected = os.environ.get("SAFEAGENT_API_TOKEN")

    if not expected:
        raise HTTPException(
            status_code=503,
            detail="API authentication is not configured",
        )

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid authorization",
            headers={"WWW-Authenticate": "Bearer"},
        )

    supplied = authorization.removeprefix("Bearer ").strip()

    if not hmac.compare_digest(supplied, expected):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid authorization",
            headers={"WWW-Authenticate": "Bearer"},
        )
