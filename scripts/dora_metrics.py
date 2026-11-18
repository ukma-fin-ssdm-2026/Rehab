import argparse
import json
import math
import os
import statistics
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def dt(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def auth_token():
    value = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if value:
        return value
    try:
        return subprocess.check_output(["gh", "auth", "token"], text=True, stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


class Api:
    def __init__(self, repo):
        self.repo = repo
        self.token = auth_token()
        if not self.token:
            raise RuntimeError("Немає авторизації GitHub API. Виконайте gh auth login та повторіть запуск або використайте --snapshot.")

    def get(self, path, params=None):
        url = "https://api.github.com/repos/" + self.repo + "/" + path
        if params:
            url += "?" + urlencode(params)
        headers = {"Accept": "application/vnd.github+json", "User-Agent": "rehab-dora", "X-GitHub-Api-Version": "2022-11-28"}
        if self.token:
            headers["Authorization"] = "Bearer " + self.token
        try:
            with urlopen(Request(url, headers=headers), timeout=45) as response:
                return json.load(response)
        except HTTPError as error:
            if error.code in (403, 429):
                remaining = error.headers.get("X-RateLimit-Remaining")
                if remaining == "0":
                    detail = "Вичерпано ліміт GitHub API. Перевірте gh api rate_limit та дочекайтеся його відновлення."
                else:
                    detail = "Доступ обмежено. Перевірте gh auth status, права доступу й ліміти GitHub API."
                raise RuntimeError(f"GitHub API: HTTP {error.code}, {path}. {detail}") from error
            raise RuntimeError(f"GitHub API: HTTP {error.code}, {path}") from error
        except URLError as error:
            raise RuntimeError(f"Немає доступу до GitHub API: {error}") from error

    def pages(self, path, key=None, filters=None):
        result = []
        page = 1
        while True:
            params = dict(filters or {})
            params.update({"per_page": 100, "page": page})
            payload = self.get(path, params)
            records = payload[key] if key else payload
            result.extend(records)
            if len(records) < 100:
                break
            page += 1
        return result


def collect(repo, start, end):
    api = Api(repo)
    runs = api.pages("actions/runs", "workflow_runs", {"branch": "main", "event": "push", "created": start + ".." + end})
    runs = [r for r in runs if r["name"] == "CI Pipeline" and r["head_branch"] == "main" and r["event"] == "push"]
    prs = api.pages("pulls", filters={"state": "all"})
    prs = [p for p in prs if p.get("merged_at") and p["base"]["ref"] == "main" and start <= p["merged_at"][:10] <= end]
    first = {}
    for pr in prs:
        commits = api.pages(f"pulls/{pr['number']}/commits")
        timestamps = [c["commit"]["author"]["date"] for c in commits if c.get("commit", {}).get("author", {}).get("date")]
        if timestamps:
            first[str(pr["number"])] = min(timestamps)
    jobs = {}
    for run in runs:
        jobs[str(run["id"])] = api.pages(f"actions/runs/{run['id']}/jobs", "jobs")
    return {"repo": repo, "start": start, "end": end, "runs": runs, "prs": prs, "first_commits": first, "jobs": jobs}


def median(values):
    return statistics.median(values) if values else None


def finished_at(run, job_map):
    completed = [job["completed_at"] for job in job_map.get(str(run["id"]), []) if job.get("completed_at")]
    if completed:
        return max(completed)
    return run.get("updated_at") if run.get("status") == "completed" else None


def calculate(data):
    start, end = date.fromisoformat(data["start"]), date.fromisoformat(data["end"])
    if end < start:
        raise ValueError("Дата завершення раніше дати початку")
    days = (end - start).days + 1
    runs = sorted(data["runs"], key=lambda r: (r["created_at"], r["id"]))
    completed = [r for r in runs if r["status"] == "completed"]
    success = [r for r in completed if r["conclusion"] == "success"]
    failures = [r for r in completed if r["conclusion"] in {"failure", "timed_out", "startup_failure"}]
    pending = [r for r in runs if r["status"] != "completed"]
    excluded = [r for r in completed if r["conclusion"] not in {"success", "failure", "timed_out", "startup_failure"}]
    mapped = {}
    for run in runs:
        mapped.setdefault(run["head_sha"], []).append(run)
    lead = []
    lead_parts = []
    for pr in data["prs"]:
        first = data["first_commits"].get(str(pr["number"]))
        green = sorted(
            (r for r in mapped.get(pr.get("merge_commit_sha"), []) if r["status"] == "completed" and r["conclusion"] == "success"),
            key=lambda r: dt(finished_at(r, data["jobs"])),
        )
        if first and green:
            hours = (dt(finished_at(green[0], data["jobs"])) - dt(first)).total_seconds() / 3600
            if hours >= 0:
                lead.append(hours)
                chosen = green[0]
                selected_jobs = data["jobs"].get(str(chosen["id"]), [])
                starts = [dt(job["started_at"]) for job in selected_jobs if job.get("started_at")]
                ends = [dt(job["completed_at"]) for job in selected_jobs if job.get("completed_at")]
                if starts and ends:
                    before = (dt(chosen["created_at"]) - dt(first)).total_seconds()
                    queued = (min(starts) - dt(chosen["created_at"])).total_seconds()
                    running = (max(ends) - min(starts)).total_seconds()
                    if min(before, queued, running) >= 0:
                        lead_parts.append((before, queued, running))
    incidents = []
    failed_at = None
    finished_runs = [(dt(moment), run) for run in success + failures if (moment := finished_at(run, data["jobs"]))]
    for ended, run in sorted(finished_runs, key=lambda item: item[0]):
        if run["conclusion"] != "success" and failed_at is None:
            failed_at = ended
        elif run["conclusion"] == "success" and failed_at is not None:
            hours = (ended - failed_at).total_seconds() / 3600
            if hours > 0:
                incidents.append(hours)
            failed_at = None
    waiting = []
    execution = []
    for run in runs:
        for job in data["jobs"].get(str(run["id"]), []):
            if job.get("created_at") and job.get("started_at"):
                seconds = (dt(job["started_at"]) - dt(job["created_at"])).total_seconds()
                if seconds >= 0:
                    waiting.append(seconds)
            if job.get("started_at") and job.get("completed_at"):
                seconds = (dt(job["completed_at"]) - dt(job["started_at"])).total_seconds()
                if seconds >= 0:
                    execution.append(seconds)
    run_parts = []
    for run in completed:
        selected_jobs = data["jobs"].get(str(run["id"]), [])
        starts = [dt(job["started_at"]) for job in selected_jobs if job.get("started_at")]
        ends = [dt(job["completed_at"]) for job in selected_jobs if job.get("completed_at")]
        if starts and ends:
            queued = (min(starts) - dt(run["created_at"])).total_seconds()
            running = (max(ends) - min(starts)).total_seconds()
            if queued >= 0 and running >= 0:
                run_parts.append((queued, running))
    total_ci = sum(queue + running for queue, running in run_parts)
    total_lead = sum(sum(parts) for parts in lead_parts)
    weeks = []
    current = start
    while current <= end:
        last = min(current + timedelta(days=6), end)
        count = sum(current <= dt(r["created_at"]).date() <= last for r in success)
        weeks.append((str(current), str(last), count))
        current = last + timedelta(days=1)
    return {
        "days": days, "runs": len(runs), "success": len(success), "failures": len(failures),
        "pending": len(pending), "excluded": len(excluded), "leads": len(lead),
        "frequency": len(success) / days, "lead_median": median(lead),
        "lead_mean": statistics.mean(lead) if lead else None,
        "failure_rate": len(failures) / (len(success) + len(failures)) * 100 if success or failures else None,
        "recovery": median(incidents), "recoveries": len(incidents),
        "unresolved": failed_at is not None, "wait": median(waiting), "execute": median(execution),
        "wait_count": len(waiting), "execute_count": len(execution),
        "run_wait": median([parts[0] for parts in run_parts]),
        "run_execute": median([parts[1] for parts in run_parts]),
        "run_count": len(run_parts),
        "ci_queue_pct": 100 * sum(parts[0] for parts in run_parts) / total_ci if total_ci else None,
        "ci_execute_pct": 100 * sum(parts[1] for parts in run_parts) / total_ci if total_ci else None,
        "lead_parts_count": len(lead_parts),
        "lead_before_pct": 100 * sum(parts[0] for parts in lead_parts) / total_lead if total_lead else None,
        "lead_queue_pct": 100 * sum(parts[1] for parts in lead_parts) / total_lead if total_lead else None,
        "lead_execute_pct": 100 * sum(parts[2] for parts in lead_parts) / total_lead if total_lead else None,
        "weeks": weeks,
    }


def pretty(number, unit=""):
    return "Не визначається" if number is None else f"{number:.2f}".replace(".", ",") + unit


def render(data, m):
    rows = [
        "# Бонус №1 — автоматичний підрахунок DORA",
        "",
        f"**Репозиторій:** https://github.com/{data['repo']}",
        f"**Період:** {data['start']} — {data['end']} включно (UTC, {m['days']} днів).",
        "",
        "## Чотири метрики",
        "",
        "| Метрика | Результат |",
        "| --- | ---: |",
        f"| Deployment Frequency (CI-проксі) | {pretty(m['frequency'])} успішних CI/день; {pretty(m['frequency'] * 7)} на тиждень |",
        f"| Lead Time for Changes (CI-проксі) | Медіана {pretty(m['lead_median'])} год; середнє {pretty(m['lead_mean'])} год |",
        f"| Change Failure Rate (CI-проксі) | {pretty(m['failure_rate'], '%')} |",
        f"| Time to Restore Service (CI-проксі) | {pretty(m['recovery'], ' год')} |",
        "",
        f"Вибірка: {m['runs']} запусків CI Pipeline на main; {m['success']} успішних, {m['failures']} невдалих, {m['pending']} незавершених, {m['excluded']} з іншими завершеними статусами. Lead Time обчислено для {m['leads']} PR.",
        "Для завершення CI взято останній jobs.completed_at, а якщо завершених jobs немає — run.updated_at завершеного запуску.",
        "Статуси наведені на момент отримання даних; незавершені запуски не вважаються невдалими. Відсутність збоїв не дорівнює нульовому часу відновлення.",
        "",
        "## Черга та виконання CI-запусків",
        "",
        "Черга: від створення запуску до початку першого job. Виконання: від початку першого job до завершення останнього.",
        "",
        "| Показник | Медіана | Завершених запусків |",
        "| --- | ---: | ---: |",
        f"| Черга | {pretty(m['run_wait'], ' с')} | {m['run_count']} |",
        f"| Виконання | {pretty(m['run_execute'], ' с')} | {m['run_count']} |",
        "",
        f"У сумарній тривалості CI-запусків черга займає {pretty(m['ci_queue_pct'], '%')}, а виконання — {pretty(m['ci_execute_pct'], '%')}.",
        "",
        "## Структура часу проходження змін",
        "",
        f"За {m['lead_parts_count']} успішними PR: до запуску CI — {pretty(m['lead_before_pct'], '%')}, черга CI — {pretty(m['lead_queue_pct'], '%')}, виконання CI — {pretty(m['lead_execute_pct'], '%')}.",
        "",
        "## Додаткова деталізація окремих jobs",
        "",
        "| Показник | Медіана | Кількість jobs |",
        "| --- | ---: | ---: |",
        f"| Черга jobs | {pretty(m['wait'], ' с')} | {m['wait_count']} |",
        f"| Виконання jobs | {pretty(m['execute'], ' с')} | {m['execute_count']} |",
        "",
        "## Успішні CI за тижнями",
        "",
        "| Тиждень (UTC) | Успішні CI |",
        "| --- | ---: |",
    ]
    rows.extend(f"| {a} — {b} | {n} |" for a, b, n in m["weeks"])
    comparable = data["start"] == "2026-10-27" and data["end"] == "2026-11-16" and data["repo"] == "ukma-fin-ssdm-2026/Rehab"
    rows.extend(["", "## Порівняння з ручним підрахунком", ""])
    if comparable:
        matched = (m["runs"] == 54 and m["success"] == 53 and m["failures"] == 0 and m["pending"] == 1 and m["leads"] == 53 and math.isclose(m["frequency"], 2.52, rel_tol=0, abs_tol=0.005) and m["lead_median"] is not None and math.isclose(m["lead_median"], 1.44, rel_tol=0, abs_tol=0.005) and m["lead_mean"] is not None and math.isclose(m["lead_mean"], 15.91, rel_tol=0, abs_tol=0.005))
        rows.append("Автоматичний підрахунок збігається з ручним для всіх чотирьох метрик." if matched else "Автоматичний підрахунок відрізняється від ручного знімка: історія запусків або їхні статуси могли змінитися.")
        rows.append("Ручний знімок: 53 успішні CI, 2,52 CI/день, Lead Time 1,44 год (медіана) і 15,91 год (середнє), 0% невдалих завершених CI, без вимірювань відновлення.")
    else:
        rows.append("Для вибраного періоду ручної базової вибірки немає; результати розраховано без припущень.")
    if m["unresolved"]:
        rows.append("Є невдалий CI без наступного успішного запуску; цей незавершений епізод відновлення виключений з медіани.")
    rows.extend([
        "",
        "## Відтворення",
        "",
        "Команда запускається локально після gh auth login або з GH_TOKEN:",
        "",
        "    python scripts/dora_metrics.py --repo ukma-fin-ssdm-2026/Rehab --start 2026-10-27 --end 2026-11-16 --output docs/ci-cd/dora-auto-results.md",
        "",
        "Для повторення підрахунку за збереженими даними GitHub API:",
        "",
        "    python scripts/dora_metrics.py --snapshot docs/ci-cd/evidence/dora-auto-api-snapshot.json --output docs/ci-cd/dora-auto-results.md",
        "",
        "Скрипт не запускає GitHub Actions та не займає раннер. Показники є навчальними CI-проксі, а не production deployment чи incidents.",
        "",
    ])
    return "\n".join(rows)


def main():
    parser = argparse.ArgumentParser(description="Автоматичний підрахунок DORA із GitHub API")
    parser.add_argument("--repo", default="ukma-fin-ssdm-2026/Rehab")
    parser.add_argument("--start", default="2026-10-27")
    parser.add_argument("--end", default="2026-11-16")
    parser.add_argument("--output", default="docs/ci-cd/dora-auto-results.md", choices=["docs/ci-cd/dora-auto-results.md"])
    parser.add_argument("--snapshot", choices=["docs/ci-cd/evidence/dora-auto-api-snapshot.json"])
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    if args.snapshot:
        snapshot = root / "docs" / "ci-cd" / "evidence" / "dora-auto-api-snapshot.json"
        data = json.loads(snapshot.read_text(encoding="utf-8"))
        if (data["repo"], data["start"], data["end"]) != (args.repo, args.start, args.end):
            parser.error("Період або репозиторій у знімку не збігаються з аргументами")
    else:
        data = collect(args.repo, args.start, args.end)
    results = calculate(data)
    target = root / "docs" / "ci-cd" / "dora-auto-results.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    output = render(data, results)
    target.write_text(output, encoding="utf-8")
    print(output)


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, KeyError, TypeError, ValueError) as error:
        print("Помилка: " + str(error), file=sys.stderr)
        sys.exit(1)
