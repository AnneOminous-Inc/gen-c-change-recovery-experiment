"""Run one bounded, fictional change/verify/recover exercise offline.

Only allowlisted practice files and the explicitly supplied trusted zipapp are
copied. All practice edits happen in a fresh temporary directory. An optional
transcript is the only persistent output; it must name a new regular file.
This is scripted verification, not evidence of a beginner's comprehension.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import stat
import subprocess
import sys
import tempfile
import unicodedata


ROOT = Path(__file__).resolve().parents[1]
PRACTICE_FILES = (
    "practice/word-counter/counter.py",
    "practice/word-counter/test_counter.py",
    "practice/word-counter/CHANGE.md",
)
RECORD_FILES = (
    "agentos.json", "BRIEF.md", "ACTIONS.json", "DECISIONS.json",
    "CORRECTIONS.json", "HANDOFF.md", "RECOVERY.md", "evidence/SMOKE.md",
)
GOOD_LINE = b"return len(text.split())"
BAD_LINE = b'return len(text.split(" "))'
OLD_HELP = b"Count words separated by whitespace. Put your text in quotes."
NEW_HELP = b"Count words in your draft. Keep the whole phrase in quotes."
OPERATOR_NOTE = b"Fictional operator note: keep the revised help text during recovery.\n"
SAMPLE = "Small steps make progress"


class ExerciseError(Exception):
    """An observed acceptance failure, with a portable explanation."""


class InputError(Exception):
    """An input boundary that needs the caller's attention."""


def no_symlinks(path):
    for part in list(reversed(path.parents)) + [path]:
        try:
            mode = part.lstat().st_mode
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(mode):
            raise InputError("Symlink boundary refused; use the physical directory path.")


def explicit_path(value):
    if not value or any(unicodedata.category(c) in ("Cc", "Cs") for c in value):
        raise InputError("Use a nonempty path without control characters.")
    raw = Path(value)
    if ".." in raw.parts:
        raise InputError("Path traversal ('..') is refused.")
    path = Path(os.path.abspath(str(raw)))
    no_symlinks(path)
    return path


def regular_file(path, label):
    no_symlinks(path)
    try:
        mode = path.lstat().st_mode
    except FileNotFoundError:
        raise InputError(label + " is missing.")
    if not stat.S_ISREG(mode):
        raise InputError(label + " must be a regular file.")


def prepare_inputs(app_value, record_value):
    app = explicit_path(app_value)
    regular_file(app, "Packaged app")
    if app.suffix != ".pyz":
        raise InputError("--app must name the trusted packaged .pyz file.")
    for relative in PRACTICE_FILES:
        regular_file(ROOT / relative, "Allowlisted practice file " + relative)
    if record_value is None:
        return app, None
    record = explicit_path(record_value)
    if not record.parent.is_dir():
        raise InputError("Record parent must already exist as a real directory.")
    if record.exists():
        raise InputError("Record destination is occupied; choose a new file (no overwrite).")
    return app, record


def reserve_record(path):
    """Exclusive creation also protects against a competing final-file write."""
    if path is None:
        return None
    no_symlinks(path)
    try:
        descriptor = os.open(
            str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL
            | getattr(os, "O_NOFOLLOW", 0), 0o600,
        )
    except FileExistsError:
        raise InputError("Record destination is occupied; choose a new file (no overwrite).")
    return os.fdopen(descriptor, "w", encoding="utf-8", newline="\n")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def snapshot(root):
    return {
        path.relative_to(root).as_posix(): digest(path.read_bytes())
        for path in sorted(root.rglob("*")) if path.is_file()
    }


def sanitize(text, base):
    # A subprocess can render paths plainly or as escaped JSON/repr text.
    # Replace longest variants first, retaining the command's actual output.
    variants = set()
    for actual, portable in ((str(base), "."), (str(ROOT), "<release>"),
                             (sys.executable, "python3")):
        for value in (actual, json.dumps(actual)[1:-1],
                      json.dumps(actual, ensure_ascii=False)[1:-1],
                      repr(actual)[1:-1]):
            variants.add((value, portable))
    for actual, portable in sorted(variants, key=lambda pair: len(pair[0]), reverse=True):
        text = text.replace(actual, portable)
    return "".join(
        c if unicodedata.category(c) not in ("Cc", "Cs") or c in "\n\t"
        else "\\u%04x" % ord(c) for c in text
    )


def prepare_word_counter_fixture(records, transcript):
    """Make the checker comparison about the actual copied project.

    These are scripted fixture edits to existing records, not a new template
    mode or an observed beginner filling out a project brief.
    """
    for relative in PRACTICE_FILES:
        target = records / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as handle:
            handle.write((ROOT / relative).read_bytes())
    config_path = records / "agentos.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["project"] = "Fictional Word Counter"
    config["owner"] = "Practice Operator"
    scope = "Fictional Word Counter / whitespace counting"
    links = list(PRACTICE_FILES)
    actions = [{
        "id": "A-001", "owner": config["owner"], "scope": scope,
        "next_action": "Explain the synthetic counting change, run tests, and repair only its faulty return line while preserving unrelated edits.",
        "status": "open", "evidence": links,
    }]
    decisions = [{
        "id": "D-001", "scope": scope,
        "decision": "Use split() so each run of whitespace separates words; punctuation stays in each whitespace-delimited word.",
        "reason": "This makes empty input, repeated spaces, tabs and newlines match the small project's documented rule.",
        "evidence": links,
    }]
    corrections = [{
        "id": "C-001", "scope": scope,
        "original": "Count groups separated only by a literal space.",
        "correction": "Use all whitespace as word separators.",
        "reason": "The scripted practice covers empty input, repeated spaces, tabs and newlines.",
        "evidence": links, "status": "superseded", "supersedes": None,
        "superseded_by": "C-002",
    }, {
        "id": "C-002", "scope": scope,
        "original": "Use all whitespace as word separators.",
        "correction": "Use split(), verify the documented cases, and repair only the known faulty line while preserving unrelated edits.",
        "reason": "Restoring an entire baseline file could erase a later intentional help-text edit.",
        "evidence": links, "status": "active", "supersedes": "C-001",
        "superseded_by": None,
    }]
    documents = {
        "BRIEF.md": """# Fictional Word Counter brief

This is scripted fixture setup, not evidence that a human beginner completed it.

## Outcome
Run one understandable local command that counts whitespace-delimited words.

## In scope
The copied counter.py, its seven unittest cases and one synthetic return-line
mistake. Preserve an intentional same-file help edit and separate operator note.

## Out of scope
Accounts, dependencies, network access, databases, deployment and outside edits.

## Acceptance
The example prints Words: 4. Project tests pass, fail on the synthetic mistake,
and pass after limited recovery. Unrelated help text and operator notes remain.
Passing workspace structure checks verifies records and references only.
The checker's application_tests value remains not_run; it does not run tests.

## Permissions
The scripted runner may edit only its fresh temporary fixture. It must preserve
the source release and existing user files. No public release is authorized.
""",
        "HANDOFF.md": """# Fictional Word Counter handoff

## Current state
Original runnable exercise files are copied into this managed fixture. Results
come from the actual commands in the runner transcript, not these statements.
This setup does not represent an observed human beginner completing the task.

## Next action
Practice Operator owns A-001: explain the one-line counting change, run the
counter and its tests, then repair only the known faulty line after practice.

## Boundaries
Scope is Fictional Word Counter / whitespace counting. Preserve the same-file
help edit and separate operator notes. C-002 is active; C-001 is superseded.
All writes stay in this temporary fixture; no accounts, deployment or deletion
of outside data is part of this exercise.

## Resume checklist
1. Read BRIEF.md, A-001, D-001 and C-002.
2. Read practice/word-counter/CHANGE.md and inspect the copied source.
3. Run the example and python3 -m unittest -v from practice/word-counter.
4. Compare a repair's scope and rerun the same checks.
""",
        "evidence/SMOKE.md": """# Scripted word-counter fixture evidence index

The original exercise code is practice/word-counter/counter.py. Its executable
behavior examples are practice/word-counter/test_counter.py. The change intent
and scope are practice/word-counter/CHANGE.md. Actual observed commands, exits
and hashes are retained in the runner transcript. These records alone do not
prove the code works and do not record a human user's success.
""",
    }
    for relative, value in (("agentos.json", config), ("ACTIONS.json", actions),
                            ("DECISIONS.json", decisions), ("CORRECTIONS.json", corrections)):
        (records / relative).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for relative, content in documents.items():
        (records / relative).write_text(content, encoding="utf-8")
    transcript.extend([
        "\n## Scripted fixture setup: scope the existing records to the actual project",
        "Copied the three allowlisted practice files inside the managed workspace.",
        "Updated existing config, brief, action, decision, correction, handoff and evidence records.",
        "Project: Fictional Word Counter; owner: Practice Operator.",
        "Scope: " + scope,
        "Local evidence links: " + ", ".join(links),
        "This setup is scripted; no human beginner completed these records.",
        "The packaged --demo remains the fictional notes example; no template mode was added.",
    ])


def run_exercise(app, transcript):
    with tempfile.TemporaryDirectory(prefix="agentos-beginner-") as temporary:
        base = Path(temporary).resolve()
        copied_app = base / "genc-agentos.pyz"
        copied_app.write_bytes(app.read_bytes())
        environment = os.environ.copy()
        environment.pop("PYTHONPATH", None)
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        environment["PYTHONIOENCODING"] = "utf-8"

        def require(condition, explanation):
            if not condition:
                raise ExerciseError(explanation)

        def command(label, arguments, expected, cwd="."):
            transcript.append("\n## " + label)
            transcript.append("Working directory: " + cwd)
            transcript.append("$ " + shlex.join(["python3"] + list(arguments)))
            try:
                result = subprocess.run(
                    [sys.executable] + list(arguments), cwd=base / cwd,
                    env=environment, capture_output=True, text=True,
                    encoding="utf-8", timeout=15, check=False,
                )
            except subprocess.TimeoutExpired:
                raise ExerciseError(label + " exceeded the 15-second local command limit.")
            transcript.append("Expected exit: %s; observed exit: %s" % (expected, result.returncode))
            for name, output in (("stdout", result.stdout), ("stderr", result.stderr)):
                transcript.append(name + ":")
                transcript.append(sanitize(output, base).rstrip("\n") or "(empty)")
            require(result.returncode == expected, label + " returned an unexpected exit status.")
            require("Traceback (most recent call last)" not in result.stdout,
                    label + " emitted an unexpected stdout traceback.")
            return result

        dest = "records demo 简报"
        init_args = [copied_app.name, "init", "--dest", dest, "--demo"]
        before_dry_run = snapshot(base)
        command("Dry run: inspect the scaffold before writing", init_args + ["--dry-run"], 0)
        require(not (base / dest).exists(), "Dry run created the destination.")
        require(snapshot(base) == before_dry_run, "Dry run changed temporary contents.")
        transcript.append("Verified: dry run wrote no files.")
        command("Create fictional records", init_args, 0)
        records = base / dest
        require(records.is_dir(), "Init did not create the records workspace.")
        prepare_word_counter_fixture(records, transcript)
        records_before = snapshot(records)
        record_document_hashes = {name: digest((records / name).read_bytes()) for name in RECORD_FILES}
        command("Repeated init: occupied destination is refused", init_args, 2)
        require(snapshot(records) == records_before, "Repeated init changed existing records.")
        transcript.append("Verified: occupied directory contents are unchanged.")

        def structure_check(label):
            before_check = snapshot(records)
            result = command(label, [copied_app.name, "check", "--dest", dest], 0)
            require("Workspace structure checks passed." in result.stdout,
                    "Check output did not explicitly report workspace structure checks passed.")
            require("Readiness:" not in result.stdout,
                    "Check output used the old application-readiness framing.")
            machine = command(label + " (JSON)",
                              [copied_app.name, "check", "--dest", dest, "--json"], 0)
            try:
                report = json.loads(machine.stdout)
            except json.JSONDecodeError:
                raise ExerciseError("Records JSON output was malformed.")
            require(report.get("structure_status") == "passed",
                    "Records JSON did not report structure_status=passed.")
            require(report.get("verification_scope") == "workspace_structure",
                    "Records JSON did not limit verification_scope to workspace_structure.")
            require(report.get("application_tests") == "not_run",
                    "Records JSON incorrectly implied the checker ran application tests.")
            require("readiness" not in report,
                    "Records JSON retained the misleading readiness field.")
            require(report.get("project") == "Fictional Word Counter", "Records described the wrong project.")
            require(snapshot(records) == before_check, "Read-only records check changed fixture files.")
            require({name: digest((records / name).read_bytes()) for name in RECORD_FILES} == record_document_hashes,
                    "Existing project records changed during the code exercise.")
            return result.stdout, machine.stdout

        first_check = structure_check("Baseline workspace structure check: passed")
        second_check = structure_check("Repeated workspace structure check is read only")
        require(first_check == second_check, "Repeated records checks were not idempotent.")
        practice = (Path(dest) / "practice/word-counter").as_posix()

        def working_counter(label):
            result = command(label, ["counter.py", SAMPLE], 0, cwd=practice)
            require(result.stdout == "Words: 4\n", "Counter did not produce exactly 'Words: 4'.")
            require(result.stderr == "", "Working counter emitted unexpected stderr.")

        def project_tests(label, expected):
            result = command(label, ["-m", "unittest", "-v"], expected, cwd=practice)
            combined = result.stdout + result.stderr
            if expected == 0:
                require("\nOK\n" in combined, "Project tests did not confirm OK.")
            else:
                require("FAILED (failures=" in combined and "AssertionError" in combined,
                        "Deliberate mistake did not cause the expected assertion failures.")
            return result

        working_counter("Working result before the change")
        project_tests("Project tests before the change: PASS", 0)
        counter = base / practice / "counter.py"
        original = counter.read_bytes()
        require(original.count(GOOD_LINE) == 1,
                "Expected exactly one original count_words return line; no change made.")
        require(original.count(OLD_HELP) == 1,
                "Expected exactly one original help description; no change made.")
        backup = counter.with_name("counter.py.before-practice")
        with backup.open("xb") as handle:
            handle.write(original)
        require(backup.read_bytes() == original, "Practice backup did not match exact baseline bytes.")
        before_regression = original.replace(OLD_HELP, NEW_HELP, 1)
        counter.write_bytes(before_regression)
        operator_notes = counter.with_name("OPERATOR_NOTES.md")
        with operator_notes.open("xb") as handle:
            handle.write(OPERATOR_NOTE)
        require(counter.read_bytes() == before_regression, "Unrelated help edit was not recorded exactly.")
        help_before = command("Unrelated help edit before the regression", ["counter.py", "--help"], 0, cwd=practice)
        require(NEW_HELP.decode("utf-8") in help_before.stdout,
                "The intentional help-text edit did not appear in --help.")
        transcript.extend([
            "\n## Explain the one-line practice change before applying it",
            "Original: return len(text.split())",
            'Practice-only mistake: return len(text.split(" "))',
            "split() separates all whitespace and ignores empty groups. split(\" \")",
            "separates only literal spaces and counts empty groups. Repeated spaces,",
            "empty text, tabs and newlines can now produce the wrong count.",
            "Backup: practice/word-counter/counter.py.before-practice (exclusive creation).",
            "Baseline SHA-256: " + digest(original),
            "Before-regression SHA-256: " + digest(before_regression),
            "Unrelated same-file edit: the help description now refers to a draft.",
            "Separate sentinel: practice/word-counter/OPERATOR_NOTES.md (exclusive creation).",
            "Operator-notes SHA-256: " + digest(OPERATOR_NOTE),
        ])
        failed = before_regression.replace(GOOD_LINE, BAD_LINE, 1)
        counter.write_bytes(failed)
        transcript.append("Practice-mistake SHA-256: " + digest(failed))
        working_counter("Simple example still works despite the counting regression")
        transcript.append("Observed gap: this one successful input misses the whitespace regression.")
        project_tests("Project tests after the deliberate safe mistake: EXPECTED FAIL", 1)
        structure_check("Workspace structure check while project tests fail: still passed")
        transcript.extend([
            "Explicit counterexample: application tests failed while structure_status=passed.",
            "The checker reports verification_scope=workspace_structure and application_tests=not_run.",
            "The runner ran application tests separately; passing structure checks do not prove project code works.",
        ])
        failed_artifact = counter.with_name("counter.py.practice-bad")
        with failed_artifact.open("xb") as handle:
            handle.write(counter.read_bytes())
        require(failed_artifact.read_bytes() == failed, "Failed-version artifact was not preserved.")
        full_restore_preview = backup.read_bytes()
        require(full_restore_preview != before_regression and NEW_HELP not in full_restore_preview,
                "Full-file restore preview did not expose the unrelated edit it would lose.")
        transcript.extend([
            "\n## Preview a full-file restore — do not apply it",
            "Candidate: replace counter.py with the baseline backup's bytes.",
            "This would change the help description back to:",
            OLD_HELP.decode("utf-8"),
            "It would erase the intended same-file edit:",
            NEW_HELP.decode("utf-8"),
            "Decision: full-file restore rejected; preview only, no restoration applied.",
        ])
        require(counter.read_bytes().count(BAD_LINE) == 1,
                "Expected exactly one known faulty return line; recovery stopped.")
        repaired = counter.read_bytes().replace(BAD_LINE, GOOD_LINE, 1)
        counter.write_bytes(repaired)
        require(counter.read_bytes() == before_regression,
                "Limited recovery changed content beyond the known faulty return line.")
        require(NEW_HELP in counter.read_bytes(), "Recovery erased the unrelated same-file help edit.")
        require(operator_notes.read_bytes() == OPERATOR_NOTE, "Recovery changed the operator notes.")
        require(backup.read_bytes() == original, "The baseline backup was changed.")
        require(failed_artifact.read_bytes() == failed, "The failed source artifact was changed.")
        transcript.extend([
            "\n## Recover only the copied counter.py",
            "Replaced only the exact known faulty count_words return line with the original line.",
            "Recovered bytes match the before-regression state, including the unrelated help edit.",
            "Verified: OPERATOR_NOTES.md and the same-file help edit are preserved.",
            "Kept practice/word-counter/counter.py.practice-bad inside the temporary workspace.",
            "Recovered SHA-256: " + digest(counter.read_bytes()),
        ])
        project_tests("Project tests after bounded recovery: PASS", 0)
        working_counter("Working result after recovery")
        help_after = command("Unrelated help edit after recovery", ["counter.py", "--help"], 0, cwd=practice)
        require(help_after.stdout == help_before.stdout, "Recovery changed --help output.")
        structure_check("Final workspace structure check")
        transcript.extend([
            "\nRESULT: PASS -> EXPECTED FAIL -> RECOVERED PASS",
            "Verified: dry run, occupied/repeated init, repeated read-only checks,",
            "real counter output, expected failing assertions and limited recovery",
            "that preserves the unrelated same-file edit and separate operator notes.",
            "All modified copies, backup and failed-version artifacts lived only in the",
            "fresh temporary workspace; it is removed when this scripted run exits.",
            "The original practice files were not modified. No human user was observed.",
        ])


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Verify the fictional change/verify/recover exercise using a trusted local .pyz."
    )
    parser.add_argument("--app", required=True, metavar="PATH", help="trusted packaged Gen C AgentOS .pyz")
    parser.add_argument("--record", metavar="PATH", help="optional new transcript file; parent must exist; no overwrite")
    args = parser.parse_args(argv)
    try:
        app, record = prepare_inputs(args.app, args.record)
        handle = reserve_record(record)
    except (InputError, OSError) as error:
        print("Error: " + (str(error) if isinstance(error, InputError)
                           else "Input filesystem operation failed; check permissions and file types."), file=sys.stderr)
        return 2
    transcript = [
        "Gen C AgentOS beginner exercise — scripted evidence",
        "Python runtime: " + ".".join(map(str, sys.version_info[:3])),
        "Scope: fictional local code and records; no network, account or dependency installation.",
        "Commands use portable relative paths from the stated working directory.",
        "Agent simulation is not human-user validation or a productivity result.",
    ]
    code = 0
    try:
        run_exercise(app, transcript)
    except (ExerciseError, InputError, OSError, UnicodeError) as error:
        code = 1
        message = str(error) if isinstance(error, (ExerciseError, InputError)) else "Local exercise filesystem or text operation failed."
        transcript.append("\nRESULT: ACCEPTANCE FAILURE — " + message)
    text = "\n".join(transcript) + "\n"
    try:
        if handle is not None:
            handle.write(text)
            handle.close()
        print(text, end="")
    except OSError:
        print("Error: transcript output failed; check the explicitly selected output destination.", file=sys.stderr)
        return 2
    return code


if __name__ == "__main__":
    raise SystemExit(main())
