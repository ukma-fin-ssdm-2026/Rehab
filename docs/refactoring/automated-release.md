# Автоматизований реліз Rehab — Lab 08

У GitHub Actions налаштовано [Release Please](https://github.com/googleapis/release-please-action) для автоматизованого формування версій за [Conventional Commits](https://www.conventionalcommits.org/). Конфігурація міститься в [PR №239](https://github.com/ukma-fin-ssdm-2026/Rehab/pull/239).

## Реалізація

- `.github/workflows/release-please.yml` — запуск при оновленні `main` та через `workflow_dispatch`; використовує `GITHUB_TOKEN` і права `contents: write`, `pull-requests: write`, `issues: write`.
- `release-please-config.json` — стратегія `simple`, підписи релізних змін за Conventional Commits, секція **Refactoring** для `refactor:`, формат тегів `vX.Y.Z` і оновлення `[tool.rehab].version` у `pyproject.toml`.
- `.release-please-manifest.json` і `version.txt` — початкове значення версії `1.0.1`, узгоджене з `pyproject.toml`.
- `CHANGELOG.md` — журнал релізних змін, який автоматично формує Release Please.
- `tests/test_release_config.py` — перевірка узгодженості версій, секції рефакторингу та конфігурації оновлення TOML.
- `bootstrap-sha` — коміт `29399f8`, що обмежує історію, яку Release Please опрацьовує для першого автоматичного релізу.

## Життєвий цикл релізу

Після появи релізної зміни в `main` Release Please аналізує коміти, формує окремий релізний PR з оновленим номером версії та `CHANGELOG.md`. Після злиття релізного PR наступний запуск автоматизації створює Git-тег і GitHub Release.

За звичайними правилами інструмента `fix:` підвищує patch-версію, `feat:` — minor, а breaking change — major. `refactor:` відображається у секції **Refactoring**; сам по собі цей тип не гарантує створення релізного PR без релізної зміни.

Для створення автоматичних PR репозиторій використовує налаштування **Settings → Actions → General → Allow GitHub Actions to create and approve pull requests**. Використання вбудованого `GITHUB_TOKEN` обмежує автоматичний запуск інших workflows для PR і тегів, створених цим токеном.

## Перевірка

[CI для PR №239](https://github.com/ukma-fin-ssdm-2026/Rehab/pull/239/checks) підтвердив успішне проходження Backend, Frontend, Code Quality, Dependency Audit, Traceability і SonarQube. Це перевірка конфігурації та застосунку; окремий релізний запуск відображається в [GitHub Actions — Lab08 Automated Release](https://github.com/ukma-fin-ssdm-2026/Rehab/actions/workflows/release-please.yml).
