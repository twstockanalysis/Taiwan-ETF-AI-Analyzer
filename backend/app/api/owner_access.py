"""Single-owner access gate for private decision-profile data."""

import hashlib
import os
import secrets
from typing import Annotated

from fastapi import Header, HTTPException, status


OWNER_TOKEN_ENV = "TW_ETF_OWNER_TOKEN"
OWNER_TOKEN_HEADER = "X-Owner-Token"
MINIMUM_OWNER_TOKEN_LENGTH = 32
MAXIMUM_OWNER_TOKEN_LENGTH = 256


def _token_digest(value: str) -> bytes:
    return hashlib.sha256(value.encode("utf-8")).digest()


def require_owner_access(
    owner_token: Annotated[str | None, Header(alias=OWNER_TOKEN_HEADER)] = None,
) -> None:
    """Require the deployment owner token using constant-time comparison."""

    configured = os.environ.get(OWNER_TOKEN_ENV, "")
    if not (
        MINIMUM_OWNER_TOKEN_LENGTH
        <= len(configured)
        <= MAXIMUM_OWNER_TOKEN_LENGTH
    ):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Owner-only 功能尚未在伺服器設定",
        )
    candidate = owner_token or ""
    valid_length = len(candidate) <= MAXIMUM_OWNER_TOKEN_LENGTH
    valid_digest = secrets.compare_digest(
        _token_digest(candidate if valid_length else ""),
        _token_digest(configured),
    )
    if not valid_length or not valid_digest:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Owner token 無效",
            headers={"WWW-Authenticate": "OwnerToken"},
        )
