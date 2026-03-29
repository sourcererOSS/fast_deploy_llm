"""Admin: API keys, usage, model map (read-only). Protected by ``ADMIN_API_KEY``."""

from __future__ import annotations

from typing import Any

import fastapi
from starlette.responses import Response
from pydantic import BaseModel, Field

from api.dependencies.admin_auth import require_admin
from config.bedrock import MODELS
from core import key_store
from core import usage_log as usage_log_core

router = fastapi.APIRouter(prefix="/admin", tags=["admin"], dependencies=[require_admin])


class CreateKeyBody(BaseModel):
    label: str = Field(default="", max_length=256)


@router.post("/keys", status_code=fastapi.status.HTTP_201_CREATED)
async def create_api_key(body: CreateKeyBody) -> dict[str, Any]:
    raw, public = key_store.create_key(body.label)
    return {"api_key": raw, **public}


@router.get("/keys")
async def list_api_keys() -> dict[str, Any]:
    return {"keys": key_store.list_public_keys()}


@router.delete("/keys/{key_id}", status_code=fastapi.status.HTTP_204_NO_CONTENT)
async def remove_api_key(key_id: str) -> Response:
    if not key_store.delete_key(key_id):
        raise fastapi.HTTPException(status_code=404, detail="Unknown key id")
    return Response(status_code=204)


@router.get("/usage")
async def get_usage_events(limit: int = fastapi.Query(default=100, ge=1, le=10_000)) -> dict[str, Any]:
    events = usage_log_core.read_tail_lines(limit)
    return {"limit": limit, "count": len(events), "events": events}


@router.get("/usage/summary")
async def get_usage_summary(limit: int = fastapi.Query(default=5000, ge=1, le=100_000)) -> dict[str, Any]:
    events = usage_log_core.read_tail_lines(limit)
    by_key = usage_log_core.summarize_key_events(events)
    return {"window_events": len(events), "by_key": list(by_key.values())}


@router.get("/models")
async def admin_list_models() -> dict[str, Any]:
    return {"models": MODELS}
