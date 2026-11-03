# Вимоги та реалізовані компоненти

Назви Routes, Services, DB, Job, Mail і Web відповідають псевдонімам у [діаграмі компонентів](uml/component-diagram.puml). Конкретні модулі наведені від backend/app/. Перелік вузлів тестів — у [RTM](../requirements/rtm.md).

| Вимога | Компоненти діаграми та модулі | Рішення | Верифікація |
|---|---|---|---|
| FR-001 | Routes / Services / DB: routers/calendar_postgres.py; repositories/entries.py | Власний запис, UNIQUE(user_id,date), одна транзакція | `tests/test_calendar_postgres_api.py::test_create_list_details_and_progress_callback` |
| FR-002 | Routes / Services / DB: models.py; repositories/entries.py | Серверна бізнес-дата Europe/Kyiv, відхилення майбутніх дат | `tests/test_entry_details.py::test_future_date_is_rejected` |
| FR-003 | Routes / Services / DB: services/notifications.py; routers/calendar_postgres.py | Перша подія й приватне повідомлення без повтору | `tests/test_calendar_relapse_notifications.py::test_calendar_emits_once_and_support_reaches_mentee` |
| FR-004 | Routes / Services / DB: routers/goals.py; services/statistics.py | П’ять незмінних етапів без CRUD | `tests/test_goals.py::test_list_returns_fixed_milestones_without_user_goal_rows` |
| FR-005 | Routes / Services / DB: services/statistics.py; routers/goals.py | Історичне досягнення за longest_streak | `tests/test_goal_progress.py::test_five_milestone_boundaries_and_historical_badges` |
| FR-006 | Routes / Services / DB: services/progress_sync.py; services/statistics.py | Перерахунок з усієї історії після виправлень | `tests/test_progress_sync.py::test_recompute_progress_updates_best_streak_from_calendar` |
| FR-007 | Routes / Services / DB: routers/admin.py; services/statistics.py | Агрегати 30 київських дат без персональних полів | `tests/test_admin.py::test_distribution_is_30_days_with_correct_shares_and_no_personal_data` |
| FR-008 | Routes / Services / DB: routers/calendar_postgres.py; repositories/entries.py | 48 годин включно, лише власник, created_at незмінний | `tests/test_postgres_entries.py::test_exact_edit_window_and_original_creation_time` |
| FR-009 | Routes / Services / DB: routers/mentorship.py; services/mentorship.py | Код, активна пара, остаточне завершення | `tests/test_mentorship_api.py::test_private_code_and_normalized_idempotent_join` |
| FR-010 | Routes / Services / DB: routers/admin.py; services/complaints.py; services/mentorship.py | Рішення за скаргою закриває конкретну пару | `tests/test_system_integration.py::test_full_relapse_support_complaint_flow` |
| FR-011 | Routes / Services / DB: security.py; routers/auth.py; repositories/users.py | Підпис/строк JWT і token_version із БД | `tests/test_auth_postgres.py::test_logout_revokes_other_tokens_but_not_other_accounts` |
| PERF-001 | Web / Routes / DB | Вимірювання поточного API з реальними JWT | Окремий навантажувальний прогін, ще потрібен |
| SEC-001 | Routes / Services: security.py, services/mentorship.py | Роль + право на ресурс | test_security_dependency.py; test_mentorship_api.py |
| SEC-002 | Services: services/auth.py, services/profile.py | Argon2, без повернення хешів | test_auth.py; test_profile_postgres_integration.py |
| REL-001 | Routes / DB: routers/health.py, db/session.py | /health та /ready; окреме спостереження за uptime | test_health.py; місячний моніторинг окремо |
| USAB-001 | Web: goals.tsx, useProgressStatistics | Зрозумілий прогрес і оновлення без reload | frontend/tests/progress.test.cjs; ручний кейс №29 |

## Зворотний зв’язок компонентів

Web реалізує всі користувацькі сценарії й адміністративний інтерфейс; Routes/Services/DB покривають FR-001…011 та SEC-001/002. Job і Mail реалізують додаткове погоджене правило щоденних opt-in нагадувань (US-012): routers/jobs.py, services/reminders.py, services/email_reminders.py; перевірки test_reminders.py, test_email_reminders.py. Це не повідомлення про зрив на пошту.

## Вимірювані сценарії якості

1. За 100 одночасних авторизованих користувачів p95 оновлення календаря/статистики ≤500 мс. Потрібен окремий актуальний прогін; холодний старт Free вимірюється окремо.
2. Усі запити неадміністратора до admin-маршрутів відхиляються 403; усі спроби стороннього або колишнього ментора читати підопічного відхиляються без персональних даних. Перевірка test_admin.py і test_mentorship_api.py; одна успішна заборонена дія означає провал.

## Використання ШІ — оновлення документації

Codex (OpenAI) використано для звірки архітектурних описів, модулів і обмежень із кодом. Агент прочитав відповідні файли й зауваження викладача, звірив локальні посилання та узгодженість requirements/test-plan/RTM; результати запусків зазначаються окремо з датою. Історичні результати не видаються за нові, людський взаємний огляд та ручне онлайн-приймання цим записом не підтверджуються. Команда переглядає зміни в PR перед злиттям. Джерела правил: [критерії курсу](https://ssdm-2026.cs-courses.org/midterm-evaluation.html), [політика ШІ](https://ssdm-2026.cs-courses.org/ai-policy.html).
