"""Configuration: env paths, settings, Bedrock model map."""

from .bedrock import DEFAULT_MODEL, MODELS
from .env import ENV_FILE, ROOT_DIR, load_env
from .settings import BackendSettings, get_settings, settings

__all__ = [
    "DEFAULT_MODEL",
    "ENV_FILE",
    "MODELS",
    "ROOT_DIR",
    "BackendSettings",
    "get_settings",
    "load_env",
    "settings",
]
