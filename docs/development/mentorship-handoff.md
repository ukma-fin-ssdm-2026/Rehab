# Менторство: передача модуля для спільної інтеграції

## Що реалізовано

Модуль Поліни після foundation №213: справжні SQL/JWT API менторства,
читання календаря/статистики підопічного, вкладка підтримки й захищений
екран підопічного. Нових таблиць або міграцій немає; потрібна вже погоджена
`0002_team_foundation`. Neon цією зміною не оновлюється.

Новий router навмисно не реєструється в чужому `main.py` до узгодженої
інтеграції. Немає заглушок повідомлень/скарг або фіктивного успіху.

## Софії: підключення API

У `backend/app/main.py` під час інтеграції додати:

```python
from backend.app.routers import mentorship
app.include_router(mentorship.router, prefix=API_PREFIX)
```

Після підключення всіх модулів експортувати спільний OpenAPI штатним
`scripts/export_openapi.py`. У поточному спільному main нові маршрути ще
не з'являться лише від існування файлу router.

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
Функція emit_relapse_once та її підключення до календаря залишаються
на спільну інтеграцію з готовим модулем повідомлень. Цей PR не пропускає
події через production-заглушку й не оголошує їх реалізованими.

## Анастасії: маршрути та профіль

Додати `<Stack.Screen name="mentee" />` до чинного захищеного user-стека
в root layout під час об'єднання змін. Папка `app/mentee` вже має власний
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

`SupportPanel` приймає messageStyle і необов'язковий onReport(id).
До злиття ProfileProvider екран використовує formal; до наявності
справжньої форми скарги кнопка скарги не показується, зламаного URL немає.
На інтеграції замінити wrapper friends-support.tsx на підключення
ProfileProvider та callback до `/support/report` із relationship_id.
Власну форму скарги або другий profile provider тут не реалізовувати.

Підтвердження завершення — модальне вікно з конкретним username,
попередженням про остаточність, підтвердженням і скасуванням. Лише
підтвердження робить DELETE. Копіювання коду має ручний fallback.

## Перевірка без зміни спільних entrypoint

```powershell
python -m pytest tests/test_mentorship_api.py -q
```

Тести монтують справжній router до ізольованого test-app, використовують
PostgreSQL та JWT. Для локального UI-preview можна тимчасово підключити
цей самий router у пам'яті, не редагуючи чужий main.py:

```powershell
python -c "from dotenv import load_dotenv; load_dotenv('.env'); from backend.app.main import app; from backend.app.routers.mentorship import router; app.include_router(router,prefix='/api/v1'); import uvicorn; uvicorn.run(app,host='127.0.0.1',port=8000)"
```

DATABASE_URL має вказувати на локальну dev-БД із застосованою 0002,
JWT_SECRET — налаштований; frontend API URL відповідає цьому серверу.
Не використовувати таку перевірку проти Neon або з реальними чужими даними.

Онлайн-приймання з Render/Neon та Safari/iPhone залишається окремою
спільною перевіркою після міграції й реєстрації router/provider/форми.
