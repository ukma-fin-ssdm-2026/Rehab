"""Помилки API. Єдиний формат ErrorResponse та спільні описи відповідей."""

from fastapi import HTTPException

from src.api.models import ErrorResponse


def api_error(status_code: int, code: str, message: str, details=None) -> HTTPException:
    """Створює HTTPException з тілом {code, message, details}."""
    return HTTPException(
        status_code=status_code,
        detail={"code": code, "message": message, "details": details},
    )


# Відповіді, спільні для всіх захищених ендпоінтів (потрапляють в OpenAPI).
COMMON_RESPONSES = {
    401: {
        "model": ErrorResponse,
        "description": "Відсутній або недійсний Bearer-токен",
    },
    422: {"model": ErrorResponse, "description": "Помилка валідації вхідних даних"},
}
