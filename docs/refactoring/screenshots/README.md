# Докази SonarQube для лабораторної роботи №8

Скриншоти з проєкту Rehab. Повне пояснення, порівняльна таблиця та висновки наведені в [звіті](../sonarcloud-report.md).

| Файл | Що підтверджує |
|---|---|
| `sonarqube-duplication-before.jpg` | Історія `main`: 29.10.2026 13:45, Duplicated Lines 13,0% |
| `sonarqube-ratings-before.jpg` | Історія `main`: 29.10.2026 13:45, Maintainability A, Reliability C, Security C |
| `sonarqube-duplication-after.jpg` | `main`: Duplicated Lines 2,3% |
| `sonarqube-maintainability-after.jpg` | `main`: Maintainability Rating A |
| `sonarqube-reliability-after.jpg` | `main`: Reliability Rating A |
| `sonarqube-security-after.jpg` | `main`: Security Rating C, п'ять відкритих issues |

Історичні значення «до» зняті з графіків **Activity**, а не отримані повторним запуском аналізу гілки `pre-refactor`. Поточні скриншоти «після» зроблено 03.11.2026, до злиття PR №236.
