"""
Append-only JSONL usage events under repo logs/.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = REPO_ROOT / "logs"
USAGE_FILE = LOG_DIR / "usage.jsonl"

os.makedirs(LOG_DIR, exist_ok=True)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def append_event(event: dict[str, Any]) -> None:
    entry = {"ts": _now_iso(), **event}
    os.makedirs(LOG_DIR, exist_ok=True)
    with USAGE_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def read_tail_lines(n: int) -> list[dict[str, Any]]:
    if not USAGE_FILE.is_file() or n <= 0:
        return []
    lines = USAGE_FILE.read_text(encoding="utf-8").splitlines()
    out: list[dict[str, Any]] = []
    for line in lines[-n:]:
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def summarize_key_events(events: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_key: dict[str, dict[str, Any]] = {}
    for ev in events:
        kid = str(ev.get("key_id") or "anonymous")
        r = by_key.setdefault(
            kid,
            {
                "key_id": kid,
                "key_prefix": ev.get("key_prefix"),
                "requests": 0,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "streamed_chars": 0,
            },
        )
        r["requests"] = int(r["requests"]) + 1
        for f in ("prompt_tokens", "completion_tokens", "total_tokens"):
            v = ev.get(f)
            if v is not None:
                r[f] = int(r[f]) + int(v)
        sc = ev.get("streamed_chars")
        if sc is not None:
            r["streamed_chars"] = int(r["streamed_chars"]) + int(sc)
        if r.get("key_prefix") is None and ev.get("key_prefix"):
            r["key_prefix"] = ev.get("key_prefix")
    return by_key
