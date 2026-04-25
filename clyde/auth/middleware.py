import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp

from .config import AUTH_CONFIG
from .google import fetch_token_info
from .token_cache import CACHE


logger = logging.getLogger(__name__)


PUBLIC_PATH_PREFIXES = (
    "/.well-known/",
    "/authorize",
    "/token",
    "/api/status",
)


def is_public(path: str) -> bool:
    for prefix in PUBLIC_PATH_PREFIXES:
        if path == prefix or path.startswith(prefix):
            return True
    return False


def unauthorized(request: Request, message: str) -> JSONResponse:
    scheme = request.url.scheme
    host = request.headers.get("host", request.url.hostname or "localhost")
    resource_metadata = f"{scheme}://{host}/.well-known/oauth-protected-resource"
    return JSONResponse(
        {"error": "unauthorized", "detail": message},
        status_code=401,
        headers={
            "WWW-Authenticate": f'Bearer realm="Clyde", resource_metadata="{resource_metadata}"',
        },
    )


class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):  # type: ignore[no-untyped-def]
        if is_public(request.url.path):
            return await call_next(request)

        auth_header = request.headers.get("authorization", "")
        if not auth_header.startswith("Bearer "):
            return unauthorized(request, "Missing Bearer token")

        token = auth_header[7:].strip()
        if not token:
            return unauthorized(request, "Empty Bearer token")

        cached = CACHE.get(token)
        if cached is not None:
            return await call_next(request)

        info, error = await fetch_token_info(token)
        if error is not None:
            logger.warning(f"[auth] tokeninfo failed: {error}")
            return unauthorized(request, "Invalid token")

        if info.aud != AUTH_CONFIG.google_client_id:
            logger.warning(f"[auth] aud mismatch: got {info.aud}")
            return unauthorized(request, "Token not issued for this server")

        if info.email_verified.lower() != "true":
            return unauthorized(request, "Email not verified")

        if info.email.lower() not in AUTH_CONFIG.allowed_emails:
            logger.warning(f"[auth] email {info.email} not in allowlist")
            return unauthorized(request, "Email not authorized")

        try:
            expires_at = float(info.exp)
        except ValueError:
            expires_at = time.time() + 60

        CACHE.put(token, info.email.lower(), min(expires_at, time.time() + 300))
        return await call_next(request)
