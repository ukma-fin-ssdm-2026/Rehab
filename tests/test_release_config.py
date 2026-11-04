import json
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_release_version_sources_are_consistent():
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    manifest = json.loads(
        (ROOT / ".release-please-manifest.json").read_text(encoding="utf-8")
    )
    version = (ROOT / "version.txt").read_text(encoding="utf-8").strip()

    assert manifest["."] == version == project["tool"]["rehab"]["version"]


def test_release_configuration_includes_refactoring():
    config = json.loads((ROOT / "release-please-config.json").read_text(encoding="utf-8"))
    sections = {item["type"]: item for item in config["changelog-sections"]}

    assert config["release-type"] == "simple"
    assert config["versioning"] == "default"
    assert config["include-v-in-tag"] is True
    assert config["include-component-in-tag"] is False
    assert sections["refactor"]["section"] == "Refactoring"
    assert sections["refactor"].get("hidden", False) is False
    assert {
        "type": "toml",
        "path": "pyproject.toml",
        "jsonpath": "$.tool.rehab.version",
    } in config["extra-files"]


# AI-GENERATED START
def _release_versions():
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    package = json.loads((ROOT / "frontend/package.json").read_text(encoding="utf-8"))
    lock = json.loads((ROOT / "frontend/package-lock.json").read_text(encoding="utf-8"))
    main = (ROOT / "backend/app/main.py").read_text(encoding="utf-8")
    api = [
        line.split('"')[1]
        for line in main.splitlines()
        if "x-release-please-version" in line
    ]
    return {
        "manifest": json.loads(
            (ROOT / ".release-please-manifest.json").read_text(encoding="utf-8")
        )["."],
        "version.txt": (ROOT / "version.txt").read_text(encoding="utf-8").strip(),
        "pyproject": project["tool"]["rehab"]["version"],
        "package.json": package["version"],
        "package-lock": lock["version"],
        "package-lock root": lock["packages"][""]["version"],
        "main.py": api[0] if len(api) == 1 else None,
    }


def test_every_version_source_has_the_same_release_number():
    versions = _release_versions()

    assert len(set(versions.values())) == 1, versions


def test_release_please_updates_every_version_source():
    config = json.loads(
        (ROOT / "release-please-config.json").read_text(encoding="utf-8")
    )
    updated = {(item["path"], item.get("jsonpath")) for item in config["extra-files"]}

    assert updated == {
        ("pyproject.toml", "$.tool.rehab.version"),
        ("frontend/package.json", "$.version"),
        ("frontend/package-lock.json", "$.version"),
        ("frontend/package-lock.json", "$.packages[''].version"),
        ("backend/app/main.py", None),
    }


def test_bootstrap_starts_after_the_manual_1_0_1_release():
    config = json.loads(
        (ROOT / "release-please-config.json").read_text(encoding="utf-8")
    )

    assert config["bootstrap-sha"] == "861c5043f331e7c96dc91ca160e32b8e41a3a09d"


# AI-GENERATED END
