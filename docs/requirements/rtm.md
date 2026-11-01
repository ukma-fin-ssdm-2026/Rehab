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

## Стан реалізації та наявні тести

Стан наведено для develop з інтегрованими модулями. «Реалізовано» означає наявність коду й автоматичної перевірки; публічне приймання та злиття в main фіксуються окремо. Test-01…Test-14 — початкові номери сценаріїв, не назви pytest-функцій; відповідні кейси мають конкретні вузли в тест-плані.

| Вимога | Стан у develop | Модулі від backend/app/ | Наявний тест |
|---|---|---|---|
| FR-001 | Реалізовано; онлайн-приймання окремо | routers/calendar_postgres.py; repositories/entries.py | `tests/test_calendar_postgres_api.py::test_create_list_details_and_progress_callback` |
| FR-002 | Реалізовано; онлайн-приймання окремо | models.py; repositories/entries.py | `tests/test_entry_details.py::test_future_date_is_rejected` |
| FR-003 | Реалізовано; онлайн-приймання окремо | services/notifications.py; routers/calendar_postgres.py | `tests/test_calendar_relapse_notifications.py::test_calendar_emits_once_and_support_reaches_mentee` |
| FR-004 | Реалізовано; онлайн-приймання окремо | routers/goals.py; services/statistics.py | `tests/test_goals.py::test_list_returns_fixed_milestones_without_user_goal_rows` |
| FR-005 | Реалізовано; онлайн-приймання окремо | services/statistics.py; routers/goals.py | `tests/test_goal_progress.py::test_five_milestone_boundaries_and_historical_badges` |
| FR-006 | Реалізовано; онлайн-приймання окремо | services/progress_sync.py; services/statistics.py | `tests/test_progress_sync.py::test_recompute_progress_updates_best_streak_from_calendar` |
| FR-007 | Реалізовано; онлайн-приймання окремо | routers/admin.py; services/statistics.py | `tests/test_admin.py::test_distribution_is_30_days_with_correct_shares_and_no_personal_data` |
| FR-008 | Реалізовано; онлайн-приймання окремо | routers/calendar_postgres.py; repositories/entries.py | `tests/test_postgres_entries.py::test_exact_edit_window_and_original_creation_time` |
| FR-009 | Реалізовано; онлайн-приймання окремо | routers/mentorship.py; services/mentorship.py | `tests/test_mentorship_api.py::test_private_code_and_normalized_idempotent_join` |
| FR-010 | Реалізовано; онлайн-приймання окремо | routers/admin.py; services/complaints.py; services/mentorship.py | `tests/test_system_integration.py::test_full_relapse_support_complaint_flow` |
| FR-011 | Реалізовано; онлайн-приймання окремо | security.py; routers/auth.py; repositories/users.py | `tests/test_auth_postgres.py::test_logout_revokes_other_tokens_but_not_other_accounts` |
| PERF-001 | Ціль не підтверджена на поточній версії | API/PostgreSQL | Історичний tests/performance/locustfile.py використовує demo-токен; потрібен новий JWT-прогін |
| SEC-001 | Реалізовано; перевіряються роль і активний зв’язок | security.py; services/mentorship.py | `tests/test_admin.py::test_admin_routes_for_user_and_mentor_return_403`; `tests/test_mentorship_foundation.py::test_only_active_mentor_can_read_mentee` |
| SEC-002 | Реалізовано | services/auth.py; services/profile.py | `tests/test_auth.py::test_argon2_password_hash` |
| REL-001 | Ціль, місячний uptime ще не виміряний | routers/health.py; PostgreSQL/хостинг | Перевірка /ready не замінює місячний моніторинг |
| USAB-001 | UI реалізовано; ручний звіт Марії M05–M06/M26 отримано, SHA ще не зіставлено | frontend/src/app/(tabs)/goals.tsx | Ручний кейс №29 |

| Додаткова історія | Вимоги/правила | Реалізація та перевірки |
|---|---|---|
| US-009, US-010 | FR-011, SEC-001, SEC-002 | Auth/JWT/session; test_auth_postgres.py, test_auth_revocation.py та клієнтські lifecycle-тести |
| US-011 | SEC-001/002 і правила профілю в requirements.md | Profile/avatar/preferences; test_profile_postgres_integration.py, test_message_styles.py |
| US-012 | FR-003 і правила підтримки/нагадувань у requirements.md | test_support_comments.py, test_reminders.py, test_email_reminders.py; Gmail наживо перевіряється окремо |

## Використання ШІ — оновлення документації

Codex (OpenAI) використано для узгодження вимог, критеріїв і простежуваності з реалізацією. Агент прочитав відповідні файли й зауваження викладача, звірив локальні посилання та узгодженість requirements/test-plan/RTM; результати запусків зазначаються окремо з датою. Історичні результати не видаються за нові, людський взаємний огляд та ручне онлайн-приймання цим записом не підтверджуються. Команда переглядає зміни в PR перед злиттям. Джерела правил: [критерії курсу](https://ssdm-2026.cs-courses.org/midterm-evaluation.html), [політика ШІ](https://ssdm-2026.cs-courses.org/ai-policy.html).
