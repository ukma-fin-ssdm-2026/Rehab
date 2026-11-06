# Лабораторна 9 — Етап 1: пошук ризиків надійності

Статус: перший блок — результати статичного аналізу. Класифікація й виправлення будуть додані окремими блоками.

Джерело: код Rehab у commit `1f7237664b6d954d417d15d16316c1218159cb5b`, перевірений 06.11.2026. Нижче наведено потенційні ризики, а не доведені інциденти у production. Для кожної знахідки вказано категорію, фрагмент коду, причину небезпеки та потенційний вплив.

## R1. HTTP-запит клієнта без власного дедлайну

- Категорія: **B, E**.
- Код: [frontend/src/api/client.ts:43](https://github.com/ukma-fin-ssdm-2026/Rehab/blob/1f7237664b6d954d417d15d16316c1218159cb5b/frontend/src/api/client.ts#L43).

```typescript
const response = await fetch(`${API_BASE_URL}/api/v1${path}`, {
  ...options,
  headers,
});
```

**Чому небезпечно:** Якщо сервер або мережа не завершують відповідь, apiRequest не задає часу припинення очікування. Окремі виклики можуть передавати signal, але загального дедлайну немає.

**Потенційний вплив:** Екран може довго залишатися в loading, а користувач не отримує своєчасної можливості повторити дію.

## R2. Розбір JSON перед обробкою HTTP-помилки

- Категорія: **A**.
- Код: [frontend/src/api/client.ts:49](https://github.com/ukma-fin-ssdm-2026/Rehab/blob/1f7237664b6d954d417d15d16316c1218159cb5b/frontend/src/api/client.ts#L49).

```typescript
const payload: unknown = contentType.includes('application/json')
  ? await response.json()
  : await response.text();
if (!response.ok) {
```

**Чому небезпечно:** Некоректний або обірваний JSON із Content-Type application/json спричинить виняток раніше, ніж код обробить HTTP-статус. Зокрема, для 401 не виконається sessionInvalid.

**Потенційний вплив:** Замість узгодженої ApiError користувач отримує технічну помилку парсингу; недійсна сесія може залишитися у клієнтському стані.

## R3. Успішна відповідь не перевіряється за структурою

- Категорія: **C**.
- Код: [frontend/src/api/client.ts:78](https://github.com/ukma-fin-ssdm-2026/Rehab/blob/1f7237664b6d954d417d15d16316c1218159cb5b/frontend/src/api/client.ts#L78).

```typescript
return payload as T;
```

**Чому небезпечно:** Приведення типу не перевіряє дані під час виконання. Успішна відповідь із null, HTML або JSON неправильної структури передається далі як очікуваний тип. Наприклад, календар очікує result.items як масив.

**Потенційний вплив:** Після відповіді 200 екран може впасти на обробці даних або показати некоректний стан. Коректний JSON ще не означає коректний контракт.

## R4. Час SQL-запиту та очікування блокування не обмежений у конфігурації застосунку

- Категорія: **B, E**.
- Код: [backend/app/db/session.py:17](https://github.com/ukma-fin-ssdm-2026/Rehab/blob/1f7237664b6d954d417d15d16316c1218159cb5b/backend/app/db/session.py#L17).

```python
return create_engine(url, pool_pre_ping=True, connect_args={"connect_timeout": 5})
```

**Чому небезпечно:** У коді задано connect_timeout, але не видно statement_timeout або lock_timeout. Це різні обмеження: встановлення з’єднання не обмежує подальший запит або очікування row lock. Перед виправленням треба перевірити налаштування ролі/БД: сервер може вже задавати ці ліміти.

**Потенційний вплив:** Якщо серверні ліміти також відсутні, заблоковані запити довго утримують з’єднання; інші запити можуть чекати вільного ресурсу.

## R5. Синхронна БД всередині async-обробника аватара

- Категорія: **E**.
- Код: [backend/app/routers/profile.py:104](https://github.com/ukma-fin-ssdm-2026/Rehab/blob/1f7237664b6d954d417d15d16316c1218159cb5b/backend/app/routers/profile.py#L104).

```python
processed = await run_in_threadpool(normalize_avatar, bytes(raw))
account = lock_user_for_update(db, user.user_id)
# ...
avatar = db.get(UserAvatar, user.user_id)
# ...
db.commit()
```

**Чому небезпечно:** Обробку картинки винесено у threadpool, але синхронні звернення SQLAlchemy після await виконуються безпосередньо в async def. Повільний запит або очікування блокування затримує event loop цього worker.

**Потенційний вплив:** Один повільний upload може затримати й інші запити, які обслуговує той самий event loop.

## R6. Увесь прохід поштової черги виконується в одному HTTP-запиті без бюджету пакета

- Категорія: **E**.
- Код: [backend/app/services/email_reminders.py:241](https://github.com/ukma-fin-ssdm-2026/Rehab/blob/1f7237664b6d954d417d15d16316c1218159cb5b/backend/app/services/email_reminders.py#L241).

```python
while True:
    current = clock()
    if current.astimezone(BUSINESS_TIMEZONE).date() != today:
        break
    # ... захоплення одного листа ...
    message_id = sender.send(to, SUBJECT, reminder_body(style, today))
```

**Чому небезпечно:** Є завершення на порожній черзі та зміні дати, але немає малого ліміту кількості листів або загальної тривалості запуску. jobs.run_reminders синхронно очікує цей прохід і тримає advisory lock. Тайм-аут окремого Gmail-запиту не обмежує сумарний час для багатьох листів.

**Потенційний вплив:** За великої черги job може перевищити HTTP-дедлайн викликача або проксі; наступний запуск отримує JOB_ALREADY_RUNNING, поки попередній ще працює. Це довга операція, а не доведений нескінченний цикл.

## R7. ImportError залежності маскується як непідключений модуль нагадувань

- Категорія: **A, D**.
- Код: [backend/app/routers/jobs.py:46](https://github.com/ukma-fin-ssdm-2026/Rehab/blob/1f7237664b6d954d417d15d16316c1218159cb5b/backend/app/routers/jobs.py#L46).

```python
try:
    from backend.app.services.reminders import create_due_reminders
except ImportError:
    raise api_error(
        503, "REMINDERS_NOT_READY", "Створення нагадувань ще не підключено"
    ) from None
```

**Чому небезпечно:** ImportError може виникнути всередині reminders через зламану транзитивну залежність або неправильний імпорт, навіть коли сам модуль існує. Перехоплення не розрізняє причини, не логує виняток і приховує його ланцюг.

**Потенційний вплив:** Job не працює, а оператор отримує оманливе пояснення про непідключену функцію; пошук причини та відновлення ускладнюються.

## Використання ШІ

Статичний аналіз і чернетку описів підготував Codex. Посилання звірено з указаною версією коду. Відтворення сценаріїв, класифікація та результати виправлень не входять до цього блоку; їх потрібно документувати окремо. Учасники мають перевірити та вміти пояснити прийняті знахідки.
