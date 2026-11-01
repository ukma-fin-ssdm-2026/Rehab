# AI-GENERATED START
"""Одноразова OAuth-авторизація скриньки rehab.support.web@gmail.com (ТЗ С-3).

Запускає лише власниця скриньки на своєму комп'ютері. Користувачі Rehab
Google-вхід не проходять. Потрібен OAuth client типу «Desktop app» із
Google Cloud Console (Gmail API увімкнено) і окрема бібліотека:
    python -m pip install google-auth-oauthlib==1.5.0

1. Отримати refresh-токен (scope лише gmail.send):
    python scripts/authorize_gmail.py authorize --client-secrets ~/Downloads/client_secret.json
   Токени записуються у файл поза Git (за замовчуванням ~/.rehab/gmail-oauth.json,
   права 600) і НЕ друкуються. Значення переносяться в Render Environment:
   GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET, GMAIL_REFRESH_TOKEN, MAIL_FROM.

2. Технічний лист для перевірки налаштування, з тими самими змінними в середовищі:
    python scripts/authorize_gmail.py test-send --to rehab.support.web@gmail.com
"""

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

DEFAULT_OUT = Path.home() / ".rehab" / "gmail-oauth.json"
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


def authorize(client_secrets: Path, out: Path) -> int:
    from google_auth_oauthlib.flow import InstalledAppFlow

    if out.resolve().is_relative_to(ROOT):
        print("Файл із токенами має бути поза репозиторієм")
        return 2
    flow = InstalledAppFlow.from_client_secrets_file(str(client_secrets), SCOPES)
    credentials = flow.run_local_server(port=0, access_type="offline", prompt="consent")
    if not credentials.refresh_token:
        print("Google не повернув refresh-токен; повторіть з prompt=consent")
        return 1
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(
            {
                "GMAIL_CLIENT_ID": credentials.client_id,
                "GMAIL_CLIENT_SECRET": credentials.client_secret,
                "GMAIL_REFRESH_TOKEN": credentials.refresh_token,
                "MAIL_FROM": "rehab.support.web@gmail.com",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    os.chmod(out, 0o600)
    print(f"Збережено у {out}. Перенесіть значення в Render і видаліть файл.")
    return 0


def test_send(to: str) -> int:
    from backend.app.services.email_reminders import (
        SUBJECT,
        SendRejected,
        SendUncertain,
        sender_from_env,
    )

    sender = sender_from_env()
    if sender is None:
        print(
            "Задайте GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET, GMAIL_REFRESH_TOKEN, MAIL_FROM"
        )
        return 2
    body = "Технічна перевірка поштового транспорту Rehab. Відповідати не потрібно."
    try:
        for attempt in (1, 2):
            # Другий лист — після оновлення access-токена (новий сеанс sender).
            message_id = sender.send(to, SUBJECT, body)
            print(f"Лист {attempt} прийнято Gmail: id={message_id}")
            sender = sender_from_env()
    except (SendRejected, SendUncertain) as error:
        print(f"Не вдалося надіслати: {error.code}")
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    auth = sub.add_parser("authorize")
    auth.add_argument("--client-secrets", type=Path, required=True)
    auth.add_argument("--out", type=Path, default=DEFAULT_OUT)
    send = sub.add_parser("test-send")
    send.add_argument("--to", required=True)
    args = parser.parse_args()
    if args.command == "authorize":
        return authorize(args.client_secrets.expanduser(), args.out.expanduser())
    return test_send(args.to)


if __name__ == "__main__":
    sys.exit(main())
# AI-GENERATED END
