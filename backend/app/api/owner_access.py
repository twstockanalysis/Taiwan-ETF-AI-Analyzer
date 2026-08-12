"""Single-owner access gate for private decision-profile data."""

import os
import secrets
from typing import Annotated

from fastapi import Header, HTTPException, status


OWNER_TOKEN_ENV = "TW_ETF_OWNER_TOKEN"
OWNER_TOKEN_HEADER = "X-Owner-Token"
MINIMUM_OWNER_TOKEN_LENGTH = 32


def require_owner_access(
    owner_token: Annotated[str | None, Header(alias=OWNER_TOKEN_HEADER)] = None,
) -> None:
    """Require the deployment owner token using constant-time comparison."""

    configured = os.environ.get(OWNER_TOKEN_ENV, "")
    if len(configured) < MINIMUM_OWNER_TOKEN_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Owner-only 功能尚未在伺服器設定",
        )
    if owner_token is None or not secrets.compare_digest(owner_token, configured):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Owner token 無效",
            headers={"WWW-Authenticate": "OwnerToken"},
        )
