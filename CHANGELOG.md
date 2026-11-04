# Changelog

Формат — [Keep a Changelog](https://keepachangelog.com/uk/1.1.0/), версії — [SemVer](https://semver.org/lang/uk/).

## [1.0.1] - 2026-11-04

### Refactoring
- Усунуто дублювання форматування днів через повторне використання `_day_word()` (Reuse Method).
- Узгоджено рефакторинг цілей з актуальними етапами 7, 30, 90, 180, 365 днів (`FIXED_GOAL_DAYS`).
- `progress.py` використовує публічну `format_days()` замість приватної `_day_word()`; додано 11 граничних тестів (Reuse Method).
- У `formatting.py` магічні числа 11, 14, 2, 4, 1 замінено іменованими константами, умову «11–14» винесено в `_is_teen()` (Replace Magic Number with Constant, Decompose Conditional). Перед цим додано 22 характеризаційні тести `format_days`.

### Security
- Обмежено встановлення Python-залежностей у GitHub Actions бінарними дистрибутивами.

[1.0.1]: https://github.com/ukma-fin-ssdm-2026/Rehab/releases/tag/v1.0.1
