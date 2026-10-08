"""Security and authentication utilities.

Provides API key and Bearer token verification.
When AUTH_ENABLED is False (e.g. local MVP demo), requests pass without credentials.
When AUTH_ENABLED is True, requests must provide either:
- Header: `X-API-Key: <token>`
- Header: `Authorization: Bearer <token>`
"""
from typing import Optional
from fastapi import Header, HTTPException, Security, status
from pydantic_settings import BaseSettings
from app.config import settings
import os

AUTH_TOKEN = os.getenv("APP_API_KEY", "")
REQUIRE_AUTH = os.getenv("AUTH_ENABLED", "false").lower() in ("true", "1", "yes")


def verify_api_key(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
) -> bool:
    """Verify incoming client request authorization."""
    if not REQUIRE_AUTH or not AUTH_TOKEN:
        return True

    provided_token = x_api_key
    if not provided_token and authorization:
        if authorization.startswith("Bearer "):
            provided_token = authorization.replace("Bearer ", "").strip()
        else:
            provided_token = authorization.strip()

    if not provided_token or provided_token != AUTH_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return True
