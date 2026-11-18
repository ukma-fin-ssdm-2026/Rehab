"""Sequential full-suite flakiness experiment for Lab10."""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import time
import xml.etree.ElementTree as ET


def read_junit(path):
    """Read outcomes without silently overwriting duplicate test identities."""
    try:
        root = ET.parse(path).getroot()
    except (OSError, ET.ParseError) as error:
        raise ValueError(f"Unavailable or invalid JUnit report: {path}") from error
    if root.tag not in ("testsuite", "testsuites"):
        raise ValueError("Expected JUnit testsuite/testsuites")
    results = {}
    for suite in root.iter("testsuite"):
        if suite.find("error") is not None:
            raise ValueError("Suite-level collection/infrastructure error")
    for case in root.iter("testcase"):
        name = case.get("name")
        if not name:
            raise ValueError("Testcase without a name")
        identity = f"{case.get('classname', '')}::{name}"
        if identity in results:
            raise ValueError(f"Ambiguous duplicate testcase: {identity}")
        states = [value for tag, value in (
            ("failure", "failed"), ("error", "error"), ("skipped", "skipped")
        ) if case.find(tag) is not None]
        if len(states) > 1:
            raise ValueError(f"Conflicting testcase outcomes: {identity}")
        results[identity] = states[0] if states else "passed"
    if not results:
        raise ValueError("Report contains no tests")
    # pytest uses aggregate testcase totals; Node suites count immediate children.
    # Accept either documented convention, but never contradictory declarations.
    for suite in root.iter():
        if suite.tag not in ("testsuite", "testsuites"):
            continue
        declared = {}
        for key in ("tests", "failures", "errors", "skipped"):
            if key in suite.attrib:
                try:
                    declared[key] = int(suite.get(key))
                except ValueError as error:
                    raise ValueError(f"Invalid JUnit count: {key}") from error
                if declared[key] < 0:
                    raise ValueError(f"Negative JUnit count: {key}")
        leaves = list(suite.iter("testcase"))
        children = [child for child in suite if child.tag in ("testcase", "testsuite")]
        aggregate = {"tests": len(leaves)}
        immediate = {"tests": len(children)}
        for tag, key in (("failure", "failures"), ("error", "errors"), ("skipped", "skipped")):
            aggregate[key] = sum(case.find(tag) is not None for case in leaves)
            immediate[key] = sum(
                child.find(tag) is not None or int(child.get(key, "0")) > 0
                for child in children
            )
        if not any(all(counts[key] == value for key, value in declared.items())
                   for counts in (aggregate, immediate)):
            raise ValueError("JUnit declared totals disagree with reported tests/outcomes")
    return results


def compare_results(repeats):
    identities = sorted(set().union(*(set(row) for row in repeats)))
    histories = {name: [row.get(name, "missing") for row in repeats]
                 for name in identities}
    return {
        "variable_tests": {name: states for name, states in histories.items()
                           if len(set(states)) > 1},
        "stable_failures": [name for name, states in histories.items()
                            if len(set(states)) == 1 and states[0] in ("failed", "error")],
        "consistent_collection": bool(identities) and all(
            "missing" not in states for states in histories.values()
        ),
    }


def repeat_suite(name, command, cwd, output, repeats):
    """Continue every repeat after a test failure; retain invalid reports as errors."""
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    records = []
    for attempt in range(1, repeats + 1):
        report = output / f"{name}-{attempt}.xml"
        # A prior file must never be mistaken for the current invocation's result.
        report.unlink(missing_ok=True)
        args = [arg.replace("{report}", str(report)) for arg in command]
        started = datetime.now(timezone.utc).isoformat()
        before = time.monotonic()
        error = None
        with (output / f"{name}-{attempt}.log").open("w", encoding="utf-8") as log:
            try:
                completed = subprocess.run(
                    args, cwd=cwd, stdout=log, stderr=subprocess.STDOUT,
                    timeout=180, check=False,
                )
                exit_code = completed.returncode
            except (OSError, subprocess.TimeoutExpired) as failure:
                exit_code = None
                error = f"Command could not finish: {type(failure).__name__}"
        try:
            outcomes = read_junit(report)
        except ValueError as failure:
            outcomes = {}
            error = str(failure)
        if exit_code not in (0, 1):
            error = error or f"Infrastructure/collection exit code: {exit_code}"
        if any(state == "error" for state in outcomes.values()):
            error = error or "Test setup/collection error; inspect JUnit and logs"
        if outcomes and all(state == "skipped" for state in outcomes.values()):
            error = error or "All tests were skipped; no execution evidence"
        if exit_code == 1 and not any(state == "failed" for state in outcomes.values()):
            error = error or "Command failed without a reported failing test"
        if exit_code == 0 and any(state in ("failed", "error") for state in outcomes.values()):
            error = error or "Exit code conflicts with reported failures"
        records.append({
            "attempt": attempt, "started_at": started,
            "duration_seconds": round(time.monotonic() - before, 3),
            "exit_code": exit_code, "command": args,
            "report": report.name, "report_error": error, "outcomes": outcomes,
        })
        print(f"{name} {attempt}/{repeats}: exit={exit_code}, "
              f"tests={len(outcomes)}, report_error={error}", flush=True)
    comparison = compare_results([record["outcomes"] for record in records])
    return {
        "name": name, "repeats": records, **comparison,
        "complete": not any(record["report_error"] for record in records)
        and comparison["consistent_collection"],
    }


def run_checks(root, output, repeats=5):
    root, output = Path(root).resolve(), Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    sha = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True
    ).strip()
    files = sorted(str(path.relative_to(root / "frontend"))
                   for path in (root / "frontend" / "tests").glob("*.test.cjs"))
    if not files:
        raise ValueError("No frontend test files found")
    backend = repeat_suite(
        "backend", [sys.executable, "-m", "pytest", "-q", "--junitxml={report}"],
        root, output, repeats,
    )
    frontend = repeat_suite(
        "frontend", ["node", "--test", "--test-reporter=junit",
                     "--test-reporter-destination={report}", *files],
        root / "frontend", output, repeats,
    )
    unchanged = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True
    ).strip() == sha
    clean = subprocess.run(["git", "diff", "--quiet", "HEAD", "--"], cwd=root).returncode == 0
    result = {
        "commit_sha": sha, "repeats_per_suite": repeats,
        "same_commit": unchanged, "tracked_files_unchanged": clean,
        "complete": unchanged and clean and backend["complete"] and frontend["complete"],
        "suites": [backend, frontend],
    }
    (output / "summary.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    lines = ["# Lab10 — пошук нестабільних тестів", "", f"SHA: `{sha}`", "",
             f"Повторів кожного набору: {repeats}. Повний експеримент: {result['complete']}.",
             "", "Один checkout, послідовні процеси, без повторного checkout між прогонами.", ""]
    for suite in result["suites"]:
        lines += [f"## {suite['name']}", "", "| Повтор | Код | Тестів | Секунд | Помилка звіту |",
                  "| ---: | ---: | ---: | ---: | --- |"]
        for row in suite["repeats"]:
            lines.append(f"| {row['attempt']} | {row['exit_code']} | {len(row['outcomes'])} | "
                         f"{row['duration_seconds']} | {row['report_error'] or '—'} |")
        lines += ["", "### Змінні результати (кандидати, не діагноз причини)", ""]
        lines += [f"- `{name}`: {' → '.join(states)}"
                  for name, states in suite["variable_tests"].items()] or ["Не виявлено."]
        lines += ["", "### Стабільні падіння", ""]
        lines += [f"- `{name}`" for name in suite["stable_failures"]] or ["Не виявлено."]
        lines += [""]
    lines += ["Неповний експеримент не дозволяє зробити висновок про відсутність нестабільності.",
              "Зміни skip/missing потребують окремого аналізу; стабільне падіння не є flakiness.",
              "П'ять однакових результатів не доводять відсутності рідкісної нестабільності.", ""]
    (output / "summary.md").write_text("\n".join(lines), encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="flaky-results")
    args = parser.parse_args()
    try:
        result = run_checks(Path(__file__).resolve().parents[1], args.output)
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(f"Experiment failed: {error}", file=sys.stderr)
        return 2
    print((Path(args.output) / "summary.md").read_text(encoding="utf-8"))
    return 0 if result["complete"] and not any(
        suite["variable_tests"] or suite["stable_failures"] for suite in result["suites"]
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
