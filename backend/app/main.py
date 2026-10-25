from __future__ import annotations

import os
import secrets
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .auth import TokenService
from .database import default_database_url, instrument_database
from .routers import assets, audit, auth, dashboard, findings, remediation, sites
from .store import DatabaseStore, StoreError
from .telemetry import instrument_app


def _error(request: Request, status_code: int, code: str, message: str,
           fields: dict[str, str] | None = None, headers: dict[str, str] | None = None) -> JSONResponse:
    body: dict[str, object] = {"code": code, "message": message, "requestId": request.state.request_id}
    if fields:
        body["fields"] = fields
    return JSONResponse(status_code=status_code, content=body, headers=headers)


def create_app(*, store: DatabaseStore | None = None, token_service: TokenService | None = None,
               database_url: str | None = None, static_dir: str | Path | None = None) -> FastAPI:
    app = FastAPI(title="OTARM Frontend Backend API", version="1.0.0")
    configured_demo_password = os.getenv("OTARM_DEMO_PASSWORD")
    demo_password = configured_demo_password or secrets.token_urlsafe(24)
    app.state.store = store or DatabaseStore(
        database_url or os.getenv("OTARM_DATABASE_URL", default_database_url()), demo_password,
        sync_demo_password=configured_demo_password is not None,
    )
    secret = os.getenv("OTARM_TOKEN_SECRET", "").encode() or secrets.token_bytes(48)
    ttl = int(os.getenv("OTARM_TOKEN_TTL_SECONDS", "3600"))
    app.state.token_service = token_service or TokenService(secret, ttl)
    _, _, metrics = instrument_app(app)
    app.state.store.metrics = metrics
    instrument_database(app.state.store.engine, metrics)

    origins = [origin.strip() for origin in os.getenv(
        "OTARM_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",") if origin.strip()]
    app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=False,
                       allow_methods=["GET", "POST", "PATCH"], allow_headers=["Authorization", "Content-Type"])

    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        request.state.request_id = request.headers.get("X-Request-ID") or f"req-{uuid4()}"
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        return response

    @app.exception_handler(StoreError)
    async def store_error_handler(request: Request, exc: StoreError):
        request.app.state.metrics.http_errors.add(1, {
            "error.code": exc.code,
            "http.route": str(getattr(request.scope.get("route"), "path", "unmatched")),
        })
        if exc.status_code == 403:
            request.app.state.metrics.authorization_denials.add(1, {"reason": "domain_policy"})
        return _error(request, exc.status_code, exc.code, exc.message)

    @app.exception_handler(HTTPException)
    async def http_error_handler(request: Request, exc: HTTPException):
        if isinstance(exc.detail, dict):
            code = str(exc.detail.get("code", "INTERNAL"))
            message = str(exc.detail.get("message", "Request failed."))
        else:
            code, message = "INTERNAL", str(exc.detail)
        request.app.state.metrics.http_errors.add(1, {
            "error.code": code,
            "http.route": str(getattr(request.scope.get("route"), "path", "unmatched")),
        })
        return _error(request, exc.status_code, code, message, headers=exc.headers)

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        fields = {".".join(str(item) for item in error["loc"][1:]): error["msg"] for error in exc.errors()}
        request.app.state.metrics.http_errors.add(1, {
            "error.code": "VALIDATION",
            "http.route": str(getattr(request.scope.get("route"), "path", "unmatched")),
        })
        return _error(request, 400, "VALIDATION", "One or more request values are invalid.", fields)

    api_prefix = "/api/v1"
    for router in (auth.router, sites.router, dashboard.router, assets.router,
                   findings.router, remediation.router, audit.router):
        app.include_router(router, prefix=api_prefix)

    @app.get("/healthz", include_in_schema=False)
    async def health_check() -> dict[str, str]:
        return {
            "status": "ok",
            "revision": os.getenv("RENDER_GIT_COMMIT", "local"),
        }

    frontend_dir = Path(static_dir or os.getenv(
        "OTARM_STATIC_DIR", Path(__file__).resolve().parent.parent / "static"
    ))
    if frontend_dir.joinpath("index.html").is_file():
        app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
    return app


app = create_app()
