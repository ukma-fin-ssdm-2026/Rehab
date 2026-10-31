# PostgreSQL: спільна основа для КТ-А

## Стан цієї зміни

Міграція `0002_team_foundation` продовжує `0001_initial`, не змінюючи її.
Реалізовано схему, ORM, генерацію кодів та внутрішні функції доступу.
Нові API/UI профілю, менторства, повідомлень і скарг ще не підключені.
Міграція не надсилає повідомлень або листів. Це не підтвердження її
застосування в Neon: онлайн-застосування відбувається після спільного review.

Наступний модуль менторства вже реалізує окремий router та екрани:
[передача для спільного підключення](mentorship-handoff.md).

Чинний `backend.app.main:app` уже використовує PostgreSQL для авторизації,
календаря й статистики. Нинішні етапи 7/30 розраховуються з історії,
не з legacy-таблиці goals; 90/180/365 — наступна частина Марії.

## Таблиці та модулі

Модулі лежать у `backend.app.db.models`; імпорт пакета реєструє всі моделі
без відкриття з'єднання. [Модель даних](../architecture/data-model.md).

| Модель / модуль | Таблиця | Контракт |
| --- | --- | --- |
| User / user | users | mentor_code, email_reminders_enabled=false, message_style=formal |
| DayRecord / entry | day_records | first_relapse_at; історичні relapse заповнені без розсилки |
| UserAvatar / avatar | user_avatars | Приватне JPEG BYTEA <=256 KiB, version>=1 |
| Mentorship / mentorship | mentorships | Унікальна пара за всю історію, один active на mentee |
| Notification / notification | notifications | UNIQUE(recipient_id,event_key), три типи |
| SupportComment / support_comment | support_comments | Один коментар на relapse_notification_id |
| Complaint / complaint | complaints | Одна pending-скарга на пару осіб |
| EmailReminderDelivery / email_delivery | email_reminder_deliveries | Одне завдання на notification_id, без OAuth-секретів |

Код: 12 символів `ABCDEFGHJKLMNPQRSTUVWXYZ23456789`, криптографічний
`secrets` у Python. ORM-default сумісний із чинним seed.
PostgreSQL-default використовує вбудований gen_random_uuid без розширень
і підтримує старі SQL INSERT без нового поля. Реєстрація повторює лише
конфлікт коду через savepoint, не відкидаючи чужі зміни транзакції.
Код не включений до чинних register/login/me.

Завершення не видаляє рядок. UNIQUE(mentor_id,mentee_id) забороняє повторну
вставку; сервіс не повинен повторно активувати завершений рядок.
Зворотна пара незалежна. Роль mentor не відкриває довільних чужих даних.

## Анастасії

Використати готові User/UserAvatar, не створювати другий Base або users.
Фото отримувати окремо від auth/me. Новий profile API явно обмежує поля
власника, код не додається до загальних DTO. Зміна пароля використовує
token_version, як чинний logout.

Міграція скидає старі is_blocked=false, але залишає колонку.
Видалення перевірок account block і admin/block API координується із
Софією наступним кроком, а не оголошується готовим цією основою.

## Марії

Використати Notification, SupportComment, EmailReminderDelivery.
Типи: daily_reminder, relapse, support_comment.
Ключі: reminder:YYYY-MM-DD, relapse:mentee_id:YYYY-MM-DD,
support:support_comment_id.

Ваш майбутній emit_relapse_once(db,record_id,previous_status) не робить
commit, атомарно встановлює first_relapse_at за першої події та не
розсилає історію новому ментору. Поліна підключить його до календаря
на наступній інтеграції, в одній транзакції із записом/прогресом.
Створення in-app нагадування й opt-in поштового завдання — ваш сервіс;
транспорт Gmail і розклад — Софії. Зрив/коментар поштою не надсилаються.

## Софії

Використати Complaint та EmailReminderDelivery. Скарга завершує тільки
конкретну пару, не ставить is_blocked=true й не відкликає сесії.
Не змінювати ended_* напряму, викликати сервіс завершення.
Не створювати дубльованих таблиць або паралельних Alembic heads.

Для Neon потрібен прямий URL без -pooler, спільний review і контрольна
точка відновлення. Цей PR не застосовує міграцію онлайн. Чинний seed
сумісний через ORM-default; новий демо-сценарій готується окремо.

## Функції доступу для спільного використання

Модуль `backend.app.services.mentorship`:

- require_relationship_participant(db,actor_id,relationship_id): обидві
  сторони, включно з історичним зв'язком. Чужий/невідомий ID → 404.
- require_active_mentor(db,actor_id,relationship_id,lock=False): тільки
  ментор active-зв'язку; завершений свій → 403 MENTORSHIP_INACTIVE.
- end_relationship(db,relationship_id,actor_id,reason): власна сторона
  з mentor_left/mentee_left. Повтор не змінює історії; complaint заборонено.
- end_relationship_for_complaint(db,relationship_id,admin_id): внутрішня
  операція для транзакції модерації, перевіряє admin.

Функції flush-ять, але не commit/rollback. Єдиний порядок блокувань writer:
users підопічного → mentorships → day_records/notifications.
lock=True бере users і mentorships сам. Календар надалі бере той самий
порядок до зміни запису, а не блокує mentorship після day_record.

DTO: `backend.app.schemas.mentorship` — MentorshipCreate, RelationshipContact,
RelationshipOut, RelationshipList. Код trim+uppercase, зайві поля запиту
(наприклад mentor_id) заборонені. Контакти: user_id, nickname, email.

## Локальна перевірка

Потрібні Docker та ізольована TEST_DATABASE_URL. Секрети лишаються в .env.

```powershell
docker compose up -d postgres-test
.venv/Scripts/python.exe -m alembic -x test_db=true upgrade head
.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider
.venv/Scripts/python.exe -m alembic heads
```

Очікуваний head: 0002_team_foundation. Перевіряються upgrade зі старими
даними в окремій схемі тестової PostgreSQL, повторний upgrade, defaults,
constraints, старі HTTP register/login/me, зіткнення кодів, доступ,
завершення, відкликання доступу між двома сесіями та rollback. Старі тести адмінки тепер теж використовують
ізольовану PostgreSQL замість SQLite-копії users.

Поточний backfill 0002 читає наявні рядки через з'єднання: офлайн-експорт
`alembic upgrade head --sql` для нього не підтримується. Застосовувати
версію штатною командою upgrade із прямим з'єднанням; готовий SQL-файл
для ручного виконання цією зміною не надається.

Downgrade видаляє нові таблиці/поля та їхні дані. Перевіряти його можна
тільки на одноразовій тестовій БД; для спільної бази потрібен окремий план
збереження нових даних. Скинуті старі блокування не відновлюються.
