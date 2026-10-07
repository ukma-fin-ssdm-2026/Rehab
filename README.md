[![CI Pipeline](https://github.com/ukma-fin-ssdm-2026/Rehab/actions/workflows/ci.yml/badge.svg)](https://github.com/ukma-fin-ssdm-2026/Rehab/actions/workflows/ci.yml)

# Rehab

Наш застосунок **_Rehab_** - це дуже зручний, інтуїтивно зрозумілий та ходовий застосунок для відстежування днів тверезості

Він допомагає відмічати дні без вживання, дивитися статистику, ставити цілі та звичайно отримувати допомогу у разі потреби

> _Rehab - кожен тверезий день у новий commit_

---

## Команда

| **Учасник**          | **Роль Лаб1**                         |   **Роль Лаб2**           |  **Роль Лаб3**                 | **Роль Лаб3**     |
| -------------------- | ------------------                    |------------------         |------------------              |------------------ |  
| _Киричата Анастасія_ | Repo Maintainer                       |Traceability Lead          |Requirements-Architecture Mapper|Quality Lead       |
| _Мілевська Софія_    | CI Maintainer                         |Requirements Lead+FR Lead  |UML Lead                        |Integration Lead   |
| _Морозова Поліна_    | Documentation Lead+Project Brief Lead |Documentation Lead         |Architecture+Documentation Lead |Backend Lead       |
| _Колесник Марія_     | Issue Tracker Lead                    |Quality Lead               |Data & Threat Modeler           |Integration Lead   |


---

## Структура репозиторію

<pre>
project-root/
├── .github/
│   └── workflows/
│       └── <a href=".github/workflows/ci.yml">ci.yml</a>                  # CI/CD конфігурація
├── <a href="Lab01/">Lab01/</a>
├── <a href="Lab02/">Lab02/</a>
├── <a href="Lab02/">Lab03/</a>
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
│   └── <a href="docs/api/">api/</a>
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
...

## Запуск API (Лабораторна 4)
...
