# Високорівнева архітектура Rehab

## Архітектурний стиль

Клієнт-серверна система з багатошаровим монолітом FastAPI: routers → services/repositories → SQLAlchemy/PostgreSQL. Expo Web спілкується зі спільним API-клієнтом через HTTPS/JSON і JWT. Основний застосунок — backend.app.main:app; історичний прототип не є сервером онлайн-версії.

## Компоненти

- Frontend: авторизація й відновлення сесії, ProfileProvider, календар, статистика, цілі, менторство, inbox, скарги та адмінка.
- Backend: auth/profile/mentorship/calendar/goals/statistics/notifications/complaints/admin і окремо захищений internal job.
- PostgreSQL: облікові записи, фото BYTEA, календар, зв’язки, повідомлення, підтримка, скарги та outbox. Міграції Alembic 0001_initial → 0002_team_foundation.
- Gmail sender: лише opt-in копії щоденних нагадувань; секрети зберігаються в середовищі backend.

## Транзакції та доступ

Запис календаря, перерахунок прогресу й emit_relapse_once фіксуються разом. Порядок блокувань: users (FOR NO KEY UPDATE) → mentorships → day_records/notifications/complaints. Перша подія не дублюється при повторній зміні статусу.

Роль не замінює право на ресурс. Ментор читає календар і статистику лише активного підопічного; після завершення чи схвалення скарги новий доступ і підтримка закриті. Історія зберігається. Адмін бачить скарги з доказом і агрегати; акаунти не блокуються.

Job серіалізується PostgreSQL advisory lock, створює inbox/outbox і робить commit перед зовнішнім надсиланням. Унікальні ключі захищають від повторів; невизначена доставка не повторюється сліпо.

## Узгодженість клієнта

POST/PATCH календаря повідомляє пов’язані екрани про зміну. Фокус і видимість оновлюють дані; запізніла відповідь іншого акаунта або періоду не підміняє поточний екран. Помилка запиту має окремий стан і повтор. Приватна навігація очікує відновлення сесії; прямі посилання обслуговує SPA rewrite.

## Розгортання та діаграми

Render Static Site (Expo dist), Render Web Service Free (FastAPI) та Neon Free (PostgreSQL через TLS). Локальні dev/test бази PostgreSQL 16 відокремлені. Тести не використовують онлайн-БД.

- [Компоненти](uml/component-diagram.puml)
- [Сценарій зриву](uml/sequence-diagram.puml)
- [Розгортання](uml/deployment-diagram.puml)
- [Модель даних](data-model.md)
- [Налаштування розгортання](../deployment/render-neon.md)

Зображення згенеровано з відповідних PlantUML-джерел:

![Компоненти](uml/component-diagram.png)

![Сценарій зриву](uml/sequence-diagram.png)

![Розгортання](uml/deployment-diagram.png)

## Внутрішні інтерфейси

| Межа | Реальний інтерфейс | Відповідальність |
|---|---|---|
| Routes → Security | security.get_current_user, require_role | Валідація JWT, token_version і ролі за БД; user_id не береться з довільного тіла |
| Routes → Database | db.session.get_db / security._db_session | Session на запит, відкат помилок; URI обирає core/config.py |
| Calendar → Repository | repositories.entries.create_entry/update_entry/list_user_entries | Власник, дати, збереження DayRecord; точні сигнатури — в модулі |
| Calendar → Progress | services.progress_sync.recompute_progress | Перерахунок рекорду без самостійного commit |
| Calendar → Notifications | services.notifications.emit_relapse_once | Перша подія після flush, у тій самій транзакції |
| Mentorship/Support → Access | services.mentorship.require_active_mentor | Активний зв’язок і узгоджені блокування; не лише роль |
| Admin → Complaints | services.complaints.decide_complaint | Рішення та завершення пари в одній транзакції |
| Job → Reminder/Email services | create_due_reminders; deliver_pending_reminders | Спочатку inbox/outbox і commit, потім зовнішня Gmail-відправка |

Схеми HTTP — Pydantic у models.py та schemas/; збереження — окремі ORM у db/models/. Межі довіри: TB-1 Browser/Web, TB-2 API/Services/Job/Mail, TB-3 PostgreSQL; Gmail — зовнішній сервіс. Відповідні ризики — у [STRIDE](threat-model.md).

## Використання ШІ — оновлення документації

Codex (OpenAI) використано для звірки архітектурних описів, модулів і обмежень із кодом. Агент прочитав відповідні файли й зауваження викладача, звірив локальні посилання та узгодженість requirements/test-plan/RTM; результати запусків зазначаються окремо з датою. Історичні результати не видаються за нові, людський взаємний огляд та ручне онлайн-приймання цим записом не підтверджуються. Команда переглядає зміни в PR перед злиттям. Джерела правил: [критерії курсу](https://ssdm-2026.cs-courses.org/midterm-evaluation.html), [політика ШІ](https://ssdm-2026.cs-courses.org/ai-policy.html).
