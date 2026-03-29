"""Admin routes: require ``ADMIN_API_KEY`` via ``X-Admin-Key`` or Bearer."""

from __future__ import annotations

import secrets
from typing import Annotated

import fastapi

from config import BackendSettings, get_settings


def _admin_token(request: fastapi.Request) -> str | None:
    if key := request.headers.get("X-Admin-Key"):
        return key.strip() or None
    auth = request.headers.get("Authorization") or ""
    if auth.lower().startswith("bearer "):
        return auth[7:].strip() or None
    return None


async def verify_admin(
    request: fastapi.Request,
    app_settings: Annotated[BackendSettings, fastapi.Depends(get_settings)],
) -> None:
    expected = app_settings.ADMIN_API_KEY
    if not expected:
        raise fastapi.HTTPException(
            status_code=503,
            detail="ADMIN_API_KEY is not set — configure it in config/.env to use admin endpoints",
        )
    provided = _admin_token(request)
    if not provided or len(provided) != len(expected) or not secrets.compare_digest(provided, expected):
        raise fastapi.HTTPException(status_code=401, detail="Invalid or missing admin key")


require_admin = fastapi.Depends(verify_admin)
