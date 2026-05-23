"""HTTP middleware: request-id correlation, security headers."""

from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

REQUEST_ID_HEADER = "X-Request-ID"

log = structlog.get_logger(__name__)


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Read or generate a request id, expose it to logs and downstream code.

    Logs an access record at the end of the request including method, path,
    status code and the request id, so traces stay correlated in JSON logs.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid.uuid4())
        request.state.request_id = request_id
        structlog.contextvars.bind_contextvars(request_id=request_id)
        try:
            response = await call_next(request)
        finally:
            structlog.contextvars.unbind_contextvars("request_id")
        response.headers[REQUEST_ID_HEADER] = request_id
        log.info(
            "http_request",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
        )
        return response


SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    "X-Frame-Options": "DENY",
}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Attach a baseline set of security headers to every response."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        response = await call_next(request)
        for k, v in SECURITY_HEADERS.items():
            response.headers.setdefault(k, v)
        return response
