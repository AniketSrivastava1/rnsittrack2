"""Security middleware: path sanitization, request size limit."""
from __future__ import annotations

import logging

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

_MAX_BODY_BYTES = 10 * 1024 * 1024  # 10 MB
_TRAVERSAL_SEQUENCES = ["..", "%2e%2e", "%2E%2E"]


class SecurityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Check content length
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > _MAX_BODY_BYTES:
            return JSONResponse(
                status_code=413,
                content={"error_code": "PAYLOAD_TOO_LARGE", "message": "Request body exceeds 10 MB limit", "details": {}},
            )

        # Check for path traversal in URL
        path = str(request.url.path)
        for seq in _TRAVERSAL_SEQUENCES:
            if seq in path:
                logger.warning("Path traversal attempt blocked: %s", path)
                return JSONResponse(
                    status_code=400,
                    content={"error_code": "INVALID_PATH", "message": "Path traversal not allowed", "details": {}},
                )

        return await call_next(request)
