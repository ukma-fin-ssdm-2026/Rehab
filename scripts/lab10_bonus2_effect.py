# AI-GENERATED START
"""Lab 10, бонус 2: вимірювання ефекту concurrency + paths-ignore.

Для кожного push-коміту в main за період збирає запуски врахованих workflow
і рахує чергу (створення запуску -> старт першого job) та виконання
(старт першого job -> завершення останнього) окремо, а також хвилини раннерів.
Позначає коміти, що змінили лише документацію (docs/, Labs/, *.md).

Потрібен gh CLI з доступом до репозиторію:
    python scripts/lab10_bonus2_effect.py --since 2026-10-28 --until 2026-11-18 --label before

Результат завжди записується в docs/ci-cd/evidence/bonus2/<label>.json.
"""

import argparse
import json
import shutil
import statistics
import subprocess
from datetime import date, datetime, timezone
from fnmatch import fnmatch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs" / "ci-cd" / "evidence" / "bonus2"
LABELS = ("before", "after")
REPO = "ukma-fin-ssdm-2026/Rehab"
WORKFLOWS = ["ci.yml", "code-quality.yml", "dependency-audit.yml", "traceability.yml"]
DOC_PATTERNS = ["docs/*", "Labs/*", "*.md"]


def gh(path: str):
    # Шлях API складається лише з констант, перевірених дат, числових id і SHA.
    executable = shutil.which("gh")
    if executable is None:
        raise SystemExit("Потрібен gh CLI")
    out = subprocess.run(  # nosec B603
        [executable, "api", path], check=True, capture_output=True, text=True
    ).stdout
    return json.loads(out)


def ts(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def minutes(start: datetime | None, end: datetime | None) -> float | None:
    if start is None or end is None:
        return None
    return round((end - start).total_seconds() / 60, 1)


def docs_only(sha: str) -> bool:
    files = [f["filename"] for f in gh(f"repos/{REPO}/commits/{sha}").get("files", [])]
    return bool(files) and all(
        any(fnmatch(name, p) for p in DOC_PATTERNS) for name in files
    )


def run_summary(run: dict) -> dict:
    jobs = gh(f"repos/{REPO}/actions/runs/{run['id']}/jobs")["jobs"]
    starts = [ts(j["started_at"]) for j in jobs if j["started_at"]]
    ends = [ts(j["completed_at"]) for j in jobs if j["completed_at"]]
    created = ts(run["created_at"])
    first, last = (min(starts) if starts else None), (max(ends) if ends else None)
    runner = sum(
        minutes(ts(j["started_at"]), ts(j["completed_at"])) or 0
        for j in jobs
        if j["started_at"] and j["completed_at"]
    )
    return {
        "workflow": run["name"],
        "run_id": run["id"],
        "url": run["html_url"],
        "status": run["status"],
        "conclusion": run["conclusion"],
        "attempt": run["run_attempt"],
        "queue_min": minutes(created, first),
        "exec_min": minutes(first, last),
        "runner_min": round(runner, 1),
    }


def collect(since: str, until: str) -> list[dict]:
    commits: dict[str, dict] = {}
    for wf in WORKFLOWS:
        page = gh(
            f"repos/{REPO}/actions/workflows/{wf}/runs"
            f"?branch=main&event=push&per_page=100&created={since}..{until}"
        )
        for run in page["workflow_runs"]:
            sha = run["head_sha"]
            entry = commits.setdefault(
                sha,
                {
                    "sha": sha[:7],
                    "message": run["head_commit"]["message"].splitlines()[0],
                    "created": run["created_at"],
                    "runs": [],
                },
            )
            entry["created"] = min(entry["created"], run["created_at"])
            entry["runs"].append(run_summary(run))
    rows = sorted(commits.values(), key=lambda c: c["created"])
    for row in rows:
        row["docs_only"] = docs_only(row["sha"])
        ci = [r for r in row["runs"] if r["workflow"] == "CI Pipeline"]
        row["ci_queue_min"] = ci[0]["queue_min"] if ci else None
        row["ci_exec_min"] = ci[0]["exec_min"] if ci else None
        row["runner_min"] = round(sum(r["runner_min"] for r in row["runs"]), 1)
    return rows


def stats(values: list[float]) -> dict:
    values = [v for v in values if v is not None]
    if not values:
        return {"n": 0}
    return {
        "n": len(values),
        "mean": round(statistics.mean(values), 1),
        "median": round(statistics.median(values), 1),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--since", required=True, type=date.fromisoformat)
    parser.add_argument("--until", required=True, type=date.fromisoformat)
    parser.add_argument("--label", required=True, choices=LABELS)
    args = parser.parse_args()
    if args.since > args.until:
        parser.error("--since має бути не пізніше за --until")
    since, until = args.since.isoformat(), args.until.isoformat()
    out = OUT_DIR / f"{LABELS[LABELS.index(args.label)]}.json"

    rows = collect(since, until)
    code = [r for r in rows if not r["docs_only"]]
    docs = [r for r in rows if r["docs_only"]]
    result = {
        "ai_generated": (
            "AI-GENERATED: файл створено скриптом scripts/lab10_bonus2_effect.py, "
            "код якого згенеровано ШІ; дані взято з GitHub Actions API"
        ),
        "repo": REPO,
        "period": f"{since}..{until}",
        "collected_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "workflows": WORKFLOWS,
        "summary": {
            "code_commits": len(code),
            "docs_only_commits": len(docs),
            "ci_queue_min_code": stats([r["ci_queue_min"] for r in code]),
            "ci_exec_min_code": stats([r["ci_exec_min"] for r in code]),
            "runner_min_per_code_commit": stats([r["runner_min"] for r in code]),
            "runner_min_docs_only_total": round(sum(r["runner_min"] for r in docs), 1),
        },
        "commits": rows,
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")

    print("| Коміт | Зміни | Черга CI, хв | Виконання CI, хв | Хв раннерів (усі wf) |")
    print("|---|---|---|---|---|")
    for r in rows:
        kind = "лише docs" if r["docs_only"] else "код/тести/конфіг"
        print(
            f"| {r['sha']} {r['message'][:45]} | {kind} | {r['ci_queue_min']} "
            f"| {r['ci_exec_min']} | {r['runner_min']} |"
        )
    print(json.dumps(result["summary"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
# AI-GENERATED END
