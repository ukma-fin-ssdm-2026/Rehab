"""Генерує docs/api/openapi-generated.yaml з коду FastAPI-застосунку.

Запуск з кореня репозиторію:
    python scripts/export_openapi.py
"""

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.api.main import app  # noqa: E402

OUT = ROOT / "docs" / "api" / "openapi-generated.yaml"


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        yaml.safe_dump(app.openapi(), f, allow_unicode=True)
    print(f"OpenAPI записано в {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()