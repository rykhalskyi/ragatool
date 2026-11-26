import copy

import pytest
from cryptography.fernet import Fernet

import app.database as database
from app.crud import crud_setting
from app.internal.agent import llm_client, profiles, service, tool_bridge
from app.schemas.agent import (
    AgentChatHistoryMessage,
    AgentChatRequest,
    LlmProfileCreate,
)
from app.schemas.setting import SettingCreate, SettingsName


@pytest.fixture
def db(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DATABASE_URL", str(tmp_path / "agent.db"))
    monkeypatch.setenv("RAGATOOL_ENCRYPTION_KEY", Fernet.generate_key().decode())
    database.create_tables()
    connection = database.get_db_connection()
    yield connection
    connection.close()


def make_profile(db):
    return profiles.create_profile(
        db,
        LlmProfileCreate(
            name="Mock",
            provider="openai",
            base_url="https://example.invalid/v1",
            api_key="sk-secret-1234",
            model="mock-model",
            temperature=0.2,
            max_tokens=512,
            connect_timeout_seconds=5,
            read_timeout_seconds=5,
        ),
    )


def tool_call_response(name="query_collection", arguments=None, model="mock-model"):
    return {
        "model": model,
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call-1",
                            "type": "function",
                            "function": {
                                "name": name,
                                "arguments": arguments
                                or '{"collection_name": "books", "query_text": "dune"}',
                            },
                        }
                    ],
                }
            }
        ],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "total_tokens": 15,
        },
    }


def final_response(content="Final answer", model="mock-model"):
    return {
        "model": model,
        "choices": [{"message": {"role": "assistant", "content": content}}],
        "usage": {
            "prompt_tokens": 7,
            "completion_tokens": 3,
            "total_tokens": 10,
        },
    }


@pytest.mark.asyncio
async def test_agent_loop_executes_tool_and_returns_final_answer(db, monkeypatch):
    make_profile(db)
    calls = []
    executed = []

    async def fake_chat(profile, api_key, messages, tools):
        calls.append(
            {
                "messages": copy.deepcopy(messages),
                "tools": copy.deepcopy(tools),
            }
        )
        if len(calls) == 1:
            return tool_call_response()
        return final_response()

    async def fake_list_tools():
        return [{"type": "function", "function": {"name": "query_collection"}}]

    async def fake_execute(name, arguments):
        executed.append((name, arguments))
        return {
            "ok": True,
            "content": '{"status": "success", "results": []}',
            "error": None,
        }

    monkeypatch.setattr(llm_client, "chat_completion", fake_chat)
    monkeypatch.setattr(tool_bridge, "list_openai_tools", fake_list_tools)
    monkeypatch.setattr(tool_bridge, "execute_tool", fake_execute)

    response = await service.run_chat(
        db,
        AgentChatRequest(message="What is Dune about?", collection_name="Books"),
    )

    assert response.message == "Final answer"
    assert response.model == "mock-model"
    assert response.usage.total_tokens == 25
    assert len(response.tool_calls) == 1
    assert response.tool_calls[0].name == "query_collection"
    assert response.tool_calls[0].status == "success"
    assert executed == [
        ("query_collection", {"collection_name": "books", "query_text": "dune"})
    ]
    assert response.warnings == []

    system_prompt = calls[0]["messages"][0]["content"]
    assert "Books" in system_prompt

    second_messages = calls[1]["messages"]
    assert second_messages[-2]["role"] == "assistant"
    assert second_messages[-2]["tool_calls"][0]["id"] == "call-1"
    assert second_messages[-1]["role"] == "tool"
    assert second_messages[-1]["tool_call_id"] == "call-1"


@pytest.mark.asyncio
async def test_agent_loop_rejects_missing_profile(db):
    with pytest.raises(service.AgentConfigurationError):
        await service.run_chat(db, AgentChatRequest(message="hello"))


@pytest.mark.asyncio
async def test_agent_loop_warns_and_stops_after_max_rounds(db, monkeypatch):
    make_profile(db)
    calls = []

    async def fake_chat(profile, api_key, messages, tools):
        calls.append(tools)
        if tools is None:
            return final_response("Summary after limit")
        return tool_call_response()

    async def fake_list_tools():
        return [{"type": "function", "function": {"name": "query_collection"}}]

    async def fake_execute(name, arguments):
        return {"ok": True, "content": "{}", "error": None}

    monkeypatch.setattr(llm_client, "chat_completion", fake_chat)
    monkeypatch.setattr(tool_bridge, "list_openai_tools", fake_list_tools)
    monkeypatch.setattr(tool_bridge, "execute_tool", fake_execute)

    response = await service.run_chat(db, AgentChatRequest(message="loop"))

    assert response.message == "Summary after limit"
    assert len(response.tool_calls) == service.MAX_TOOL_ROUNDS
    assert calls[-1] is None
    assert any("tool-call limit" in warning for warning in response.warnings)


@pytest.mark.asyncio
async def test_agent_loop_respects_configured_tool_rounds(db, monkeypatch):
    make_profile(db)
    crud_setting.update_settings(
        db,
        [SettingCreate(name=SettingsName.AGENT_MAX_TOOL_ROUNDS.value, value="2")],
    )

    async def fake_chat(profile, api_key, messages, tools):
        if tools is None:
            return final_response("Summary after limit")
        return tool_call_response()

    async def fake_list_tools():
        return [{"type": "function", "function": {"name": "query_collection"}}]

    async def fake_execute(name, arguments):
        return {"ok": True, "content": "{}", "error": None}

    monkeypatch.setattr(llm_client, "chat_completion", fake_chat)
    monkeypatch.setattr(tool_bridge, "list_openai_tools", fake_list_tools)
    monkeypatch.setattr(tool_bridge, "execute_tool", fake_execute)

    response = await service.run_chat(db, AgentChatRequest(message="loop"))

    assert response.message == "Summary after limit"
    assert len(response.tool_calls) == 2


@pytest.mark.asyncio
async def test_agent_loop_returns_fallback_when_final_answer_is_empty(db, monkeypatch):
    make_profile(db)
    captured = []

    async def fake_chat(profile, api_key, messages, tools):
        if tools is not None:
            return tool_call_response()
        captured.append(copy.deepcopy(messages))
        return final_response("   ")

    async def fake_list_tools():
        return [{"type": "function", "function": {"name": "query_collection"}}]

    async def fake_execute(name, arguments):
        return {"ok": True, "content": "{}", "error": None}

    monkeypatch.setattr(llm_client, "chat_completion", fake_chat)
    monkeypatch.setattr(tool_bridge, "list_openai_tools", fake_list_tools)
    monkeypatch.setattr(tool_bridge, "execute_tool", fake_execute)

    response = await service.run_chat(db, AgentChatRequest(message="loop"))

    assert response.message == service.EMPTY_ANSWER_FALLBACK
    assert captured[-1][-1] == {
        "role": "user",
        "content": service.TOOL_LIMIT_INSTRUCTION,
    }


@pytest.mark.asyncio
async def test_agent_loop_trims_history(db, monkeypatch):
    make_profile(db)
    captured = []

    async def fake_chat(profile, api_key, messages, tools):
        captured.append(copy.deepcopy(messages))
        return final_response()

    async def fake_list_tools():
        return []

    monkeypatch.setattr(llm_client, "chat_completion", fake_chat)
    monkeypatch.setattr(tool_bridge, "list_openai_tools", fake_list_tools)

    history = [
        AgentChatHistoryMessage(role="user" if index % 2 == 0 else "assistant", content="x" * 1000)
        for index in range(30)
    ]
    response = await service.run_chat(
        db, AgentChatRequest(message="recent question", history=history)
    )

    assert any("older conversation" in warning.lower() for warning in response.warnings)
    replayed = captured[0]
    assert len(replayed) == 1 + service.MAX_HISTORY_MESSAGES + 1
    assert replayed[-1]["content"] == "recent question"


@pytest.mark.asyncio
async def test_agent_loop_returns_tool_errors_as_data(db, monkeypatch):
    make_profile(db)

    async def fake_chat(profile, api_key, messages, tools):
        if len(messages) < 4:
            return tool_call_response(arguments="not-json")
        return final_response("Recovered")

    async def fake_list_tools():
        return []

    monkeypatch.setattr(llm_client, "chat_completion", fake_chat)
    monkeypatch.setattr(tool_bridge, "list_openai_tools", fake_list_tools)

    response = await service.run_chat(db, AgentChatRequest(message="bad args"))

    assert response.message == "Recovered"
    assert response.tool_calls[0].status == "error"


@pytest.mark.asyncio
async def test_tool_call_truncation_keeps_ids_consistent(db, monkeypatch):
    make_profile(db)
    crud_setting.update_settings(
        db,
        [
            SettingCreate(
                name=SettingsName.AGENT_MAX_TOOL_CALLS_PER_ROUND.value, value="2"
            )
        ],
    )
    captured = []

    def many_calls_response():
        return {
            "model": "mock-model",
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [
                            {
                                "id": f"call-{index}",
                                "type": "function",
                                "function": {
                                    "name": "query_collection",
                                    "arguments": "{}",
                                },
                            }
                            for index in range(4)
                        ],
                    }
                }
            ],
        }

    async def fake_chat(profile, api_key, messages, tools):
        captured.append(copy.deepcopy(messages))
        if len(captured) > 1:
            return final_response("done")
        return many_calls_response()

    async def fake_list_tools():
        return [{"type": "function", "function": {"name": "query_collection"}}]

    async def fake_execute(name, arguments):
        return {"ok": True, "content": "{}", "error": None}

    monkeypatch.setattr(llm_client, "chat_completion", fake_chat)
    monkeypatch.setattr(tool_bridge, "list_openai_tools", fake_list_tools)
    monkeypatch.setattr(tool_bridge, "execute_tool", fake_execute)

    response = await service.run_chat(db, AgentChatRequest(message="many"))

    second = captured[1]
    assistant = next(
        message
        for message in second
        if message["role"] == "assistant" and message.get("tool_calls")
    )
    tool_messages = [message for message in second if message["role"] == "tool"]

    assert len(assistant["tool_calls"]) == 2
    assert [call["id"] for call in assistant["tool_calls"]] == [
        message["tool_call_id"] for message in tool_messages
    ]
    assert len(response.tool_calls) == 2
    assert response.message == "done"
