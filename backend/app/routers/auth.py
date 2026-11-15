from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from app.crud import crud_user
from app.database import db_session
from app.internal.auth import (
    LOGIN_IP_LIMITER,
    LOGIN_USER_LIMITER,
    check_request_origin,
    clear_session_cookie,
    clear_setup_code,
    create_session,
    delete_current_session,
    get_dummy_password_hash,
    hash_password,
    require_user,
    set_session_cookie,
    verify_password,
    verify_setup_code,
)
from app.schemas.auth import AuthStatus, LoginRequest, SetupRequest, UserOut

router = APIRouter()


@router.get("/status", response_model=AuthStatus)
def auth_status() -> AuthStatus:
    with db_session() as db:
        return AuthStatus(initialized=crud_user.count_users(db) > 0)


@router.post("/setup", response_model=UserOut)
def setup(request: Request, response: Response, payload: SetupRequest) -> UserOut:
    check_request_origin(request)

    with db_session() as db:
        if crud_user.count_users(db) > 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Setup has already been completed",
            )
        if not verify_setup_code(payload.setup_code):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid setup code",
            )

        user = crud_user.create_first_user(
            db, payload.username.strip(), hash_password(payload.password)
        )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Setup has already been completed",
        )

    clear_setup_code()
    set_session_cookie(response, create_session(user))
    return UserOut(id=user["id"], username=user["username"])


@router.post("/login", response_model=UserOut)
def login(request: Request, response: Response, payload: LoginRequest) -> UserOut:
    check_request_origin(request)

    client_ip = request.client.host if request.client else "unknown"
    username = payload.username.strip()
    user_key = f"{client_ip}:{username.lower()}"

    retry_after = LOGIN_IP_LIMITER.consume(client_ip)
    if not retry_after:
        retry_after = LOGIN_USER_LIMITER.consume(user_key)
    if retry_after:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Try again later.",
            headers={"Retry-After": str(retry_after)},
        )

    with db_session() as db:
        user = crud_user.get_user_by_username(db, username)

    # Always run bcrypt so unknown users and wrong passwords take similar time.
    if user is None:
        verify_password(payload.password, get_dummy_password_hash())
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    if not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    LOGIN_USER_LIMITER.reset(user_key)
    set_session_cookie(response, create_session(user))
    return UserOut(id=user["id"], username=user["username"])


@router.post("/logout")
def logout(request: Request, response: Response) -> dict:
    delete_current_session(request)
    clear_session_cookie(response)
    return {"status": "success"}


@router.get("/me", response_model=UserOut)
def me(user: dict = Depends(require_user)) -> UserOut:
    return UserOut(id=user["id"], username=user["username"])
