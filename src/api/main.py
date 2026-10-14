"""Точка входу REST API застосунку «Рехаб».

Запуск (з кореня репозиторію):
    uvicorn src.api.main:app --reload

Swagger UI:   http://127.0.0.1:8000/docs
OpenAPI JSON: http://127.0.0.1:8000/openapi.json

При імпорті модуля не відбувається побічних ефектів (БД, мережа),
тому `app` безпечно імпортувати зі скрипта експорту та з CI.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.api.routers import calendar, goals

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


app.include_router(calendar.router, prefix=API_PREFIX)
app.include_router(goals.router, prefix=API_PREFIX)
