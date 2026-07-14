"""Minimal HTTP JSON helper (httpx)."""

from __future__ import annotations

import time
from typing import Any

import httpx

# Cap sleep so a huge Retry-After (e.g. OpenAlex budget reset at midnight UTC)
# cannot freeze harvest or tests for hours.
MAX_RETRY_WAIT_S = 20.0


class HttpRateLimited(RuntimeError):
    """Hard rate limit / exhausted quota; do not keep sleeping."""


def get_json(
    url: str,
    params: dict[str, Any] | None = None,
    retries: int = 4,
    user_agent: str = "Domain-KB-Harvester/0.1",
) -> dict[str, Any]:
    headers = {
        "User-Agent": user_agent,
        "Accept": "application/json",
    }
    last_err: Exception | None = None
    for attempt in range(retries):
        try:
            with httpx.Client(timeout=45.0, follow_redirects=True, headers=headers) as client:
                resp = client.get(url, params=params)
                if resp.status_code in {429, 503}:
                    ra = resp.headers.get("Retry-After")
                    if ra and str(ra).replace(".", "", 1).isdigit():
                        wait = float(ra)
                    else:
                        wait = 3.0 * (attempt + 1)
                    if wait > MAX_RETRY_WAIT_S:
                        detail = ""
                        try:
                            detail = resp.text[:300]
                        except Exception:
                            pass
                        raise HttpRateLimited(
                            f"{resp.status_code} rate limited (Retry-After={wait}s): {url} {detail}"
                        )
                    time.sleep(wait)
                    continue
                resp.raise_for_status()
                return resp.json()
        except HttpRateLimited:
            raise
        except (httpx.HTTPError, ValueError) as e:
            last_err = e
            time.sleep(0.8 * (attempt + 1))
    raise RuntimeError(f"GET failed after {retries} tries: {url} ({last_err})") from last_err
