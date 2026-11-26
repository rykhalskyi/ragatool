import pytest

from app.internal.agent import llm_client


@pytest.mark.asyncio
async def test_blocks_private_endpoint_by_default(monkeypatch):
    monkeypatch.delenv("RAGATOOL_LLM_ALLOW_PRIVATE_URLS", raising=False)

    with pytest.raises(llm_client.LlmProviderError) as excinfo:
        await llm_client._ensure_endpoint_allowed(
            "http://127.0.0.1:11434/v1/chat/completions"
        )

    assert excinfo.value.kind == "blocked_url"


@pytest.mark.asyncio
async def test_blocks_public_http_endpoint(monkeypatch):
    monkeypatch.delenv("RAGATOOL_LLM_ALLOW_PRIVATE_URLS", raising=False)

    with pytest.raises(llm_client.LlmProviderError) as excinfo:
        await llm_client._ensure_endpoint_allowed("http://8.8.8.8/v1/chat/completions")

    assert excinfo.value.kind == "blocked_url"


@pytest.mark.asyncio
async def test_allows_public_https_endpoint(monkeypatch):
    monkeypatch.delenv("RAGATOOL_LLM_ALLOW_PRIVATE_URLS", raising=False)

    await llm_client._ensure_endpoint_allowed(
        "https://8.8.8.8/v1/chat/completions"
    )


@pytest.mark.asyncio
async def test_allows_private_endpoint_when_opted_in(monkeypatch):
    monkeypatch.setenv("RAGATOOL_LLM_ALLOW_PRIVATE_URLS", "true")

    await llm_client._ensure_endpoint_allowed(
        "http://127.0.0.1:11434/v1/chat/completions"
    )
