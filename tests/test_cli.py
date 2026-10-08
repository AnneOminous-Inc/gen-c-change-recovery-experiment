"""Acceptance tests for the bounded, offline AgentOS CLI.

Every mutation is confined to a temporary fixture. These tests never remove
an existing user workspace, fetch evidence URLs, or use credentials.
"""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from genc_agentos import __version__


REPO = Path(__file__).resolve().parents[1]


class AgentOSCLITests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="agentos-test-")
        self.addCleanup(self.temporary.cleanup)
        # macOS /var and /tmp can be system aliases. Test the real directory.
        self.base = Path(self.temporary.name).resolve()
        self.workspace = self.base / "workspace"

    def cli(self, *args):
        environment = os.environ.copy()
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        result = subprocess.run(
            [sys.executable, "-m", "genc_agentos", *map(str, args)],
            cwd=REPO,
            env=environment,
            text=True,
            capture_output=True,
            timeout=15,
            check=False,
        )
        self.assertNotIn("Traceback (most recent call last)", result.stdout)
        self.assertNotIn("Traceback (most recent call last)", result.stderr)
        return result

    def init(self, destination=None, demo=True):
        destination = destination or self.workspace
        arguments = ["init", "--dest", destination]
        if demo:
            arguments.append("--demo")
        result = self.cli(*arguments)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return destination

    def report(self, destination=None):
        result = self.cli("check", "--dest", destination or self.workspace, "--json")
        try:
            report = json.loads(result.stdout)
        except json.JSONDecodeError as error:
            self.fail("check --json did not emit JSON: {}\n{}\n{}".format(
                error, result.stdout, result.stderr
            ))
        self.assertEqual(report["schema_version"], 2)
        self.assertIn(report["structure_status"], ("passed", "needs_attention", "invalid"))
        self.assertEqual(report["verification_scope"], "workspace_structure")
        self.assertEqual(report["application_tests"], "not_run")
        self.assertNotIn("readiness", report,
                         "A structure check must not claim application readiness")
        self.assertIsInstance(report["checks"], list)
        self.assertIsInstance(report["issues"], list)
        for issue in report["issues"]:
            self.assertIn(issue["severity"], ("warning", "error"))
            self.assertIsInstance(issue["location"], str)
            self.assertIsInstance(issue["message"], str)
        self.assertNotIn(str(self.base), result.stdout,
                         "Report must not disclose machine-specific absolute paths")
        return result, report

    def invalid(self, destination=None):
        result, report = self.report(destination)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertEqual(report["structure_status"], "invalid")
        self.assertTrue(any(issue["severity"] == "error" for issue in report["issues"]))
        return report

    def read_json(self, name):
        return json.loads((self.workspace / name).read_text(encoding="utf-8"))

    def write_json(self, name, value):
        (self.workspace / name).write_text(
            json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    def snapshot(self, root):
        return {
            path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(root.rglob("*")) if path.is_file()
        }

    def test_version_and_required_destination(self):
        result = self.cli("--version")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(__version__, result.stdout)
        for command in ("init", "check"):
            with self.subTest(command=command):
                result = self.cli(command)
                self.assertEqual(result.returncode, 2)
                self.assertIn("dest", result.stderr.lower() + result.stdout.lower())

    def test_empty_or_control_character_destination_is_rejected(self):
        for value in ("", "bad\npath", "bad\x1bpath"):
            for command in ("init", "check"):
                with self.subTest(value=repr(value), command=command):
                    result = self.cli(command, "--dest", value)
                    self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                    self.assertIn("destination", result.stderr.lower())

    def test_fictional_demo_passes_structure_checks_and_report_states_scope(self):
        self.init()
        result, report = self.report()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(report["structure_status"], "passed")
        self.assertTrue(report["project"])
        self.assertTrue(report["owner"])
        self.assertTrue(report["checks"])
        human = self.cli("check", "--dest", self.workspace)
        self.assertEqual(human.returncode, 0, human.stdout + human.stderr)
        for word in ("AgentOS", "check"):
            self.assertIn(word.lower(), human.stdout.lower())
        self.assertIn("Workspace structure checks passed.", human.stdout)
        self.assertIn("application tests: not run", human.stdout.lower())
        self.assertNotRegex(human.stdout, r"(?i)\bready\b")

    def test_default_templates_have_actionable_structure_gaps(self):
        self.init(demo=False)
        result, report = self.report()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(report["structure_status"], "needs_attention")
        self.assertTrue(report["issues"])
        self.assertFalse(any(issue["severity"] == "error" for issue in report["issues"]))

    def test_occupied_directory_refuses_init_and_preserves_data(self):
        self.workspace.mkdir()
        sentinel = self.workspace / "keep-me.txt"
        sentinel.write_bytes(b"user-owned fixture\n")
        before = self.snapshot(self.workspace)
        for option in ([], ["--dry-run"]):
            with self.subTest(option=option):
                result = self.cli("init", "--dest", self.workspace, *option)
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertEqual(self.snapshot(self.workspace), before)
        self.assertEqual(sentinel.read_bytes(), b"user-owned fixture\n")

    def test_repeated_init_refuses_and_repeated_check_is_read_only(self):
        self.init()
        before = self.snapshot(self.workspace)
        first, first_report = self.report()
        second, second_report = self.report()
        self.assertEqual(first.returncode, 0)
        self.assertEqual(first.stdout, second.stdout)
        self.assertEqual(first_report, second_report)
        result = self.cli("init", "--dest", self.workspace, "--demo")
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertEqual(self.snapshot(self.workspace), before)

    def test_dry_run_creates_neither_destination_nor_files(self):
        result = self.cli("init", "--dest", self.workspace, "--demo", "--dry-run")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse(self.workspace.exists())
        self.assertIn("agentos.json", result.stdout)
        self.workspace.mkdir()
        result = self.cli("init", "--dest", self.workspace, "--dry-run")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(list(self.workspace.iterdir()), [])

    def test_empty_directory_and_relative_unicode_destination(self):
        destination = self.base / "solo operator 简报"
        destination.mkdir()
        # Use a fixture cwd so relative input needs no forbidden traversal.
        environment = os.environ.copy()
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        environment["PYTHONPATH"] = str(REPO)
        result = subprocess.run(
            [sys.executable, "-m", "genc_agentos", "init", "--dest", destination.name,
             "--project", "Tiny project 简报", "--owner", "Solo operator", "--demo"],
            cwd=self.base, env=environment, text=True, capture_output=True,
            timeout=15, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        result, report = self.report(destination)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(report["project"], "Tiny project 简报")
        self.assertEqual(report["owner"], "Solo operator")

    def test_missing_or_file_parent_is_rejected_without_writes(self):
        for destination in (self.base / "missing-parent" / "kit",):
            with self.subTest(destination=destination.name):
                result = self.cli("init", "--dest", destination)
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertFalse(destination.parent.exists())
        parent_file = self.base / "parent-file"
        parent_file.write_text("fixture", encoding="utf-8")
        result = self.cli("init", "--dest", parent_file / "kit")
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertEqual(parent_file.read_text(encoding="utf-8"), "fixture")

    def test_destination_lexical_traversal_is_rejected(self):
        container = self.base / "container"
        container.mkdir()
        traversing = str(container) + "/../workspace"
        for command in ("init", "check"):
            with self.subTest(command=command):
                result = self.cli(command, "--dest", traversing)
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertFalse(self.workspace.exists())

    def test_symlink_destination_and_ancestor_are_rejected(self):
        real = self.base / "real"
        real.mkdir()
        link = self.base / "alias"
        link.symlink_to(real, target_is_directory=True)
        for destination in (link, link / "nested"):
            for command in ("init", "check"):
                with self.subTest(destination=destination.name, command=command):
                    result = self.cli(command, "--dest", destination)
                    self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertEqual(list(real.iterdir()), [])
        broken = self.base / "broken"
        broken.symlink_to(self.base / "absent", target_is_directory=True)
        result = self.cli("init", "--dest", broken)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertFalse((self.base / "absent").exists())

    def test_malformed_and_duplicate_json_config_are_rejected(self):
        self.init()
        path = self.workspace / "agentos.json"
        original = path.read_text(encoding="utf-8")
        malformed = ("{", "[]", "null", '{"schema_version": 1, "schema_version": 1}')
        for raw in malformed:
            with self.subTest(raw=raw):
                path.write_text(raw, encoding="utf-8")
                self.invalid()
        config = json.loads(original)
        raw = original.replace('"brief":', '"brief": "BRIEF.md", "brief":', 1)
        path.write_text(raw, encoding="utf-8")
        self.invalid()
        path.write_text(original, encoding="utf-8")
        config["unexpected"] = True
        self.write_json("agentos.json", config)
        self.invalid()

    def test_managed_document_paths_must_be_portable_and_unique(self):
        self.init()
        original = self.read_json("agentos.json")
        rejected = (
            "/outside.md", "../outside.md", "docs/../BRIEF.md", "docs/./brief.md",
            "docs//brief.md", "C:/brief.md", "C:\\brief.md", "docs\\brief.md",
            "brief:stream.md", "docs/brief.md.", "docs/brief.md ", "CON.md",
            "docs/aux.txt", "COM1.md", "LPT9.txt", "docs/brief\x00.md",
            "docs/brief\n.md", "", ".", "docs/",
        )
        for value in rejected:
            with self.subTest(path=repr(value)):
                config = json.loads(json.dumps(original))
                config["documents"]["brief"] = value
                self.write_json("agentos.json", config)
                self.invalid()
        config = json.loads(json.dumps(original))
        config["documents"]["brief"] = config["documents"]["handoff"]
        self.write_json("agentos.json", config)
        self.invalid()

    def test_config_types_missing_fields_and_schema_version_are_rejected(self):
        self.init()
        original = self.read_json("agentos.json")
        changes = (
            ("schema_version", True), ("schema_version", 2),
            ("kit_version", ""), ("kit_version", 123),
            ("project", ""), ("project", []),
            ("owner", "   "), ("owner", None), ("documents", []),
        )
        for field, value in changes:
            with self.subTest(field=field, value=value):
                config = json.loads(json.dumps(original))
                config[field] = value
                self.write_json("agentos.json", config)
                self.invalid()
        for field in ("project", "owner", "documents"):
            with self.subTest(missing=field):
                config = json.loads(json.dumps(original))
                del config[field]
                self.write_json("agentos.json", config)
                self.invalid()

    def test_nested_space_and_unicode_document_path_is_supported(self):
        self.init()
        config = self.read_json("agentos.json")
        original = self.workspace / config["documents"]["brief"]
        moved = self.workspace / "project notes" / "简报.md"
        moved.parent.mkdir()
        # Demo action evidence still references the original brief.
        moved.write_bytes(original.read_bytes())
        config["documents"]["brief"] = moved.relative_to(self.workspace).as_posix()
        self.write_json("agentos.json", config)
        result, report = self.report()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(report["structure_status"], "passed")

    def test_document_symlink_is_rejected_even_if_target_is_inside_workspace(self):
        self.init()
        config = self.read_json("agentos.json")
        brief = self.workspace / config["documents"]["brief"]
        real = self.workspace / "real-brief.md"
        brief.rename(real)
        brief.symlink_to(real.name)
        self.invalid()

    def test_document_symlink_ancestor_is_rejected(self):
        self.init()
        alias = self.workspace / "linked-documents"
        alias.symlink_to(self.workspace, target_is_directory=True)
        config = self.read_json("agentos.json")
        config["documents"]["brief"] = "linked-documents/BRIEF.md"
        self.write_json("agentos.json", config)
        self.invalid()

    def test_config_symlink_and_nonregular_document_are_rejected(self):
        self.init()
        config = self.workspace / "agentos.json"
        saved = self.workspace / "saved-config.json"
        config.rename(saved)
        config.symlink_to(saved.name)
        self.invalid()
        config.unlink()
        saved.rename(config)
        brief = self.workspace / self.read_json("agentos.json")["documents"]["brief"]
        brief.unlink()
        brief.mkdir()
        self.invalid()

    def test_missing_evidence_is_an_error_and_empty_evidence_is_a_warning(self):
        self.init()
        actions = self.read_json("ACTIONS.json")
        actions[0]["evidence"] = ["evidence/missing.md"]
        self.write_json("ACTIONS.json", actions)
        self.invalid()
        actions[0]["evidence"] = []
        self.write_json("ACTIONS.json", actions)
        result, report = self.report()
        self.assertNotEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertTrue(any(issue["severity"] == "warning" for issue in report["issues"]))

    def test_nonregular_evidence_is_rejected(self):
        self.init()
        actions = self.read_json("ACTIONS.json")
        actions[0]["evidence"] = ["evidence"]
        self.write_json("ACTIONS.json", actions)
        self.invalid()

    def test_evidence_path_boundaries_and_unsafe_urls_are_rejected(self):
        self.init()
        actions = self.read_json("ACTIONS.json")
        rejected = (
            "../outside.md", "/outside.md", "C:/outside.md", "evidence\\SMOKE.md",
            "evidence/../BRIEF.md", "evidence//SMOKE.md", "CON.md",
            "http://example.invalid/evidence", "https://user:password@example.invalid/evidence",
            "file:///outside.md",
        )
        for value in rejected:
            with self.subTest(evidence=value):
                actions[0]["evidence"] = [value]
                self.write_json("ACTIONS.json", actions)
                self.invalid()

    def test_evidence_symlink_and_symlink_ancestor_are_rejected(self):
        self.init()
        outside = self.base / "fixture-evidence.md"
        outside.write_text("fixture only", encoding="utf-8")
        link = self.workspace / "evidence" / "linked.md"
        link.symlink_to(outside)
        actions = self.read_json("ACTIONS.json")
        actions[0]["evidence"] = ["evidence/linked.md"]
        self.write_json("ACTIONS.json", actions)
        self.invalid()
        ancestor = self.workspace / "linked-directory"
        ancestor.symlink_to(self.base, target_is_directory=True)
        actions[0]["evidence"] = ["linked-directory/fixture-evidence.md"]
        self.write_json("ACTIONS.json", actions)
        self.invalid()
        self.assertEqual(outside.read_text(encoding="utf-8"), "fixture only")

    def test_evidence_fragment_and_https_reference_are_handled_without_fetch(self):
        self.init()
        actions = self.read_json("ACTIONS.json")
        actions[0]["evidence"] = ["evidence/SMOKE.md#result", "https://example.invalid/proof"]
        self.write_json("ACTIONS.json", actions)
        result, report = self.report()
        self.assertNotEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertTrue(any(issue["severity"] == "warning" for issue in report["issues"]))

    def test_unrelated_symlink_is_ignored(self):
        self.init()
        (self.workspace / "unrelated").symlink_to(self.base / "absent")
        result, report = self.report()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(report["structure_status"], "passed")

    def test_duplicate_json_register_keys_and_invalid_records_are_rejected(self):
        self.init()
        path = self.workspace / "ACTIONS.json"
        original = path.read_text(encoding="utf-8")
        path.write_text('[{"id":"a", "id":"b"}]', encoding="utf-8")
        self.invalid()
        path.write_text(original, encoding="utf-8")
        actions = self.read_json("ACTIONS.json")
        actions[0]["status"] = "unknown"
        self.write_json("ACTIONS.json", actions)
        self.invalid()
        actions[0]["status"] = "open"
        actions.append(dict(actions[0]))
        self.write_json("ACTIONS.json", actions)
        self.invalid()

    def test_no_next_action_or_decision_is_a_structure_gap(self):
        self.init()
        actions = self.read_json("ACTIONS.json")
        for action in actions:
            action["status"] = "done"
        self.write_json("ACTIONS.json", actions)
        self.write_json("DECISIONS.json", [])
        result, report = self.report()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(report["structure_status"], "needs_attention")
        self.assertFalse(any(issue["severity"] == "error" for issue in report["issues"]))

    def test_register_roots_must_be_arrays(self):
        self.init()
        for filename in ("ACTIONS.json", "DECISIONS.json", "CORRECTIONS.json"):
            original = (self.workspace / filename).read_text(encoding="utf-8")
            for value in (None, {}, "records", True, 1):
                with self.subTest(filename=filename, value=value):
                    self.write_json(filename, value)
                    self.invalid()
            (self.workspace / filename).write_text(original, encoding="utf-8")

    def correction(self, record_id, scope="handoff", status="active", supersedes=None,
                   superseded_by=None):
        return {
            "id": record_id, "scope": scope, "original": "Old instruction",
            "correction": "Use the reviewed instruction", "reason": "Fictional fixture",
            "evidence": ["evidence/SMOKE.md"], "status": status,
            "supersedes": supersedes, "superseded_by": superseded_by,
        }

    def test_empty_corrections_and_valid_reciprocal_supersession_pass_structure_checks(self):
        self.init()
        self.write_json("CORRECTIONS.json", [])
        result, _ = self.report()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        records = [self.correction("c1", status="superseded", superseded_by="c2"),
                   self.correction("c2", supersedes="c1")]
        self.write_json("CORRECTIONS.json", records)
        result, _ = self.report()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_correction_scope_mismatch_nonreciprocal_and_active_successor_rejected(self):
        self.init()
        fixtures = [
            [self.correction("c1", status="superseded", superseded_by="c2"),
             self.correction("c2", scope="other-scope", supersedes="c1")],
            [self.correction("c1", status="superseded", superseded_by="c2"),
             self.correction("c2")],
            [self.correction("c1", superseded_by="c2"),
             self.correction("c2", supersedes="c1")],
            [self.correction("c1", supersedes="missing")],
        ]
        for records in fixtures:
            with self.subTest(records=records):
                self.write_json("CORRECTIONS.json", records)
                self.invalid()

    def test_correction_cycle_is_rejected(self):
        self.init()
        records = [
            self.correction("c1", status="superseded", supersedes="c3", superseded_by="c2"),
            self.correction("c2", status="superseded", supersedes="c1", superseded_by="c3"),
            self.correction("c3", status="superseded", supersedes="c2", superseded_by="c1"),
        ]
        self.write_json("CORRECTIONS.json", records)
        self.invalid()

    def test_bounded_file_reads_reject_oversized_config_and_markdown(self):
        self.init()
        path = self.workspace / "agentos.json"
        original = path.read_bytes()
        path.write_bytes(b" " * (1024 * 1024 + 1))
        self.invalid()
        path.write_bytes(original)
        brief = self.workspace / self.read_json("agentos.json")["documents"]["brief"]
        brief.write_bytes(b"x" * (1024 * 1024 + 1))
        self.invalid()

    def test_invalid_utf8_is_a_clear_error(self):
        self.init()
        brief = self.workspace / self.read_json("agentos.json")["documents"]["brief"]
        brief.write_bytes(b"\xff\xfe")
        self.invalid()


if __name__ == "__main__":
    unittest.main()
