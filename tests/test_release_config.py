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
