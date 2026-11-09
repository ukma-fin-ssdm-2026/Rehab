"""Перевірки стану сервісу: /health (без БД) і /ready (SELECT 1).

Підключається в main.py БЕЗ префікса /api/v1. Залежність від сесії БД та ж,
що в security.py, а імпорт шару БД відкладений, тому модуль безпечно
імпортувати з OpenAPI-скрипта й CI без підключення до PostgreSQL.
"""

import requests
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from backend.app.errors import api_error
from backend.app.security import _db_session

router = APIRouter(tags=["Health"])
GMAIL_DISCOVERY_URL = "https://gmail.googleapis.com/$discovery/rest?version=v1"


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
        raise api_error(
            503, "DATABASE_UNAVAILABLE", "База даних тимчасово недоступна"
        ) from None
    return {"status": "ok", "database": "ok"}


@router.get("/health/dependencies")
def dependency_health(db=Depends(_db_session)):
    dependencies = {"database": "ok", "gmail_api": "ok"}
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        dependencies["database"] = "unhealthy"

    try:
        response = requests.get(GMAIL_DISCOVERY_URL, timeout=3)
        response.raise_for_status()
        payload = response.json()
        if (
            not isinstance(payload, dict)
            or payload.get("name") != "gmail"
            or payload.get("version") != "v1"
        ):
            dependencies["gmail_api"] = "unhealthy"
    except (requests.RequestException, ValueError):
        dependencies["gmail_api"] = "unhealthy"

    healthy = all(value == "ok" for value in dependencies.values())
    return JSONResponse(
        status_code=200 if healthy else 503,
        content={
            "status": "healthy" if healthy else "unhealthy",
            "dependencies": dependencies,
        },
    )
