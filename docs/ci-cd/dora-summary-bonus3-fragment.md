# Блок для кінця командного dora-summary.md

Це доповнення для відповідальної за документацію; решту командного звіту воно не замінює.

## Бонуси

### Бонус №3 — швидкий і повільний набори тестів

У [PR #271](https://github.com/ukma-fin-ssdm-2026/Rehab/pull/271) 538 backend-тестів розділено на 88 модульних fast і 450 slow, включно зі справжніми PostgreSQL integration-тестами. Нові тестові файли автоматично входять у slow; склад наборів не перетинається і не втрачає жодного із чинних 538 тестів. Усі 129 frontend unit-тестів збережені.

| Успішний запуск | Backend fast | Backend slow | Frontend fast | БД |
| --- | --- | --- | --- | --- |
| [PR #44320372628](https://github.com/ukma-fin-ssdm-2026/Rehab/actions/runs/44320372628) | 88 passed / 3 с | skipped | 129 passed / 7 с | без service/міграцій |
| [main #44322487244](https://github.com/ukma-fin-ssdm-2026/Rehab/actions/runs/44322487244) | 88 passed / 3 с | 450 passed / 66 с | 129 passed / 7 с | PostgreSQL 16, міграції success |

Час — тривалість відповідного job step за GitHub API. На PR виконується лише fast-набір; на main — обидва. Два обов'язкові jobs залишаються справжніми checks із тими самими назвами, але виконуються послідовно: одночасно в CI Pipeline зайнято не більше одного раннера. Main coverage поєднано через --cov-append, підсумок 94%.

Приклад фактичної інтеграції: `tests.test_auth_postgres::test_duplicate_email_is_rejected_by_real_database` у main slow.xml перевіряє повторний email через HTTP TestClient і SQL count на реальному disposable PostgreSQL. Код застосунку й тести не переписано, захист main не змінено.

Постійні докази: [звірка JSON](./evidence/bonus3/verification.json), [PR metadata](./evidence/bonus3/pr/run-metadata.json), [main metadata](./evidence/bonus3/main/run-metadata.json), оригінальні JUnit XML у evidence/bonus3/pr та evidence/bonus3/main. Подробиці, джерела й часові межі: [bonus-test-tiers.md](./bonus-test-tiers.md).

Технічну частину виконано. Для зарахування хоча б один учасник має пояснити цей бонус у Loom; фактичне посилання додається після запису. Прискорення всього workflow окремо не заявляється, а інтеграційні дефекти тепер можуть виявлятися після злиття.

Codex використано для форматування й упорядкування наданих даних та технічної підготовки погодженої конфігурації, селектора й перевірок за завданням користувачки.
