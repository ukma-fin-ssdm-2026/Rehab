# Модель даних Rehab

## 1. Фактична схема PostgreSQL

Міграція `0001_initial` створює users, day_records і goals. Усі три таблиці
збережені; застосована онлайн-міграція не переписується. Таблиця goals є
legacy-схемою: поточні етапи 7/30 обчислюються з календаря, її рядки не читаються
й не змінюються runtime API. Історичні або seed-рядки goals не визначають
прогрес етапів. Для КТ3 нова міграція не потрібна.

![Реалізована схема PostgreSQL](uml/implemented-data-model.png)
[Джерело PlantUML](uml/implemented-data-model.puml)

## 2. Сутності та обмеження

| Таблиця | Призначення та основні обмеження |
|---|---|
| users | Identity PK; унікальний нормалізований email; name/nickname; Argon2 password_hash; role; is_blocked; token_version; tracking_start_date; best_streak; created_at UTC |
| day_records | Identity PK; FK user_id → users; UNIQUE(user_id,date); status sober/relapse; trigger stress/holiday/social/other або null; drinks JSONB-масив; comment до 2000 символів; created_at/updated_at UTC |
| goals (legacy) | FK user_id → users; target_days 1..3650 за старим CHECK; is_achieved; created_at/updated_at. Нових записів застосунок не створює |

Users → day_records: 1:N. FK має ON DELETE CASCADE; без користувача запис
створити не можна. Один календарний запис містить масив напоїв виду
`{type, volume_ml}`; окремого довідника напоїв немає. Pydantic перевіряє
тип напою й додатний цілий об'єм. DB CHECK перевіряє JSONB-масив,
статус, категорію тригера та відсутність напоїв/тригера для sober.

## 3. Правила запису й перерахунку

Дата належить tracking_start_date..current_date (Europe/Kyiv).
Створення й редагування блокують рядок users та перераховують прогрес у тій
самій транзакції; окремого незбереженого стану цілей немає. Best_streak —
перераховуваний кеш, джерело істини — календарна історія.

Рівно 48 годин від created_at редагувати можна, більше — не можна.
PATCH приймає тільки status і trigger_category. Зміна на sober очищує drinks
і trigger_category; comment, date, user_id та created_at залишаються.

Pydantic Entry-схеми описують API, SQLAlchemy ORM — фактичне збереження.
Запуск API не виконує create_all, скидання або автоматичний seed.
[ADR-002](decisions/ADR-002.md), [налаштування PostgreSQL](../development/postgres-local.md).

## 4. Межі початкової концепції

[Початкова концептуальна ER-модель Лаб 3](uml/diagram.png) також містить
MentorRequest, Notification і Complaint. Це майбутні сутності; поточна міграція
їх не створює, а застосунок не реалізує відповідні запити/сповіщення/скарги.
Фактичну схему релізу показано в розділі 1.

## 5. Персональні дані

Email, хеш пароля й календарні записи користувача приватні. Паролі не
повертаються API; читання й редагування запису перевіряє власника. Admin отримує
керування акаунтами та агреговану діаграму тригерів без публікації персональної
календарної історії. Майбутні соціальні зв'язки/скарги зараз не зберігаються.
