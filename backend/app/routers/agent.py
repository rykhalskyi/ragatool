from sqlite3 import Connection
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.dependencies import get_db
from app.internal.agent import llm_client, profiles, service
from app.schemas.agent import (
    AgentChatRequest,
    AgentChatResponse,
    LlmProfileActivate,
    LlmProfileCreate,
    LlmProfileOut,
    LlmProfileTestResult,
    LlmProfileUpdate,
    LlmProviderOut,
)

router = APIRouter()


@router.get("/providers", response_model=List[LlmProviderOut])
def list_providers() -> List[LlmProviderOut]:
    return profiles.list_providers()


@router.get("/profiles", response_model=List[LlmProfileOut])
def list_profiles(db: Connection = Depends(get_db)) -> List[LlmProfileOut]:
    return profiles.list_profiles(db)


@router.post("/profiles", response_model=LlmProfileOut, status_code=201)
def create_profile(
    payload: LlmProfileCreate, db: Connection = Depends(get_db)
) -> LlmProfileOut:
    try:
        return profiles.create_profile(db, payload)
    except profiles.ProfileValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=500, detail="Could not save the LLM profile.")


@router.patch("/profiles/{profile_id}", response_model=LlmProfileOut)
def update_profile(
    profile_id: str, payload: LlmProfileUpdate, db: Connection = Depends(get_db)
) -> LlmProfileOut:
    try:
        return profiles.update_profile(db, profile_id, payload)
    except profiles.ProfileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except profiles.ProfileValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=500, detail="Could not update the LLM profile.")


@router.delete("/profiles/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_profile(profile_id: str, db: Connection = Depends(get_db)) -> Response:
    try:
        profiles.delete_profile(db, profile_id)
    except profiles.ProfileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/profiles/{profile_id}/activate", response_model=LlmProfileOut)
def activate_profile(
    profile_id: str,
    payload: LlmProfileActivate,
    db: Connection = Depends(get_db),
) -> LlmProfileOut:
    try:
        return profiles.activate_profile(db, profile_id, payload.active)
    except profiles.ProfileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/profiles/{profile_id}/test", response_model=LlmProfileTestResult)
async def test_profile(
    profile_id: str, db: Connection = Depends(get_db)
) -> LlmProfileTestResult:
    try:
        profile = profiles.get_raw_profile(db, profile_id)
        api_key = profiles.decrypt_profile_key(profile)
    except profiles.ProfileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except profiles.ProfileValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return await llm_client.test_connection(profile, api_key)


@router.post("/chat", response_model=AgentChatResponse)
async def chat(
    payload: AgentChatRequest, db: Connection = Depends(get_db)
) -> AgentChatResponse:
    try:
        return await service.run_chat(db, payload)
    except service.AgentConfigurationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except profiles.ProfileValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except service.AgentBusyError as exc:
        raise HTTPException(status_code=429, detail=str(exc))
    except llm_client.LlmProviderError as exc:
        if exc.kind == "auth":
            status_code = 400
        elif exc.kind == "rate_limit":
            status_code = 429
        else:
            status_code = 502
        raise HTTPException(status_code=status_code, detail=str(exc))
