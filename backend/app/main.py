"""Точка входу REST API застосунку «Рехаб».

Запуск (з кореня репозиторію):
    uvicorn backend.app.main:app --reload

Swagger UI:   http://127.0.0.1:8000/docs
OpenAPI JSON: http://127.0.0.1:8000/openapi.json

При імпорті модуля не відбувається побічних ефектів (БД, мережа),
тому `app` безпечно імпортувати зі скрипта експорту та з CI.
"""

import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.routers import admin, auth, goals, health, statistics

# AI-GENERATED START
# KT-1: календар на PostgreSQL (Поліна) замість in-memory stubs.
from backend.app.routers import calendar_postgres as calendar

# AI-GENERATED END

API_PREFIX = "/api/v1"


tags_metadata = [
    {
        "name": "Calendar",
        "description": (
            "Щоденні відмітки користувача (DayRecord): тверезий день або зрив. "
            "FR-001, FR-002, FR-003, FR-008."
        ),
    },
    {
        "name": "Goals",
        "description": (
            "Цілі тверезості (Goal): цільова кількість днів і прогрес. "
            "FR-004, FR-005."
        ),
    },
    {
        "name": "Admin",
        "description": (
            "Лише для ролі admin: акаунти, блокування й анонімна діаграма "
            "тригерів за 30 днів."
        ),
    },
    {
        "name": "Health",
        "description": "Перевірки стану сервісу: /health і /ready.",
    },
    {
        "name": "Statistics",
        "description": (
            "Статистика тверезості: кількість днів, серії "
            "та автоматичні цілі на 7 і 30 днів."
        ),
    },
]


app = FastAPI(
    title="Rehab API",
    summary="REST API застосунку для відстеження періоду тверезості.",
    description=(
        "Code-First API: специфікація OpenAPI генерується автоматично з коду.\n\n"
        "Архітектура: Layered Monolith (ADR-001), СУБД PostgreSQL (ADR-002). "
        "У цій версії замість БД використовуються дані-заглушки в пам'яті."
    ),
    version="1.0.0",
    openapi_tags=tags_metadata,
)


# AI-GENERATED START
def cors_origins() -> list[str]:
    """Локальні адреси для розробки + точні адреси клієнта з CORS_ORIGINS."""
    local = ["http://localhost:8081", "http://127.0.0.1:8081"]
    extra = [
        origin.strip().rstrip("/")
        for origin in os.getenv("CORS_ORIGINS", "").split(",")
        if origin.strip() and origin.strip() != "*"
    ]
    return [*local, *extra]


# AI-GENERATED END

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(
    request: Request,
    exc: HTTPException,
):
    """Перетворює HTTPException у єдиний формат ErrorResponse."""

    if isinstance(exc.detail, dict) and "code" in exc.detail:
        content = {
            "code": exc.detail.get("code"),
            "message": exc.detail.get("message"),
            "details": exc.detail.get("details"),
        }
    else:
        content = {
            "code": "HTTP_ERROR",
            "message": str(exc.detail),
            "details": None,
        }

    return JSONResponse(
        status_code=exc.status_code,
        content=content,
        headers=exc.headers,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    """Перетворює помилки валідації FastAPI/Pydantic у ErrorResponse."""

    details = []

    for error in exc.errors():
        details.append(
            {
                "field": ".".join(str(part) for part in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            }
        )

    return JSONResponse(
        status_code=422,
        content={
            "code": "VALIDATION_ERROR",
            "message": "Помилка валідації вхідних даних",
            "details": details,
        },
    )


# AI-GENERATED START
app.include_router(auth.router, prefix=API_PREFIX)
# AI-GENERATED END
app.include_router(calendar.router, prefix=API_PREFIX)
app.include_router(goals.router, prefix=API_PREFIX)
app.include_router(statistics.router, prefix=API_PREFIX)

# AI-GENERATED START
app.include_router(health.router)
app.include_router(admin.router, prefix=API_PREFIX)
# AI-GENERATED END
