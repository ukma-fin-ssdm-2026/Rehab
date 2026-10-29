"""Account registration and signed JWT session endpoints.

Sofia integrates this router into backend/app/main.py after DB foundation is merged.
"""
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.exc import IntegrityError

from backend.app.schemas.auth import (
    RegisterRequest, LoginRequest, LoginResponse, UserPublic, MeResponse,
)
from backend.app.security import (
    ACCESS_TOKEN_SECONDS, CurrentUser, _db_session,
    create_access_token, get_current_user,
)
from backend.app.services.auth import authenticate, hash_password
from backend.app.repositories.users import (
    create_user, get_user, get_user_by_email, revoke_sessions,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", status_code=201, response_model=UserPublic)
def register(data: RegisterRequest, db=Depends(_db_session)):
    from backend.app.core.clock import today_local
    if get_user_by_email(db, data.email) is not None:
        raise HTTPException(
            status_code=409,
            detail={"code": "EMAIL_ALREADY_EXISTS", "message": "Ця адреса вже зареєстрована", "details": None},
        )
    try:
        account = create_user(
            db, name=data.name, nickname=data.nickname, email=data.email,
            password_hash=hash_password(data.password), tracking_start_date=today_local(),
        )
        db.commit()
        db.refresh(account)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail={"code": "EMAIL_ALREADY_EXISTS", "message": "Ця адреса вже зареєстрована", "details": None},
        ) from exc
    return account


@router.post("/login", response_model=LoginResponse)
def login(data: LoginRequest, db=Depends(_db_session)):
    account = authenticate(db, data.email, data.password)
    return LoginResponse(
        access_token=create_access_token(account.user_id, account.token_version),
        expires_in=ACCESS_TOKEN_SECONDS,
        user=UserPublic.model_validate(account),
    )


@router.get("/me", response_model=MeResponse)
def me(user: CurrentUser = Depends(get_current_user), db=Depends(_db_session)):
    from backend.app.core.clock import today_local
    account = get_user(db, user.user_id)
    return MeResponse(**UserPublic.model_validate(account).model_dump(), current_date=today_local())


@router.post("/logout", status_code=204)
def logout(user: CurrentUser = Depends(get_current_user), db=Depends(_db_session)):
    account = get_user(db, user.user_id)
    revoke_sessions(db, account)
    db.commit()
    return Response(status_code=204)
