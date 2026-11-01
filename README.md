[![CI Pipeline](https://github.com/ukma-fin-ssdm-2026/Rehab/actions/workflows/ci.yml/badge.svg)](https://github.com/ukma-fin-ssdm-2026/Rehab/actions/workflows/ci.yml)

# Rehab

**[Відкрити онлайн-версію Rehab](https://rehab-web-b9d5.onrender.com)**

**Rehab** — застосунок для відстеження тверезості, аналізу особистого прогресу та підтримки користувачів на шляху до здоровіших звичок.

Мета проєкту — створити зручний та інтуїтивно зрозумілий інструмент, який допомагає користувачам відстежувати дні без вживання алкоголю, вести календар, аналізувати статистику та відстежувати фіксовані етапи тверезості.

Проєкт розробляється командою студенток НаУКМА в межах курсу **«Методи розробки програмних систем» (SSDM 2026)**.

> *Rehab — кожен тверезий день у новий commit.*

## 1. Команда

Над проєктом працюють чотири учасниці, які розподіляють відповідальність за вимоги, архітектуру, реалізацію, тестування, інтеграцію та документацію.

### Розподіл ролей за лабораторними роботами

| Лабораторна | Киричата Анастасія | Мілевська Софія | Морозова Поліна | Колесник Марія |
|---|---|---|---|---|
| **Lab 01** | Repo Maintainer | CI Maintainer | Documentation Lead + Project Brief Lead | Issue Tracker Lead |
| **Lab 02** | Traceability Lead | Requirements Lead + FR Lead | Documentation Lead | Quality Lead |
| **Lab 03** | Requirements-Architecture Mapper | UML Lead | Architecture + Documentation Lead | Data & Threat Modeler |
| **Lab 04** | Quality Lead | Integration Lead | Backend Lead + API Design Lead | Documentation Lead |
| **Lab 05** | Quality Lead + Prototype Lead | Code Reviewer | Documentation Lead | Security Analyst |
| **Lab 06** | Debugging Lead | Testing Strategist | Integration Lead | Testing Lead + Test stand manager |

Командні домовленості, правила співпраці, стандарти кодування, Code Review та Definition of Done описано в [TeamCharter.md](TeamCharter.md).

Історія внесків також доступна через [Pull Requests](https://github.com/ukma-fin-ssdm-2026/Rehab/pulls), [Issues](https://github.com/ukma-fin-ssdm-2026/Rehab/issues) та [історію комітів](https://github.com/ukma-fin-ssdm-2026/Rehab/commits/main).

## 2. Поточний стан проєкту

На поточному етапі Rehab представлений інтегрованим прототипом, який складається із серверної частини **FastAPI** та клієнтського застосунку **React Native / Expo**.

### Основна функціональність

- **Календар тверезості:** створення та перегляд щоденних записів, відображення статусу дня.
- **Деталізація записів:** зазначення статусу тверезості, типів і об'ємів напоїв, тригерів та коментарів.
- **Статистика:** перегляд показників прогресу, сформованих на основі записів користувача.
- **Цілі:** відображення прогресу та етапів досягнення тверезості.
- **Головний екран:** перегляд узагальнених показників користувача.
- **Навігація:** перехід між основними розділами застосунку.

### Інтегровані модулі

Поточне розгортання за звітом Софії від 01.11.2026:

| Сервіс | Коміт | Час Europe/Kyiv |
|---|---|---|
| [Frontend](https://rehab-web-b9d5.onrender.com) | [0ab8f53](https://github.com/ukma-fin-ssdm-2026/Rehab/commit/0ab8f53), PR №224 | 31.10.2026 22:24 |
| [Backend](https://rehab-api-0na0.onrender.com) | [f9110bc](https://github.com/ukma-fin-ssdm-2026/Rehab/commit/f9110bc), PR №225 | 01.11.2026 13:17 |

Frontend після №225 не перезбирався: frontend/ у цьому PR не змінювався. Neon оновлено до 0002_team_foundation 31.10.2026. Джерела, перевірки й непідтверджені сценарії — [інструкція розгортання](docs/deployment/render-neon.md).

Реєстрація й вхід використовують Argon2/JWT; дані зберігаються в PostgreSQL.
Доступні профіль із фото/паролем/налаштуваннями, менторство за постійним кодом,
читання даних підопічного, приватні повідомлення й коментарі підтримки.
Скарги розглядаються в адмінці; схвалення закриває конкретну пару, без глобального
блокування акаунта. Фіксовані етапи: 7/30/90/180/365 днів.

Календар, перерахунок прогресу й перша подія зриву зберігаються разом.
Відсутність запису означає тверезий день. Нагадування створюються після 20:00
Europe/Kyiv; email-копія лише за opt-in. За звітом Софії, Gmail OAuth налаштовано й два технічні листи отримано.
Job на Render, лист саме від job та автоматичний розклад ще не перевірені;
деталі й джерела — в інструкції розгортання.

Сценарії приймання — [тест-план](docs/validation/test-plan.md).
Онлайн-приймання та iPhone перевіряються після узгодженого розгортання.
Інструкція запуску — [setup_and_run.md](setup_and_run.md).

## 3. Технологічний стек та архітектура

| Компонент | Технології |
|---|---|
| Backend | Python, FastAPI, Pydantic |
| Frontend | React Native, Expo, TypeScript |
| API | REST, HTTP, OpenAPI, Swagger UI |
| Зберігання даних | PostgreSQL, SQLAlchemy, Alembic |
| Тестування Backend | pytest |
| Перевірка Frontend | Node tests, TypeScript, ESLint, Expo web export |
| Якість коду | Black, Flake8, статичний аналіз |
| CI/CD | GitHub Actions |
| Документація | Markdown, UML, ADR, OpenAPI |
| UI/UX-дизайн | Figma |

Архітектура Rehab побудована на розділенні клієнтської та серверної частин.

```text
Користувач
    |
    v
Frontend (React Native / Expo)
    |
    | HTTP / REST API
    v
Backend (FastAPI)
    |
    +-- API Routers
    +-- Business Logic / Services
    +-- Data Models
    |
    v
PostgreSQL (Neon онлайн, Docker локально)
```

Frontend відповідає за інтерфейс, навігацію та взаємодію з користувачем.

Backend обробляє HTTP-запити, перевіряє дані, реалізує бізнес-логіку та надає API для роботи з календарем, цілями й статистикою.

Основний FastAPI використовує PostgreSQL. Історичні модулі прототипу не підключені як робоче сховище.

Деталі описані в [High-Level Design](docs/architecture/high-level-design.md).

## 4. Структура репозиторію

Основні каталоги та файли проєкту:

```text
Rehab/
├── .github/
│   └── workflows/
│       ├── ci.yml
│       ├── code-quality.yml
│       ├── dependency-audit.yml
│       ├── docs.yml
│       ├── reminders.yml
│       └── traceability.yml
│
├── backend/
│   └── app/
│       ├── main.py
│       ├── routers/
│       ├── services/
│       ├── models.py
│       └── db/                 # ORM і підключення PostgreSQL
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   └── config/
│   │       └── api.ts
│   ├── package.json
│   └── package-lock.json
│
├── docs/
│   ├── requirements/
│   │   ├── user-stories.md
│   │   ├── requirements.md
│   │   └── rtm.md
│   │
│   ├── architecture/
│   │   ├── decisions/
│   │   ├── uml/
│   │   ├── high-level-design.md
│   │   ├── traceability-matrix.md
│   │   ├── data-model.md
│   │   └── threat-model.md
│   │
│   ├── api/
│   │   ├── api-design.md
│   │   ├── quality-attributes.md
│   │   ├── openapi-generated.yaml
│   │   └── index.html
│   │
│   ├── code-quality/
│   │   ├── progress.md
│   │   ├── static-analysis.md
│   │   └── review-report.md
│   │
│   ├── testing/
│   │   ├── testing-strategy.md
│   │   └── debugging-log.md
│   │
│   └── design/
│       ├── design.md
│       └── overview.png
│
├── Labs/
├── scripts/
│   └── export_openapi.py
├── tests/
├── requirements.txt
├── Project-Description.md
├── TeamCharter.md
├── setup_and_run.md
├── README.md
└── .gitignore
```

Документація організована за окремими напрямами: вимоги, архітектура, API, якість коду та тестування. Такий підхід забезпечує простежуваність між проєктними рішеннями, реалізацією й перевірками.

## 5. Документація лабораторних робіт (Labs 1–6)

У таблиці зібрано основні результати лабораторних робіт і відповідні матеріали репозиторію.

| Лабораторна | Основні артефакти |
|---|---|
| **Lab 01 — Організація команди** | [Team Charter](TeamCharter.md), [README](README.md), [CI Pipeline](.github/workflows/ci.yml) |
| **Lab 02 — Вимоги** | [User Stories](docs/requirements/user-stories.md), [FR/NFR](docs/requirements/requirements.md), [RTM](docs/requirements/rtm.md), [Опис проєкту](Project-Description.md) |
| **Lab 03 — Архітектура** | [HLD](docs/architecture/high-level-design.md), [UML](docs/architecture/uml/), [ADR](docs/architecture/decisions/), [Data Model](docs/architecture/data-model.md), [STRIDE](docs/architecture/threat-model.md), [Architecture Traceability](docs/architecture/traceability-matrix.md) |
| **Lab 04 — API** | [API Design](docs/api/api-design.md), [OpenAPI](docs/api/openapi-generated.yaml), [Quality Attributes](docs/api/quality-attributes.md), [Swagger UI](https://ukma-fin-ssdm-2026.github.io/Rehab/) |
| **Lab 05 — Якість коду** | [Progress Report](docs/code-quality/progress.md), [Static Analysis](docs/code-quality/static-analysis.md), [Code Review](docs/code-quality/review-report.md) |
| **Lab 06 — Тестування та налагодження** | [Testing Strategy](docs/testing/testing-strategy.md), [Debugging Log](docs/testing/debugging-log.md), [Tests](tests/), [CI Results](https://github.com/ukma-fin-ssdm-2026/Rehab/actions/workflows/ci.yml) |

Матеріали лабораторних робіт та посилання на індивідуальні демонстраційні відео розміщуються в каталозі [Labs/](Labs/).

Основні артефакти взаємопов'язані:

**User Stories → FR/NFR → RTM → Architecture → API → Implementation → Tests → CI**

Ця структура дозволяє відстежувати шлях від користувацьких потреб до реалізації та перевірки відповідної функціональності.

## 6. Артефакти вимог (Лабораторна 2)

Документація вимог визначає функціональні можливості Rehab, нефункціональні характеристики системи та критерії прийняття.

### Основні документи

- [User Stories](docs/requirements/user-stories.md) — користувацькі історії, що відображають потреби користувачів і містять критерії прийняття.
- [Requirements](docs/requirements/requirements.md) — функціональні вимоги (FR) та нефункціональні вимоги (NFR), пов'язані з характеристиками якості системи відповідно до ISO/IEC 25010.
- [Requirements Traceability Matrix](docs/requirements/rtm.md) — матриця простежуваності між вимогами та їх перевіркою.
- [Project Description](Project-Description.md) — опис проблеми, мети, концепції, функціональних можливостей та обмежень проєкту.

RTM забезпечує зв'язок між вимогами та відповідними артефактами розробки й тестування.

Це дозволяє оцінювати не лише наявність функціональності, але і її відповідність початковим вимогам.

## 7. Архітектурна документація (Лабораторна 3)

Архітектурна документація описує структуру Rehab, взаємодію компонентів, модель даних і прийняті проєктні рішення.

### Основні документи

- [High-Level Design](docs/architecture/high-level-design.md) — загальна архітектура, компоненти та архітектурний стиль.
- [UML-діаграми](docs/architecture/uml/) — візуальне представлення архітектури й взаємодій.
- [Architecture Decision Records](docs/architecture/decisions/) — архітектурні рішення та їх обґрунтування.
- [Data Model](docs/architecture/data-model.md) — модель предметної області та структура даних.
- [Architecture Traceability Matrix](docs/architecture/traceability-matrix.md) — зв'язок між вимогами й компонентами системи.
- [Threat Model](docs/architecture/threat-model.md) — аналіз загроз за методологією STRIDE та запропоновані контрзаходи.

Документи архітектури пов'язані з вимогами та API, що дозволяє простежити вплив проєктних рішень на реалізацію системи.

## 8. Документація API (Лабораторна 4)

Серверна частина Rehab реалізована на FastAPI та надає REST API для взаємодії з клієнтським застосунком.

Основні групи API охоплюють:

- роботу із записами календаря;
- роботу з цілями користувача;
- отримання статистики.

### Основні документи та ресурси

- [API Design](docs/api/api-design.md) — структура API, маршрути, моделі запитів і відповідей, правила обробки помилок.
- [OpenAPI Specification](docs/api/openapi-generated.yaml) — машинозчитувана специфікація API.
- [Quality Attributes](docs/api/quality-attributes.md) — атрибути якості та їх зв'язок із нефункціональними вимогами.
- [Swagger UI на GitHub Pages](https://ukma-fin-ssdm-2026.github.io/Rehab/) — опублікована API-документація.
- [GitHub Actions — docs.yml](.github/workflows/docs.yml) — workflow генерації та публікації документації.

### Генерація OpenAPI

Специфікація OpenAPI формується автоматично на основі FastAPI за допомогою скрипта [export_openapi.py](scripts/export_openapi.py).

Для локальної генерації з кореня проєкту використовується команда:

```powershell
python scripts/export_openapi.py
```

Після запуску Backend актуальні маршрути API доступні через локальний Swagger UI:

http://127.0.0.1:8000/docs

**Примітка:** GitHub Pages використовується для публікації API-документації та не є окремим публічним розгортанням повного застосунку Rehab.

## 9. Налаштування та локальний запуск

Повна інструкція з налаштування середовища, запуску Backend і Frontend, перевірки API та основних сценаріїв:

**[setup_and_run.md — Налаштування та запуск Rehab](setup_and_run.md)**

Нижче наведено короткий спосіб запуску інтегрованого прототипу на Windows / PowerShell.

### 9.1. Клонування репозиторію

```powershell
git clone https://github.com/ukma-fin-ssdm-2026/Rehab.git
cd Rehab
git switch develop
```

### 9.2. Запуск Backend

Із кореня `Rehab/`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
# Перед запуском налаштувати .env за setup_and_run.md
docker compose up -d postgres-dev
python -m alembic upgrade head
python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

Після успішного запуску доступні:

- **Swagger UI:** http://127.0.0.1:8000/docs
- **OpenAPI JSON:** http://127.0.0.1:8000/openapi.json

### 9.3. Налаштування Frontend

Відкрийте другий термінал і перейдіть до каталогу `frontend/`:

```powershell
cd frontend
npm ci
```

Для локального підключення до Backend можна використовувати файл `frontend/.env.local`:

```dotenv
EXPO_PUBLIC_API_URL=http://127.0.0.1:8000
```

Адреса API використовується відповідно до конфігурації клієнта в `frontend/src/config/api.ts`.

### 9.4. Запуск Expo Web

Із каталогу `frontend/`:

```powershell
npx expo start --web
```

Expo виведе адресу локального застосунку. Зазвичай це:

http://localhost:8081

Для коректної взаємодії між Frontend і Backend обидва процеси мають працювати одночасно.

### 9.5. Перевірка роботи

Основний демонстраційний сценарій охоплює:

1. Відкриття Rehab у браузері.
2. Реєстрацію та вхід у тестовий акаунт.
3. Створення запису в календарі.
4. Перегляд збереженого запису.
5. Перевірку статистики та прогресу цілей.
6. Навігацію між основними екранами.

Для захищених API-запитів використовується справжній JWT після `/api/v1/auth/login`; демонстраційні токени не приймаються.

Детальні запити, приклади JSON, типові проблеми та опис сценаріїв доступні у [setup_and_run.md](setup_and_run.md).

## 10. Якість коду (Лабораторна 5)

У межах Lab 05 команда працювала над якістю програмного коду, автоматизацією перевірок, статичним аналізом і проведенням Code Review.

### Основні артефакти

- [Progress Report](docs/code-quality/progress.md) — історичний звіт Lab 05; чинний стан наведено вище.
- [Static Analysis](docs/code-quality/static-analysis.md) — результати статичного аналізу коду та перевірок безпеки.
- [Code Review](docs/code-quality/review-report.md) — результати огляду коду та рекомендації.
- [Team Charter](TeamCharter.md) — домовленості щодо стандартів розробки, перегляду коду та Definition of Done.

Для автоматизації перевірок використовується GitHub Actions.

[Переглянути CI Pipeline](https://github.com/ukma-fin-ssdm-2026/Rehab/actions/workflows/ci.yml)

## 11. Тестування та налагодження (Лабораторна 6)

Тестування Rehab спрямоване на перевірку коректності бізнес-логіки, API, обробки помилок та взаємодії компонентів.

### Основні артефакти

- [Testing Strategy](docs/testing/testing-strategy.md) — підходи до тестування, використані інструменти, рівні тестів і цілі покриття.
- [Debugging Log](docs/testing/debugging-log.md) — документування процесу виявлення, аналізу та виправлення помилок.
- [Automated Tests](tests/) — автоматизовані тести Backend.
- [CI Pipeline](.github/workflows/ci.yml) — конфігурація автоматичного запуску перевірок.
- [GitHub Actions Results](https://github.com/ukma-fin-ssdm-2026/Rehab/actions/workflows/ci.yml) — результати виконання CI та доступні артефакти тестування.

### Запуск тестів Backend

Із кореня `Rehab/`, після встановлення Python-залежностей:

```powershell
# Спочатку налаштувати окремий TEST_DATABASE_URL за setup_and_run.md
python -m pytest -q
```

### Перевірка Frontend

Із каталогу `frontend/`:

```powershell
npm run test:api
npm run typecheck
npm run lint
npm run export:web
```

Тестова документація описує стратегію перевірок, процес налагодження та взаємозв'язок тестування з вимогами системи.

Актуальні результати автоматизованих перевірок відображаються у GitHub Actions.

## 12. UI/UX-дизайн та документація прототипу

Для Rehab розроблено попередню візуальну концепцію користувацького інтерфейсу у Figma.

### Матеріали дизайну

- [UI/UX Design](docs/design/design.md) — опис концепції, структури інтерфейсу та дизайн-рішень.
- [Design Overview](docs/design/overview.png) — загальний вигляд підготовлених макетів.

Дизайн охоплює основні сценарії взаємодії користувача із застосунком: головний екран, календар, статистику, цілі та профіль.

Макети відображають дизайн-концепцію та можуть мати відмінності від поточної функціональної реалізації.

### Документація інтегрованого прототипу

- [setup_and_run.md](setup_and_run.md) — встановлення залежностей, запуск застосунку та перевірка роботи.
- <!-- AI-GENERATED START -->[docs/deployment/render-neon.md](docs/deployment/render-neon.md) — онлайн-розгортання (Render + Neon): сайт https://rehab-web-b9d5.onrender.com, API https://rehab-api-0na0.onrender.com; порядок підтвердження розгортання — розділ 6. Демоакаунти створює `python -m scripts.seed_demo`, облікові дані передаються викладачу окремо, не в репозиторії. Безкоштовний Render засинає: перше відкриття може тривати до хвилини<!-- AI-GENERATED END -->
- [Labs/](Labs/) — матеріали лабораторних робіт і демонстраційні відео.

## 13. CI/CD та доступні ресурси

У проєкті використовується GitHub Actions для автоматизації тестування, перевірок якості коду та публікації API-документації.

### GitHub Actions

- [CI Pipeline](.github/workflows/ci.yml) — автоматизовані перевірки проєкту.
- [API Documentation Workflow](.github/workflows/docs.yml) — генерація та публікація OpenAPI-документації.

### Корисні посилання

| Ресурс | Посилання |
|---|---|
| Репозиторій Rehab | [GitHub](https://github.com/ukma-fin-ssdm-2026/Rehab) |
| CI Pipeline | [GitHub Actions](https://github.com/ukma-fin-ssdm-2026/Rehab/actions/workflows/ci.yml) |
| API-документація | [Swagger UI](https://ukma-fin-ssdm-2026.github.io/Rehab/) |
| Інструкція запуску | [setup_and_run.md](setup_and_run.md) |
| Командний статут | [TeamCharter.md](TeamCharter.md) |
| Документація проєкту | [docs/](docs/) |
| Матеріали лабораторних | [Labs/](Labs/) |

## 14. Використання ШІ

У процесі розробки Rehab команда використовує інструменти штучного інтелекту як допоміжні засоби для аналізу, вдосконалення та документування окремих частин проєкту.

Під час оновлення цього README **ChatGPT використовувався для структурування матеріалів, покращення формулювань, виявлення застарілих посилань та узгодження опису проєкту з наявною документацією**.

Основою README є матеріали, вимоги, архітектурні рішення та реалізація, створені учасницями команди Rehab. Використання ШІ доповнює роботу команди, але не замінює технічний аналіз, Code Review, тестування та перевірку коректності інформації.

Відповідальність за технічні рішення, перевірку результатів і кінцеву якість документації залишається за командою Rehab.

## Приймання та повний покажчик документації

Офіційні критерії: [проміжне оцінювання](https://ssdm-2026.cs-courses.org/midterm-evaluation.html), [політика ШІ](https://ssdm-2026.cs-courses.org/ai-policy.html). Конкретні зауваження до Rehab: [№216](https://github.com/ukma-fin-ssdm-2026/Rehab/issues/216), [Lab 7 №215](https://github.com/ukma-fin-ssdm-2026/Rehab/issues/215). Посилання є джерелами вимог до оформлення, а не твердженням про вже виставлену фінальну оцінку.

- [Тест-план і статуси кейсів](docs/validation/test-plan.md), [журнал взаємного огляду](docs/validation/review-log.md), [історія валідатора простежуваності](docs/validation/traceability-check.md).
- [Мутаційне тестування](docs/testing/mutation-testing.md), [рекомендації щодо якості тестів](docs/testing/test-quality-recommendations.md).
- [ADR-001](docs/architecture/decisions/ADR-001.md), [ADR-002](docs/architecture/decisions/ADR-002.md), [джерело ER-моделі](docs/architecture/uml/implemented-data-model.puml).
- [Локальна PostgreSQL](docs/development/postgres-local.md), [онлайн-розгортання й Gmail](docs/deployment/render-neon.md).
- Workflows: [CI](.github/workflows/ci.yml), [якість коду](.github/workflows/code-quality.yml), [залежності](.github/workflows/dependency-audit.yml), [API Pages](.github/workflows/docs.yml), [простежуваність](.github/workflows/traceability.yml), [нагадування](.github/workflows/reminders.yml).
- Лабораторні відео: [Lab01](Labs/Lab01/), [Lab02](Labs/Lab02/), [Lab03](Labs/Lab03/), [Lab04](Labs/Lab04/), [Lab05](Labs/Lab05/), [Lab06](Labs/Lab06/), [Lab07](Labs/Lab07/).

Відео Анастасії за Lab02 синхронізоване з уже наявного main (PR №218), без зміни посилання. Для Lab01–06 є файли з посиланнями всіх чотирьох учасниць; наявність файлу не означає перевірку доступності чи перегляд відео. У Lab07 немає файлу Софії, а спільне фінальне демо ще не надане.

Командне фінальне відео 4–5 хвилин ще не надане: після запису потрібне справжнє посилання у Labs/midterm-presentation.txt. Порожній файл або вигадане посилання не створюється. Офіційні критерії допускають робочий публічний deployment замість відео; командний план додатково передбачає спільне демо. Паролі демоакаунтів передаються викладачу окремо.

## Використання ШІ — оновлення документації

Codex (OpenAI) використано для перевірки актуальності тексту, посилань і джерел результатів. Агент прочитав відповідні файли й зауваження викладача, звірив локальні посилання та узгодженість requirements/test-plan/RTM; результати запусків зазначаються окремо з датою. Історичні результати не видаються за нові, людський взаємний огляд та ручне онлайн-приймання цим записом не підтверджуються. Команда переглядає зміни в PR перед злиттям. Джерела правил: [критерії курсу](https://ssdm-2026.cs-courses.org/midterm-evaluation.html), [політика ШІ](https://ssdm-2026.cs-courses.org/ai-policy.html).
