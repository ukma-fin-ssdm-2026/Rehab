# Rehab — налаштування та запуск

Для спільної розробки використовуйте `develop`, для прийнятого релізу — `main`.
Запускайте сервер `backend.app.main:app` із кореня Rehab, не історичний `src/api`.

## 1. Залежності

Python 3.12, Node.js 22 (не нижче 22.13), npm, Docker Desktop, Git. Команди нижче для PowerShell.
Для перевірки на iPhone використовується Safari та публічна HTTPS-версія;
Expo Go й Android для приймання не потрібні.

```powershell
git clone https://github.com/ukma-fin-ssdm-2026/Rehab
cd Rehab
git switch develop
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

У `.env` замініть обидва паролі й відповідні URL. Dev та test — різні БД;
`TEST_DATABASE_URL` закінчується на `_test` і не має вказувати на Neon.
Додайте випадковий `JWT_SECRET` щонайменше 32 символи та локальні CORS origins.
Не комітьте `.env`. Секрети не повинні мати префікс `EXPO_PUBLIC_`.

```powershell
docker compose up -d postgres-dev postgres-test
.venv/Scripts/python.exe -m alembic upgrade head
.venv/Scripts/python.exe -m alembic -x test_db=true upgrade head
.venv/Scripts/python.exe -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

Очікуваний head: `0002_team_foundation`. Це не створення таблиць через create_all.
`/health` перевіряє процес, `/ready` — доступність БД. Swagger: http://127.0.0.1:8000/docs.

## 2. Frontend — другий термінал

```powershell
cd frontend
npm ci
```

У `frontend/.env.local`:

```dotenv
EXPO_PUBLIC_API_URL=http://127.0.0.1:8000
```

Адреса без `/api/v1`: його додає спільний API-клієнт. При зміні env перезапустіть Expo.

```powershell
npm run web
```

Використовуйте адресу й порт із виводу Expo (зазвичай http://localhost:8081).
Для іншого порту додайте точний origin до `CORS_ORIGINS` backend.

## 3. Акаунти й перевірка

Зареєструйте два окремі синтетичні акаунти через UI. Захищені запити використовують
JWT після `/api/v1/auth/login`; `user-42` не є дійсною сесією.
Для демо-адміна й пар `scripts/seed_demo.py` читає приватні `SEED_*` змінні;
див. його заголовок. Seed ідемпотентний, не очищає дані й не надсилає листів.

Сценарій приймання: [тест-план](docs/validation/test-plan.md).
Кожна вкладка має власну сесію; для ментора, підопічного й admin можна використати
окремі вкладки браузера. Відсутність календарного запису означає тверезий день.

## 4. Автоматичні перевірки

Із кореня:

```powershell
.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider
.venv/Scripts/python.exe scripts/export_openapi.py
.venv/Scripts/python.exe scripts/check_traceability.py
```

У frontend:

```powershell
npm run test:api
npm run typecheck
npm run lint
npm run export:web
```

Pytest очищає тільки захищену тестову БД. Не запускайте його на production.

## 5. Нагадування, пошта й онлайн

POST `/internal/jobs/reminders` захищений окремим `REMINDERS_JOB_TOKEN`.
Створення повідомлень і поштової черги працює без Gmail; реальна відправка потребує
OAuth для `rehab.support.web@gmail.com`. Деталі, env і ручний запуск:
[render-neon.md](docs/deployment/render-neon.md).

Розклад Actions виконується лише з default branch. До фінального main перевіряйте
endpoint вручну через `scripts/run_reminders_job.py`; не переносіть продукт у main
лише заради таймера. Render/Neon та iPhone — окреме онлайн-приймання.
