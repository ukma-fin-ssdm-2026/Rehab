# Профіль — контракт КТ-А

Цей документ відповідає розділам 5.1, 5.2, 5.3 і 7 погодженого командного ТЗ від 30.10.2026. Описує **підготовлені типи та перевірки**, а не готовий API або завершену КТ-А.

## Власні контракти

- `backend/app/schemas/profile.py`: `ProfileOut`, `ProfileUpdateRequest`, `ProfilePasswordRequest`, `ProfilePreferencesRequest`, `AvatarUploadOut`, `AvatarDataOut`.
- `frontend/src/profile/types.ts`: `ProfileOut`, `ProfileContextValue`, `MessageStyle` і запити/відповіді.
- `frontend/src/api/profile.ts`: клієнт `GET /profile`, `PATCH /profile`, `PUT /profile/password`, `PATCH /profile/preferences` та три avatar-операції через наявний `apiRequest` і JWT.
- `frontend/src/profile/ProfileProvider.tsx`: `profile`, `loading`, `error`, `refreshProfile()`; кеш відокремлено за `user_id`, дані попереднього акаунта не відображаються після зміни користувача. **Не встановлено в кореневий layout**, поки `GET /profile` не працює з реальною БД. Немає підміни даних тестовими production-моками.

Поля `ProfileOut`: `user_id`, `name`, `nickname`, `email`, `has_avatar`, `avatar_version`, `email_reminders_enabled`, `message_style`. Підтримувані стилі: `formal`, `humorous`, `zen`, `strict`. Поки фото відсутнє, клієнтський контракт допускає `avatar_version=null`; із появою фото версія має бути додатним цілим числом. Це узгоджувана деталь відсутнього фото, оскільки у ТЗ зазначено лише наявність поля й версію від 1 для збереженого фото.

Форми редагування приймають тільки `name`/`nickname`, мінімум одне; пробіли по краях видаляються до перевірки 1–100 та 1–50. Параметри `email_reminders_enabled` і `message_style` змінюються лише через preferences, також щонайменше одне поле. Зміна пароля потребує `current_password` та нового `new_password` довжиною 8–128; пароль не обрізається. Відкликання JWT при успіху, а також повернення 400 `CURRENT_PASSWORD_INCORRECT` для невірного поточного пароля має забезпечити реальний серверний маршрут, не схема сама по собі.

## Залежність від спільної міграції

Поліна володіє новими колонками `users.email_reminders_enabled` (false) і `users.message_style` (formal), таблицею `user_avatars` з `BYTEA` і єдиною міграцією після `0001_initial`. До її foundation PR сервер профілю не може достовірно читати/зберігати ці значення. **Тут не змінено ORM, Alembic, `backend/app/main.py`, requirements, frontend root layout або живий профіль.**

Після погодженого foundation PR:

1. Реалізувати `backend/app/routers/profile.py` та `services/profile.py`, перевірити власника через JWT і встановлювати `Cache-Control: no-store` для приватного фото. Пароль хешувати Argon2, при успіху підвищувати `token_version`, не завершуючи сесію при невірному поточному паролі.
2. Зробити вибір фото лише з галереї через `expo-image-picker` для Expo SDK 57. Сервер: Pillow, pillow-heif, EXIF-орієнтація, 512×512, JPEG до 256 KiB, без EXIF/GPS. 5 MiB на файл, до 64 Мпікселів на декодування; виміряти HEIC із iPhone і пам'ять Render Free.
3. Підключити `ProfileProvider` і маршрути `/profile/edit`, `/profile/password`, `/profile/notifications`, `/profile/style`, `/profile/privacy`, `/profile/help` у захищений стек; оновити наявну вкладку профілю. Викликати `AuthProvider.refresh()` після зміни імені/нікнейма. Не створювати фіктивний успіх у production.
4. Зробити локальні тести схем/пароля/аватара/сесій; після інтеграції — справжнє приймання з двома тестовими акаунтами й iPhone Safari.

Тести з цього PR обмежуються схемами та контрактами клієнта. Вони не означають, що endpoint, завантаження HEIC або збереження після перезапуску перевірені.

## Передача іншим модулям

Марія може використовувати `MessageStyle` і `ProfileOut` із `frontend/src/profile/types.ts` замість локального сховища чи власного дубльованого типу. Живий `ProfileProvider` підключатиметься на КТ-Б після готовності backend. Поліна й Софія не повинні змінювати ці файли паралельно. Для нових екранів повідомлень, підопічного та скарг Анастасія на КТ-Б додасть лише реєстрацію приватних маршрутів у root layout.

Ця технічна специфікація є командною, а не незалежно підтвердженою офіційною рубрикою викладача.
