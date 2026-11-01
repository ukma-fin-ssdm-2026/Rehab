#!/usr/bin/env python3
"""Бонус №1 Lab07: двостороння перевірка вимог і кейсів тест-плану.

Перевіряємо три джерела:
1. docs/requirements/requirements.md — справжні ID FR/NFR;
2. docs/validation/test-plan.md — кейси №N з ID вимоги;
3. docs/requirements/rtm.md — таблиця «Простежуваність тест-кейсів Лаб 7».

Підтримка 7/8 колонок також наявна в main після PR №219.

Зв'язок «вимога ↔ кейс» означає заплановане покриття, НЕ виконаний
автоматизований тест. Запуски та статус реалізації перевіряються окремо.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS = ROOT / "docs/requirements/requirements.md"
PLAN = ROOT / "docs/validation/test-plan.md"
RTM = ROOT / "docs/requirements/rtm.md"

REQ_ID = re.compile(r"(?:FR|PERF|SEC|REL|USAB)-\d{3}")
REQ_DEFINITION = re.compile(
    r"^\s*[-*]\s+\*\*((?:FR|PERF|SEC|REL|USAB)-\d{3})(?=\s|\*\*)", re.M
)
CASE_CELL = re.compile(r"^\d+$")
CASE_REF = re.compile(r"№\s*(\d+)")


def table_cells(line: str) -> list[str]:
    """Розібрати звичайний рядок Markdown-таблиці."""
    if not line.startswith("|") or not line.endswith("|"):
        return []
    return [cell.strip() for cell in line.strip("|").split("|")]


def defined_requirements(text: str) -> set[str]:
    return set(REQ_DEFINITION.findall(text))


def plan_cases(text: str) -> tuple[dict[int, str], list[str]]:
    cases: dict[int, str] = {}
    issues: list[str] = []
    for line in text.splitlines():
        cells = table_cells(line)
        if len(cells) not in (7, 8) or not CASE_CELL.fullmatch(cells[0]):
            continue
        number = int(cells[0])
        req = cells[-1].replace("`", "").strip()
        if number in cases:
            issues.append(f"Дубль кейсу №{number} у тест-плані")
        elif not REQ_ID.fullmatch(req):
            issues.append(
                f"Кейс №{number} без коректного одиничного ID вимоги: {req!r}"
            )
        else:
            cases[number] = req
    if not cases:
        issues.append("У тест-плані не знайдено таблиці кейсів із 7 або 8 колонками")
    return cases, issues


def rtm_links(text: str) -> tuple[dict[str, set[int]], list[str]]:
    heading = "## Простежуваність тест-кейсів Лаб 7"
    issues: list[str] = []
    if heading not in text:
        return {}, [f"RTM не містить розділу {heading!r}"]
    section = text.split(heading, 1)[1].split("\n## ", 1)[0]
    links: dict[str, set[int]] = {}
    for line in section.splitlines():
        cells = table_cells(line)
        if len(cells) != 2:
            continue
        req = cells[0].replace("`", "").strip()
        if not REQ_ID.fullmatch(req):
            continue
        if req in links:
            issues.append(f"Дубль вимоги {req} у таблиці RTM")
            continue
        numbers = {int(n) for n in CASE_REF.findall(cells[1])}
        if not numbers:
            issues.append(f"{req}: немає ID тест-кейсів у RTM")
        links[req] = numbers
    return links, issues


def validate(requirements: str, plan: str, rtm: str) -> list[str]:
    defined = defined_requirements(requirements)
    cases, problems = plan_cases(plan)
    links, rtm_problems = rtm_links(rtm)
    problems.extend(rtm_problems)

    if not defined:
        problems.append("У requirements.md не знайдено FR/NFR")
    for number, req in sorted(cases.items()):
        if req not in defined:
            problems.append(f"Кейс №{number}: {req} не визначено в requirements.md")

    for req in sorted(defined - set(links)):
        problems.append(f"{req}: вимога відсутня в таблиці простежуваності RTM")
    for req in sorted(set(links) - defined):
        problems.append(f"{req}: RTM посилається на неіснуючу вимогу")

    inverse: dict[int, set[str]] = {}
    for req, numbers in links.items():
        for number in numbers:
            inverse.setdefault(number, set()).add(req)
            if number not in cases:
                problems.append(f"RTM: {req} посилається на відсутній кейс №{number}")
            elif cases[number] != req:
                problems.append(
                    f"RTM: кейс №{number} віднесено до {req}, "
                    f"але в тест-плані вказано {cases[number]}"
                )

    for number, req in sorted(cases.items()):
        if req not in inverse.get(number, set()):
            problems.append(f"Кейс №{number} ({req}) не внесено в RTM")

    for req in sorted(defined):
        if req not in {value for value in cases.values()}:
            problems.append(f"{req}: немає жодного кейсу в тест-плані")

    return problems


def main() -> int:
    problems = validate(
        REQUIREMENTS.read_text(encoding="utf-8"),
        PLAN.read_text(encoding="utf-8"),
        RTM.read_text(encoding="utf-8"),
    )
    if problems:
        print(f"FAIL: {len(problems)} розбіжностей у простежуваності:")
        for issue in problems:
            print(f" - {issue}")
        return 1
    print("PASS: усі FR/NFR і тест-кейси узгоджені між requirements, plan і RTM.")
    print("Примітка: це перевірка плану, а не фактичного виконання тестів.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
