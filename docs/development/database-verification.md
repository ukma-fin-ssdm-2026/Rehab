# Перевірка PostgreSQL-основи перед КТ-1

Локальна перевірка у Windows, Python 3.12, PostgreSQL 16.14, окремі rehab_dev/rehab_test.
Це результати локального запуску, а не GitHub Actions або публічного розгортання.

| Перевірка | Результат |
|---|---|
| Повний `pytest -q` | 172 passed; одне попередження Starlette/httpx |
| Нові перевірки БД/часу/схем/календаря | 45 тестів входять у цей повний набір |
| Окремий валідатор простежуваності | 4 passed |
| requirements → test-plan → RTM | PASS; це узгодженість плану, не виконання всіх сценаріїв |
| Покриття нових core/db/repositories/calendar_postgres | 95% statements; це не покриття всього Rehab |
| Black і Flake8 змінених Python-модулів | Успішно |
| Bandit нових серверних модулів і міграцій | 559 рядків, 0 знахідок, 0 помилок аналізу |
| pip check | No broken requirements found |
| git diff --check | Успішно |

Міграція `upgrade head` виконана для обох локальних БД. Повторне застосування,
унікальність дати, FK та діапазон цілей перевіряються тестами на PostgreSQL.
Календарні перевірки включають нове з’єднання замість спільного in-memory стану,
конкурентний дублікат, точну межу 48 годин, власників та rollback запису й похідних
змін у разі помилки перерахунку.

Під час незалежного огляду додатково перевірена безпека адреси тестової БД.
Потенційне перевизначення цілі через query-параметри psycopg усунуте;
регресійні тести перевіряють відхилення таких параметрів і різні назви dev/test.
Після виправлення важливих зауважень до цього блоку огляд не виявив.

## Як повторити

Запустити PostgreSQL за [postgres-local.md](postgres-local.md), установити
актуальний requirements.txt та виконати:

```powershell
python -m alembic upgrade head
python -m alembic -x test_db=true upgrade head
python -m pytest -q --cov=backend.app.core --cov=backend.app.db --cov=backend.app.repositories --cov=backend.app.routers.calendar_postgres --cov-report=term-missing
python -m pytest scripts/test_check_traceability.py -q
python scripts/check_traceability.py
```

## Що цим ще не підтверджено

- Головний app усе ще реєструє старі prototype-маршрути.
- Новий PostgreSQL-router тестується в окремому FastAPI app; auth і progress — явні
  тестові підміни цих двох командних меж. Це не доказ реальної JWT-інтеграції.
- Реальний recompute_progress Марії ще не інтегровано. За його відсутності новий
  router відхиляє записи з 503, а не зберігає дані без оновлення статистики.
- Повна вебзбірка, телефон і зовнішнє розгортання цього блоку ще не перевірені.

До злиття потрібна спільна перевірка КТ-1 за
[database-handoff.md](database-handoff.md).

## Використання ШІ

ChatGPT допоміг підготувати реалізацію, тести, незалежний огляд і цей звіт.
Наведено результати фактичних локальних запусків; оцінку викладача та повну
готовність системи ці результати не гарантують.
