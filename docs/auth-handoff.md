# Інтеграція авторизації Rehab — передача контрактів

**Статус станом на 29.10.2026:** авторизація та її форматування включені до `develop` через PR №172 і №178; PostgreSQL-основа та міграція — через PR №182. CI із реальною тестовою PostgreSQL проходить. Реєстрацію, JWT, `/me`, вихід і блокування перевірено на окремому інтеграційному FastAPI-додатку, а після злиття PR №183 **основний `backend/app/main.py` підключає `auth.router`, `admin.router` та `calendar_postgres` через alias `calendar`**. Після застосування `0001_initial` до Neon онлайн-авторизацію й роботу з даними перевірено через публічний API; браузерний сценарій ще не підтверджений.

## Фактична онлайн-перевірка Поліни — 29.10.2026

[Звіт із PR №188](https://github.com/ukma-fin-ssdm-2026/Rehab/blob/0350d6245cbbdc94bc05a09981988617d8831d9c/docs/development/neon-migration-verification.md): міграція `0001_initial` застосована до `production/neondb`; 25 перевірок публічного API пройшли на синтетичних акаунтах. Підтверджені реєстрація, вхід, `/me`, календар, цілі, статистика, перерахунок після редагування, ізоляція користувачів, вихід і відмова старому JWT. Новий HTTP-клієнт прочитав збережений запис.

**Ще не підтверджено:** збереження після перезапуску саме Render API, блокування через онлайн-адмінку, вебклієнт та iPhone/Safari. Новий HTTP-клієнт не є перезапуском сервера. Повна КТ-1 залишається відкритою.

## Анастасія — контракти

- `backend/app/db/models/user.py` описує таблицю `users` із полями: `user_id`, `email` (unique, lower/trim), `name`, `nickname`, `password_hash`, `role`, `is_blocked`, `token_version`, `tracking_start_date`, `best_streak`, `created_at`.
- `backend/app/repositories/users.py`: `get_user(db,user_id)`, `get_user_by_email(db,email)`, `set_blocked(db,user_id,blocked)`, `revoke_sessions(db,user)`. Репозиторій виконує `flush`, але не `commit`.
- `backend/app/security.py`: `get_current_user` повертає `CurrentUser(user_id,role)` **з перевіреної БД**, `require_role(*roles)` обмежує доступ. JWT: HS256, `sub`, `iat`, `exp`, `token_version`, 3600 секунд. `JWT_SECRET` із середовища, щонайменше 32 символи; без секрету сервер не видає токен.
- `backend/app/routers/auth.py`: `POST /api/v1/auth/register` (201), `POST /api/v1/auth/login` (200), `GET /api/v1/auth/me` (200), `POST /api/v1/auth/logout` (204).
- `frontend/src/api/client.ts`: `apiRequest<T>('/calendar/entries', options)` сам додає `/api/v1`, Bearer й форматує помилки. `AuthProvider` дає `user`, `signIn`, `signUp`, `signOut`, `refresh`.
- `Button`, `FormField`, `ScreenState` — спільні компоненти для екранів.

## Короткий приклад спільного frontend-контракту

Приклад для файлу в `frontend/src/app/` (у вкладених папках відносні імпорти відрізнятимуться). Для запитів достатньо передавати шлях **без** `/api/v1`: `apiRequest` сам додає адресу API, префікс і чинний Bearer-токен; не читати токен у компонентах вручну.

```tsx
import { useState } from 'react';
import { useAuth } from '../auth/AuthProvider';
import { apiRequest } from '../api/client';
import { Button } from '../components/ui/Button';
import { FormField } from '../components/ui/FormField';
import { ScreenState } from '../components/ui/ScreenState';

export function CalendarAccessExample() {
  const { user } = useAuth();
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);

  async function loadOwnEntries() {
    setLoading(true);
    setError(false);
    try {
      return await apiRequest<{ items: unknown[]; total: number }>(
        '/calendar/entries',
      );
    } catch {
      setError(true);
      return null;
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <FormField label="Email" value={email} onChangeText={setEmail} />
      {!user ? (
        <ScreenState state="empty" message="Увійдіть для доступу" />
      ) : (
        <Button
          title="Завантажити мої записи"
          loading={loading}
          onPress={() => { void loadOwnEntries(); }}
        />
      )}
      {error ? (
        <ScreenState
          state="error"
          message="Не вдалося отримати календар"
          onRetry={() => { void loadOwnEntries(); }}
        />
      ) : null}
    </>
  );
}
```

Це **приклад інтеграції**, не окремий екран застосунку і не доказ проходження онлайн-сценарію. `AuthProvider` вже підключено в кореневому `frontend/src/app/_layout.tsx`. Для виходу викликати `useAuth().signOut()`, а не очищати лише стан екрана. Інші учасниці додають власні обробники показу результату та помилок.

## Поліна — основа, вже інтегрована у `develop`

- Надано `backend.app.db.base.Base` і `backend.app.db.session.get_db()` з окремою сесією на запит та rollback.
- Таблицю `users` включено в єдину початкову Alembic-міграцію разом із `day_records` і `goals`; окремої стартової міграції не потрібно.
- Надано `backend.app.core.clock.today_local()` для дати реєстрації та відповіді `/me` (Europe/Kyiv).
- У `tests/conftest.py` є фікстури для ізольованої тестової PostgreSQL, справжніх реєстрацій і JWT. Тестова БД має окреме ім'я й не замінює dev.

## Софія — інтегровані маршрути та незавершені онлайн-перевірки

- [PR №183](https://github.com/ukma-fin-ssdm-2026/Rehab/pull/183) **злито в `develop`**: у `backend/app/main.py` зареєстровано `auth.router`, `admin.router`, `health.router`, а `calendar_postgres` імпортовано як `calendar` та підключено замість старого in-memory роутера. Онлайн-запити до auth і календаря вже перевірені; блокування через адмінський API залишається для спільної перевірки.
- `PyJWT`, `pwdlib[argon2]`, SQLAlchemy та `psycopg` уже є в спільному `requirements.txt` з зафіксованими версіями; підтверджено встановлення в CI.
- Налаштувати `JWT_SECRET` тільки в середовищі; **ніколи** не додавати значення секрету у Git чи публічний Expo env.
- У PR №183 додано налаштування CORS, захищені адмін-маршрути, `/health`, `/ready`, конфігурацію Render/Neon та CI. Вони проходять CI; онлайн `/health`, `/ready` та основні API-сценарії підтверджені після міграції. Перезапуск API, адмінське блокування і браузерна перевірка ще не завершені.

## Відкриті завдання на інтеграцію

- [Issue №179 — auth.router, Python-залежності та CI](https://github.com/ukma-fin-ssdm-2026/Rehab/issues/179) — роутери, залежності та CI вже інтегровані; залишено для підтвердження наскрізної онлайн-перевірки.
- [Issue №180 — PostgreSQL, Alembic і get_db](https://github.com/ukma-fin-ssdm-2026/Rehab/issues/180) — основа Поліни вже злита через PR №182; issue залишається відкритим до завершення наскрізної інтеграції.
- [PR №178 — форматування backend авторизації](https://github.com/ukma-fin-ssdm-2026/Rehab/pull/178) — злитий у `develop`; локальні Black, Flake8 і 44 auth-тести пройшли.
- [PR №185 — PostgreSQL-тести авторизації](https://github.com/ukma-fin-ssdm-2026/Rehab/pull/185) — **злитий у `develop`**. На останньому коміті PR `fb3913c` CI: **258 passed, 1 warning, backend coverage 94%**, Code Quality і Lab07 Traceability — зелені. Ціль покриття 95% ще не підтверджена.

## Перевірка публічної авторизації — Render + Neon, 0 грн

Узгоджені адреси: [Expo Web](https://rehab-web-b9d5.onrender.com) і [FastAPI](https://rehab-api-0na0.onrender.com). Це адреси з командної інструкції; саме існування URL **не доводить** коректний вхід. Поліна підтвердила `/health`, `/ready` і 25 API-перевірок після міграції Neon; посилання на протокол наведене вище. Це не замінює перевірку опублікованого вебклієнта.

- `EXPO_PUBLIC_API_URL=https://rehab-api-0na0.onrender.com` — **без** `/api/v1`, оскільки спільний `apiRequest` додає його автоматично. Після зміни потрібна **нова збірка Expo Web**.
- `CORS_ORIGINS=https://rehab-web-b9d5.onrender.com` — точна HTTPS-адреса, а не `*`. Вхід використовує `Authorization: Bearer ...` і `Content-Type: application/json`.
- `DATABASE_URL` (PostgreSQL Neon із TLS, `postgresql+psycopg://`) та `JWT_SECRET` (≥32 символи) залишаються виключно в приватних змінних Render. `APP_ENV` поточний backend не читає: не стверджувати, що зміна цієї змінної активує будь-який режим.
- Не запускати pytest, `TRUNCATE` або тестові фікстури проти онлайн Neon. Початкову міграцію `0001_initial` Поліна вже застосувала через інструмент Neon, використовуючи SQL, згенерований Alembic; дві тимчасові гілки видалені. Повторно створювати таблиці або нову початкову міграцію не потрібно. Не публікувати URL бази чи облікові дані.
- Render Free може прокидатися після простою: перша відповідь не є репрезентативним заміром PERF-001. Перед тестуванням відкрити API завчасно.

Після підтвердження міграції **вручну в опублікованому клієнті** перевірити:

1. Новий тестовий акаунт: реєстрація → автоматичний вхід → onboarding → персональні дані профілю. Для окремого негативного тесту повторний email має повернути 409; невірний пароль — 401, без розкриття існування email.
2. `/auth/me`: особисті дані без `password_hash`; після reload у тій самій вкладці сесію перевірено повторно. Після виходу старий токен має отримувати 401.
3. Два різні акаунти: календар, цілі і статистика не відкривають чужих даних. Адмін блокує другого користувача → захищений запит і новий вхід повертають 403; після розблокування старий JWT не оживає.
4. Дані календаря й цілей залишаються після **перезапуску backend**; перевіряє команда без очищення Neon.
5. **Тільки iPhone Safari:** зафіксувати модель iPhone, версію iOS, реєстрацію/вхід, клавіатуру у формах, навігацію, відкриття прямого приватного URL, reload та вихід. Android не входить до перевірок і не позначається як перевірений.

**Стан на момент створення цього розділу:** наведені пункти 1–5 є планом приймальної перевірки, а не результатами. Фактичні коди HTTP, дату, браузер і доказ збереження після перезапуску потрібно внести до `docs/deployment/render-neon.md` відповідальною за розгортання. Не додавати скриншоти з токенами, паролями чи приватними даними.

## Що має зафіксувати відповідальна за командну перевірку КТ1

- [x] PostgreSQL, єдина міграція `0001_initial`, JWT та Argon2 перевірені в CI для тестового FastAPI app (PR №182, №185).
- [x] Дублі email, відмова в підвищенні ролі, підроблений токен, ізоляція акаунтів і відкликання сесій покриті PostgreSQL-тестами (PR №185).
- [x] У вихідному коді головного `backend.app.main:app` зареєстровані auth, admin і PostgreSQL-календар через PR №183.
- [x] Після міграції Neon HTTP-запитами до **онлайн** головного app перевірені `/api/v1/auth/register`, `/login`, `/me`, `/logout`; старий JWT після виходу відхиляється (401).
- [ ] Виконати наскрізний сценарій **на Render + Neon після міграцій**: реєстрація → вхід → власний календар → ціль і статистика → перезапуск API та перевірка збережених даних → адмінське блокування (403) → вихід (старий JWT — 401).
- [ ] Звірити браузерний login/onboarding/profile/logout, збереження токена лише у вкладці та сценарії 401/403.
- [x] Після злиття PR №183 серверний GitHub Actions на `develop` (коміт `2fb5b2c`) завершився: **279 passed, 1 warning, 93% backend coverage**; Code Quality і Lab07 Traceability також зелені.
- [ ] Перед релізом після наступних змін повторити CI на точному коміті `develop`, який розглядатимуть для `main`, і зафіксувати його у релізному PR.

## Перевірки перед інтеграцією

- На локальній Windows-копії Rehab шість auth-test файлів: **44 passed, 1 warning**, включно з `pwdlib`/Argon2. TypeScript і web export пройшли; ESLint власних файлів авторизації пройшов. Повний Expo lint мав помилки в інших вкладках.
- У GitHub Actions із тестовою PostgreSQL: **258 passed, 1 warning in 32.44s**, покриття backend **94%** на останньому коміті PR №185 (CI run 40890740429); це тестування окремого інтеграційного app і модулів, а не підтвердження повного запуску головного застосунку.
- `python -m pytest tests/test_auth.py tests/test_auth_revocation.py tests/test_auth_schema_contract.py tests/test_auth_schema_boundaries.py tests/test_auth_routes_unit.py tests/test_security_dependency.py -q`.
- У `tests/test_calendar_auth_postgres.py` та `tests/test_auth_postgres.py` перевіряються реальна реєстрація з Argon2, вхід, `/me`, ізоляція акаунтів, вихід і старі JWT, блокування та недійсність попереднього токена після розблокування, дубль email і заборона реєстрації ролі admin. Основні auth/календарні сценарії вже перевірені через публічний основний app; блокування/розблокування онлайн й браузерний сценарій залишаються окремими перевірками.
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
