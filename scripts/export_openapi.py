"""Генерує docs/api/openapi-generated.yaml з FastAPI.

Запуск із кореня репозиторію:
    python scripts/export_openapi.py
"""

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.main import app  # noqa: E402

OUT = ROOT / "docs" / "api" / "openapi-generated.yaml"


def main() -> None:
    """Зберегти актуальну OpenAPI-специфікацію у YAML."""
    OUT.parent.mkdir(parents=True, exist_ok=True)

    with OUT.open("w", encoding="utf-8") as file:
        yaml.safe_dump(
            app.openapi(),
            file,
            allow_unicode=True,
            sort_keys=False,
        )

    print(f"OpenAPI записано в {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
