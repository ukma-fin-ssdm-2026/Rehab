"""Contract tests for the Lab10 report runner; no application dependencies."""

import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).with_name("check_flaky_tests.py")


class FlakyReportTests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location("flaky_runner", SCRIPT)
        self.runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.runner)
        self.assertTrue(hasattr(self.runner, "read_junit"), "JUnit reader is not implemented")
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)

    def report(self, text):
        path = self.directory / "report.xml"
        path.write_text(text, encoding="utf-8")
        return path

    def test_reads_nested_junit_and_preserves_distinct_outcomes(self):
        report = self.report(
            '<testsuites><testsuite name="backend"><testsuite>'
            '<testcase classname="a" name="passes"/>'
            '<testcase classname="a" name="fails"><failure/></testcase>'
            '<testcase classname="a" name="errors"><error/></testcase>'
            '<testcase classname="a" name="skips"><skipped/></testcase>'
            '</testsuite></testsuite></testsuites>'
        )
        self.assertEqual(self.runner.read_junit(report), {
            "a::passes": "passed", "a::fails": "failed",
            "a::errors": "error", "a::skips": "skipped",
        })

    def test_invalid_empty_and_duplicate_reports_cannot_look_green(self):
        for xml in (
            'not xml', '<html/>', '<testsuites/>',
            '<testsuite><error>collection failed</error></testsuite>',
            '<testsuite><testcase name="same"/><testcase name="same"/></testsuite>',
        ):
            with self.subTest(xml=xml), self.assertRaises(ValueError):
                self.runner.read_junit(self.report(xml))
        with self.assertRaises(ValueError):
            self.runner.read_junit(self.directory / "missing.xml")

    def test_declared_junit_totals_cannot_hide_missing_tests_or_failures(self):
        for xml in (
            '<testsuite tests="2" failures="1"><testcase name="visible"/></testsuite>',
            '<testsuite tests="1" failures="1"><testcase name="visible"/></testsuite>',
            '<testsuite tests="1" errors="1"><testcase name="visible"/></testsuite>',
            '<testsuite tests="1" skipped="1"><testcase name="visible"/></testsuite>',
            '<testsuite tests="invalid"><testcase name="visible"/></testsuite>',
        ):
            with self.subTest(xml=xml), self.assertRaises(ValueError):
                self.runner.read_junit(self.report(xml))

    def test_compares_failures_skips_and_missing_tests_without_hiding_them(self):
        repeats = [
            {"stable": "passed", "flip": "passed", "broken": "failed",
             "skip": "skipped", "gone": "passed"},
            {"stable": "passed", "flip": "failed", "broken": "failed",
             "skip": "passed"},
        ]
        result = self.runner.compare_results(repeats)
        self.assertEqual(result["variable_tests"], {
            "flip": ["passed", "failed"], "gone": ["passed", "missing"],
            "skip": ["skipped", "passed"],
        })
        self.assertEqual(result["stable_failures"], ["broken"])
        self.assertFalse(result["consistent_collection"])

    def test_stable_passes_do_not_create_flaky_candidates(self):
        result = self.runner.compare_results([{"a": "passed"}] * 5)
        self.assertEqual(result["variable_tests"], {})
        self.assertEqual(result["stable_failures"], [])
        self.assertTrue(result["consistent_collection"])

    def test_all_skipped_suite_does_not_count_as_completed_experiment(self):
        child = self.directory / "skip.py"
        child.write_text(
            'from pathlib import Path\nimport sys\n'
            'Path(sys.argv[1]).write_text(\'<testsuite><testcase name="a">'
            '<skipped/></testcase></testsuite>\')\n', encoding="utf-8",
        )
        result = self.runner.repeat_suite(
            "skip", [sys.executable, str(child), "{report}"],
            self.directory, self.directory / "skips", 5,
        )
        self.assertFalse(result["complete"])

    def test_failed_commands_still_run_five_times_and_record_infrastructure_errors(self):
        # Real child process: fails once, then succeeds; no subprocess mock.
        child = self.directory / "child.py"
        child.write_text(
            'from pathlib import Path\nimport sys\n'
            'counter = Path(sys.argv[1])\n'
            'n = int(counter.read_text()) + 1 if counter.exists() else 1\n'
            'counter.write_text(str(n))\n'
            'xml = "<testsuite><testcase classname=\\"demo\\" name=\\"x\\">"\n'
            'xml += "<failure/>" if n == 1 else ""\n'
            'Path(sys.argv[2]).write_text(xml + "</testcase></testsuite>")\n'
            'sys.exit(1 if n == 1 else 0)\n', encoding="utf-8",
        )
        counter = self.directory / "counter"
        command = [sys.executable, str(child), str(counter), "{report}"]
        suite = self.runner.repeat_suite(
            "example", command, self.directory, self.directory / "out", 5
        )
        self.assertEqual(counter.read_text(), "5")
        self.assertEqual([r["exit_code"] for r in suite["repeats"]], [1, 0, 0, 0, 0])
        self.assertEqual(suite["variable_tests"]["demo::x"],
                         ["failed", "passed", "passed", "passed", "passed"])
        self.assertTrue(suite["complete"])

        missing_report = self.runner.repeat_suite(
            "infra", [sys.executable, "-c", "raise SystemExit(2)"],
            self.directory, self.directory / "infra", 5,
        )
        self.assertFalse(missing_report["complete"])
        self.assertEqual(len(missing_report["repeats"]), 5)
        self.assertTrue(all(r["report_error"] for r in missing_report["repeats"]))

    def test_cli_help_lists_output_option(self):
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "--help"], capture_output=True, text=True
        )
        self.assertEqual(completed.returncode, 0)
        self.assertIn("--output", completed.stdout)


if __name__ == "__main__":
    unittest.main()
