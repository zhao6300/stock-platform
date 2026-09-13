from __future__ import annotations

import os

from fastapi import HTTPException, Request, status

from stock_platform.application.access import AccessContext, LocalAccessGuard
from stock_platform.domain.common import Failure

_LOOPBACK_HOSTS = frozenset({"127.0.0.1", "::1", "localhost"})


def runtime_context(request: Request) -> AccessContext:
    """Build an application access context from local HTTP headers."""
    owner_uid = int(request.headers.get("x-platform-owner-uid", str(os.getuid())))
    current_uid = int(request.headers.get("x-platform-effective-uid", str(os.getuid())))
    source_host = request.headers.get("x-platform-source-host")
    if source_host is None:
        client_host = request.client.host if request.client else "127.0.0.1"
        source_host = "127.0.0.1" if client_host in _LOOPBACK_HOSTS else client_host
    return AccessContext(
        owner_uid=owner_uid,
        current_uid=current_uid,
        source_host=source_host,
        csrf_token=request.headers.get("x-csrf-token"),
        idempotency_key=request.headers.get("idempotency-key"),
    )


def enforce_loopback(request: Request, *, write: bool = False) -> None:
    """Reject non-loopback or improper write contexts before business work."""
    context = runtime_context(request)
    result = LocalAccessGuard().check(context, write=write)
    if isinstance(result, Failure):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=result.error.code.value,
        )
