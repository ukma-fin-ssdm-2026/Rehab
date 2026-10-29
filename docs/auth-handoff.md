# Інтеграція авторизації Rehab — передача контрактів

**Статус:** код модуля підготовлений у гілці `feature/auth-session`. Наскрізне тестування на PostgreSQL, CI й опублікованій вебверсії ще не виконане.

## Анастасія — контракти

- `backend/app/db/models/user.py` описує таблицю `users` із полями: `user_id`, `email` (unique, lower/trim), `name`, `nickname`, `password_hash`, `role`, `is_blocked`, `token_version`, `tracking_start_date`, `best_streak`, `created_at`.
- `backend/app/repositories/users.py`: `get_user(db,user_id)`, `get_user_by_email(db,email)`, `set_blocked(db,user_id,blocked)`, `revoke_sessions(db,user)`. Репозиторій виконує `flush`, але не `commit`.
- `backend/app/security.py`: `get_current_user` повертає `CurrentUser(user_id,role)` **з перевіреної БД**, `require_role(*roles)` обмежує доступ. JWT: HS256, `sub`, `iat`, `exp`, `token_version`, 3600 секунд. `JWT_SECRET` із середовища, щонайменше 32 символи; без секрету сервер не видає токен.
- `backend/app/routers/auth.py`: `POST /api/v1/auth/register` (201), `POST /api/v1/auth/login` (200), `GET /api/v1/auth/me` (200), `POST /api/v1/auth/logout` (204).
- `frontend/src/api/client.ts`: `apiRequest<T>('/calendar/entries', options)` сам додає `/api/v1`, Bearer й форматує помилки. `AuthProvider` дає `user`, `signIn`, `signUp`, `signOut`, `refresh`.
- `Button`, `FormField`, `ScreenState` — спільні компоненти для екранів.

## Поліна — що потрібно для запуску

- Надати `backend.app.db.base.Base` і `backend.app.db.session.get_db()` з окремою сесією на запит та rollback.
- Включити `User` у **єдину** початкову Alembic-міграцію разом із `day_records` і `goals`. Не створювати другу базу даних або окрему стартову міграцію.
- Надати `backend.app.core.clock.today_local()` для дати реєстрації та відповіді `/me`.
- Передбачити тестову PostgreSQL і auth-фікстури в `tests/conftest.py`; адреси dev і test БД повинні відрізнятися.

## Софія — що потрібно для запуску

- Додати `auth.router` до `backend/app/main.py` під `API_PREFIX`; реєстрація й логін не підключаються автоматично.
- У спільні залежності додати сумісні `PyJWT`, `pwdlib[argon2]`, SQLAlchemy та драйвер БД (останній за погодженням із Поліною), після чого зафіксувати версії.
- Налаштувати `JWT_SECRET` тільки в середовищі; **ніколи** не додавати значення секрету у Git чи публічний Expo env.
- Налаштувати CORS для опублікованого клієнта і `POST`/інші методи, CI для інтеграційних тестів; додати `/admin/users` для ролі admin.

## Перевірки перед інтеграцією

- Окремий локальний smoke-прогін скопійованої JWT-залежності та тестових сценаріїв: **17 passed, 1 skipped**. Це не повний запуск репозиторію; перевірку `pwdlib`/Argon2 пропущено через відсутню бібліотеку. TypeScript, Expo lint, web export та інтеграцію PostgreSQL не підтверджено.
- `python -m pytest tests/test_auth_schema_contract.py tests/test_auth.py tests/test_auth_revocation.py tests/test_auth_routes_unit.py tests/test_security_dependency.py -q`.
- Після появи PostgreSQL: реєстрація двох акаунтів → вхід → `/me` → доступ тільки до своїх записів → вихід → старий JWT дає 401 → блокування дає 403 → після розблокування старий JWT не оживає.
- У `frontend`: `npm ci`, `npx tsc --noEmit`, `npx expo lint`, `npx expo export --platform web`. Перевірити прямі URL, reload і мобільний браузер.

Тут описано контракти й залежності, а не вигадані результати тестування. Файли `main.py`, `requirements.txt`, CI, `docs/validation/*` і `docs/requirements/rtm.md` ця гілка не змінює.

## Використання ШІ

ChatGPT допоміг підготувати код, тести та цей документ. Перед прийняттям команда перевіряє зміни, результати тестування, безпеку та відповідність вимогам.
