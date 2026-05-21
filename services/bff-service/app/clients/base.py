"""Shared HTTP helper for the upstream-service clients.

The BFF owns no database; every read is a fan-out to prediction, fixture and
ledger. This helper centralises timeout handling and error translation so an
upstream failure surfaces as a sensible HTTP status rather than a 500.
"""

import httpx
from fastapi import HTTPException

from app.config import settings


def request(
    method: str,
    base_url: str,
    path: str,
    *,
    token: str | None = None,
    admin_key: str | None = None,
    params: dict | None = None,
    json: dict | None = None,
):
    """Call an upstream service and return the parsed JSON body (or None)."""
    headers: dict[str, str] = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if admin_key:
        headers["X-Admin-Api-Key"] = admin_key
    try:
        with httpx.Client(
            base_url=base_url, timeout=settings.http_timeout_seconds
        ) as client:
            response = client.request(
                method, path, params=params, json=json, headers=headers
            )
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502, detail=f"upstream service unavailable: {exc}"
        ) from exc
    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    if response.status_code == 204 or not response.content:
        return None
    return response.json()
