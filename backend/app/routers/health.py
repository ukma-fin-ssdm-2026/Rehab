# AI-GENERATED START
"""Перевірки стану сервісу: /health (без БД) і /ready (SELECT 1).

Підключається в main.py БЕЗ префікса /api/v1. Залежність від сесії БД та ж,
що в security.py, а імпорт шару БД відкладений, тому модуль безпечно
імпортувати з OpenAPI-скрипта й CI без підключення до PostgreSQL.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from backend.app.errors import api_error
from backend.app.security import _db_session

router = APIRouter(tags=["Health"])


@router.get("/health")
def health() -> dict:
    """Процес працює. До БД не звертається."""
    return {"status": "ok"}


@router.get("/ready")
def ready(db=Depends(_db_session)) -> dict:
    """Сервіс готовий: БД відповідає на SELECT 1."""
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        # Текст помилки й рядок підключення клієнту не віддаємо.
        raise api_error(
            503, "DATABASE_UNAVAILABLE", "База даних тимчасово недоступна"
        ) from None
    return {"status": "ok", "database": "ok"}


# AI-GENERATED END
