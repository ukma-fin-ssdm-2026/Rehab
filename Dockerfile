FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements-ci-hashes.lock ./
RUN python -m pip install --no-cache-dir --disable-pip-version-check --require-hashes --only-binary=:all: -r requirements-ci-hashes.lock

COPY backend/ ./backend/
COPY alembic/ ./alembic/
COPY alembic.ini ./

RUN addgroup --system app && adduser --system --ingroup app app
USER app

EXPOSE 8000

CMD ["sh", "-c", "exec uvicorn backend.app.main:app --host 0.0.0.0 --port \"${PORT:-8000}\""]
