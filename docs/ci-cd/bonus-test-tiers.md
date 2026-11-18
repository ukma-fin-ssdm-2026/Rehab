# Lab10 — бонус №3: швидкий і повільний набори

## Принцип поділу

Швидкий backend-набір містить вісім перевірених модульних файлів з [manifest](../../tests/test-tiers.json): перевірки схем, форматування, підсумків напоїв, прогресу цілей, тверезих днів і стану прототипних даних. Вони не потребують БД. Повільний набір — усі решта pytest-файлів у tests та підкаталогах, у тому числі reliability й інтеграційні перевірки зі справжнім PostgreSQL.

Нові тестові файли автоматично потрапляють у slow. [Селектор](../../scripts/test_tiers.py) читає налаштування testpaths/python_files/norecursedirs проєкту, перевіряє manifest і не дозволяє втратити файл через застарілий чи небезпечний шлях. Для поточного discovery виконано незалежне порівняння справжніх pytest node IDs: 88 fast + 450 slow = 538 усіх backend-тестів, перетин порожній.

## Поведінка CI

| Подія | Backend fast | PostgreSQL / міграції | Backend slow | Frontend unit tests |
| --- | --- | --- | --- | --- |
| Pull request | так | ні | ні | усі 129 |
| Push у main | так | так | так | усі 129 |
| Інші вже налаштовані push-гілки | так | ні | ні | усі 129 |

[CI Pipeline](../../.github/workflows/ci.yml) зберігає обов'язкові назви Backend tests and coverage та Frontend lint, types and web export. Frontend job має needs: backend-tests та if: !cancelled(), тому в межах цього workflow одночасно зайнято не більше одного раннера. Після backend-падіння frontend все одно звітує, а окрема обов'язкова backend-перевірка блокує merge; скасований workflow не продовжується. Інші існуючі workflow та захист main не змінено; нових workflow, schedule або matrix немає.

На PR образ PostgreSQL порожній і контейнер не стартує, а міграції/slow step пропущені. Fast виконується з недоступною localhost-адресою БД: випадкова залежність від реальної БД спричинить падіння, а не непомітне використання service. На main fast і slow виконуються послідовно в одному backend job; slow отримує реальний dynamic port disposable PostgreSQL service після міграцій.

Coverage на PR стосується лише fast. На main slow додає дані через --cov-append, тому HTML-артефакт backend-coverage-report охоплює обидва набори. Окремий повтор tests/reliability прибрано: ці 30 тестів уже входять у slow, їх не вилучено. Наявні frontend lint, typecheck і web export залишаються.

## Локальна перевірка

- Дев'ять контрактних перевірок селектора та узгодженості dependency locks: поділ і нові файли, вкладені тести, обидва pytest-шаблони назв, виключені каталоги, дублікати, відсутні/небезпечні шляхи та зміна testpaths.
- Справжній fast-прогін без PostgreSQL: 88 passed in 0.59s. Тимчасове Windows-середовище створено окремо; Linux-only uvloop виключено лише з локальної перевірочної копії requirements, залежності проєкту не змінено.
- Справжній collection: all=538, fast=88, slow=450, об'єднання точно дорівнює повному набору, перетину немає.
- actionlint v1.7.12 перевірив синтаксис та вирази CI.

Команди з кореня після встановлення залежностей:

```bash
python -m unittest discover -s scripts -p test_test_tiers.py -v
python scripts/test_tiers.py fast -- -q
python scripts/test_tiers.py slow -- -q
```

Остання команда потребує disposable PostgreSQL та міграцій; локальний slow-прогін без БД тут не заявляється. Для встановлення в Linux CI використано ті самі 52 точні версії з requirements-ci-hashes.lock і --require-hashes. Перед встановленням --check-locks порівнює точні pins із основним requirements.lock: зміна версії, додавання чи вилучення пакета без оновлення hashed lock зупиняє CI, а не перевіряє застарілі залежності. При оновленні залежностей потрібно синхронізувати обидва locks і SHA256 відповідних wheel-файлів; основний requirements.lock лишається джерелом версій.

## Фактичні CI-докази

[PR #271](https://github.com/ukma-fin-ssdm-2026/Rehab/pull/271) злитий після семи зелених checks і Approve від Sof222. Є два справжні успішні запуски:

| Запуск | SHA | Backend fast | Backend slow | Frontend fast | PostgreSQL / міграції |
| --- | --- | --- | --- | --- | --- |
| [PR #44320372628](https://github.com/ukma-fin-ssdm-2026/Rehab/actions/runs/44320372628) | 88e38e6 | 88 passed, 3 с | skipped | 129 passed, 7 с | не запускалися |
| [main #44322487244](https://github.com/ukma-fin-ssdm-2026/Rehab/actions/runs/44322487244) | b6a8bf8 | 88 passed, 3 с | 450 passed, 66 с | 129 passed, 7 с | успішно |

Тривалості в таблиці — різниця started_at/completed_at відповідних GitHub job steps, з точністю API до секунди; вони включають запуск pytest/Node та формування звіту. JUnit suite time для backend становить 0,961 с на PR; на main — 1,051 с для fast і 64,953 с для slow. Це різні межі вимірювання, тому числа не підміняються одне одним.

У PR backend job немає Initialize containers; міграції та slow явно skipped, backend artifact містить fast.xml без slow.xml. На main є Initialize containers і реальне завантаження postgres:16; міграції та slow success. В обох запусках завершення backend передує початку frontend — послідовність підтверджена API, не лише конфігурацією needs.

Усі 88 + 450 backend cases на main успішні, їхній перетин порожній, об'єднання точно дорівнює 538 ідентичностям попереднього повного прогону. Усі fast cases на PR і main збігаються; 129 frontend cases також збігаються. Помилок/падінь/пропущених випадків немає. У підсумковому main coverage після --cov-append — 2040 statements, 124 missed, **94%**; fast-only PR coverage не видається за повне.

### Конкретний integration testcase

У main slow.xml пройшов `tests.test_auth_postgres::test_duplicate_email_is_rejected_by_real_database`. [Тест у перевіреному коміті](https://github.com/ukma-fin-ssdm-2026/Rehab/blob/b6a8bf84badafd2e97b5e11f9d8c196681bc843f/tests/test_auth_postgres.py) робить повторну реєстрацію через TestClient, очікує HTTP409 і перевіряє кількість User через справжню SQLAlchemy-сесію. [Fixtures](https://github.com/ukma-fin-ssdm-2026/Rehab/blob/b6a8bf84badafd2e97b5e11f9d8c196681bc843f/tests/conftest.py) створюють PostgreSQL engine, застосовують Alembic та працюють із disposable rehab_test. Це інтеграція з реальною БД, а не mock або заявлений production-тест.

### Постійні докази

- [Машиночитна звірка](./evidence/bonus3/verification.json): counts, точні часові межі, ідентичності, відсутність перетину та SHA256 кожного XML.
- [PR metadata](./evidence/bonus3/pr/run-metadata.json), [PR backend XML](./evidence/bonus3/pr/backend-fast.xml), [PR frontend XML](./evidence/bonus3/pr/frontend-fast.xml), [цілісність PR ZIP](./evidence/bonus3/pr/artifact-integrity.json).
- [Main metadata](./evidence/bonus3/main/run-metadata.json), [main fast XML](./evidence/bonus3/main/backend-fast.xml), [main slow XML](./evidence/bonus3/main/backend-slow.xml), [main frontend XML](./evidence/bonus3/main/frontend-fast.xml), [цілісність main ZIP](./evidence/bonus3/main/artifact-integrity.json).
- [Витяг main-логу](./evidence/bonus3/main/backend-log-excerpt.txt): postgres:16, 88/450 passed, --cov-append, підсумкові 94%.
- Папки pr/main містять фактичні fast-files.txt і slow-files.txt; їхня однаковість між запусками перевірена. Оригінальні ZIP завантажено через GitHub artifact API й SHA256 порівняно з digest GitHub до розпакування. Постійні XML/JSON у репозиторії не залежать від строку зберігання Actions artifacts.

Технічну частину бонусу №3 виконано. Готовий [блок](./dora-summary-bonus3-fragment.md) потрібно інтегрувати в кінець командного dora-summary.md; хоча б один учасник команди має пояснити бонус у Loom. Без відеопояснення зарахування ще не підтверджується.

Поділ не доводить прискорення всього workflow: встановлення залежностей, збірка та послідовні jobs також займають час. Інтеграційний дефект може бути знайдений уже після злиття в main — це передбачений умовами бонусу компроміс.

## Використання Codex

Codex використано для форматування та впорядкування даних, доступ до яких надано користувачкою, і технічної підготовки погодженої конфігурації, селектора та перевірок за визначеними нею завданням, межами роботи й критеріями.
