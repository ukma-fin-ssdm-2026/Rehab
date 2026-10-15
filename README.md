[![CI Pipeline](https://github.com/ukma-fin-ssdm-2026/Rehab/actions/workflows/ci.yml/badge.svg)](https://github.com/ukma-fin-ssdm-2026/Rehab/actions/workflows/ci.yml)

# Rehab

Наш застосунок **_Rehab_** - це дуже зручний, інтуїтивно зрозумілий та ходовий застосунок для відстежування днів тверезості

Він допомагає відмічати дні без вживання, дивитися статистику, ставити цілі та звичайно отримувати допомогу у разі потреби

> _Rehab - кожен тверезий день у новий commit_

## Команда

| **Учасник**          | **Роль Лаб1**                           | **Роль Лаб2**               | **Роль Лаб3**                     | **Роль Лаб4**      | **Роль Лаб5**          |
| -------------------- | --------------------------------------- | --------------------------- | --------------------------------- | ------------------ | ---------------------- |
| _Киричата Анастасія_ | Repo Maintainer                         | Traceability Lead           | Requirements-Architecture Mapper  | Quality Lead       | Quality Lead           |
| _Мілевська Софія_    | CI Maintainer                           | Requirements Lead + FR Lead | UML Lead                          | Integration Lead   | Code Reviewer          |
| _Морозова Поліна_    | Documentation Lead + Project Brief Lead | Documentation Lead          | Architecture + Documentation Lead | Backend Lead       | Documentation Lead     |
| _Колесник Марія_     | Issue Tracker Lead                      | Quality Lead                | Data & Threat Modeler             | Documentation Lead | Security Analyst       |

## Структура репозиторію

<pre>
project-root/
├── .github/
│   └── workflows/
│       ├── <a href=".github/workflows/ci.yml">ci.yml</a>                  # CI (перевірка)
│       └── <a href=".github/workflows/docs.yml">docs.yml</a>              # Публікація API-документації
├── <a href="Lab01/">Lab01/</a>
├── <a href="Lab02/">Lab02/</a>
├── <a href="Lab03/">Lab03/</a>
├── <a href="Lab04/">Lab04/</a>
├── <a href="Lab05/">Lab05/</a>
├── docs/
│   ├── <a href="docs/requirements/">requirements/</a>               # Документація вимог 
│   │   ├── <a href="docs/requirements/requirements.md">requirements.md</a>
│   │   ├── <a href="docs/requirements/user-stories.md">user-stories.md</a>
│   │   └── <a href="docs/requirements/rtm.md">rtm.md</a>
│   ├── <a href="docs/architecture/">architecture/</a>               # Архітектура
│   │   ├── <a href="docs/architecture/decisions/">decisions/</a>
│   │   ├── <a href="docs/architecture/uml/">uml/</a>                    
│   │   ├── <a href="docs/architecture/high-level-design.md">high-level-design.md</a>
│   │   ├── <a href="docs/architecture/traceability-matrix.md">traceability-matrix.md</a>
│   │   ├── <a href="docs/architecture/data-model.md">data-model.md</a>
│   │   └── <a href="docs/architecture/threat-model.md">threat-model.md</a>
│   ├── <a href="docs/api/">api/</a>                         # Документація API
│   │   ├── <a href="docs/api/api-design.md">api-design.md</a>               # Проєктні рішення API
│   │   ├── <a href="docs/api/quality-attributes.md">quality-attributes.md</a>       # Атрибути якості
│   │   ├── <a href="docs/api/openapi-generated.yaml">openapi-generated.yaml</a>      # Специфікація OpenAPI (автогенерація)
│   │   └── <a href="docs/api/index.html">index.html</a>                   # Swagger UI
│   ├── <a href="docs/code-quality/">code-quality/</a>                # Документація якості коду (Lab 05)
│   │   ├── <a href="docs/code-quality/progress.md">progress.md</a>               # Звіт Lab 05
│   │   ├── <a href="docs/code-quality/static-analysis.md">static-analysis.md</a>      # Статичний аналіз
│   │   └── <a href="docs/code-quality/review-report.md">review-report.md</a>        # Code Review
│   └── <a href="docs/design/">design/</a>                     # Попередній UI/UX-дизайн
│       ├── <a href="docs/design/design.md">design.md</a>                   # Опис дизайну та Figma
│       └── <a href="docs/design/overview.png">overview.png</a>                # Загальний вигляд макетів

├── <a href="scripts/">scripts/</a>                        # Скрипт генерації OpenAPI
├── <a href="src/">src/</a>
├── <a href="tests/">tests/</a>                          # Тести
├── <a href="Project-Description.md">Project-Description.md</a>          # Детальний опис проєкту
├── <a href="README.md">README.md</a>                       # Головний опис проєкту
├── <a href="PROGRESS.md">PROGRESS.md</a>                     # Прогрес розробки прототипу
├── <a href="SETUP_AND_RUN.md">SETUP_AND_RUN.md</a>                # Інструкція з налаштування та запуску
├── <a href="TeamCharter.md">TeamCharter.md</a>                  # Командний статут
└── <a href=".gitignore">.gitignore</a>
</pre>

## Артефакти вимог (Лабораторна 2)

<pre>
<a href="docs/requirements/">requirements/</a>
├── <a href="docs/requirements/user-stories.md">user-stories.md</a>         # Користувацькі історії (User Stories)
├── <a href="docs/requirements/requirements.md">requirements.md</a>         # Вимоги до системи (FR та NFR)
└── <a href="docs/requirements/rtm.md">rtm.md</a>                  # Матриця простежуваності вимог (RTM)
</pre>

## Архітектурна документація (Лабораторна 3)

<pre>
<a href="docs/architecture/">architecture/</a>
├── <a href="docs/architecture/decisions/">decisions/</a>              # Архітектурні рішення (ADR)
├── <a href="docs/architecture/uml/">uml/</a>                    # Діаграми
├── <a href="docs/architecture/high-level-design.md">high-level-design.md</a>    # Високорівневий дизайн (HLD)
├── <a href="docs/architecture/traceability-matrix.md">traceability-matrix.md</a>  # Матриця простежуваності архітектури
├── <a href="docs/architecture/data-model.md">data-model.md</a>           # Модель даних (ER)
└── <a href="docs/architecture/threat-model.md">threat-model.md</a>         # Моделювання загроз (STRIDE)
</pre>

## Документація API (Лабораторна 4)
- [Swagger UI на GitHub Pages](https://ukma-fin-ssdm-2026.github.io/Rehab/)
- [Специфікація OpenAPI (генерується з коду)](docs/api/openapi-generated.yaml)
- [Проєктні рішення API](docs/api/api-design.md)
- [Атрибути якості API](docs/api/quality-attributes.md)

Специфікація не пишеться вручну: workflow [`docs.yml`](.github/workflows/docs.yml) на кожен push у `main` генерує її скриптом [`scripts/export_openapi.py`](scripts/export_openapi.py) з анотацій у `src/api/` і публікує на GitHub Pages.

## Запуск API
Наведені нижче команди стосуються базової реалізації API в `src/api/`. Для запуску інтегрованого прототипу з окремими `backend/` і `frontend/` використовуйте [інструкцію з налаштування та запуску](SETUP_AND_RUN.md).

Для запуску серверної частини Rehab потрібен Python 3.10 або новіший.

1. Клонувати репозиторій і перейти в кореневу папку проєкту.
2. Встановити залежності:

   ```bash
   python -m pip install -r requirements.txt
   ```

3. Запустити FastAPI:

   ```bash
   python -m uvicorn src.api.main:app --reload
   ```

4. Після запуску відкрити:
   - **Swagger UI:** http://127.0.0.1:8000/docs
   - **OpenAPI JSON:** http://127.0.0.1:8000/openapi.json

### Автоматична генерація OpenAPI

Специфікація OpenAPI генерується безпосередньо з коду FastAPI.

Для експорту документації використовується команда:

```bash
python scripts/export_openapi.py
```

Опублікована документація доступна на [GitHub Pages](https://ukma-fin-ssdm-2026.github.io/Rehab/).

Локальна Swagger UI та документація на GitHub Pages — два різні способи перегляду API.

## Якість коду та документація (Лабораторна 5)

У межах Лабораторної роботи 5 команда виконала перевірку
якості Python-коду, статичний аналіз безпеки та налаштувала
інструменти для автоматизації перевірок.

Результати роботи:

- [Прогрес розробки](docs/code-quality/progress.md) —
  стан реалізації, перевірки та подальші кроки.
- [Статичний аналіз](docs/code-quality/static-analysis.md) —
  результати аналізу безпеки та виявлені ризики.
- [Code Review](docs/code-quality/review-report.md) —
  огляд коду іншої команди та рекомендації.
- [Командний статут](TeamCharter.md) —
  стандарти кодування, правила Code Review
  та Definition of Done.
  
## Документація прототипу (КТ-5)

У межах подальшої розробки Rehab командою підготовлено функціональний прототип мобільного застосунку на React Native / Expo із серверною частиною FastAPI.

Прототип містить 16 маршрутів, зокрема екрани календаря, статистики, цілей та профілю користувача. Частина екранів має демонстраційний характер і призначена для подальшої реалізації функціональності.

Для документування виконаної роботи підготовлено такі матеріали:

- [Звіт про прогрес розробки прототипу](PROGRESS.md) — опис реалізованої функціональності, архітектури, інтеграції Backend і Frontend, результатів тестування та обмежень поточної версії.
- [Інструкція з налаштування та запуску](SETUP_AND_RUN.md) — встановлення залежностей, налаштування середовища, запуск FastAPI та Expo Web, перевірка роботи прототипу.
- [Попередній UI/UX-дизайн](docs/design/design.md) — опис візуальної концепції застосунку, створеної у Figma, та макети основних екранів.
- [Загальний огляд дизайн-макетів](docs/design/overview.png) — зображення підготовлених екранів застосунку.

Інтегрована версія прототипу розроблялася в гілці `feature/rehab-prototype`.

Макети Figma є попередньою концепцією майбутнього інтерфейсу Rehab та можуть відрізнятися від поточної функціональної реалізації застосунку.

