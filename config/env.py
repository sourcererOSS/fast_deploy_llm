"""Paths and loading for ``.env`` files (repo root via ``Path(__file__).parents[...]``)."""

from __future__ import annotations

import pathlib

# This file: llm_deploy/config/env.py
# parents[0] → llm_deploy/config/
# parents[1] → llm_deploy/ (repository root — application base)
ROOT_DIR: pathlib.Path = pathlib.Path(__file__).resolve().parents[1]

# Prefer config-local secrets; optional second file at repo root is loaded in load_env().
ENV_FILE: pathlib.Path = pathlib.Path(__file__).resolve().parent / ".env"


def load_env() -> None:
    """Load env vars: ``config/.env`` then ``llm_deploy/.env`` (later wins on duplicate keys)."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv(ENV_FILE)
    load_dotenv(ROOT_DIR / ".env")
