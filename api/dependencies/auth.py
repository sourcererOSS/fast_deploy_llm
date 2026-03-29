import secrets
from typing import Annotated

import fastapi

from config import BackendSettings, get_settings
from core import key_store


def _request_token(request: fastapi.Request) -> str | None:
    if key := request.headers.get("X-API-Key"):
        return key.strip() or None
    auth = request.headers.get("Authorization") or ""
    if auth.lower().startswith("bearer "):
        return auth[7:].strip() or None
    return None


async def verify_api_key(
    request: fastapi.Request,
    app_settings: Annotated[BackendSettings, fastapi.Depends(get_settings)],
) -> None:
    expected_env = app_settings.BEDROCK_ENDPOINT_API_KEY
    provided = _request_token(request)
    n_file = key_store.key_count()

    if not expected_env and n_file == 0:
        request.state.api_key_id = None
        request.state.key_prefix = None
        return

    if not provided:
        raise fastapi.HTTPException(status_code=401, detail="Invalid or missing API key")

    if expected_env and len(provided) == len(expected_env) and secrets.compare_digest(
        provided, expected_env
    ):
        request.state.api_key_id = "env"
        request.state.key_prefix = "env"
        return

    hit = key_store.verify_file_key(provided)
    if hit:
        request.state.api_key_id = hit[0]
        request.state.key_prefix = hit[1]
        return

    raise fastapi.HTTPException(status_code=401, detail="Invalid or missing API key")


require_api_key = fastapi.Depends(verify_api_key)
