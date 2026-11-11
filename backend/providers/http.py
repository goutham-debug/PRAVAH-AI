"""HTTP retrieval with timeouts, bounded retries, backoff and a small TTL cache.

Uses `requests.get/post` at call time (not a Session) so tests can patch the transport.
Nothing here fabricates a response: failures are returned as FetchResult(ok=False, error=...).
"""
from __future__ import annotations

import hashlib
import json
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional

import requests

RETRY_STATUS = {429, 500, 502, 503, 504}
USER_AGENT = "PRAVAH-AI/1.0 (flood decision support; contact: set PROVIDER_CONTACT)"


@dataclass
class FetchResult:
    ok: bool
    url: str
    status_code: Optional[int] = None
    content: bytes = b""
    elapsed_ms: int = 0
    attempts: int = 0
    error: Optional[str] = None
    fetched_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    from_cache: bool = False

    @property
    def text(self) -> str:
        return self.content.decode("utf-8", errors="replace")

    def json(self) -> Any:
        return json.loads(self.content.decode("utf-8"))

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.content).hexdigest()


class TTLCache:
    def __init__(self):
        self._d: Dict[str, tuple] = {}
        self._lock = threading.Lock()

    def get(self, key: str, ttl: float):
        with self._lock:
            hit = self._d.get(key)
        if hit and time.time() - hit[0] < ttl:
            return hit[1]
        return None

    def put(self, key: str, value):
        with self._lock:
            self._d[key] = (time.time(), value)

    def clear(self):
        with self._lock:
            self._d.clear()


_cache = TTLCache()


def clear_cache():
    _cache.clear()


def fetch(url: str, *, method: str = "GET", params: Optional[dict] = None, headers: Optional[dict] = None,
          data: Any = None, timeout: tuple = (3.5, 15), retries: int = 2, backoff: float = 0.6,
          cache_ttl: float = 0, sleep: Callable[[float], None] = time.sleep,
          max_bytes: int = 64 * 1024 * 1024) -> FetchResult:
    key = None
    if cache_ttl and method == "GET":
        key = hashlib.sha256(f"{url}|{sorted((params or {}).items())}".encode()).hexdigest()
        hit = _cache.get(key, cache_ttl)
        if hit is not None:
            cached = FetchResult(**{**hit.__dict__, "from_cache": True})
            return cached

    h = {"User-Agent": USER_AGENT, **(headers or {})}
    started = time.time()
    last_error = None
    status = None
    attempts = 0
    for attempt in range(retries + 1):
        attempts = attempt + 1
        try:
            fn = requests.post if method == "POST" else requests.get
            kwargs = dict(params=params, headers=h, timeout=timeout)
            if method == "POST":
                kwargs["data"] = data
            resp = fn(url, **kwargs)
            status = resp.status_code
            if status in RETRY_STATUS and attempt < retries:
                last_error = f"HTTP {status}"
                sleep(backoff * (2 ** attempt))
                continue
            if status != 200:
                return FetchResult(False, url, status, b"", int((time.time() - started) * 1000), attempts,
                                   f"HTTP {status}")
            content = resp.content or b""
            if len(content) > max_bytes:
                return FetchResult(False, url, status, b"", int((time.time() - started) * 1000), attempts,
                                   f"Response exceeds {max_bytes} bytes")
            result = FetchResult(True, url, status, content, int((time.time() - started) * 1000), attempts)
            if key:
                _cache.put(key, result)
            return result
        except (requests.Timeout, requests.ConnectionError) as e:
            last_error = f"{type(e).__name__}: {str(e)[:160]}"
            if attempt < retries:
                sleep(backoff * (2 ** attempt))
        except requests.RequestException as e:
            return FetchResult(False, url, status, b"", int((time.time() - started) * 1000), attempts,
                               f"{type(e).__name__}: {str(e)[:160]}")
    return FetchResult(False, url, status, b"", int((time.time() - started) * 1000), attempts, last_error)
