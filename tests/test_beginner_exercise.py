"""Verify the packaged beginner exercise from clean temporary working folders."""

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts/verify_beginner_exercise.py"
spec = importlib.util.spec_from_file_location("beginner_release_builder", ROOT / "scripts/build_release.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
PRACTICE = ("counter.py", "test_counter.py", "CHANGE.md")


class BeginnerExerciseTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="agentos-beginner-test-")
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name).resolve()
        self.app = self.base / "tool with spaces 简报.pyz"
        builder.build_zipapp(self.app)
        self.environment = os.environ.copy()
        self.environment.pop("PYTHONPATH", None)
        self.environment["PYTHONDONTWRITEBYTECODE"] = "1"

    def run_exercise(self, *arguments, app=None):
        result = subprocess.run(
            [sys.executable, str(RUNNER), "--app", str(app or self.app), *map(str, arguments)],
            cwd=self.base, env=self.environment, capture_output=True, text=True,
            encoding="utf-8", timeout=45, check=False,
        )
        self.assertNotIn("Traceback (most recent call last)", result.stderr)
        return result

    def source_hashes(self):
        return {
            name: hashlib.sha256((ROOT / "practice/word-counter" / name).read_bytes()).hexdigest()
            for name in PRACTICE
        }

    def test_clean_packaged_exercise_records_pass_failure_and_recovery(self):
        record = self.base / "evidence with spaces 简报.txt"
        before = self.source_hashes()
        result = self.run_exercise("--record", record)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        evidence = record.read_text(encoding="utf-8")
        self.assertEqual(evidence, result.stdout)
        self.assertEqual(before, self.source_hashes())
        self.assertNotIn(str(self.base), evidence)
        self.assertNotIn(str(ROOT), evidence)
        self.assertNotIn(sys.executable, evidence)
        self.assertIn("RESULT: PASS -> EXPECTED FAIL -> RECOVERED PASS", evidence)
        self.assertIn("Expected exit: 1; observed exit: 1", evidence)
        self.assertIn("Expected exit: 2; observed exit: 2", evidence)
        self.assertIn("Words: 4\n", evidence)
        self.assertIn("FAILED (failures=", evidence)
        self.assertIn("Simple example still works despite the counting regression", evidence)
        self.assertIn("Workspace structure check while project tests fail: still passed", evidence)
        self.assertIn("Scripted fixture setup", evidence)
        self.assertIn("Project: Fictional Word Counter", evidence)
        self.assertIn("Local evidence links: practice/word-counter/counter.py", evidence)
        self.assertIn("Scope: Fictional Word Counter / whitespace counting", evidence)
        self.assertIn("application tests failed while structure_status=passed", evidence)
        self.assertIn("application_tests=not_run", evidence)
        self.assertNotIn("Readiness:", evidence)
        # Inspect the actual checker JSON emitted immediately after failing
        # project tests, rather than inferring its scope from a summary label.
        failed_app_check = evidence.split(
            "## Workspace structure check while project tests fail: still passed (JSON)\n", 1
        )[1]
        report, _ = json.JSONDecoder().raw_decode(failed_app_check.split("stdout:\n", 1)[1])
        self.assertEqual(report["structure_status"], "passed")
        self.assertEqual(report["verification_scope"], "workspace_structure")
        self.assertEqual(report["application_tests"], "not_run")
        self.assertNotIn("readiness", report)
        self.assertIn("Workspace structure checks passed.", evidence)
        self.assertIn("counter.py.before-practice", evidence)
        self.assertIn("counter.py.practice-bad", evidence)
        self.assertIn("No human user was observed", evidence)
        baseline = next(line for line in evidence.splitlines() if line.startswith("Baseline SHA-256: "))
        before_regression = next(line for line in evidence.splitlines() if line.startswith("Before-regression SHA-256: "))
        recovered = next(line for line in evidence.splitlines() if line.startswith("Recovered SHA-256: "))
        self.assertNotEqual(baseline.split(": ")[1], before_regression.split(": ")[1])
        self.assertEqual(before_regression.split(": ")[1], recovered.split(": ")[1])
        self.assertIn("full-file restore rejected; preview only", evidence)
        self.assertIn("OPERATOR_NOTES.md and the same-file help edit are preserved", evidence)
        self.assertIn("Unrelated help edit after recovery", evidence)
        self.assertIn("Count words in your draft. Keep the whole phrase in quotes.", evidence)
        self.assertEqual({p.name for p in self.base.iterdir()}, {self.app.name, record.name})

    def test_existing_record_is_refused_and_preserved(self):
        record = self.base / "keep-existing.txt"
        record.write_bytes(b"existing user-owned fixture\n")
        result = self.run_exercise("--record", record)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("occupied", result.stderr)
        self.assertEqual(record.read_bytes(), b"existing user-owned fixture\n")
        self.assertEqual(result.stdout, "")

    def test_symlink_record_and_symlink_parent_are_refused(self):
        target = self.base / "keep-target.txt"
        target.write_bytes(b"do not change\n")
        link = self.base / "record-link.txt"
        link.symlink_to(target)
        real = self.base / "real-folder"
        real.mkdir()
        directory_link = self.base / "folder-link"
        directory_link.symlink_to(real, target_is_directory=True)
        for output in (link, directory_link / "new-record.txt"):
            with self.subTest(output=output.name):
                result = self.run_exercise("--record", output)
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertIn("Symlink", result.stderr)
        self.assertEqual(target.read_bytes(), b"do not change\n")
        self.assertEqual(list(real.iterdir()), [])

    def test_traversal_and_missing_record_parent_are_refused(self):
        for record in ("folder/../outside.txt", "missing-parent/record.txt"):
            with self.subTest(record=record):
                result = self.run_exercise("--record", record)
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertEqual(result.stdout, "")
        self.assertEqual({p.name for p in self.base.iterdir()}, {self.app.name})

    def test_missing_symlink_or_non_zipapp_inputs_are_refused(self):
        linked_app = self.base / "linked.pyz"
        linked_app.symlink_to(self.app)
        wrong_type = self.base / "package.txt"
        wrong_type.write_text("not a package", encoding="utf-8")
        for app in (self.base / "missing.pyz", linked_app, wrong_type):
            with self.subTest(app=app.name):
                result = self.run_exercise(app=app)
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertEqual(result.stdout, "")

    def test_repeated_invocations_use_fresh_copies_and_do_not_overwrite_record(self):
        before = self.source_hashes()
        for _ in range(2):
            result = self.run_exercise()
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        record = self.base / "one-record.txt"
        first = self.run_exercise("--record", record)
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        saved = record.read_bytes()
        second = self.run_exercise("--record", record)
        self.assertEqual(second.returncode, 2, second.stdout + second.stderr)
        self.assertEqual(record.read_bytes(), saved)
        self.assertEqual(before, self.source_hashes())


if __name__ == "__main__":
    unittest.main()
