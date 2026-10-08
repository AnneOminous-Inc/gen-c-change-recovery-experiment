"""Exercise the actual packaged launcher outside the source checkout."""

import importlib.util
import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile
from genc_agentos import __version__


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("agentos_build", ROOT / "scripts/build_release.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class StandaloneReleaseTests(unittest.TestCase):
    def assert_structure_report(self, output, expected_status):
        report = json.loads(output)
        self.assertEqual(report["schema_version"], 2)
        self.assertEqual(report["structure_status"], expected_status)
        self.assertEqual(report["verification_scope"], "workspace_structure")
        self.assertEqual(report["application_tests"], "not_run")
        self.assertNotIn("readiness", report)
        return report

    def test_zipapp_is_independent_and_forwards_all_exit_codes(self):
        with tempfile.TemporaryDirectory(prefix="agentos-zipapp-test-") as temporary:
            base = Path(temporary).resolve()
            app = base / "tool with spaces.pyz"
            builder.build_zipapp(app)
            with zipfile.ZipFile(app) as packaged_app:
                self.assertEqual(packaged_app.read("LICENSE"), (ROOT / "LICENSE").read_bytes())
                self.assertIn("Gen C", packaged_app.read("LICENSE").decode("utf-8"))
            environment = os.environ.copy()
            environment.pop("PYTHONPATH", None)
            environment["PYTHONDONTWRITEBYTECODE"] = "1"

            def run(*args, expected=0):
                result = subprocess.run(
                    [sys.executable, str(app), *map(str, args)],
                    cwd=base, env=environment, capture_output=True, text=True,
                    timeout=15,
                )
                self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
                self.assertNotIn("Traceback", result.stderr)
                return result.stdout

            self.assertIn(__version__, run("--version"))
            demo = base / "demo 简报"
            run("init", "--dest", demo, "--demo", "--dry-run")
            self.assertFalse(demo.exists())
            run("init", "--dest", demo, "--demo")
            first = run("check", "--dest", demo, "--json")
            self.assert_structure_report(first, "passed")
            self.assertEqual(first, run("check", "--dest", demo, "--json"))
            before = {p.relative_to(demo): p.read_bytes() for p in demo.rglob("*") if p.is_file()}
            run("init", "--dest", demo, expected=2)
            self.assertEqual(before, {p.relative_to(demo): p.read_bytes() for p in demo.rglob("*") if p.is_file()})
            default = base / "default"
            run("init", "--dest", default)
            self.assert_structure_report(
                run("check", "--dest", default, "--json", expected=1), "needs_attention"
            )
            (demo / "agentos.json").write_text("{", encoding="utf-8")
            self.assert_structure_report(
                run("check", "--dest", demo, "--json", expected=2), "invalid"
            )

    def test_public_zip_contains_only_allowlisted_deliverables_and_license(self):
        excluded = (
            "PUBLIC_REPOSITORY_PLAN.md", "PUBLIC_RELEASE_READINESS.md",
            "MIT_NOTICE_DRAFT.txt", "PUBLICATION_RECEIPT.md", "RELEASE_RECEIPT.md",
            "private-planning/notes.md", "releases/old/README.md",
        )
        self.assertIn("LICENSE", builder.RELEASE_FILES)
        for filename in excluded:
            self.assertNotIn(filename, builder.RELEASE_FILES)
        with tempfile.TemporaryDirectory(prefix="agentos-public-release-test-") as temporary:
            stage = Path(temporary).resolve()
            # Stage explicit files only. The builder never writes to the checkout
            # and never packages the intentionally unrelated fixture records.
            for filename in builder.RELEASE_FILES:
                target = stage / filename
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((ROOT / filename).read_bytes())
            for filename in excluded:
                target = stage / filename
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("Private fixture; must not be distributed.\n", encoding="utf-8")
            with patch.object(builder, "ROOT", stage), contextlib.redirect_stdout(io.StringIO()):
                builder.main()
            app_name = "genc-agentos-" + __version__ + ".pyz"
            archive_name = "genc-agentos-" + __version__ + ".zip"
            archive = stage / "dist" / archive_name
            self.assertTrue(archive.is_file())
            self.assertFalse((stage / "dist" / ("genc-agentos-" + __version__ + "-private.zip")).exists())
            expected = set(builder.RELEASE_FILES) | {app_name}
            expected.update("demo/" + name for name in builder.build_files(
                "Pocket Field Notes", "Demo Operator", True
            ))
            with zipfile.ZipFile(archive) as release:
                self.assertEqual(set(release.namelist()), expected)
                self.assertEqual(len(release.namelist()), len(expected), "No duplicate archive entries")
                self.assertEqual(release.read("LICENSE"), (ROOT / "LICENSE").read_bytes())
                self.assertIn("Gen C", release.read("LICENSE").decode("utf-8"))
                for filename in excluded:
                    self.assertNotIn(filename, release.namelist())
                for filename in release.namelist():
                    self.assertFalse(filename.startswith(("/", "releases/", "private-planning/")))
                    self.assertNotIn("..", Path(filename).parts)
            with zipfile.ZipFile(stage / "dist" / app_name) as packaged_app:
                self.assertEqual(packaged_app.read("LICENSE"), (ROOT / "LICENSE").read_bytes())


if __name__ == "__main__":
    unittest.main()
