# AI-GENERATED START
"""Запускає службовий job нагадувань на розгорнутому API (ТЗ С-4).

Використовують GitHub Actions (reminders.yml) і ручна перевірка до main:
    REHAB_API_URL=https://... REMINDERS_JOB_TOKEN=... python scripts/run_reminders_job.py

URL і секрет беруться лише із середовища й не друкуються. Виводяться тільки
підсумкові лічильники. Безкоштовний Render може «прокидатися» до ~1 хв, тому
тимчасова недоступність повторюється до ~3 хв: job ідемпотентний.
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request

TOTAL_WAIT = 180
CONNECT_READ_TIMEOUT = 60
RETRY_DELAY = 15
RETRYABLE = {502, 503, 504}


def _api_code(error: urllib.error.HTTPError) -> str:
    try:
        return str(json.loads(error.read() or b"{}").get("code", ""))
    except (ValueError, AttributeError):
        return ""


def main() -> int:
    base = os.environ.get("REHAB_API_URL", "").strip().rstrip("/")
    token = os.environ.get("REMINDERS_JOB_TOKEN", "").strip()
    local = base.startswith(("http://127.0.0.1", "http://localhost"))
    if not (base.startswith("https://") or local) or not token:
        print("Потрібні REHAB_API_URL (https://...) і REMINDERS_JOB_TOKEN")
        return 2
    request = urllib.request.Request(
        f"{base}/internal/jobs/reminders",
        method="POST",
        headers={"X-Job-Token": token, "Content-Length": "0"},
    )
    deadline = time.monotonic() + TOTAL_WAIT
    while True:
        try:
            with urllib.request.urlopen(  # nosec B310 — схема перевірена вище
                request, timeout=CONNECT_READ_TIMEOUT
            ) as response:
                counts = json.load(response)
            print(" ".join(f"{key}={value}" for key, value in counts.items()))
            return 0
        except urllib.error.HTTPError as error:
            if error.code == 409:
                print("Job уже виконується іншим запуском")
                return 0
            api_code = _api_code(error)
            # JSON із code — відповів сам Rehab API, повтор не допоможе.
            if api_code or error.code not in RETRYABLE or time.monotonic() > deadline:
                print(f"Помилка API: HTTP {error.code} {api_code or ''}".rstrip())
                return 1
        except (urllib.error.URLError, TimeoutError):
            if time.monotonic() > deadline:
                print("API недоступний після очікування холодного старту")
                return 1
        time.sleep(RETRY_DELAY)


if __name__ == "__main__":
    sys.exit(main())
# AI-GENERATED END
