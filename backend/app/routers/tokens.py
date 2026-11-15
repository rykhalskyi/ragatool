from fastapi import APIRouter, Depends, HTTPException, status

from app.crud import crud_token
from app.database import get_db_connection
from app.internal.auth import (
    generate_token,
    hash_token,
    require_user,
    token_prefix,
)
from app.schemas.auth import TokenCreate, TokenCreated, TokenOut

router = APIRouter(dependencies=[Depends(require_user)])


@router.get("", response_model=list[TokenOut])
def list_tokens() -> list[TokenOut]:
    with get_db_connection() as db:
        return [TokenOut(**row) for row in crud_token.list_tokens(db)]


@router.post("", response_model=TokenCreated)
def create_token(payload: TokenCreate) -> TokenCreated:
    token = generate_token()
    with get_db_connection() as db:
        row = crud_token.create_token(
            db, payload.name.strip(), hash_token(token), token_prefix(token)
        )
    return TokenCreated(**row, token=token)


@router.delete("/{token_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_token(token_id: str) -> None:
    with get_db_connection() as db:
        revoked = crud_token.revoke_token(db, token_id)
    if not revoked:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Token not found or already revoked",
        )
