import time

import httpx

from app.schemas.agent import LlmProfileTestResult


def chat_completions_url(base_url: str) -> str:
    base = base_url.rstrip("/")
    if base.endswith("/chat/completions"):
        return base
    return f"{base}/chat/completions"


async def test_connection(profile: dict, api_key: str) -> LlmProfileTestResult:
    url = chat_completions_url(profile["base_url"])
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
