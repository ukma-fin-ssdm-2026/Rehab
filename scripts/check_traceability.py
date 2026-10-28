#!/usr/bin/env python3
"""Перевірка простежуваності Лаб 07: вимога RTM ↔ виконуваний тест у коді.

Перед кожним тестом вказується коментар `# REQ: FR-001` (можна кілька ID
через кому). Перевіряються функції pytest із назвою test_* і задача Locust.
Тести, позначені skip/xfail, рахуються як описані, але НЕ як виконані:
для підтвердження реалізації необхідний окремий успішний запуск тестів.
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RTM = ROOT / "docs" / "requirements" / "rtm.md"
TESTS = ROOT / "tests"
REQUIREMENT = re.compile(r"\b(?:FR|PERF|SEC|REL|USAB)-\d{3}\b")
MARKER = re.compile(r"^\s*#\s*REQ:\s*(.+?)\s*$")


def declared_requirements() -> set[str]:
    """Усі ID вимог, що зазначені в RTM (не вигадуємо окремий каталог)."""
    return set(REQUIREMENT.findall(RTM.read_text(encoding="utf-8")))


def requirement_marker(lines: list[str], line_number: int) -> set[str]:
    """Зчитати однорядковий коментар безпосередньо перед def тесту."""
    if line_number <= 1:
        return set()
    match = MARKER.fullmatch(lines[line_number - 2])
    if not match:
        return set()
    raw = match.group(1)
    items = [item.strip() for item in raw.split(",")]
    if not items or any(REQUIREMENT.fullmatch(item) is None for item in items):
        raise ValueError(f"Некоректний маркер вимог: {raw!r}")
    return set(items)


def is_locust_task(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Враховуємо тільки методи, позначені @task / @task(...)."""
    for decorator in node.decorator_list:
        if isinstance(decorator, ast.Name) and decorator.id == "task":
            return True
        if (
            isinstance(decorator, ast.Call)
            and isinstance(decorator.func, ast.Name)
            and decorator.func.id == "task"
        ):
            return True
    return False


def main() -> int:
    requirements = declared_requirements()
    used: set[str] = set()
    problems: list[str] = []
    test_count = 0
    files = sorted(TESTS.glob("test_*.py"))
    locust = TESTS / "performance" / "locustfile.py"
    if locust.exists():
        files.append(locust)

    for path in files:
        source = path.read_text(encoding="utf-8")
        lines = source.splitlines()
        tree = ast.parse(source, filename=str(path))
        relative = path.relative_to(ROOT)

        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            is_pytest = path != locust and node.name.startswith("test_")
            is_load_test = path == locust and is_locust_task(node)
            if not (is_pytest or is_load_test):
                continue

            test_count += 1
            location = f"{relative}:{node.lineno} ({node.name})"
            try:
                ids = requirement_marker(lines, node.lineno)
            except ValueError as exc:
                problems.append(f"{location}: {exc}")
                continue

            if not ids:
                problems.append(f"{location}: немає коментаря # REQ: <ID>")
                continue

            for req in sorted(ids):
                if req not in requirements:
                    problems.append(f"{location}: {req} відсутня в RTM")
                else:
                    used.add(req)

    for req in sorted(requirements - used):
        problems.append(f"{req}: вимога є в RTM, але не має тесту в коді")

    if not requirements:
        problems.append("RTM не містить жодної вимоги")
    if not test_count:
        problems.append("Не знайдено жодного тесту")

    print(f"Простежуваність: {len(used)}/{len(requirements)} вимог, {test_count} визначень тестів.")
    if problems:
        print("ПОМИЛКИ простежуваності:")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print("OK: кожен тест має ID вимоги, кожна вимога RTM має хоча б один тест.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
