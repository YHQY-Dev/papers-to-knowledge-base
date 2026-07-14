"""Minimal HTTP JSON helper (httpx)."""

from __future__ import annotations

import time
from typing import Any

import httpx


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
                    wait = float(ra) if ra and str(ra).isdigit() else (3.0 * (attempt + 1))
                    time.sleep(wait)
                    continue
                resp.raise_for_status()
                return resp.json()
        except (httpx.HTTPError, ValueError) as e:
            last_err = e
            time.sleep(0.8 * (attempt + 1))
    raise RuntimeError(f"GET failed after {retries} tries: {url} ({last_err})") from last_err
