"""OpenAI-compatible routes: GET /models, POST /chat/completions."""

from __future__ import annotations

import logging
import time
from collections.abc import AsyncIterator
from typing import Annotated, Any

import fastapi
from fastapi.responses import JSONResponse, StreamingResponse

from api.dependencies.auth import require_api_key
from config import BackendSettings, get_settings
from config.bedrock import MODELS
from core import bedrock as bedrock_core
from core import usage_log as usage_log_core
from models.chat import ChatCompletionRequest

logger = logging.getLogger(__name__)

router = fastapi.APIRouter(dependencies=[require_api_key], tags=["openai"])


def _log_chat(
    http_request: fastapi.Request,
    *,
    model_alias: str,
    stream: bool,
    message_count: int,
    usage: dict[str, int] | None = None,
    streamed_chars: int | None = None,
) -> None:
    key_id = getattr(http_request.state, "api_key_id", None)
    key_prefix = getattr(http_request.state, "key_prefix", None)
    ev: dict[str, Any] = {
        "route": "chat.completions",
        "model": model_alias,
        "stream": stream,
        "message_count": message_count,
        "key_id": key_id,
        "key_prefix": key_prefix,
    }
    if usage:
        ev.update(usage)
    if streamed_chars is not None:
        ev["streamed_chars"] = streamed_chars
    usage_log_core.append_event(ev)


async def _stream_logged(
    http_request: fastapi.Request,
    *,
    llm: Any,
    msgs: list[tuple[str, str]],
    model_alias: str,
    cid: str,
    created: int,
    message_count: int,
) -> AsyncIterator[str]:
    accum: list[int] = []
    try:
        async for line in bedrock_core.stream_sse(
            llm, msgs, model_alias, cid, created, accum_chars=accum
        ):
            yield line
    finally:
        _log_chat(
            http_request,
            model_alias=model_alias,
            stream=True,
            message_count=message_count,
            streamed_chars=sum(accum),
        )


@router.get("/models", name="openai:list-models", status_code=fastapi.status.HTTP_200_OK)
async def list_models() -> dict:
    return bedrock_core.list_models_payload()


@router.post(
    "/chat/completions",
    name="openai:chat-completions",
    response_model=None,
)
async def chat_completions(
    http_request: fastapi.Request,
    request: ChatCompletionRequest,
    app_settings: Annotated[BackendSettings, fastapi.Depends(get_settings)],
) -> JSONResponse | StreamingResponse:
    logger.info(
        "chat completion: model=%s stream=%s messages=%s",
        request.model,
        request.stream,
        len(request.messages),
    )

    model_alias = bedrock_core.normalize_model(request.model)
    if model_alias not in MODELS:
        raise fastapi.HTTPException(
            status_code=400,
            detail=f"Unknown model '{request.model}'. Available: {list(MODELS.keys())}",
        )
    if not request.messages:
        raise fastapi.HTTPException(status_code=400, detail="messages array cannot be empty")

    llm = bedrock_core.build_llm(
        model_alias=model_alias,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
        region=app_settings.AWS_REGION,
        bedrock_api_key=app_settings.AWS_BEDROCK_API_KEY,
    )
    msgs = bedrock_core.lc_messages(request.messages)
    if not msgs:
        raise fastapi.HTTPException(status_code=400, detail="No valid messages with content found")

    cid = bedrock_core.completion_id()
    created = int(time.time())

    if request.stream:
        return StreamingResponse(
            _stream_logged(
                http_request,
                llm=llm,
                msgs=msgs,
                model_alias=model_alias,
                cid=cid,
                created=created,
                message_count=len(request.messages),
            ),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    response = await llm.ainvoke(msgs)
    content = bedrock_core.extract_text(response.content if hasattr(response, "content") else "")
    usage = bedrock_core.usage_from_response(response)
    _log_chat(
        http_request,
        model_alias=model_alias,
        stream=False,
        message_count=len(request.messages),
        usage=usage or None,
    )

    return JSONResponse(
        {
            "id": cid,
            "object": "chat.completion",
            "created": created,
            "model": model_alias,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": content},
                    "finish_reason": "stop",
                }
            ],
            "usage": usage,
        }
    )
