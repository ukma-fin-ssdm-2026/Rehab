# Менторство: передача модуля для спільної інтеграції

## Що реалізовано

Модуль Поліни після foundation №213: справжні SQL/JWT API менторства,
читання календаря/статистики підопічного, вкладка підтримки й захищений
екран підопічного. Нових таблиць або міграцій немає; потрібна вже погоджена
`0002_team_foundation`. Neon цією зміною не оновлюється.

У КТ-Б router зареєстрований у спільному `main.py` разом із профілем,
повідомленнями, скаргами та job. Немає заглушок або фіктивного успіху.

## Софії: підключення API

У `backend/app/main.py` вже підключено:

```python
from backend.app.routers import mentorship
app.include_router(mentorship.router, prefix=API_PREFIX)
```

Після підключення всіх модулів експортувати спільний OpenAPI штатним
`scripts/export_openapi.py`. Специфікація генерується з інтегрованого app.

Усі маршрути мають префікс `/api/v1/mentorships`, справжній Bearer JWT
і допускають звичайні акаунти user/legacy mentor, але не admin:

| Метод/шлях | Результат |
| --- | --- |
| GET /code | Тільки власний постійний код |
| GET /my-mentor | `{item: RelationshipOut або null}` |
| GET /my-mentees?limit=30&offset=0 | items,total,limit,offset; тільки active |
| POST / | `{code}`; 201 новий зв'язок, 200 та сама вже активна пара |
| GET /{id} | Історичний/активний зв'язок тільки для його учасника |
| DELETE /{id} | 204, повтор безпечний, причина визначається стороною |
| GET /{id}/calendar/entries | from/to/limit/offset як у власному календарі |
| GET /{id}/calendar/entries/{record_id} | Тільки запис цього підопічного |
| GET /{id}/statistics?period=all | all/week/month/year, чинний StatisticsOut |

Невідомий код → 404 INVALID_MENTOR_CODE, неправильний формат → 422,
власний код → 422 SELF_MENTORSHIP_NOT_ALLOWED. Чужий активний ментор →
409 MENTEE_ALREADY_HAS_MENTOR. Завершена така сама пара →
403 MENTORSHIP_REJOIN_FORBIDDEN. Чужий зв'язок/запис → 404.
Перегляд власного колишнього підопічного → 403 MENTORSHIP_INACTIVE.

Приєднання не змінює users.role. Ментор може мати кількох підопічних
і сам бути підопічним. Завершення остаточне тільки для конкретного
напрямку пари. Чужого write API немає; GET статистики не змінює навіть
best_streak підопічного. Контакти в DTO: user_id,nickname,email.

## Марії: транзакції та подія зриву

Використовувати вже спільні require_active_mentor та функції завершення.
Для writer порядок: users підопічного → mentorships → запис/повідомлення.
Рядок users блокується FOR NO KEY UPDATE: це серіалізує операції над
підопічним, але не блокує FK KEY SHARE інших користувачів при взаємному
менторстві. Не замінювати його на FOR UPDATE у нових багатокористувацьких
операціях: тест двох одночасних зворотних приєднань відтворює deadlock.
Рядок mentorships після цього блокується FOR UPDATE.

Сервіси не роблять commit. Router фіксує успішний POST/DELETE;
читання перевіряє active під блокуванням і не змінює дані підопічного.
Календар після flush і recompute_progress викликає emit_relapse_once перед
commit у тій самій Session. Подія, запис і прогрес відкочуються разом.
users блокуються FOR NO KEY UPDATE також у job нагадувань.

## Анастасії: маршрути та профіль

У root layout уже додано `<Stack.Screen name="mentee" />` та messages
до захищеного user-стека. Папка `app/mentee` вже має власний
guard для прямого URL, відновлення сесії, guest/admin/onboarding;
цей guard зберігається й після root-реєстрації.

Канонічний екран: `/mentee/[relationship_id]`. Він читає весь період
відстеження, має календар/деталі/періоди статистики, жодного редагування.
Запити скасовуються при виході/зміні маршруту; попередні приватні дані
не записуються у browser storage, приховуються при новому завантаженні
та помилці доступу. На відкритому екрані є оновлення раз на 60 секунд
і при поверненні вкладки у видимий стан. Це не WebSocket/push-відкликання
вже показаної інформації; кожний новий захищений запит перевіряє БД.

`frontend/src/api/mentorship.ts` експортує getMyMentorCode,getMyMentor,
getMyMentees,joinMentorship,endMentorship,getMentorship,getMenteeEntries,
getMenteeEntry,getMenteeStatistics. Не дублювати Bearer-логіку.

## Підключення стилю й скарги

`SupportPanel` отримує message_style із useProfile(), а onReport веде
на `/support/report` із relationship_id. Із повідомлення передаємо
relationship_id + notification_id; форма читає лише власне notification
та бере support_comment_id із відповіді сервера. Невдале завантаження доказу
блокує надсилання, зміна акаунта скидає стан форми.

Підтвердження завершення — модальне вікно з конкретним username,
попередженням про остаточність, підтвердженням і скасуванням. Лише
підтвердження робить DELETE. Копіювання коду має ручний fallback.

## Перевірка без зміни спільних entrypoint

```powershell
python -m pytest tests/test_mentorship_api.py -q
```

Тести монтують справжній router до ізольованого test-app, використовують
PostgreSQL та JWT. Для локального UI використовується штатний `backend.app.main:app`,
без додаткового include_router чи preview-adapter. DATABASE_URL має вказувати
на локальну dev-БД із 0002; JWT_SECRET налаштований.

Онлайн-приймання з Render/Neon та Safari/iPhone залишається окремою
спільною перевіркою після міграції й реєстрації router/provider/форми.
