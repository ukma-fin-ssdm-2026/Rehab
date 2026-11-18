"""Selection contracts: a new or misplaced test must not silently disappear."""

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest


class TestTierSelection(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location(
            "test_tiers", Path(__file__).with_name("test_tiers.py")
        )
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)
        self.assertTrue(hasattr(self.module, "select_tier"), "Tier selector not implemented")
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "tests").mkdir()
        (self.root / "pyproject.toml").write_text(
            '[tool.pytest.ini_options]\ntestpaths=["tests"]\n'
            'norecursedirs=["mutants", "node_modules"]\n', encoding="utf-8",
        )
        self.file("tests/test_fast.py")
        self.file("tests/test_database.py")
        self.manifest(["tests/test_fast.py"])

    def file(self, name):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("def test_example():\n    assert True\n", encoding="utf-8")
        return path

    def manifest(self, entries):
        (self.root / "tests/test-tiers.json").write_text(
            json.dumps({"fast": entries}), encoding="utf-8"
        )

    def test_fast_and_slow_cover_all_discovered_files_without_overlap(self):
        self.file("tests/nested/integration_test.py")
        self.file("tests/helper.py")
        fast = self.module.select_tier(self.root, "fast")
        slow = self.module.select_tier(self.root, "slow")
        self.assertEqual(fast, ["tests/test_fast.py"])
        self.assertEqual(slow, ["tests/nested/integration_test.py", "tests/test_database.py"])
        self.assertFalse(set(fast) & set(slow))

    def test_new_test_files_default_to_slow(self):
        self.file("tests/reliability/test_new_risk.py")
        self.assertEqual(self.module.select_tier(self.root, "slow"), [
            "tests/reliability/test_new_risk.py", "tests/test_database.py",
        ])

    def test_pytest_excluded_directories_do_not_leak_into_the_partition(self):
        self.file("tests/mutants/test_copy.py")
        self.file("tests/nested/node_modules/test_copy.py")
        self.assertEqual(self.module.select_tier(self.root, "slow"), ["tests/test_database.py"])

    def test_custom_pytest_filename_patterns_are_respected(self):
        (self.root / "pyproject.toml").write_text(
            '[tool.pytest.ini_options]\ntestpaths=["tests"]\n'
            'python_files=["check_*.py"]\n', encoding="utf-8",
        )
        self.file("tests/check_fast.py")
        self.file("tests/nested/check_database.py")
        self.manifest(["tests/check_fast.py"])
        self.assertEqual(self.module.select_tier(self.root, "fast"), ["tests/check_fast.py"])
        self.assertEqual(self.module.select_tier(self.root, "slow"), ["tests/nested/check_database.py"])

    def test_duplicate_missing_and_unsafe_manifest_entries_are_errors(self):
        outside = self.file("outside.py")
        for entries in (
            ["tests/test_fast.py", "tests/test_fast.py"],
            ["tests/test_missing.py"], ["../outside.py"], ["outside.py"],
            [str(outside.resolve())], ["tests"], [],
        ):
            with self.subTest(entries=entries):
                self.manifest(entries)
                with self.assertRaises(ValueError):
                    self.module.select_tier(self.root, "fast")

    def test_manifest_cannot_select_non_test_or_excluded_files(self):
        self.file("tests/helper.py")
        self.file("tests/mutants/test_copy.py")
        for entry in ("tests/helper.py", "tests/mutants/test_copy.py"):
            with self.subTest(entry=entry):
                self.manifest([entry])
                with self.assertRaises(ValueError):
                    self.module.select_tier(self.root, "fast")

    def test_changed_test_roots_and_unknown_tiers_fail_explicitly(self):
        with self.assertRaises(ValueError):
            self.module.select_tier(self.root, "typo")
        (self.root / "pyproject.toml").write_text(
            '[tool.pytest.ini_options]\ntestpaths=["tests", "another-root"]\n', encoding="utf-8",
        )
        with self.assertRaises(ValueError):
            self.module.select_tier(self.root, "slow")

    def test_command_uses_exact_partition_and_preserves_pytest_arguments(self):
        self.assertEqual(
            self.module.build_command(self.root, "fast", ["-q", "--junitxml=out.xml"]),
            [sys.executable, "-m", "pytest", "tests/test_fast.py", "-q", "--junitxml=out.xml"],
        )

    def test_ci_hash_lock_must_match_project_dependency_pins(self):
        self.assertTrue(hasattr(self.module, "validate_lock_pins"), "Lock parity check missing")
        source = self.root / "requirements.lock"
        hashed = self.root / "requirements-ci-hashes.lock"
        source.write_text("example==1.0\nother[extra]==2.0\n", encoding="utf-8")
        hashed.write_text(
            "# generated lock\nexample==1.0 \\\n    --hash=sha256:" + "a" * 64 + "\n"
            "other[extra]==2.0 \\\n    --hash=sha256:" + "b" * 64 + "\n", encoding="utf-8",
        )
        self.module.validate_lock_pins(self.root)
        for content in (
            "example==1.1\nother[extra]==2.0\n",  # stale version in hashed copy
            "example==1.0\nother[extra]==2.0\nnew-package==3\n",  # new dependency
            "example==1.0\n",  # removed dependency
            "example>=1.0\nother[extra]==2.0\n",  # no longer an exact lock
            "",  # empty lock must not use preinstalled runner packages
        ):
            with self.subTest(content=content):
                source.write_text(content, encoding="utf-8")
                with self.assertRaises(ValueError):
                    self.module.validate_lock_pins(self.root)


if __name__ == "__main__":
    unittest.main()
