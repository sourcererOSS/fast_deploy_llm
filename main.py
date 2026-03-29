from __future__ import annotations

import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

# llm_deploy/ — same root as ``config.env.ROOT_DIR`` (see ``Path(__file__).parents`` there).
_APP_ROOT = Path(__file__).resolve().parent
if str(_APP_ROOT) not in sys.path:
    sys.path.insert(0, str(_APP_ROOT))

import fastapi
import loguru
import uvicorn
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.endpoints import format_http_routes, router as api_router
from config import settings
from core import usage_log as usage_log_core

logger = logging.getLogger(__name__)


@asynccontextmanager
async def _lifespan(app: fastapi.FastAPI):
    usage_log_core.LOG_DIR.mkdir(parents=True, exist_ok=True)
    loguru.logger.info("Bedrock proxy up: {}", app.title)
    for line in format_http_routes(app):
        loguru.logger.info("endpoint {}", line)
    yield
    loguru.logger.info("Bedrock proxy down: {}", app.title)


def _mount_openai_routes(app: fastapi.FastAPI) -> None:
    # prefix = (settings.API_PREFIX or "").rstrip("/")
    # if prefix:
    #     app.include_router(api_router, prefix=f"{prefix}/v1")
    #     app.include_router(api_router, prefix=prefix)
    # else:
    app.include_router(api_router, prefix="/api/v1")
    # app.include_router(api_router)


def create_app() -> fastapi.FastAPI:
    app = fastapi.FastAPI(lifespan=_lifespan, **settings.set_backend_app_attributes)  # type: ignore[arg-type]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=settings.IS_ALLOWED_CREDENTIALS,
        allow_methods=settings.ALLOWED_METHODS,
        allow_headers=settings.ALLOWED_HEADERS,
    )

    @app.exception_handler(RequestValidationError)
    async def _validation(request: fastapi.Request, exc: RequestValidationError) -> JSONResponse:
        errors = exc.errors()
        logger.error("Validation error on %s: %s", request.url.path, errors)
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "message": "Invalid request format",
                    "type": "invalid_request_error",
                    "param": None,
                    "code": "validation_error",
                    "details": errors,
                }
            },
        )

    _mount_openai_routes(app)
    return app


backend_app = create_app()
# Alias for ``uvicorn main:app``; production scripts may use ``main:backend_app``.
app = backend_app

if __name__ == "__main__":
    kw: dict[str, Any] = dict(
        app="main:backend_app",
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        log_level=settings.LOGGING_LEVEL.lower(),
    )
    if settings.DEBUG:
        kw["reload"] = True
    else:
        kw["workers"] = max(1, settings.SERVER_WORKERS)
    uvicorn.run(**kw)
