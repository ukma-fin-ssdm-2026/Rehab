"""JWT access control shared by Rehab routers.

Database infrastructure is supplied by the database workstream. No database
connection is created while importing this module (OpenAPI export remains safe).
"""
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

ALLOWED_ROLES = {"user", "mentor", "admin"}
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_SECONDS = 3600

bearer_scheme = HTTPBearer(
    scheme_name="BearerAuth", bearerFormat="JWT",
    description="Підписаний JWT-токен доступу.", auto_error=False,
)


@dataclass(frozen=True)
class CurrentUser:
    user_id: int
    role: str


def _unauthorized(message: str = "Недійсна або прострочена сесія") -> HTTPException:
    return HTTPException(
        status_code=401,
        detail={"code": "UNAUTHORIZED", "message": message, "details": None},
        headers={"WWW-Authenticate": "Bearer"},
    )


def _secret() -> str:
    secret = os.getenv("JWT_SECRET", "")
    if len(secret) < 32:
        raise RuntimeError("JWT_SECRET має бути заданий і містити щонайменше 32 символи")
    return secret


def create_access_token(user_id: int, token_version: int) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "sub": str(user_id),
            "iat": now,
            "exp": now + timedelta(seconds=ACCESS_TOKEN_SECONDS),
            "token_version": token_version,
        },
        _secret(),
        algorithm=JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> tuple[int, int]:
    try:
        claims = jwt.decode(
            token, _secret(), algorithms=[JWT_ALGORITHM],
            options={"require": ["sub", "iat", "exp", "token_version"]},
        )
        sub, version = claims["sub"], claims["token_version"]
        if not isinstance(sub, str) or not sub.isdecimal() or int(sub) <= 0:
            raise ValueError("invalid sub")
        if type(version) is not int or version < 0:
            raise ValueError("invalid token_version")
        return int(sub), version
    except (jwt.PyJWTError, ValueError, KeyError, TypeError) as exc:
        raise _unauthorized() from exc


def _db_session():
    """Delegates to Polina's per-request Session dependency once integrated."""
    from backend.app.db.session import get_db
    yield from get_db()


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db=Depends(_db_session),
) -> CurrentUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _unauthorized("Відсутній або некоректний Bearer-токен")
    user_id, version = decode_access_token(credentials.credentials)
    from backend.app.repositories.users import get_user
    account = get_user(db, user_id)
    if account is None or account.token_version != version:
        raise _unauthorized()
    if account.is_blocked:
        raise HTTPException(
            status_code=403,
            detail={"code": "ACCOUNT_BLOCKED", "message": "Ваш акаунт заблоковано", "details": None},
        )
    if account.role not in ALLOWED_ROLES:
        raise _unauthorized()
    return CurrentUser(user_id=account.user_id, role=account.role)


def require_role(*roles: str):
    def checker(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if user.role not in roles:
            raise HTTPException(
                status_code=403,
                detail={"code": "FORBIDDEN", "message": "Недостатньо прав", "details": None},
            )
        return user
    return checker
