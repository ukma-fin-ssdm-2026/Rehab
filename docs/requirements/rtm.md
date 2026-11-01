# Матриця простежуваності (RTM)

| Історія | Тип | Опис | Пов'язані FR | Пов'язані NFR | Тестові випадки |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **US-001** | FR | Відмітка поточного дня в календарі | FR-001, FR-002 | PERF-001, REL-001 | Test-01: Успішна відмітка сьогодні<br>Test-02: Заборона відмітки майбутньої дати<br>Лаб 7: №1, №2, №3, №18, №20, №28 |
| **US-002** | FR | Сповіщення ментора про зрив підопічного | FR-003 | PERF-001 | Test-03: Зрив генерує сповіщення<br>Test-04: Перехід зі сповіщення<br>Лаб 7: №4, №5 |
| **US-003** | FR | Перегляд фіксованих етапів тверезості | FR-004, FR-005 | USAB-001 | Test-05: Активний етап і прогрес<br>Test-06: Відображення виконаного етапу<br>Лаб 7: №6, №7, №8, №32 |
| **US-004** | FR | Обробка скарг та модерація користувачів адміном | FR-010, FR-011 | SEC-001 | Test-13: Рішення щодо скарги закриває пару<br>Test-14: Відкликана сесія недійсна<br>Лаб 7: №16, №17, №19, №26 |
| **US-005** | FR | Порівняння серії з абсолютним рекордом | FR-006 | PERF-001 | Test-07: Перевищення рекорду автоматично оновлює значення<br>Лаб 7: №9, №10 |
| **US-006** | FR | Аналітика категорій тригерів для адміна | FR-007 | SEC-001, PERF-001 | Test-08: Відображення діаграми з правильними відсотками<br>Лаб 7: №11, №21, №22, №23, №30 |
| **US-007** | FR | Редагування запису протягом 48 годин | FR-008 | REL-001 | Test-09: Успішна зміна через 47 год<br>Test-10: HTTP 403 при редагуванні після 48 годин<br>Лаб 7: №12, №13, №24, №25 |
| **US-008** | FR | Менторство за постійним кодом | FR-009 | SEC-001 | Test-11: Код створює активний зв’язок<br>Test-12: Завершена пара не приєднується повторно<br>Лаб 7: №14, №15, №31 |

## Простежуваність тест-кейсів Лаб 7

Номери тест-кейсів відповідають рядкам документа `docs/validation/test-plan.md`. Зв'язок із вимогою визначає заплановану перевірку, а не підтверджує її фактичне виконання.

| Вимога | Тест-кейси з тест-плану |
|---|---|
| FR-001 | №1, №3, №20 |
| FR-002 | №2 |
| FR-003 | №4, №5 |
| FR-004 | №6, №7, №32 |
| FR-005 | №8 |
| FR-006 | №9, №10 |
| FR-007 | №11, №21, №22, №23 |
| FR-008 | №12, №13, №24, №25 |
| FR-009 | №14, №15 |
| FR-010 | №16, №26 |
| FR-011 | №17 |
| PERF-001 | №18, №30 |
| SEC-001 | №19, №31 |
| SEC-002 | №27 |
| REL-001 | №28 |
| USAB-001 | №29 |

### Автоматизовані перевірки Лаб 7

| Вимога | Автоматизована перевірка | Файл |
|---|---|---|
| FR-008 | FR008-R1 — FR008-R6 (шість правил таблиці рішень) | `tests/test_calendar.py` |
| PERF-001 | Навантажувальний тест статистики, 100 користувачів, 30 секунд, історичний p95 = 32 мс для прототипу, не поточної онлайн-версії | `tests/performance/locustfile.py` |

**Докази реалізації:**
- [PR №157 — перевірки FR-008](https://github.com/ukma-fin-ssdm-2026/Rehab/pull/157).
- Бонус №4 — результати автоматизованого тесту наведено в `docs/validation/test-plan.md`.


## Реалізація інтегрованих модулів

| Історії | Код | Автоматичні перевірки |
|---|---|---|
| US-001, US-005, US-007 | routers/calendar_postgres.py, services/progress_sync.py, services/statistics.py | test_calendar_postgres_api.py, test_progress_sync_calendar.py, test_calendar_message_flow.py; frontend/tests/calendar.test.cjs, progress.test.cjs |
| US-002, US-012 | services/notifications.py, services/reminders.py, services/email_reminders.py, routers/jobs.py | test_notifications.py, test_support_comments.py, test_reminders.py, test_email_reminders.py, test_system_integration.py |
| US-003 | routers/goals.py, services/statistics.py | test_goals.py, test_goal_progress.py |
| US-004, US-006 | routers/complaints.py, routers/admin.py | test_complaints.py, test_admin.py |
| US-008 | routers/mentorship.py, services/mentorship.py | test_mentorship_api.py, test_calendar_relapse_notifications.py; frontend/tests/mentorship.test.cjs |
| US-009, US-010 | routers/auth.py, security.py, frontend/src/auth/ | test_auth_postgres.py, test_auth_revocation.py; frontend/tests/auth-navigation.test.cjs, onboarding-session.test.cjs |
| US-011 | routers/profile.py, services/avatar.py, frontend/src/profile/, frontend/src/messages/ | test_profile_postgres_integration.py, test_avatar_image.py, test_message_styles.py; frontend/tests/style-consent.test.cjs, copy-rotation.test.cjs |

Шляхи backend наведено від backend/app/, тести Python — від tests/. Список визначає покриття сценаріїв, а фактичний результат береться з CI для конкретного SHA. Ручне онлайн-приймання фіксується в тест-плані.
