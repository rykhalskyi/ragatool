import asyncio
import os
import time
from typing import Any
from urllib.parse import urlparse

import httpx

from app.internal.url_utils import ensure_url_allowed
from app.schemas.agent import LlmProfileTestResult


def _allow_private_endpoints() -> bool:
    value = os.getenv("RAGATOOL_LLM_ALLOW_PRIVATE_URLS", "")
    return value.strip().lower() in {"1", "true", "yes", "on"}


async def _ensure_endpoint_allowed(url: str) -> None:
    """Reject loopback/private/link-local LLM endpoints unless explicitly allowed.

    This prevents the profile ``base_url`` from being used as an SSRF primitive
    against internal services or cloud metadata endpoints. Public endpoints must
    use HTTPS so the API key is never sent in cleartext.
    """
    allow_private = _allow_private_endpoints()
    try:
        await asyncio.to_thread(ensure_url_allowed, url, allow_private)
    except ValueError as exc:
        raise LlmProviderError(
            "blocked_url", f"The LLM endpoint is not allowed: {exc}"
        ) from exc

    if urlparse(url).scheme.lower() != "https" and not allow_private:
        raise LlmProviderError(
            "blocked_url",
            "Public LLM endpoints must use https://. Set "
            "RAGATOOL_LLM_ALLOW_PRIVATE_URLS=true for local http providers.",
        )


class LlmProviderError(RuntimeError):
    def __init__(self, kind: str, message: str, status_code: int | None = None):
        super().__init__(message)
        self.kind = kind
        self.status_code = status_code


def _timeout(profile: dict) -> httpx.Timeout:
    return httpx.Timeout(
        connect=float(profile["connect_timeout_seconds"]),
        read=float(profile["read_timeout_seconds"]),
        write=float(profile["read_timeout_seconds"]),
        pool=float(profile["connect_timeout_seconds"]),
    )


def _headers(api_key: str) -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


def _raise_for_status(status_code: int) -> None:
    if status_code in {401, 403}:
        raise LlmProviderError(
            "auth",
            "The provider rejected the API key. Check the active LLM profile.",
            status_code,
        )
    if status_code == 429:
        raise LlmProviderError(
            "rate_limit",
            "The provider rate-limited the request. Try again later.",
            status_code,
        )
    raise LlmProviderError(
        "http_error",
        f"The provider returned HTTP {status_code}.",
        status_code,
    )


async def chat_completion(
    profile: dict,
    api_key: str,
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    url = chat_completions_url(profile["base_url"])
    await _ensure_endpoint_allowed(url)
    body: dict[str, Any] = {
        "model": profile["model"],
        "messages": messages,
        "temperature": float(profile["temperature"]),
        "max_tokens": int(profile["max_tokens"]),
    }
    if tools:
        body["tools"] = tools
        body["tool_choice"] = "auto"

    try:
        async with httpx.AsyncClient(timeout=_timeout(profile)) as client:
            response = await client.post(url, json=body, headers=_headers(api_key))
    except httpx.TimeoutException as exc:
        raise LlmProviderError(
            "timeout",
            "The provider timed out. Check the profile timeouts and network.",
        ) from exc
    except httpx.HTTPError as exc:
        raise LlmProviderError(
            "network",
            "Could not reach the provider. Check the base URL and network.",
        ) from exc

    if response.status_code >= 400:
        _raise_for_status(response.status_code)

    try:
        payload = response.json()
    except ValueError as exc:
        raise LlmProviderError(
            "invalid_response", "The provider returned an invalid response."
        ) from exc

    if not isinstance(payload, dict) or not isinstance(payload.get("choices"), list):
        raise LlmProviderError(
            "invalid_response", "The provider returned an unexpected response."
        )
    return payload


def chat_completions_url(base_url: str) -> str:
    base = base_url.rstrip("/")
    if base.endswith("/chat/completions"):
        return base
    return f"{base}/chat/completions"


async def test_connection(profile: dict, api_key: str) -> LlmProfileTestResult:
    url = chat_completions_url(profile["base_url"])
    try:
        await _ensure_endpoint_allowed(url)
    except LlmProviderError as exc:
        return LlmProfileTestResult(ok=False, message=str(exc))
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    body = {
        "model": profile["model"],
        "messages": [{"role": "user", "content": "Reply with the word OK."}],
        "max_tokens": min(16, max(1, int(profile["max_tokens"]))),
        "temperature": 0,
    }

    started = time.perf_counter()
    try:
        timeout = httpx.Timeout(
            connect=float(profile["connect_timeout_seconds"]),
            read=float(profile["read_timeout_seconds"]),
            write=float(profile["read_timeout_seconds"]),
            pool=float(profile["connect_timeout_seconds"]),
        )
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, json=body, headers=headers)
    except httpx.TimeoutException:
        return LlmProfileTestResult(
            ok=False,
            message="The provider timed out. Check the base URL, timeouts, and network.",
        )
    except httpx.HTTPError:
        return LlmProfileTestResult(
            ok=False,
            message="Could not reach the provider. Check the base URL and network.",
        )
    except Exception:
        return LlmProfileTestResult(
            ok=False,
            message="The connection test failed unexpectedly.",
        )

    latency_ms = int((time.perf_counter() - started) * 1000)
    if response.status_code in {401, 403}:
        return LlmProfileTestResult(
            ok=False,
            message="The provider rejected the API key.",
            latency_ms=latency_ms,
        )
    if response.status_code == 429:
        return LlmProfileTestResult(
            ok=False,
            message="The provider rate-limited the request. Try again later.",
            latency_ms=latency_ms,
        )
    if response.status_code >= 400:
        return LlmProfileTestResult(
            ok=False,
            message=f"The provider returned HTTP {response.status_code}.",
            latency_ms=latency_ms,
        )

    model = profile["model"]
    try:
        payload = response.json()
        if isinstance(payload, dict) and isinstance(payload.get("model"), str):
            model = payload["model"]
    except ValueError:
        pass

    return LlmProfileTestResult(
        ok=True,
        message="Connection successful.",
        model=model,
        latency_ms=latency_ms,
    )
