# Аналіз SonarQube та рефакторинг — Лабораторна робота №8

**Проєкт:** Rehab  
**Дата звіту:** 03.11.2026 (історичний аналіз — 29.10.2026)  
**Інструмент:** SonarQube Cloud  
**Порівняння:** історія аналізів `main` у SonarQube (29.10.2026, 13:45) та актуальний `main` (03.11.2026). Гілка `pre-refactor` зберігає історичний код, але окремо в SonarQube не аналізувалася; `lab08` — гілка рефакторингу.  
**Pull Request:** [Рефакторинг Rehab #206](https://github.com/ukma-fin-ssdm-2026/Rehab/pull/206)

## 1. Аналіз якості коду (етап 1)

Переглянуто [панель Rehab у SonarQube Cloud](https://sonarcloud.io/project/overview?id=ukma-fin-ssdm-2026_Rehab) та історію показників на сторінці Activity. Початковий стан коду збережено в [гілці `pre-refactor`](https://github.com/ukma-fin-ssdm-2026/Rehab/tree/pre-refactor), але метрики «до» отримані з **реального історичного аналізу `main` від 29.10.2026, 13:45**, а не з повторного сканування цієї гілки.

Для лабораторної обрано три метрики з п'яти. **Security Rating записано окремо**, як вимагає завдання. Вихідні значення записані у звіті 30.10.2026 і підтверджені історією SonarQube за 29.10.2026. Показники «після» відображають результат **командних змін у `main`**, зокрема синхронізації 352 комітів; це не ефект лише особистого рефакторингу.

| Показник | До рефакторингу | Після рефакторингу |
|---|---|---|
| Duplicated Lines (%) | 13,0% | 2,3% |
| Maintainability Rating | A | A |
| Reliability Rating | C | A |
| Security Rating (обов'язковий) | C | C |

### Скриншоти SonarQube: «до» і «після»

Усі зображення відображають проєкт **Rehab**. Для стану «до» використано історію **Activity → main**, а для стану «після» — **Measures / Overall Code** та snapshots. Скриншоти «до» було відкрито 03.11.2026, проте курсор на графіках указує на **історичний аналіз 29.10.2026 о 13:45**. Це не скриншоти, зроблені 29 жовтня, і не аналіз окремої гілки `pre-refactor`.

**До рефакторингу — 29.10.2026, 13:45:**

![Історичний рівень дублювання 13,0% (main, 29.10.2026)](screenshots/sonarqube-duplication-before.jpg)

![Історичні рейтинги: Maintainability A, Reliability C, Security C (main, 29.10.2026)](screenshots/sonarqube-ratings-before.jpg)

**Після рефакторингу — 03.11.2026, main / Overall Code:**

![Duplicated Lines: 2,3%](screenshots/sonarqube-duplication-after.png)

![Maintainability Rating: A, 1 issue](screenshots/sonarqube-maintainability-after.png)

![Reliability Rating: A, 2 issues](screenshots/sonarqube-reliability-after.png)

![Security Rating: C, 5 issues, 3 Medium та 2 Low](screenshots/sonarqube-security-after.png)

**Висновок за знімками:** загальна частка дублікатів зменшилася з **13,0% до 2,3%** (на **10,7 відсоткових пункта**), Reliability Rating підвищився з **C до A**, Maintainability Rating залишився **A**, а Security Rating — **C**. На поточному знімку залишаються 5 відкритих Security Issues; частина виправлень підготовлена в [PR №236](https://github.com/ukma-fin-ssdm-2026/Rehab/pull/236), який на момент цього звіту не злито. Після злиття потрібне повторне сканування — не слід видавати поточний рейтинг C за виправлені всі проблеми.

**Початкові числові записи (30.10.2026; історія Activity підтверджує рейтинги та дублювання за 29.10):** Quality Gate Passed; 12 Security Issues (10 Medium, 2 Low), 4 Reliability Issues, 0 проблем супроводжуваності. Coverage у SonarQube не відображалося.

**Повторний перегляд Overall Code (03.11.2026):** Security Rating C, 5 відкритих Security Issues (3 Medium, 2 Low), 2 відкриті Reliability Issues. Maintainability і Reliability мають рейтинг A за переглядом панелі. За останні 30 днів SonarQube відображає 7 закритих Security Issues. Duplicated Lines (%) після змін становить 2,3% за Overall Code.

Найвищі локальні показники дублювання залишаються у `src/api/routers/calendar.py` (80,6%) та `backend/app/routers/calendar.py` (72,9%).

Вихідна оцінка 30.10 належить старому стану коду до синхронізації PR №206 з `main` на 352 коміти. Тому різницю в кількості issues або рейтингах не можна повністю приписувати одному рефакторингу. Для аналізу актуального `main` використовуємо коміт [`29399f8`](https://github.com/ukma-fin-ssdm-2026/Rehab/commit/29399f8a1ab11c6fb48757901c9b3f821c732461).

### Причини Security Rating C

| Файл | Відкриті issues | Серйозність | Рішення |
|---|---:|---|---|
| `.github/workflows/ci.yml`, рядки 43–44 | 2 | Medium | Закріпити версії пакетів для CI; [PR №236](https://github.com/ukma-fin-ssdm-2026/Rehab/pull/236) очікує злиття |
| `.github/workflows/docs.yml`, рядок 32 | 1 | Medium | Встановлювати ті самі зафіксовані версії; [PR №236](https://github.com/ukma-fin-ssdm-2026/Rehab/pull/236) очікує злиття |
| `docs/api/index.html`, рядки 6 і 10 | 2 | Low | Закріпити конкретну версію Swagger UI та перевірити SRI-хеші CSS/JS |

Попередні зауваження до відсутнього `--only-binary=:all:` уже мають статус Fixed. Вони відрізняються від відкритих зауважень щодо незакріплених версій. Після злиття виправлень потрібен повторний аналіз SonarQube: успішний Quality Gate сам по собі не підтверджує Security Rating A.

**Зв'язок із попередніми лабораторними:** у [STRIDE-моделі Lab 3](../architecture/threat-model.md) категорія Tampering стосується ризику несанкціонованої зміни даних. Неконтрольовані пакети та зовнішні ресурси створюють споріднений ризик підміни коду в ланцюгу постачання, не тотожний описаному сценарію зміни календарних даних. [Bandit та pip-audit із Lab 5](../code-quality/static-analysis.md) перевіряють Python-код і відомі вразливості залежностей, але не замінюють фіксацію версій або перевірку цілісності CDN-ресурсів.

## 2. Рефакторинг (етап 2)

### 2.1. Усунення повторення форматування днів

**Запах коду:** повторення умов для вибору слова «день», «дні», «днів».  
**Техніка:** використання спільного методу (*Reuse Method*).  
**Файл:** `backend/app/services/progress.py`.

**До:** `format_progress_days()` самостійно перевіряла закінчення числа. Аналогічна логіка вже була у `backend/app/services/formatting.py`.

**Після:** використано наявну `_day_word()`, тому правила більше не дублюються.

**Що не змінилося:** формат результату (наприклад, «1 день», «3 дні», «5 днів») і перевірка неправильних вхідних даних.  
**Тести:** `tests/test_progress.py`, `tests/test_formatting.py`.

### 2.2. Винесення цілей у константу

**Запах коду:** числа 7 та 30 повторювалися в обчисленнях прогресу.  
**Техніка:** *Replace Magic Number with Constant*.  
**Файл:** `backend/app/services/statistics.py`.

**До:** `get_goal_progress()` і `get_days_remaining()` містили однакові значення цілей 7 і 30 окремо.

**Після синхронізації:** в актуальному `main` використовується `FIXED_GOAL_DAYS = (7, 30, 90, 180, 365)`, тому стару реалізацію не переносили.

**Що не змінилося:** поведінка актуальної реалізації п'яти етапів.  
**Тести:** `tests/test_statistics.py`, `tests/test_goal_remaining.py`.

### 2.3. Безпека

У GitHub Actions додала `--only-binary=:all:` для безпечнішого встановлення Python-пакетів. Потім виправила помилки YAML.

### 2.4. Використання ШІ

ChatGPT допоміг з оформленням документації та підказав варіанти рефакторингу.

## 3. Перевірка результату (етап 3)

Після синхронізації [PR №206](https://github.com/ukma-fin-ssdm-2026/Rehab/pull/206) та його злиття у `main` успішно пройшли Backend, Frontend, Code Quality, Dependency Audit, Traceability і Publish API docs. Аналіз SonarQube для PR №206 показав Quality Gate Passed. Для [PR №236](https://github.com/ukma-fin-ssdm-2026/Rehab/pull/236) перевірки також успішні; це ще не підтвердження усунення трьох відкритих issues в Overall Code.

## 4. Підготовка релізу та висновок

Версію оновлено до `1.0.1`, додано `CHANGELOG.md`. Показники якості та безпеки, посилання на шість скриншотів «до/після» й невирішені Security Issues задокументовано вище.
