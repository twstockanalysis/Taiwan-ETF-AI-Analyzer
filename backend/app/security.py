"""Application-level HTTP safety boundaries for public and owner APIs."""

from __future__ import annotations

from collections import OrderedDict
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
import math
import os
from threading import Lock
import time
from typing import Any

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.datastructures import MutableHeaders
from starlette.types import Message, Receive, Scope, Send


MAX_REQUEST_BODY_BYTES = 64 * 1024
MAX_REQUEST_TARGET_BYTES = 8 * 1024
MAX_REQUEST_HEADER_BYTES = 32 * 1024
PRIVATE_API_PREFIX = "/api/v1/decision-profile"
PUBLIC_RATE_LIMIT_ENV = "TW_ETF_PUBLIC_RATE_LIMIT_PER_MINUTE"
PRIVATE_RATE_LIMIT_ENV = "TW_ETF_PRIVATE_RATE_LIMIT_PER_MINUTE"
DEFAULT_PUBLIC_RATE_LIMIT = 600
DEFAULT_PRIVATE_RATE_LIMIT = 120
MAX_RATE_LIMIT_CLIENTS = 4096


def _is_private_path(path: str) -> bool:
    return path == PRIVATE_API_PREFIX or path.startswith(
        f"{PRIVATE_API_PREFIX}/"
    )


def _positive_rate_limit(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return value if value > 0 else default


@dataclass
class _RateWindow:
    started_at: float
    count: int


class InMemoryRateLimiter:
    """Bounded fixed-window limiter for a single application process."""

    def __init__(
        self,
        *,
        limit: int,
        window_seconds: int = 60,
        max_clients: int = MAX_RATE_LIMIT_CLIENTS,
    ) -> None:
        if limit <= 0 or window_seconds <= 0 or max_clients <= 0:
            raise ValueError("Rate-limit settings must be positive")
        self.limit = limit
        self.window_seconds = window_seconds
        self.max_clients = max_clients
        self._windows: OrderedDict[str, _RateWindow] = OrderedDict()
        self._lock = Lock()

    def allow(self, key: str, *, now: float | None = None) -> tuple[bool, int]:
        observed_at = time.monotonic() if now is None else now
        with self._lock:
            window = self._windows.get(key)
            if (
                window is None
                or observed_at - window.started_at >= self.window_seconds
            ):
                if window is None and len(self._windows) >= self.max_clients:
                    self._windows.popitem(last=False)
                self._windows[key] = _RateWindow(observed_at, 1)
                self._windows.move_to_end(key)
                return True, self.window_seconds

            self._windows.move_to_end(key)
            retry_after = max(
                1,
                math.ceil(self.window_seconds - (observed_at - window.started_at)),
            )
            if window.count >= self.limit:
                return False, retry_after
            window.count += 1
            return True, retry_after


class SecurityBoundaryMiddleware:
    """Bound request resources and prevent storage of private responses."""

    def __init__(
        self,
        app: Callable[..., Awaitable[None]],
        public_rate_limit: int | None = None,
        private_rate_limit: int | None = None,
    ) -> None:
        self.app = app
        self.public_rate_limiter = InMemoryRateLimiter(
            limit=public_rate_limit
            or _positive_rate_limit(
                PUBLIC_RATE_LIMIT_ENV,
                DEFAULT_PUBLIC_RATE_LIMIT,
            )
        )
        self.private_rate_limiter = InMemoryRateLimiter(
            limit=private_rate_limit
            or _positive_rate_limit(
                PRIVATE_RATE_LIMIT_ENV,
                DEFAULT_PRIVATE_RATE_LIMIT,
            )
        )

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = str(scope.get("path", ""))
        private = _is_private_path(path)

        async def send_with_security_headers(message: Message) -> None:
            if message["type"] == "http.response.start" and private:
                headers = MutableHeaders(scope=message)
                headers["Cache-Control"] = "no-store, private"
                headers["Pragma"] = "no-cache"
                existing_vary = headers.get("Vary")
                if existing_vary:
                    values = {
                        item.strip().lower()
                        for item in existing_vary.split(",")
                    }
                    if "x-owner-token" not in values:
                        headers["Vary"] = f"{existing_vary}, X-Owner-Token"
                else:
                    headers["Vary"] = "X-Owner-Token"
            await send(message)

        client = scope.get("client")
        client_host = str(client[0]) if client else "unknown"
        limiter = (
            self.private_rate_limiter if private else self.public_rate_limiter
        )
        allowed, retry_after = limiter.allow(client_host[:128])
        if not allowed:
            await self._reject(
                scope,
                receive,
                send_with_security_headers,
                status.HTTP_429_TOO_MANY_REQUESTS,
                "Request rate exceeds safety limit",
                headers={"Retry-After": str(retry_after)},
            )
            return

        target_size = len(path.encode("utf-8")) + len(
            scope.get("query_string", b"")
        )
        if target_size > MAX_REQUEST_TARGET_BYTES:
            await self._reject(
                scope,
                receive,
                send_with_security_headers,
                status.HTTP_414_URI_TOO_LONG,
                "Request target exceeds safety limit",
            )
            return

        raw_headers = list(scope.get("headers", []))
        header_size = sum(len(name) + len(value) for name, value in raw_headers)
        if header_size > MAX_REQUEST_HEADER_BYTES:
            await self._reject(
                scope,
                receive,
                send_with_security_headers,
                status.HTTP_431_REQUEST_HEADER_FIELDS_TOO_LARGE,
                "Request headers exceed safety limit",
            )
            return

        content_lengths = [
            value
            for name, value in raw_headers
            if name.lower() == b"content-length"
        ]
        if len(content_lengths) > 1:
            await self._reject(
                scope,
                receive,
                send_with_security_headers,
                status.HTTP_400_BAD_REQUEST,
                "Invalid Content-Length header",
            )
            return
        if content_lengths:
            try:
                content_length = int(content_lengths[0])
            except ValueError:
                content_length = -1
            if content_length < 0:
                await self._reject(
                    scope,
                    receive,
                    send_with_security_headers,
                    status.HTTP_400_BAD_REQUEST,
                    "Invalid Content-Length header",
                )
                return
            if content_length > MAX_REQUEST_BODY_BYTES:
                await self._reject(
                    scope,
                    receive,
                    send_with_security_headers,
                    status.HTTP_413_CONTENT_TOO_LARGE,
                    "Request body exceeds safety limit",
                )
                return

        method = str(scope.get("method", "GET")).upper()
        if method not in {"POST", "PUT", "PATCH"}:
            await self.app(scope, receive, send_with_security_headers)
            return

        messages: list[Message] = []
        received_size = 0
        while True:
            message = await receive()
            messages.append(message)
            if message["type"] == "http.disconnect":
                return
            if message["type"] != "http.request":
                continue
            received_size += len(message.get("body", b""))
            if received_size > MAX_REQUEST_BODY_BYTES:
                await self._reject(
                    scope,
                    receive,
                    send_with_security_headers,
                    status.HTTP_413_CONTENT_TOO_LARGE,
                    "Request body exceeds safety limit",
                )
                return
            if not message.get("more_body", False):
                break

        message_index = 0

        async def replay_receive() -> Message:
            nonlocal message_index
            if message_index < len(messages):
                message = messages[message_index]
                message_index += 1
                return message
            return {"type": "http.request", "body": b"", "more_body": False}

        await self.app(scope, replay_receive, send_with_security_headers)

    @staticmethod
    async def _reject(
        scope: Scope,
        receive: Receive,
        send: Send,
        status_code: int,
        detail: str,
        headers: dict[str, str] | None = None,
    ) -> None:
        response = JSONResponse(
            status_code=status_code,
            content={"detail": detail},
            headers=headers,
        )
        await response(scope, receive, send)


async def sanitized_validation_exception_handler(
    request: Request,
    exception: RequestValidationError,
) -> JSONResponse:
    """Return validation locations and types without reflecting input values."""

    del request
    errors: list[dict[str, Any]] = []
    for item in exception.errors():
        errors.append(
            {
                "type": str(item.get("type", "validation_error")),
                "loc": [
                    value if isinstance(value, (str, int)) else str(value)
                    for value in item.get("loc", ())
                ],
            }
        )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={"detail": "Invalid request", "errors": errors},
    )


async def sanitized_internal_exception_handler(
    request: Request,
    exception: Exception,
) -> JSONResponse:
    """Keep unexpected exception details and local paths out of HTTP output."""

    del exception
    headers = None
    if _is_private_path(request.url.path):
        headers = {
            "Cache-Control": "no-store, private",
            "Pragma": "no-cache",
            "Vary": "X-Owner-Token",
        }
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
        headers=headers,
    )
