"""Select disjoint fast and slow pytest files for the Lab10 CI pipeline."""

import argparse
from fnmatch import fnmatchcase
import json
from pathlib import Path
import re
import subprocess
import sys
import tomllib


def validate_lock_pins(root):
    """Prevent CI from installing stale pins after requirements.lock changes."""
    def pins(path):
        result = set()
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.partition("#")[0].strip().removesuffix("\\").strip()
            if not line or line.startswith("--hash="):
                continue
            match = re.fullmatch(
                r"([A-Za-z0-9_.-]+)(\[[A-Za-z0-9_,.-]+\])?==([A-Za-z0-9.+_!-]+)", line
            )
            if not match:
                raise ValueError(f"Expected exact locked requirement in {path.name}: {line}")
            package, extras, version = match.groups()
            pin = re.sub(r"[-_.]+", "-", package).lower() + (extras or "").lower() + "==" + version
            if pin in result:
                raise ValueError(f"Duplicate locked requirement: {pin}")
            result.add(pin)
        if not result:
            raise ValueError(f"Empty dependency lock: {path.name}")
        return result

    root = Path(root)
    if pins(root / "requirements.lock") != pins(root / "requirements-ci-hashes.lock"):
        raise ValueError("Update requirements-ci-hashes.lock to match requirements.lock before CI installs")


def select_tier(root, tier):
    """Default every newly discovered test file to slow; fail on manifest drift."""
    if tier not in ("fast", "slow"):
        raise ValueError("Tier must be fast or slow")
    root = Path(root).resolve()
    config = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    options = config.get("tool", {}).get("pytest", {}).get("ini_options", {})

    def words(value):
        items = value.split() if isinstance(value, str) else value
        if not isinstance(items, list) or not all(isinstance(item, str) for item in items):
            raise ValueError("Unsupported pytest discovery configuration")
        return items

    if words(options.get("testpaths", ["tests"])) != ["tests"]:
        raise ValueError("Update tier discovery explicitly when pytest testpaths changes")
    patterns = words(options.get("python_files", ["test_*.py", "*_test.py"]))
    excluded = words(options.get("norecursedirs", [
        "*.egg", ".*", "_darcs", "build", "CVS", "dist", "node_modules", "venv", "{arch}"
    ]))
    if any("/" in pattern or "\\" in pattern for pattern in patterns + excluded):
        raise ValueError("Tier discovery requires directory/name patterns without path separators")
    tests = root / "tests"
    discovered = set()
    for path in tests.rglob("*.py"):
        relative = path.relative_to(tests)
        if not any(fnmatchcase(path.name, pattern) for pattern in patterns):
            continue
        if any(part == "__pycache__" or any(fnmatchcase(part, pattern) for pattern in excluded)
               for part in relative.parts[:-1]):
            continue
        if not path.is_file() or not path.resolve().is_relative_to(tests.resolve()):
            raise ValueError(f"Test file leaves the tests directory: {relative}")
        discovered.add(path.relative_to(root).as_posix())
    manifest = json.loads((tests / "test-tiers.json").read_text(encoding="utf-8"))
    fast = manifest.get("fast") if isinstance(manifest, dict) else None
    if not isinstance(fast, list) or not fast or not all(isinstance(item, str) for item in fast):
        raise ValueError("Fast manifest must contain a nonempty list of test file paths")
    if len(set(fast)) != len(fast):
        raise ValueError("Duplicate fast test file")
    for entry in fast:
        if (not entry.startswith("tests/") or "\\" in entry or ".." in Path(entry).parts
                or entry not in discovered):
            raise ValueError(f"Fast manifest contains an unsafe, missing or excluded test: {entry}")
    selected = set(fast) if tier == "fast" else discovered - set(fast)
    if not selected:
        raise ValueError(f"The {tier} tier contains no test files")
    return sorted(selected)


def build_command(root, tier, pytest_arguments):
    return [sys.executable, "-m", "pytest", *select_tier(root, tier), *pytest_arguments]


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("tier", choices=("fast", "slow"), nargs="?")
    parser.add_argument("--list", action="store_true", help="List files without running pytest")
    parser.add_argument("--check-locks", action="store_true", help="Verify dependency lock pin parity")
    args, forwarded = parser.parse_known_args()
    if forwarded[:1] == ["--"]:
        forwarded = forwarded[1:]
    root = Path(__file__).resolve().parents[1]
    try:
        if args.check_locks:
            validate_lock_pins(root)
            print("Dependency lock pins match")
            if args.tier is None:
                return 0
        if args.tier is None:
            parser.error("choose fast/slow or --check-locks")
        if args.list:
            print("\n".join(select_tier(root, args.tier)))
            return 0
        return subprocess.run(build_command(root, args.tier, forwarded), cwd=root, check=False).returncode
    except (OSError, ValueError) as error:
        print(f"Test tier selection failed: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
