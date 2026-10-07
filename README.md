[![CI Pipeline](https://github.com/ukma-fin-ssdm-2026/Rehab/actions/workflows/ci.yml/badge.svg)](https://github.com/ukma-fin-ssdm-2026/Rehab/actions/workflows/ci.yml)

# Rehab

Наш застосунок **_Rehab_** - це дуже зручний, інтуїтивно зрозумілий та ходовий застосунок для відстежування днів тверезості

Він допомагає відмічати дні без вживання, дивитися статистику, ставити цілі та звичайно отримувати допомогу у разі потреби

> _Rehab - кожен тверезий день у новий commit_

---

## Команда

| **Учасник**          | **Роль Лаб1**                         |   **Роль Лаб2**           |  **Роль Лаб3**                 | **Роль Лаб4**     |
| -------------------- | ------------------                    |------------------         |------------------              |------------------ |  
| _Киричата Анастасія_ | Repo Maintainer                       |Traceability Lead          |Requirements-Architecture Mapper|Quality Lead       |
| _Мілевська Софія_    | CI Maintainer                         |Requirements Lead+FR Lead  |UML Lead                        |Integration Lead   |
| _Морозова Поліна_    | Documentation Lead+Project Brief Lead |Documentation Lead         |Architecture+Documentation Lead |Backend Lead       |
| _Колесник Марія_     | Issue Tracker Lead                    |Quality Lead               |Data & Threat Modeler           |Documentation Lead |


---

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
│   └── <a href="docs/api/">api/</a>                         # Документація API
│       ├── <a href="docs/api/api-design.md">api-design.md</a>               # Проєктні рішення API
│       ├── <a href="docs/api/quality-attributes.md">quality-attributes.md</a>       # Атрибути якості
│       ├── <a href="docs/api/openapi-generated.yaml">openapi-generated.yaml</a>      # Специфікація OpenAPI (автогенерація)
│       └── <a href="docs/api/index.html">index.html</a>                    # Swagger UI
├── <a href="scripts/">scripts/</a>                        # Скрипт генерації OpenAPI
├── <a href="src/">src/</a>
├── <a href="tests/">tests/</a>                          # Тести
├── <a href="Project-Description.md">Project-Description.md</a>          # Детальний опис проєкту
├── <a href="README.md">README.md</a>                       # Головний опис проєкту
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

## Запуск API (Лабораторна 4)
Потрібен Python 3.10 або новіший.

1. Встановити залежності: `pip install -r requirements.txt`
2. Запустити сервер (з кореня репозиторію): `python -m uvicorn src.api.main:app --reload`
3. Відкрити Swagger UI: http://127.0.0.1:8000/docs
4. Згенерувати специфікацію: `python scripts/export_openapi.py`
