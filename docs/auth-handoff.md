# Інтеграція авторизації Rehab — передача контрактів

**Статус станом на 29.10.2026:** авторизація та її форматування включені до `develop` через PR №172 і №178; PostgreSQL-основа та міграція — через PR №182. CI із реальною тестовою PostgreSQL проходить. Реєстрацію, JWT, `/me`, вихід і блокування перевірено на окремому інтеграційному FastAPI-додатку, а **основний `backend/app/main.py` ще не підключає `auth.router`**. Вхід через опубліковану вебверсію не перевірено.

## Анастасія — контракти

- `backend/app/db/models/user.py` описує таблицю `users` із полями: `user_id`, `email` (unique, lower/trim), `name`, `nickname`, `password_hash`, `role`, `is_blocked`, `token_version`, `tracking_start_date`, `best_streak`, `created_at`.
- `backend/app/repositories/users.py`: `get_user(db,user_id)`, `get_user_by_email(db,email)`, `set_blocked(db,user_id,blocked)`, `revoke_sessions(db,user)`. Репозиторій виконує `flush`, але не `commit`.
- `backend/app/security.py`: `get_current_user` повертає `CurrentUser(user_id,role)` **з перевіреної БД**, `require_role(*roles)` обмежує доступ. JWT: HS256, `sub`, `iat`, `exp`, `token_version`, 3600 секунд. `JWT_SECRET` із середовища, щонайменше 32 символи; без секрету сервер не видає токен.
- `backend/app/routers/auth.py`: `POST /api/v1/auth/register` (201), `POST /api/v1/auth/login` (200), `GET /api/v1/auth/me` (200), `POST /api/v1/auth/logout` (204).
- `frontend/src/api/client.ts`: `apiRequest<T>('/calendar/entries', options)` сам додає `/api/v1`, Bearer й форматує помилки. `AuthProvider` дає `user`, `signIn`, `signUp`, `signOut`, `refresh`.
- `Button`, `FormField`, `ScreenState` — спільні компоненти для екранів.

## Поліна — основа, вже інтегрована у `develop`

- Надано `backend.app.db.base.Base` і `backend.app.db.session.get_db()` з окремою сесією на запит та rollback.
- Таблицю `users` включено в єдину початкову Alembic-міграцію разом із `day_records` і `goals`; окремої стартової міграції не потрібно.
- Надано `backend.app.core.clock.today_local()` для дати реєстрації та відповіді `/me` (Europe/Kyiv).
- У `tests/conftest.py` є фікстури для ізольованої тестової PostgreSQL, справжніх реєстрацій і JWT. Тестова БД має окреме ім'я й не замінює dev.

## Софія — що потрібно для запуску

- У [PR №183](https://github.com/ukma-fin-ssdm-2026/Rehab/pull/183) Софія вже запропонувала підключення `auth.router` під `API_PREFIX`. **До злиття PR №183 у `develop`** головний `backend/app/main.py` ще не реєструє auth-маршрути; після злиття перевірити їх на головному app.
- `PyJWT`, `pwdlib[argon2]`, SQLAlchemy та `psycopg` уже є в спільному `requirements.txt` з зафіксованими версіями; підтверджено встановлення в CI.
- Налаштувати `JWT_SECRET` тільки в середовищі; **ніколи** не додавати значення секрету у Git чи публічний Expo env.
- Налаштувати CORS для опублікованого клієнта і `POST`/інші методи, CI для інтеграційних тестів; додати `/admin/users` для ролі admin.

## Відкриті завдання на інтеграцію

- [Issue №179 — auth.router, Python-залежності та CI](https://github.com/ukma-fin-ssdm-2026/Rehab/issues/179) — Софія.
- [Issue №180 — PostgreSQL, Alembic і get_db](https://github.com/ukma-fin-ssdm-2026/Rehab/issues/180) — основа Поліни вже злита через PR №182; issue залишається відкритим до завершення наскрізної інтеграції.
- [PR №178 — форматування backend авторизації](https://github.com/ukma-fin-ssdm-2026/Rehab/pull/178) — злитий у `develop`; локальні Black, Flake8 і 44 auth-тести пройшли.
- [PR №185 — PostgreSQL-тести авторизації](https://github.com/ukma-fin-ssdm-2026/Rehab/pull/185) — **злитий у `develop`**. На останньому коміті PR `fb3913c` CI: **258 passed, 1 warning, backend coverage 94%**, Code Quality і Lab07 Traceability — зелені. Ціль покриття 95% ще не підтверджена.

## Що має зафіксувати відповідальна за командну перевірку КТ1

- [x] PostgreSQL, єдина міграція `0001_initial`, JWT та Argon2 перевірені в CI для тестового FastAPI app (PR №182, №185).
- [x] Дублі email, відмова в підвищенні ролі, підроблений токен, ізоляція акаунтів і відкликання сесій покриті PostgreSQL-тестами (PR №185).
- [ ] Після злиття PR №183 перевірити, що головний `backend.app.main:app` віддає `/api/v1/auth/register`, `/login`, `/me`, `/logout` без окремого тестового застосунку.
- [ ] Виконати основним app наскрізний сценарій із test/dev PostgreSQL: реєстрація → вхід → власний календар → ціль і статистика → адмінське блокування (403) → вихід (старий JWT — 401).
- [ ] Звірити браузерний login/onboarding/profile/logout, збереження токена лише у вкладці та сценарії 401/403.
- [ ] Після злиття всіх командних PR отримати green CI на тому самому коміті `develop`, який піде на review до `main`; результати й дату зафіксувати в релізному PR.

## Перевірки перед інтеграцією

- На локальній Windows-копії Rehab шість auth-test файлів: **44 passed, 1 warning**, включно з `pwdlib`/Argon2. TypeScript і web export пройшли; ESLint власних файлів авторизації пройшов. Повний Expo lint мав помилки в інших вкладках.
- У GitHub Actions із тестовою PostgreSQL: **258 passed, 1 warning in 32.44s**, покриття backend **94%** на останньому коміті PR №185 (CI run 40890740429); це тестування окремого інтеграційного app і модулів, а не підтвердження повного запуску головного застосунку.
- `python -m pytest tests/test_auth.py tests/test_auth_revocation.py tests/test_auth_schema_contract.py tests/test_auth_schema_boundaries.py tests/test_auth_routes_unit.py tests/test_security_dependency.py -q`.
- У `tests/test_calendar_auth_postgres.py` та `tests/test_auth_postgres.py` перевіряються реальна реєстрація з Argon2, вхід, `/me`, ізоляція акаунтів, вихід і старі JWT, блокування та недійсність попереднього токена після розблокування, дубль email і заборона реєстрації ролі admin. Це ще треба перевірити через **головний** `app` після підключення маршрутів Софією.
- У `frontend`: `npm ci`, `npx tsc --noEmit`, `npx expo lint`, `npx expo export --platform web`. Перевірити прямі URL, reload і мобільний браузер.

Тут розрізнено фактичні результати перевірок модулів та незавершену інтеграцію основного застосунку. Ця документаційна зміна не змінює `backend/app/main.py`, `requirements.txt`, CI чи файли інших учасниць.

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
