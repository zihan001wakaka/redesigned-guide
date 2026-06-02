from __future__ import annotations

import json
import ssl
import time
import urllib.parse
import urllib.request
from typing import Any
from urllib.error import URLError


DEFAULT_HEADERS = {
    "User-Agent": "DailyAIBrief/0.1 (+https://my.feishu.cn/)",
}


def ssl_context() -> ssl.SSLContext:
    try:
        import certifi  # type: ignore

        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


def get_text(url: str, headers: dict[str, str] | None = None, timeout: int = 20) -> str:
    data = request_bytes("GET", url, headers=headers, timeout=timeout)
    return data.decode("utf-8", errors="replace")


def get_bytes(url: str, headers: dict[str, str] | None = None, timeout: int = 30) -> bytes:
    return request_bytes("GET", url, headers=headers, timeout=timeout)


def get_json(url: str, headers: dict[str, str] | None = None, timeout: int = 20) -> Any:
    return json.loads(get_text(url, headers=headers, timeout=timeout))


def post_json(url: str, payload: dict[str, Any], headers: dict[str, str] | None = None, timeout: int = 20) -> Any:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    return json.loads(
        request_bytes(
            "POST",
            url,
            body=body,
            headers={**DEFAULT_HEADERS, "Content-Type": "application/json; charset=utf-8", **(headers or {})},
            timeout=timeout,
        ).decode("utf-8", errors="replace")
    )


def request_bytes(
    method: str,
    url: str,
    body: bytes | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = 20,
    retries: int = 3,
) -> bytes:
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        request = urllib.request.Request(
            url,
            data=body,
            headers={**DEFAULT_HEADERS, **(headers or {})},
            method=method,
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout, context=ssl_context()) as response:
                return response.read()
        except URLError as exc:
            last_error = exc
            if attempt == retries:
                break
            time.sleep(0.8 * attempt)
    assert last_error is not None
    raise last_error

def urlencode(params: dict[str, str | int]) -> str:
    return urllib.parse.urlencode(params)


def polite_pause(seconds: float = 0.2) -> None:
    time.sleep(seconds)
