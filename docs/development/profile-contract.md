# Профіль — контракт КТ-А

Цей документ відповідає розділам 5.1, 5.2, 5.3 і 7 погодженого командного ТЗ від 30.10.2026. Профільні модулі підготовлені в незлитому PR №212; foundation PR №213 уже злитий у `develop`, але повні інтеграційні перевірки ще не завершені.

## Власні контракти

- `backend/app/schemas/profile.py`: `ProfileOut`, `ProfileUpdateRequest`, `ProfilePasswordRequest`, `ProfilePreferencesRequest`, `AvatarUploadOut`, `AvatarDataOut`.
- `frontend/src/profile/types.ts`: `ProfileOut`, `ProfileContextValue`, `MessageStyle` і запити/відповіді.
- `frontend/src/api/profile.ts`: клієнт `GET /profile`, `PATCH /profile`, `PUT /profile/password`, `PATCH /profile/preferences` та три avatar-операції через наявний `apiRequest` і JWT.
- `frontend/src/profile/ProfileProvider.tsx`: `profile`, `loading`, `error`, `refreshProfile()`; кеш відокремлено за `user_id`, дані попереднього акаунта не відображаються після зміни користувача. **Встановлено у кореневий layout лише в незлитій feature-гілці**. До злиття №213 та реєстрації API Софією цю гілку не переносити в production. Немає підміни даних тестовими production-моками.
- `backend/app/routers/profile.py`, `backend/app/services/profile.py`: підготовлені захищені маршрути GET/PATCH /profile, PUT /profile/password, PATCH /profile/preferences; редагування змінює лише дозволені поля, невірний пароль повертає 400 без відкликання JWT, успіх змінює Argon2-хеш і token_version.
- `backend/app/services/avatar.py`: підготовлена обробка JPEG/PNG/WebP/HEIC/HEIF із перевіркою 5 MiB/64 Мпікселів і нормалізацією до JPEG ≤256 KiB; робота з BYTEA через UserAvatar після foundation. Піновані залежності Pillow і pillow-heif додані в requirements.txt, потребують review Софії та Linux CI.
- `frontend/src/app/profile/*`: підготовлені форми редагування і пароля, налаштування пошти та стилю, тексти приватності й FAQ. Маршрути й provider уже підключено в незлитій гілці; у `develop` та на публічному сервері цих змін немає.

Поля `ProfileOut`: `user_id`, `name`, `nickname`, `email`, `has_avatar`, `avatar_version`, `email_reminders_enabled`, `message_style`. Підтримувані стилі: `formal`, `humorous`, `zen`, `strict`. Поки фото відсутнє, клієнтський контракт допускає `avatar_version=null`; із появою фото версія має бути додатним цілим числом. Це узгоджувана деталь відсутнього фото, оскільки у ТЗ зазначено лише наявність поля й версію від 1 для збереженого фото.

Форми редагування приймають тільки `name`/`nickname`, мінімум одне; пробіли по краях видаляються до перевірки 1–100 та 1–50. Параметри `email_reminders_enabled` і `message_style` змінюються лише через preferences, також щонайменше одне поле. Зміна пароля потребує `current_password` та нового `new_password` довжиною 8–128; пароль не обрізається. Відкликання JWT при успіху, а також повернення 400 `CURRENT_PASSWORD_INCORRECT` для невірного поточного пароля має забезпечити реальний серверний маршрут, не схема сама по собі.

## Залежність від спільної міграції

Поліна реалізувала колонки `users.email_reminders_enabled` (false) і `users.message_style` (formal), таблицю `user_avatars` з `BYTEA` та міграцію `0002_team_foundation` у PR №213; зміни вже у `develop`. У `feat/profile` спільну основу інтегровано окремим merge-комітом «Оновлення спільної основи». Для робочого API ще потрібні реєстрація router Софією та тестова PostgreSQL з застосованою міграцією. **Тут не змінено ORM, Alembic або `backend/app/main.py`. `frontend/src/app/_layout.tsx` і вкладку профілю змінено лише у незлитому PR.** `requirements.txt` доповнено лише кодеками аватара. Прямі HTTP-маршрути й екрани профілю підготовлені, але не зареєстровані у production.

Після погодженого foundation PR:

1. Після міграції інтегрувати готові `backend/app/routers/profile.py` та `services/profile.py` в основний FastAPI через Софію, перевірити реальну PostgreSQL, `Cache-Control: no-store`, відмову чужому ID й відкликання попередніх JWT. Не позначати готовим до застосування до цього.
2. `expo-image-picker` встановлено користувачкою штатною командою для Expo SDK 57 і закомічено разом із `package-lock.json` як «додала image picker». У `frontend/src/profile/avatarPicker.ts` реалізовано вибір із галереї, MIME/ліміт 5 МіБ і передачу бінарного тіла. У вкладці профілю додані попередній перегляд, явне збереження й скасування вибору. Є 6 нових Node-тестів цього процесу; їхній прогін на поточному HEAD ще потрібно підтвердити. На iPhone перевірити native file URI, HEIC 24/48 Мпікселів і пам'ять Render Free.
3. Після погодження основи перевірити вже підключені в `feat/profile` `ProfileProvider`, захищені маршрути `/profile/edit`, `/profile/password`, `/profile/notifications`, `/profile/style`, `/profile/privacy`, `/profile/help` та оновлену вкладку. `AuthProvider.refresh()` викликається після редагування імені/нікнейма. Не зливати до готовності API, не створювати фіктивний успіх.
4. Зробити локальні тести схем/пароля/аватара/сесій; після інтеграції — справжнє приймання з двома тестовими акаунтами й iPhone Safari.

Додано тести схем, базової серверної логіки, HTTP-контракту, перетворення JPEG/PNG/WebP, профільного клієнта, provider і галереї. Ізольовано на локальному Pillow перевірено перетворення JPEG/PNG/WebP, відкидання порожніх/пошкоджених/завеликих файлів; цей допоміжний прогін не є повним pytest нового PR. **Фактично перевірено точні Git-блоби**: `tests/test_profile_contract.py` із `backend/app/schemas/profile.py` — 33/33 pytest; `frontend/tests/profile-client.test.cjs` із `frontend/src/api/profile.ts` — 6/6 Node. Це ізольовані прогони, не весь репозиторій. Решта нових pytest/Node-тестів, HEIC 24/48 Мпікселів на iPhone, пам'ять Render і збереження після перезапуску **ще не підтверджені**.

## Передача іншим модулям

Марія може використовувати `MessageStyle` і `ProfileOut` із `frontend/src/profile/types.ts` замість локального сховища чи власного дубльованого типу. `ProfileProvider` уже підключено у незлитій `feat/profile`; фактичне використання в `develop` можливе тільки після КТ-А, підключення серверного profile router і зелених перевірок. Поліна й Софія не повинні змінювати ці файли паралельно. Для нових екранів повідомлень, підопічного та скарг Анастасія на КТ-Б додасть лише реєстрацію приватних маршрутів у root layout.

Ця технічна специфікація є командною, а не незалежно підтвердженою офіційною рубрикою викладача.
