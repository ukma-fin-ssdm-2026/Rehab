# Повідомлення, підтримка та нагадування — передача на КТ-Б

Основа: develop c505010, ORM 0002 та справжній ProfileProvider. Модулі Марії використовують наявні таблиці; нових міграцій немає. Інтеграційний коміт підключає календар, головний API та root messages; спільна публікація ще очікує готовності інших модулів. Це не звіт онлайн-приймання.

## HTTP-контракт

router — backend.app.routers.notifications.router, prefix /notifications під спільним /api/v1. Використовує чинні get_current_user та _db_session, не створює окрему авторизацію. GET список із limit=30 (1–100), offset>=0; GET /unread-count; GET /{id}; PATCH /{id}/read без тіла; POST /{id}/support з {text}. Список newest-first за created_at,notification_id; читання ідемпотентне. Чужі повідомлення й підтримка через чуже повідомлення — 404; завершений зв'язок — 403 MENTORSHIP_INACTIVE; виправлений sober — 409 RELAPSE_NO_LONGER_ACTIVE; уже надіслана підтримка — 409 SUPPORT_ALREADY_SENT. Поточний коментар читається в detail власного повідомлення, загального маршруту коментарів немає.

DTO — schemas/notifications.py, клієнт — api/notifications.ts. Автоматичні title/body будуються під поточний message_style отримувача, авторський текст коментаря лишається дослівним після початкового trim. can_support/can_view_mentee/can_report_mentor обчислює сервер щоразу. Завершення зв'язку припиняє нову підтримку/перегляд, зберігає історію і право підопічного скаржитися на отриманий коментар.

## Поліні: транзакція календаря

emit_relapse_once(db, record_id, previous_status) — services/notifications.py. До зміни календаря caller бере users підопічного → активний mentorship → day_record. Після flush та recompute_progress, перед єдиним commit викликає helper; для створення previous_status=None. Helper не бере попередні locks у зворотному порядку, не commit/rollback. Він умовно заповнює first_relapse_at тільки для першого relapse та створює notification активному ментору; маркер зберігається і без ментора. UNIQUE(recipient_id,event_key) додатково захищає дубль. Подія приєднаному пізніше ментору не відтворюється. Подія та календар відкочуються разом. Calendar caller підключений інтеграційним комітом у calendar_postgres._write: порядок блокувань, previous_status та єдиний commit перевірені через справжній main API. Поліні потрібно врахувати цей коміт у своїй гілці, щоб не додати другий виклик helper.

## Софії: інтеграція API та job

Notification і profile routers вже зареєстровані у main; OpenAPI згенеровано з поточного app та оновлено опис п'яти етапів. create_due_reminders(db, now) у services/reminders.py повертає created_in_app,queued_email,skipped; now має timezone. До 20:00 Kyiv — нулі; після — лише поточна бізнес-дата. Користувачі обробляються keyset-порціями по 100; user-lock узгоджує перевірку явного запису з календарем. Одне in-app нагадування за дату та opt-in email_delivery створюються однією транзакцією, без Gmail-викликів. Orchestrator фіксує транзакцію і лише після цього викликає поштовий worker; помилка Gmail не повинна відкочувати in-app повідомлення. Надсилання пошти й endpoint job лишаються Софії. Немає scheduler у startup або мережевих дій при import.

## Анастасії: навігація

Екрани app/messages/index.tsx та [notification_id].tsx, захист у messages/_layout.tsx (guest/admin/onboarding не бачать повідомлень). messages додано до спільного захищеного user stack інтеграційним комітом; ProfileProvider вже споживається напряму. Root guard перевірений для guest/admin/onboarding, вкладений guard збережений. Анастасії потрібно врахувати один новий Stack.Screen при оновленні гілки. Передача на /mentee/[relationship_id] використовує контракт Поліни; скарга — /support/report із relationship_id та support_comment_id Софії. Не створено паралельної форми скарги чи чужого календаря.

На головній є кнопка повідомлень і лічильник unread; помилка лічильника позначається, а не видається за нуль. На відкритому списку/detail — focus, видимість вкладки й інтервал 60 s; у прихованій вкладці polling не виконує запитів. Refresh перезавантажує всі видимі порції, щоб нові надходження не залишали старі offset-сторінки. Дані та незавершені запити розділені за акаунтом; blur/зміна акаунта скасовують актуальність старих відповідей. Підтримка має screen-scoped single-flight, а остаточний захист дубля забезпечує БД.

Два старі frontend-тести приведено до вже чинного ТЗ: 403, зокрема MENTORSHIP_INACTIVE, не завершує JWT-сесію; admin переходить у /admin/complaints, а не глобальний список користувачів. Runtime авторизацію не змінено.

Успішні приватні відповіді notification router мають Cache-Control: no-store. У контракті OpenAPI detail/read описано 404, support — також 403 та 409; спільні 401/422 збережені.


## Межа наскрізного тесту

Новий test_calendar_message_flow.py використовує справжній backend.app.main:app, реєстрацію/вхід із JWT та окрему PostgreSQL. Активний mentorship готується як тестова передумова через ORM, оскільки API/екрани приєднання з PR 217 ще не входять у цей develop. Перевірено GET/PATCH профілю, POST sober, PATCH relapse, новий прогрес/етап, одне повідомлення з поточним стилем, чужий ID, POST support, повідомлення підопічному, read/unread та sober→relapse без повтору. Окремий fault-injection перевіряє повний rollback після створення події. Це локальний тест готової календарної інтеграції, не онлайн-приймання і не перевірка ще незлитих PR 217/220.
