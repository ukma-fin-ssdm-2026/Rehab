# Інтеграція авторизації Rehab — передача контрактів

**Статус:** код авторизації включено до `develop` через PR №172. Наскрізне тестування на PostgreSQL, CI й опублікованій вебверсії ще не виконане.

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

## Відкриті завдання на інтеграцію

- [Issue №179 — auth.router, Python-залежності та CI](https://github.com/ukma-fin-ssdm-2026/Rehab/issues/179) — Софія.
- [Issue №180 — PostgreSQL, Alembic і get_db](https://github.com/ukma-fin-ssdm-2026/Rehab/issues/180) — Поліна.
- [PR №178 — форматування backend авторизації](https://github.com/ukma-fin-ssdm-2026/Rehab/pull/178): локально перевірено Black (22 файли без змін), Flake8 (без зауважень) і 44 auth-тести (1 попередження). Це не заміняє загальний CI.

## Перевірки перед інтеграцією

- На локальній Windows-копії Rehab шість auth-test файлів: **44 passed, 1 warning**, включно з тестом `pwdlib`/Argon2. TypeScript і web export пройшли; ESLint файлів авторизації пройшов. Загальний lint ще має помилки в чужих вкладках. Реальна PostgreSQL-інтеграція й наскрізний вхід не перевірені.
- `python -m pytest tests/test_auth.py tests/test_auth_revocation.py tests/test_auth_schema_contract.py tests/test_auth_schema_boundaries.py tests/test_auth_routes_unit.py tests/test_security_dependency.py -q`.
- Після появи PostgreSQL: реєстрація двох акаунтів → вхід → `/me` → доступ тільки до своїх записів → вихід → старий JWT дає 401 → блокування дає 403 → після розблокування старий JWT не оживає.
- У `frontend`: `npm ci`, `npx tsc --noEmit`, `npx expo lint`, `npx expo export --platform web`. Перевірити прямі URL, reload і мобільний браузер.

Тут описано контракти й залежності, а не вигадані результати тестування. Ця гілка доповнює `docs/requirements/rtm.md`, але не змінює `backend/app/main.py`, `requirements.txt`, CI чи `docs/validation/*`.

## Передача моделі загроз авторизації

| Категорія STRIDE | Сценарій | Реалізований захист або залежність |
|---|---|---|
| Spoofing | Підроблений або прострочений токен | PyJWT перевіряє підпис HS256, `exp`, `iat`, `sub` та `token_version`; `JWT_SECRET` не зберігається в коді |
| Elevation of Privilege | Звичайний користувач викликає адмінські дії | `require_role` перевіряє поточну роль із БД; підключення адмінських маршрутів належить Софії |
| Information Disclosure | Користувач намагається отримати чужі дані | `CurrentUser.user_id` береться з перевіреного токена; власниці календаря, цілей і статистики забезпечують фільтрацію за цим ID |
| Tampering | Клієнт передає `role` або підмінений `user_id` | Публічна реєстрація забороняє `role`; серверні маршрути повинні визначати власника з `CurrentUser` |
| Denial of Service | Масові спроби входу | Обмеження частоти запитів і захист від brute force ще не підтверджені; потрібне рішення Софії для розгортання |

У вебверсії токен зберігається у `sessionStorage`, а не в `HttpOnly` cookie. Отже, загальний опис захисних cookies у `docs/architecture/threat-model.md` не відповідає поточній реалізації. Токен може бути доступний шкідливому JavaScript у разі XSS; архітектурна власниця має відобразити цей ризик і фактично налаштовані контрзаходи без тверджень про вже впроваджений CSP.

## Використання ШІ

ChatGPT допоміг підготувати код, тести та цей документ. Перед прийняттям команда перевіряє зміни, результати тестування, безпеку та відповідність вимогам.
