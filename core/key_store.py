"""
File-backed API keys (sha256), under logs/api_keys.json.
Plaintext keys are only returned once at creation.
"""
from __future__ import annotations

import hashlib
import json
import os
import secrets
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = REPO_ROOT / "logs"
KEY_FILE = LOG_DIR / "api_keys.json"

os.makedirs(LOG_DIR, exist_ok=True)


def _hash_secret(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _random_sk() -> str:
    token = secrets.token_urlsafe(32)
    return f"sk-{token}"


@dataclass
class KeyRecord:
    id: str
    label: str
    secret_hash: str
    prefix: str
    created: str


def _load_raw() -> dict[str, Any]:
    if not KEY_FILE.is_file():
        return {"keys": []}
    try:
        return json.loads(KEY_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"keys": []}


def _save_raw(data: dict[str, Any]) -> None:
    os.makedirs(LOG_DIR, exist_ok=True)
    tmp = KEY_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(KEY_FILE)


def list_public_keys() -> list[dict[str, Any]]:
    data = _load_raw()
    out = []
    for row in data.get("keys", []):
        out.append(
            {
                "id": row["id"],
                "label": row.get("label", ""),
                "prefix": row.get("prefix", ""),
                "created": row.get("created", ""),
            }
        )
    return out


def create_key(label: str) -> tuple[str, dict[str, Any]]:
    from datetime import datetime, timezone

    raw_key = _random_sk()
    prefix = raw_key[:12] + "…"
    rid = str(uuid.uuid4())
    created = datetime.now(timezone.utc).isoformat()
    row = {
        "id": rid,
        "label": label or "",
        "hash": _hash_secret(raw_key),
        "prefix": prefix,
        "created": created,
    }
    data = _load_raw()
    keys = list(data.get("keys", []))
    keys.append(row)
    data["keys"] = keys
    _save_raw(data)
    public = {"id": rid, "label": row["label"], "prefix": prefix, "created": created}
    return raw_key, public


def delete_key(key_id: str) -> bool:
    data = _load_raw()
    keys = list(data.get("keys", []))
    new_keys = [k for k in keys if k.get("id") != key_id]
    if len(new_keys) == len(keys):
        return False
    data["keys"] = new_keys
    _save_raw(data)
    return True


def verify_file_key(provided: str) -> tuple[str, str] | None:
    """Return (key_id, prefix) if provided matches stored hash."""
    if not provided:
        return None
    h = _hash_secret(provided)
    for row in _load_raw().get("keys", []):
        if row.get("hash") == h:
            return str(row["id"]), str(row.get("prefix", ""))
    return None


def key_count() -> int:
    return len(_load_raw().get("keys", []))
