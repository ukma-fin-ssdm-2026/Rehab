# Автоматизований реліз Rehab — Lab 08

У GitHub Actions налаштовано [Release Please](https://github.com/googleapis/release-please-action) для автоматизованого формування версій за [Conventional Commits](https://www.conventionalcommits.org/). Конфігурація міститься в [PR №239](https://github.com/ukma-fin-ssdm-2026/Rehab/pull/239).

## Реалізація

- `.github/workflows/release-please.yml` — запуск при оновленні `main` та через `workflow_dispatch`; права `contents: write`, `pull-requests: write`, `issues: write`. Токен — секрет `RELEASE_PLEASE_TOKEN` (fine-grained PAT з правами Contents і Pull requests на репозиторій), резервно — `GITHUB_TOKEN`.
- `release-please-config.json` — стратегія `simple`, підписи релізних змін за Conventional Commits, секція **Refactoring** для `refactor:`, формат тегів `vX.Y.Z`. Через `extra-files` номер версії синхронно оновлюється в усіх місцях: `pyproject.toml` (`[tool.rehab].version`), `frontend/package.json`, `frontend/package-lock.json` (`version` і `packages[""].version`) та `backend/app/main.py` (рядок із позначкою `x-release-please-version`).
- `.release-please-manifest.json` і `version.txt` — поточна випущена версія `1.0.1` (тег `v1.0.1`).
- `CHANGELOG.md` — журнал релізних змін, який автоматично формує Release Please.
- `tests/test_release_config.py` — перевірка, що номер версії однаковий в усіх семи джерелах, що `extra-files` охоплює кожне з них, секції рефакторингу та точки відліку історії.
- `bootstrap-sha` — коміт `861c504` релізу `v1.0.1`: наступний автоматичний реліз враховує лише зміни після нього й не повторює записи `1.0.1` у `CHANGELOG.md`.

## Життєвий цикл релізу

Після появи релізної зміни в `main` Release Please аналізує коміти, формує окремий релізний PR з оновленим номером версії та `CHANGELOG.md`. Після злиття релізного PR наступний запуск автоматизації створює Git-тег і GitHub Release.

За звичайними правилами інструмента `fix:` підвищує patch-версію, `feat:` — minor, а breaking change — major. `refactor:` відображається у секції **Refactoring**; сам по собі цей тип не гарантує створення релізного PR без релізної зміни.

Для створення автоматичних PR потрібне налаштування **Settings → Actions → General → Allow GitHub Actions to create and approve pull requests**. Релізний PR, створений через `RELEASE_PLEASE_TOKEN`, запускає всі обов'язкові перевірки гілки `main`, як і звичайний PR. Якщо використовується резервний `GITHUB_TOKEN`, GitHub не запускає інші workflows для створених ним PR; тоді перевірки релізного PR запускаються закриттям і повторним відкриттям PR.

## Перевірка

[CI для PR №239](https://github.com/ukma-fin-ssdm-2026/Rehab/pull/239/checks) підтвердив успішне проходження Backend, Frontend, Code Quality, Dependency Audit, Traceability і SonarQube. Це перевірка конфігурації та застосунку; окремий релізний запуск відображається в [GitHub Actions — Lab08 Automated Release](https://github.com/ukma-fin-ssdm-2026/Rehab/actions/workflows/release-please.yml).
