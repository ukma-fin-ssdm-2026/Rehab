# PostgreSQL і календар — поточний інтеграційний контракт

Стан перед КТ3, 30.10.2026. Календар та PostgreSQL інтегровані в головний
`backend.app.main:app`; робочий router — `calendar_postgres`. Авторизація —
справжні JWT і Argon2, права визначає `get_current_user`.

## Схема й середовища

- `0001_initial`: users, day_records, goals; legacy goals не використовується
  застосунком після переходу на фіксовані етапи 7/30.
- SQLAlchemy `Base` спільна; Pydantic Entry-схеми описують HTTP, а ORM — таблиці.
- Локально PostgreSQL 16: DATABASE_URL і окрема TEST_DATABASE_URL; онлайн Neon
  PostgreSQL 18. [Локальний запуск](postgres-local.md), [Render/Neon](../deployment/render-neon.md).
- `get_db()` закриває сесію після запиту. Запуск API не скидає й не засіває БД.
- Для КТ3 нова міграція не потрібна. Застосовану міграцію не переписувати.

## Репозиторій `backend.app.repositories.entries`

| Операція | Контракт |
|---|---|
| create_entry(db, user_id, body) | EntryOut; перевірка діапазону, flush без commit |
| get_own_entry(db, user_id, record_id) | EntryOut; чужий/відсутній запис — однаковий 404 |
| update_entry(db, user_id, record_id, body) | лише status/trigger_category; 48 годин включно |
| list_user_entries(db, user_id, date_from, date_to, limit, offset) | список за спаданням дати |
| count_user_entries(db, user_id, date_from, date_to) | число записів за тим самим фільтром |
| list_relapse_entries(db, date_from, date_to) | внутрішні записи для агрегації admin, не публічна відповідь |

POST/PATCH блокують рядок користувача, виконують flush і справжній
`recompute_progress(db, user_id, today_local())`, потім один commit.
Помилка відкочує зміни; відсутній сервіс перерахунку — 503 без збереження.
Звичайний запуск використовує інтегрований сервіс, а не тестову підміну.

## HTTP і правила

- POST `/api/v1/calendar/entries`: 201; дублікат дати — 409 ENTRY_ALREADY_EXISTS.
- GET списку: from/to, limit 1..100, offset; items/total/limit/offset.
- GET деталей `/{record_id}`: 200 або 404 ENTRY_NOT_FOUND.
- PATCH `/{record_id}`: 200; після 48 годин — 403 EDIT_WINDOW_EXPIRED.
- Дати: tracking_start_date..current_date з `/auth/me`, Europe/Kyiv.
- created_at — UTC; рівно 48 годин редагувати можна, більше — не можна.
- Дату, власника, час, напої та коментар PATCH не змінює.
- Зміна на sober очищує напої й тригер, зберігає коментар та created_at.
- На створенні напої для relapse необов'язкові; об'єм — додатне ціле;
  коментар — до 2000 символів. Власника задає сервер.
- Пропущений день у межах відстеження рахується тверезим; UI відрізняє
  розрахований стан від явно збереженого запису.

## Клієнт і перевірки

`frontend/src/api/calendar.ts` використовує спільний apiRequest; після успішної
мутації сповіщає екрани прогресу. Календар оновлюється при поверненні фокуса.
Деталі підтримують reload, а авторизація повертає до допустимого посилання
після входу. Сервер перевіряє власника незалежно від клієнтської навігації.

Тести: test_calendar_postgres_api.py, test_calendar_auth_postgres.py,
test_progress_sync_calendar.py, test_auth_main_postgres.py та календарні
frontend-тести. Вони використовують окрему тестову БД, не Neon production.

Результати: [історія локальних перевірок](database-verification.md),
[міграція Neon](neon-migration-verification.md), [онлайн-приймання КТ2](../validation/calendar-kt2.md).
Історичні числа тестів у старих звітах не є числом тестів поточного commit.
