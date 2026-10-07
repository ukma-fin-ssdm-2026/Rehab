"""Точка входу REST API застосунку «Рехаб».

Запуск (з кореня репозиторію):
    uvicorn src.api.main:app --reload

Swagger UI:   http://127.0.0.1:8000/docs
OpenAPI JSON: http://127.0.0.1:8000/openapi.json

При імпорті модуля не відбувається побічних ефектів (БД, мережа),
тому `app` безпечно імпортувати зі скрипта експорту та з CI.
"""
from fastapi import FastAPI

from src.api.routers import calendar, goals

API_PREFIX = "/api/v1"

tags_metadata = [
    {
        "name": "Calendar",
        "description": "Щоденні відмітки користувача (DayRecord): тверезий день або зрив. "
                       "FR-001, FR-002, FR-003, FR-008.",
    },
    {
        "name": "Goals",
        "description": "Цілі тверезості (Goal): цільова кількість днів і прогрес. FR-004, FR-005.",
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

app.include_router(calendar.router, prefix=API_PREFIX)
app.include_router(goals.router, prefix=API_PREFIX)