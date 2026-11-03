"""Модульні тести валідатора двосторонньої простежуваності Lab07."""

import unittest

from check_traceability import validate

REQUIREMENTS = """
- **FR-001** Створення відмітки.
- **FR-002** Заборона майбутньої дати.
* **PERF-001 (Продуктивність)** p95 не більше 500 мс.
"""

PLAN = """
| № | Компонент/функція | Рівень тесту | Тип | Очікуваний результат | Власник | Вимога |
|---|---|---|---|---|---|---|
| 1 | Календар | Модульний | Позитивний | Відмітка збережена | Учасник | FR-001 |
| 2 | Календар | Інтеграційний | Негативний | Майбутню дату відхилено | Учасник | FR-002 |
| 3 | API | Системний | Позитивний | p95 ≤ 500 мс | Учасник | PERF-001 |
"""

RTM = """
## Простежуваність тест-кейсів Лаб 7

| Вимога | Тест-кейси з тест-плану |
|---|---|
| FR-001 | №1 |
| FR-002 | №2 |
| PERF-001 | №3 |
"""


class TraceabilityValidatorTests(unittest.TestCase):
    def test_matching_requirements_plan_and_rtm_pass(self):
        self.assertEqual(validate(REQUIREMENTS, PLAN, RTM), [])

    def test_plan_with_status_column_preserves_requirement_links(self):
        with_status = PLAN.replace("| Учасник |", "| Заплановано | Учасник |")
        self.assertEqual(validate(REQUIREMENTS, with_status, RTM), [])

    def test_missing_case_in_rtm_is_reported(self):
        broken = RTM.replace("FR-002 | №2", "FR-002 | №999")
        errors = validate(REQUIREMENTS, PLAN, broken)
        self.assertTrue(any("відсутній кейс №999" in x for x in errors))
        self.assertTrue(any("Кейс №2" in x for x in errors))

    def test_nonexistent_requirement_is_reported(self):
        bad_plan = PLAN.replace("FR-001 |", "FR-999 |")
        errors = validate(REQUIREMENTS, bad_plan, RTM)
        self.assertTrue(any("FR-999 не визначено" in x for x in errors))

    def test_missing_nfr_in_plan_is_reported(self):
        shorter_plan = PLAN.replace(
            "| 3 | API | Системний | Позитивний | p95 ≤ 500 мс | Учасник | PERF-001 |",
            "",
        )
        errors = validate(REQUIREMENTS, shorter_plan, RTM)
        self.assertTrue(any("PERF-001: немає жодного кейсу" in x for x in errors))


if __name__ == "__main__":
    unittest.main()
