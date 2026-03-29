"""Bedrock + LangChain helpers (OpenAI-shaped chat)."""

from __future__ import annotations

import json
import time
import uuid
from typing import Any, AsyncIterator

from langchain_aws import ChatBedrockConverse

from config.bedrock import DEFAULT_MODEL, MODELS
from models.chat import Message


def completion_id() -> str:
    return f"chatcmpl-{uuid.uuid4().hex}"


def build_llm(
    *,
    model_alias: str,
    temperature: float,
    max_tokens: int,
    region: str,
    bedrock_api_key: str | None,
) -> ChatBedrockConverse:
    model_id = MODELS.get(model_alias, MODELS[DEFAULT_MODEL])
    kwargs: dict[str, Any] = {
        "model": model_id,
        "region_name": region,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if bedrock_api_key:
        kwargs["bedrock_api_key"] = bedrock_api_key
    return ChatBedrockConverse(**kwargs)


def normalize_message_content(content: str | list | None) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        text_parts: list[str] = []
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text" and "text" in block:
                    text_parts.append(str(block["text"]))
                elif "text" in block:
                    text_parts.append(str(block["text"]))
            elif isinstance(block, str):
                text_parts.append(block)
        return "".join(text_parts)
    return str(content)


def lc_messages(messages: list[Message]) -> list[tuple[str, str]]:
    role_map = {"user": "human", "assistant": "ai", "system": "system"}
    return [
        (role_map.get(m.role, m.role), normalize_message_content(m.content))
        for m in messages
        if normalize_message_content(m.content)
    ]


def extract_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            block.get("text", "") if isinstance(block, dict) else str(block) for block in content
        )
    return str(content) if content else ""


def normalize_model(model: str) -> str:
    for m in (x.strip() for x in model.split(",")):
        if m and m in MODELS:
            return m
    return model.strip()


async def stream_sse(
    llm: ChatBedrockConverse,
    lc_msgs: list[tuple[str, str]],
    model_alias: str,
    completion: str,
    created: int,
    accum_chars: list[int] | None = None,
) -> AsyncIterator[str]:
    async for chunk in llm.astream(lc_msgs):
        delta_text = extract_text(chunk.content if hasattr(chunk, "content") else "")
        if not delta_text:
            continue
        if accum_chars is not None:
            accum_chars.append(len(delta_text))
        payload = {
            "id": completion,
            "object": "chat.completion.chunk",
            "created": created,
            "model": model_alias,
            "choices": [
                {
                    "index": 0,
                    "delta": {"role": "assistant", "content": delta_text},
                    "finish_reason": None,
                }
            ],
        }
        yield f"data: {json.dumps(payload)}\n\n"

    stop_payload = {
        "id": completion,
        "object": "chat.completion.chunk",
        "created": created,
        "model": model_alias,
        "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
    }
    yield f"data: {json.dumps(stop_payload)}\n\n"
    yield "data: [DONE]\n\n"


def list_models_payload() -> dict[str, Any]:
    now = int(time.time())
    data = [{"id": alias, "object": "model", "created": now, "owned_by": "bedrock"} for alias in MODELS]
    return {"object": "list", "data": data}


def _usage_meta_tokens(meta: Any) -> dict[str, int]:
    if isinstance(meta, dict):
        return {
            "prompt_tokens": int(meta.get("input_tokens", 0)),
            "completion_tokens": int(meta.get("output_tokens", 0)),
            "total_tokens": int(meta.get("total_tokens", 0)),
        }
    return {
        "prompt_tokens": int(getattr(meta, "input_tokens", 0) or 0),
        "completion_tokens": int(getattr(meta, "output_tokens", 0) or 0),
        "total_tokens": int(getattr(meta, "total_tokens", 0) or 0),
    }


def usage_from_response(response: Any) -> dict[str, int]:
    if hasattr(response, "usage_metadata") and response.usage_metadata:
        return _usage_meta_tokens(response.usage_metadata)
    return {}
