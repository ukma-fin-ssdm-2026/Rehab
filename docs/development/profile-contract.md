# Профіль — контракт КТ-А

Цей документ відповідає розділам 5.1, 5.2, 5.3 і 7 погодженого командного ТЗ від 30.10.2026. Описує **підготовлені типи та перевірки**, а не готовий API або завершену КТ-А.

## Власні контракти

- `backend/app/schemas/profile.py`: `ProfileOut`, `ProfileUpdateRequest`, `ProfilePasswordRequest`, `ProfilePreferencesRequest`, `AvatarUploadOut`, `AvatarDataOut`.
- `frontend/src/profile/types.ts`: `ProfileOut`, `ProfileContextValue`, `MessageStyle` і запити/відповіді.
- `frontend/src/api/profile.ts`: клієнт `GET /profile`, `PATCH /profile`, `PUT /profile/password`, `PATCH /profile/preferences` та три avatar-операції через наявний `apiRequest` і JWT.
- `frontend/src/profile/ProfileProvider.tsx`: `profile`, `loading`, `error`, `refreshProfile()`; кеш відокремлено за `user_id`, дані попереднього акаунта не відображаються після зміни користувача. **Не встановлено в кореневий layout**, поки `GET /profile` не працює з реальною БД. Немає підміни даних тестовими production-моками.
- `backend/app/routers/profile.py`, `backend/app/services/profile.py`: підготовлені захищені маршрути GET/PATCH /profile, PUT /profile/password, PATCH /profile/preferences; редагування змінює лише дозволені поля, невірний пароль повертає 400 без відкликання JWT, успіх змінює Argon2-хеш і token_version.
- `backend/app/services/avatar.py`: підготовлена обробка JPEG/PNG/WebP/HEIC/HEIF із перевіркою 5 MiB/64 Мпікселів і нормалізацією до JPEG ≤256 KiB; робота з BYTEA через UserAvatar після foundation. Піновані залежності Pillow і pillow-heif додані в requirements.txt, потребують review Софії та Linux CI.
- `frontend/src/app/profile/*`: підготовлені форми редагування і пароля, налаштування пошти та стилю, тексти приватності й FAQ. Живий маршрут і провайдер не підключено до кореневого стеку, доки API не інтегровано.

Поля `ProfileOut`: `user_id`, `name`, `nickname`, `email`, `has_avatar`, `avatar_version`, `email_reminders_enabled`, `message_style`. Підтримувані стилі: `formal`, `humorous`, `zen`, `strict`. Поки фото відсутнє, клієнтський контракт допускає `avatar_version=null`; із появою фото версія має бути додатним цілим числом. Це узгоджувана деталь відсутнього фото, оскільки у ТЗ зазначено лише наявність поля й версію від 1 для збереженого фото.

Форми редагування приймають тільки `name`/`nickname`, мінімум одне; пробіли по краях видаляються до перевірки 1–100 та 1–50. Параметри `email_reminders_enabled` і `message_style` змінюються лише через preferences, також щонайменше одне поле. Зміна пароля потребує `current_password` та нового `new_password` довжиною 8–128; пароль не обрізається. Відкликання JWT при успіху, а також повернення 400 `CURRENT_PASSWORD_INCORRECT` для невірного поточного пароля має забезпечити реальний серверний маршрут, не схема сама по собі.

## Залежність від спільної міграції

Поліна володіє новими колонками `users.email_reminders_enabled` (false) і `users.message_style` (formal), таблицею `user_avatars` з `BYTEA` і єдиною міграцією після `0001_initial`. До її foundation PR сервер профілю не може достовірно читати/зберігати ці значення. **Тут не змінено ORM, Alembic, `backend/app/main.py`, frontend root layout або живий профіль.** `requirements.txt` доповнено лише кодеками аватара. Прямі HTTP-маршрути й екрани профілю підготовлені, але не зареєстровані у production.

Після погодженого foundation PR:

1. Після міграції інтегрувати готові `backend/app/routers/profile.py` та `services/profile.py` в основний FastAPI через Софію, перевірити реальну PostgreSQL, `Cache-Control: no-store`, відмову чужому ID й відкликання попередніх JWT. Не позначати готовим до застосування до цього.
2. Встановити `expo-image-picker` **через `npx expo install expo-image-picker` із Expo SDK 57**, комітити згенеровані package.json/package-lock.json разом. Наразі цього пакета немає, тому кнопку галереї не підключено. Після додавання перевірити frontend npm ci/typecheck/export. Серверний код нормалізації вже підготовлено, але виміряти HEIC 24/48 Мпікселів на iPhone і пам'ять Render Free ще потрібно.
3. Підключити `ProfileProvider` і маршрути `/profile/edit`, `/profile/password`, `/profile/notifications`, `/profile/style`, `/profile/privacy`, `/profile/help` у захищений стек; оновити наявну вкладку профілю. Викликати `AuthProvider.refresh()` після зміни імені/нікнейма. Не створювати фіктивний успіх у production.
4. Зробити локальні тести схем/пароля/аватара/сесій; після інтеграції — справжнє приймання з двома тестовими акаунтами й iPhone Safari.

Додано тести схем, базової серверної логіки, HTTP-контракту, перетворення JPEG/PNG/WebP, профільного клієнта й provider. Ізольовано на локальному Pillow перевірено перетворення JPEG/PNG/WebP, відкидання порожніх/пошкоджених/завеликих файлів; цей допоміжний прогін не є повним pytest нового PR. Усі нові pytest/Node-тести на точному HEAD, HEIC/24-МП/48-МП на iPhone, пам'ять Render і збереження після перезапуску **ще не підтверджені**.

## Передача іншим модулям

Марія може використовувати `MessageStyle` і `ProfileOut` із `frontend/src/profile/types.ts` замість локального сховища чи власного дубльованого типу. Живий `ProfileProvider` підключатиметься на КТ-Б після готовності backend. Поліна й Софія не повинні змінювати ці файли паралельно. Для нових екранів повідомлень, підопічного та скарг Анастасія на КТ-Б додасть лише реєстрацію приватних маршрутів у root layout.

Ця технічна специфікація є командною, а не незалежно підтвердженою офіційною рубрикою викладача.
