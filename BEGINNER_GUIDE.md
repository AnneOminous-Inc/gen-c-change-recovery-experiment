# Gen C Change and Recovery Experiment — beginner guide

This exercise uses a fictional word counter: a small working program that
prints how many whitespace-separated words you enter. You will make a useful
help-text edit and a deliberately bad counting change in the same file, observe
failing tests, then repair only the mistake. No account or agent is required.
For download or source-clone instructions, see [README.md](README.md).

## 1. Open the release and check Python

You need the extracted ZIP, an existing Python **3.9 or newer**, a terminal,
and a plain-text editor. A terminal accepts commands; an editor changes text
files. The `.pyz` file is the workspace tool. `counter.py` is the practice
program. They are separate.

Extract the ZIP with your file manager. Open a terminal in the folder containing
`genc-agentos-0.2.2.pyz`, `practice/`, and `scripts/`. You can use `cd` followed
by the quoted path to that extracted folder to change the terminal's folder.
On macOS/Linux, `pwd` prints the current folder; in Windows PowerShell,
`Get-Location` does the same. The terminal must be in the extracted release
folder for the commands below to find their files.
In a source checkout, use `python3 -m genc_agentos` in place of the `.pyz`
invocation; the practice commands stay the same.

Check the existing runtime:

```sh
python3 --version
```

On Windows, use `py -3 --version`, then replace `python3` with `py -3` in all
following commands. If Python is missing or older than 3.9, stop here and
arrange an approved runtime separately. This guide does not install software
globally. Native Windows/Linux execution has not been verified.

Run one command at a time, press Enter, and read its result before continuing.
`./workspace` means a folder named `workspace` inside the terminal's current
folder. Quotes keep a path with spaces, or the sample sentence, together.

## 2. Run and understand the actual project

```sh
python3 practice/word-counter/counter.py "Small steps make progress"
python3 -m unittest discover -s practice/word-counter -v
```

The first command should print `Words: 4`. The second runs the practice tests
and should finish with `OK`. A test is a repeatable comparison between an input
and an expected result; its name tells you which behavior it checks.

Open `practice/word-counter/counter.py` in your plain-text editor and
[CHANGE.md](practice/word-counter/CHANGE.md) beside it. Find:

```python
return len(text.split())
```

`text` is the entered sentence. `split()` separates words at whitespace,
including repeated spaces, tabs, and newlines; `len(...)` counts the resulting
pieces. This exercise treats a hyphenated expression as one word. It does not
try to understand grammar.

Before changing anything, describe the intended file, exact lines, expected
effects, tests, and backup in your own words. If using an agent, the
reviewable prompt in `CHANGE.md` limits it to this practice file. Review its
proposed change before accepting it. No dependencies or outside edits are
needed.

## 3. Optional: preview the records check's boundary

The separate workspace tool organizes records. To see its limited scope, run:

```sh
python3 genc-agentos-0.2.2.pyz --version
python3 genc-agentos-0.2.2.pyz init --dest ./workspace --demo --dry-run
```

Expect version `0.2.2` and `Dry run — no files written.` Review the creation
plan and `./workspace` destination, then run:

```sh
python3 genc-agentos-0.2.2.pyz init --dest ./workspace --demo
python3 genc-agentos-0.2.2.pyz check --dest ./workspace
python3 genc-agentos-0.2.2.pyz check --dest ./workspace --json
```

Expect `Workspace structure checks passed.` The JSON identifies
`structure_status: "passed"`, `verification_scope: "workspace_structure"`, and
`application_tests: "not_run"`. This checks records and local references; it
does **not** test application code. These demo records describe an invented,
unimplemented **Pocket Field Notes** app, separate from the real word counter.

`init` refuses an occupied directory. Preserve its files and choose another
explicit new destination. Repeated `check` is read-only. See the README for
record editing instructions. The optional scripted verifier uses word-counter
records and demonstrates a structure pass during the seeded application failure.

## 4. Make a useful edit, then one practice mistake

This is synthetic breakage for this fictional exercise, not a suggested real
feature. In your file manager, copy `counter.py` within its current folder and
name the copy exactly `counter.py.before-practice`. **Create it only if that
name is absent. Never replace an existing backup.** If it already exists, stop
and inspect it; use a freshly extracted practice folder for a new attempt.
Confirm the backup contains the original `split()` line before editing.

In `counter.py`, find the `description` text inside `argparse.ArgumentParser`.
Replace only its quoted text with:

```python
"Count words in your draft. Keep the whole phrase in quotes."
```

Save and run `python3 practice/word-counter/counter.py --help`. The new sentence
should appear. This useful edit explains the input; it does not change counting.

In `counter.py` only, replace that one line with:

```python
return len(text.split(" "))
```

Keep the four spaces before `return`; change the words on the line, not its
indentation. An `IndentationError` is a code-format error, unlike the expected
counting-test failures in this exercise.

Save, then rerun:

```sh
python3 -m unittest discover -s practice/word-counter -v
```

Expect practice tests to fail. The replacement splits at each literal space,
so repeated spaces create empty pieces and tabs/newlines no longer separate
words. Read the failures and the changed line before recovering.

If you tried the optional records commands, the workspace tool can still say
`Workspace structure checks passed.` during the application test failures.
Intact records cannot establish project behavior. Run project tests separately.
Check that boundary with `python3 genc-agentos-0.2.2.pyz check --dest ./workspace`.
A simple one-space sentence can also still print `Words: 4`; one happy-path
example does not cover all documented behavior.

## 5. Repair only the mistake, then prove it works

In your file manager, copy the current bad `counter.py` to
`counter.py.practice-bad` only if that name is absent. Decline any overwrite;
stop and inspect if it already exists. Keep this bad version for review.

Open `counter.py.before-practice` as a reference. In the current `counter.py`,
repair **only** `return len(text.split(" "))` back to
`return len(text.split())` and save. Keep the improved description text.
Replacing the entire file with the baseline would lose that useful edit.
Run:

```sh
python3 -m unittest discover -s practice/word-counter -v
python3 practice/word-counter/counter.py "Small steps make progress"
python3 practice/word-counter/counter.py --help
```

Expect seven tests with `OK`, `Words: 4`, and the improved help sentence. Inspect
the file too: its counting line is repaired and its description edit remains.
Keep the backup, bad version, explanation, and test results for handoff. This
proves only the tested local behavior. A local code repair does not undo
database changes, deployment changes, external actions, or other file edits.

## Common stops and optional evidence

| Result | What to do next |
| --- | --- |
| Command/Python not found | Check the existing runtime; stop if unavailable. |
| Cannot open `.pyz` or `counter.py` | Check the terminal's current folder and filenames. |
| Occupied destination | Preserve its files; choose a new explicit destination. |
| Path or symlink error | Use a physical local path with an existing real parent; do not bypass the check. |
| JSON/schema error | Read the named record and fix its format after backing it up. |
| Project tests fail after repair | Inspect the counting line and test output; stop before further edits. |

For developer proof of the same pass/fail/scoped-repair sequence in a temporary
folder, optionally run from the extracted release folder:

```sh
python3 scripts/verify_beginner_exercise.py --app ./genc-agentos-0.2.2.pyz --record ./evidence-run.txt
```

The runner uses temporary copies and does not edit your practice file. Its
transcript is scripted evidence, not evidence that a human beginner understood
the task. See [BEGINNER_FINDINGS.md](BEGINNER_FINDINGS.md) for observed friction.
The README's developer section gives the build command and `dist/` app path
for running the verifier from a source checkout.

No install is required. For optional copy-install, permissions, limitations,
and manual removal instructions, see [README.md](README.md). Keep any records
or practice evidence you need before removing the specific files yourself.
