# REST API Rehab

## Джерело контракту

[Згенерована OpenAPI-схема](openapi-generated.yaml) містить точні шляхи, поля, enum, статуси й помилки. Її експортують командою `python scripts/export_openapi.py` з `backend.app.main:app`; Swagger працює на `/docs`. Робочі дані зберігаються в PostgreSQL, тестові Bearer-токени прототипу не підтримуються.

## Маршрути

Користувацькі маршрути мають префікс `/api/v1`.

| Модуль | Операції |
|---|---|
| Auth | POST /auth/register, /auth/login, /auth/logout; GET /auth/me |
| Profile | GET/PATCH /profile; PUT /profile/password; PATCH /profile/preferences; GET/PUT/DELETE /profile/avatar |
| Calendar | GET/POST /calendar/entries; GET/PATCH /calendar/entries/{record_id} |
| Goals | GET /goals — список фіксованих етапів; CRUD та окремий detail-маршрут відсутні |
| Statistics | GET /statistics з period=all/week/month/year |
| Mentorship | GET /mentorships/code, /my-mentor, /my-mentees; POST /mentorships; GET/DELETE /mentorships/{relationship_id}; GET календаря, деталей і статистики підопічного під цим зв’язком |
| Notifications | GET /notifications, /notifications/unread-count, /notifications/{notification_id}; PATCH /notifications/{notification_id}/read; POST /notifications/{notification_id}/support |
| Complaints | POST /complaints |
| Admin | GET /admin/complaints, /admin/complaints/{complaint_id}, /admin/overview, /admin/trigger-distribution; PATCH /admin/complaints/{complaint_id} |

`GET /health` перевіряє процес, `GET /ready` — доступність БД. Службовий `POST /internal/jobs/reminders` не має префікса `/api/v1`, захищений `X-Job-Token`, не JWT; параметрів довільної дати чи адресата немає.

## Авторизація та приватність

Паролі — Argon2; access JWT чинний 3600 секунд, перевіряються підпис, строк і token_version із БД. Роль береться з акаунта, реєстрація не дозволяє її підмінити. Вихід та зміна пароля відкликають старі токени. Browser sessionStorage прив’язує сесію до вкладки; 403 для чужого ресурсу не має завершувати власну сесію.

Календар належить власнику. Для читання підопічного потрібен активний зв’язок, а не лише роль mentor; права перевіряються на кожний запит. Адмін має скарги з прикріпленим доказом і агрегати, без довільного доступу до календаря та inbox. Завершення пари не блокує акаунт.

## Календар і прогрес

Один запис на користувача й дату; діапазон tracking_start_date..current_date визначається сервером у Europe/Kyiv. Для sober напої порожні й тригер відсутній. Для relapse використовуються типізовані напої, тригер і коментар за схемою EntryCreate. PATCH змінює лише статус і тригер, до 48 годин включно від created_at. Чужий запис — 404, прострочене редагування — 403 EDIT_WINDOW_EXPIRED, дубль дати — 409.

Відсутність явного запису після початку відстеження вважається тверезістю. Поточна та найдовша серії обчислюються з історії; виправлення може змінити рекорд і досягнення. Етапи завжди 7/30/90/180/365: найменший невиконаний є активним, його прогрес визначає поточна серія. Всі виконані лише після досягнення 365. POST/PATCH календаря, перерахунок і перша подія зриву належать одній транзакції.

## Менторство, підтримка та скарги

Код постійний і доступний власнику окремим маршрутом. Приєднання одразу активне: створення 201, повтор чинного зв’язку 200. Самоприєднання, другий активний ментор і повтор завершеної напрямленої пари заборонені. Кожна сторона може завершити зв’язок.

Перша подія зриву за день позначається навіть без ментора; пізніше приєднання не відтворює її. Повідомлення надходить тільки тодішньому активному ментору. Один коментар підтримки на повідомлення, 1–2000 символів після обрізання пробілів. Виправлений sober забороняє нову підтримку; завершення зв’язку закриває нові дії, історія зберігається. can_support/can_view/can_report визначає сервер.

Скарга має причину й необов’язковий знімок отриманого коментаря. Схвалення адміністратором закриває конкретну пару назавжди; відхилення не відновлює завершений зв’язок. Повторне рішення — конфлікт. Глобального блокування акаунта й повного чату немає.

## Автоматичні повідомлення та пошта

Стилі formal/humorous/zen/strict і variant=0..3 впливають лише на автоматичні тексти. Коментар автора незмінний. Каталоги ключів та варіантів backend/frontend синхронізовані; inbox використовує поточні налаштування отримувача. Список повідомлень: нові спочатку, порції 30, максимум 100, відкриття позначає прочитаним ідемпотентно.

Job після 20:00 Europe/Kyiv створює одне нагадування за поточну дату без явного запису; opt-in додає поштову копію до outbox. Створення фіксується до мережевого виклику Gmail. pending/sending/sent/skipped/failed/unknown відображають життєвий цикл доставки; невизначені відправки не повторюються автоматично. Без Gmail inbox працює, актуальні pending залишаються, застаріла черга обслуговується. Деталі налаштування — [розгортання](../deployment/render-neon.md).

## Помилки та перевірки

Помилки мають code, message, details; 401 — відсутня/недійсна сесія, 403 — заборонена дія, 404 — ресурс відсутній або прихований, 409 — конфлікт, 422 — валідація. Точні коди та response_model визначає OpenAPI. Перелік сценаріїв і межі приймання — [тест-план](../validation/test-plan.md).

## Code-First та HTTP-рішення

Контракт походить із FastAPI/Pydantic, YAML є експортом для перегляду й публікації. Версія користувацького API — /api/v1; службовий job і health окремі. GET читає без зміни бізнес-даних, POST створює/виконує дію, PATCH змінює визначені поля, PUT замінює пароль/фото, DELETE завершує зв’язок або видаляє фото. Списки з limit/offset мають межі, точний response_model визначає total/items. Приклади та constraints полів — у схемах нижче OpenAPI.

Основні ресурси: ProfileOut (публічні дані власника), EntryCreate/EntryUpdate/EntryOut (дата, статус, напої type/volume_ml, тригер, коментар; серверні поля не задаються клієнтом), GoalMilestoneOut (обчислюваний етап), StatisticsOut (серії/показники), RelationshipOut (напрям і стан зв’язку), NotificationOut (текст і актуальні дозволи), ComplaintOut (скарга/стан), ErrorResponse (code/message/details). Точні назви схем звіряються з components/schemas згенерованого YAML.

### Методи й задекларовані відповіді

Таблиця отримана з OpenAPI поточного коду; вказує задекларовані статуси, не замінює виконання негативних тестів.

| Метод | Шлях | Статуси OpenAPI |
|---|---|---|
| POST | `/api/v1/auth/register` | 201, 422 |
| POST | `/api/v1/auth/login` | 200, 422 |
| GET | `/api/v1/auth/me` | 200 |
| POST | `/api/v1/auth/logout` | 204 |
| GET | `/api/v1/profile` | 200 |
| PATCH | `/api/v1/profile` | 200, 422 |
| PUT | `/api/v1/profile/password` | 204, 422 |
| PATCH | `/api/v1/profile/preferences` | 200, 422 |
| GET | `/api/v1/profile/avatar` | 200 |
| PUT | `/api/v1/profile/avatar` | 200 |
| DELETE | `/api/v1/profile/avatar` | 204 |
| GET | `/api/v1/mentorships/code` | 200, 401, 422 |
| GET | `/api/v1/mentorships/my-mentor` | 200, 401, 422 |
| GET | `/api/v1/mentorships/my-mentees` | 200, 401, 422 |
| POST | `/api/v1/mentorships` | 200, 201, 401, 422 |
| GET | `/api/v1/mentorships/{relationship_id}` | 200, 401, 422 |
| DELETE | `/api/v1/mentorships/{relationship_id}` | 204, 401, 422 |
| GET | `/api/v1/mentorships/{relationship_id}/calendar/entries` | 200, 401, 422 |
| GET | `/api/v1/mentorships/{relationship_id}/calendar/entries/{record_id}` | 200, 401, 422 |
| GET | `/api/v1/mentorships/{relationship_id}/statistics` | 200, 401, 422 |
| GET | `/api/v1/notifications` | 200, 401, 422 |
| GET | `/api/v1/notifications/unread-count` | 200, 401, 422 |
| GET | `/api/v1/notifications/{notification_id}` | 200, 401, 404, 422 |
| PATCH | `/api/v1/notifications/{notification_id}/read` | 200, 401, 404, 422 |
| POST | `/api/v1/notifications/{notification_id}/support` | 201, 401, 403, 404, 409, 422 |
| POST | `/api/v1/calendar/entries` | 201, 401, 404, 409, 422, 503 |
| GET | `/api/v1/calendar/entries` | 200, 401, 404, 422 |
| GET | `/api/v1/calendar/entries/{record_id}` | 200, 401, 404, 422 |
| PATCH | `/api/v1/calendar/entries/{record_id}` | 200, 401, 403, 404, 422, 503 |
| GET | `/api/v1/goals` | 200, 401, 422 |
| GET | `/api/v1/statistics` | 200, 401, 422 |
| GET | `/health` | 200 |
| GET | `/ready` | 200 |
| GET | `/api/v1/admin/complaints` | 200, 401, 403, 422 |
| GET | `/api/v1/admin/complaints/{complaint_id}` | 200, 401, 403, 404, 422 |
| PATCH | `/api/v1/admin/complaints/{complaint_id}` | 200, 401, 403, 404, 409, 422 |
| GET | `/api/v1/admin/overview` | 200, 401, 403, 422 |
| GET | `/api/v1/admin/trigger-distribution` | 200, 401, 403, 422 |
| POST | `/api/v1/complaints` | 201, 401, 403, 404, 409, 422 |
| POST | `/internal/jobs/reminders` | 200, 401, 409, 422, 503 |

## Використання ШІ — оновлення документації

Codex (OpenAI) використано для звірки API-опису з FastAPI/Pydantic та експортованим OpenAPI. Агент прочитав відповідні файли й зауваження викладача, звірив локальні посилання та узгодженість requirements/test-plan/RTM; результати запусків зазначаються окремо з датою. Історичні результати не видаються за нові, людський взаємний огляд та ручне онлайн-приймання цим записом не підтверджуються. Команда переглядає зміни в PR перед злиттям. Джерела правил: [критерії курсу](https://ssdm-2026.cs-courses.org/midterm-evaluation.html), [політика ШІ](https://ssdm-2026.cs-courses.org/ai-policy.html).
