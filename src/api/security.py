"""Авторизація (заглушка JWT) для SEC-001.

Замість справжнього JWT використовується токен виду `<роль>-<id>`:
    user-42, mentor-7, admin-1
У продакшені тут буде перевірка підпису JWT, терміну дії та ролі з claims.
Механізм (схема Bearer, залежність get_current_user, перевірка ролей)
залишається таким самим, тож заміна не змінює ендпоінти.
"""

from dataclasses import dataclass

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

ALLOWED_ROLES = {"user", "mentor", "admin"}

# Схема безпеки для OpenAPI: додає кнопку Authorize у Swagger UI.
bearer_scheme = HTTPBearer(
    scheme_name="BearerAuth",
    bearerFormat="JWT",
    description="Токен-заглушка у форматі `<роль>-<id>`, наприклад `user-42` або `mentor-7`.",
    auto_error=False,
)


@dataclass
class CurrentUser:
    """Користувач, отриманий з токена."""

    user_id: int
    role: str


def _unauthorized(message: str) -> HTTPException:
    return HTTPException(
        status_code=401,
        detail={"code": "UNAUTHORIZED", "message": message},
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> CurrentUser:
    """Повертає поточного користувача або відповідає 401."""
    if credentials is None:
        raise _unauthorized("Відсутній заголовок Authorization: Bearer <token>")

    role, _, raw_id = credentials.credentials.partition("-")
    if role not in ALLOWED_ROLES or not raw_id.isdigit():
        raise _unauthorized("Недійсний токен")

    return CurrentUser(user_id=int(raw_id), role=role)


def require_role(*roles: str):
    """Залежність для перевірки ролі. Відповідає 403, якщо роль не підходить.

    Приклад: Depends(require_role("admin")). У цій лабораторній роботі
    адмінських ендпоінтів немає, але механізм готовий до розширення.
    """

    def checker(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if user.role not in roles:
            raise HTTPException(
                status_code=403,
                detail={
                    "code": "FORBIDDEN",
                    "message": "Недостатньо прав для цієї дії",
                },
            )
        return user

    return checker
