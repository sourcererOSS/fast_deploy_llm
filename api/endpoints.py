"""Aggregate API routers."""

from __future__ import annotations

import fastapi

from api.routes.admin import router as admin_router
from api.routes.openai_bedrock import router as bedrock_router

router = fastapi.APIRouter()

router.include_router(router=bedrock_router)
router.include_router(router=admin_router)


def format_http_routes(app: fastapi.FastAPI) -> list[str]:
    """Return ``METHOD path`` lines for every HTTP route on the app (after all ``include_router`` calls)."""
    lines: list[str] = []
    for route in app.routes:
        methods = getattr(route, "methods", None)
        path = getattr(route, "path", None)
        if methods and path:
            for method in sorted(m for m in methods if m != "HEAD"):
                lines.append(f"{method:8} {path}")
    return sorted(lines)
