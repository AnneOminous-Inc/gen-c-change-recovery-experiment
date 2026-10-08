# Gen C Change and Recovery Experiment

An experimental beginner change-and-recovery exercise, version **0.2.2**.
Run a tiny fictional word counter, keep a useful help-text edit, introduce one
deliberate bug, then repair only the broken line and verify the result.
The same file contains both edits, so replacing it with an older backup would
discard work you want to keep.

The included Gen C AgentOS records CLI is secondary: it scaffolds and checks
project records. Its structure check cannot establish that an application works.

Start with [BEGINNER_GUIDE.md](BEGINNER_GUIDE.md) if terminals or agents are new to
you. The exercise and records CLI can overlap with tools you already use;
this experiment does not claim novelty or superiority. Scripted results do not
establish human usability, demand, or productivity gains.

## What you need

- An existing Python **3.9 or newer** runtime, a terminal, the extracted release
  ZIP, and a plain-text editor.
- An optional coding agent; no agent account is needed for the exercise.

Check `python3 --version` on macOS/Linux or `py -3 --version` on Windows. If that
command is unavailable or older than 3.9, stop and arrange an approved runtime
separately. This kit does not install Python or change global settings.

Runtime uses only Python's standard library. There are no bundled third-party
packages, SaaS accounts, network calls, telemetry, hooks, secrets, paid APIs, or
dependency installation. Native Windows/Linux execution remains unverified;
portable path behavior is tested on macOS.

## Download or run from source

Get the ZIP from the [v0.2.2 release](https://github.com/AnneOminous-Inc/gen-c-change-recovery-experiment/releases/tag/v0.2.2)
and extract it with your file manager. No package installation is required.

If you already have Git, the source alternative is:

```sh
git clone --branch v0.2.2 --single-branch https://github.com/AnneOminous-Inc/gen-c-change-recovery-experiment.git
cd gen-c-change-recovery-experiment
python3 -m genc_agentos --version
python3 practice/word-counter/counter.py "Small steps make progress"
python3 -m unittest discover -s practice/word-counter -v
```

Git refuses a nonempty clone destination. In source usage, replace
`python3 genc-agentos-0.2.2.pyz` below with `python3 -m genc_agentos`.
Cloning/downloading uses the network; running the tool and exercise does not.

## Try the working project

Open a terminal in the extracted release folder containing the `.pyz`,
`practice`, and `scripts` files. `./` means that current folder. Keep the quotes
around the sample sentence so it reaches the counter as one argument. On
Windows, use `py -3` in place of `python3` in every command below.

```sh
python3 practice/word-counter/counter.py "Small steps make progress"
python3 -m unittest discover -s practice/word-counter -v
```

The counter prints `Words: 4`; its seven tests should pass. Follow
[BEGINNER_GUIDE.md](BEGINNER_GUIDE.md) and
[practice/word-counter/CHANGE.md](practice/word-counter/CHANGE.md) to make the
wanted help edit, seed the counting bug, inspect failed tests, and repair only
the counting line. Retain the backup and failed source without overwriting.

The exercise changes local practice code. It does not deploy an app or restore
databases, external actions, or edits elsewhere.

For optional repeatable developer evidence, run:

```sh
python3 scripts/verify_beginner_exercise.py --app ./genc-agentos-0.2.2.pyz --record ./evidence-run.txt
```

The runner copies allowlisted practice files into a fresh temporary directory
and records pass → deliberate failure → scoped repair. It does not change your
working practice file. A passing script still does not demonstrate a beginner's
comprehension. See [BEGINNER_FINDINGS.md](BEGINNER_FINDINGS.md) for observed
friction and the remaining evidence gap.

## Optional workspace records CLI

From the extracted release folder:

```sh
python3 genc-agentos-0.2.2.pyz --version
python3 genc-agentos-0.2.2.pyz init --dest ./workspace --demo --dry-run
python3 genc-agentos-0.2.2.pyz init --dest ./workspace --demo
python3 genc-agentos-0.2.2.pyz check --dest ./workspace
python3 genc-agentos-0.2.2.pyz check --dest ./workspace --json
```

Expect version `0.2.2`, a preview stating `Dry run — no files written.`, then
`Workspace structure checks passed.` for the demo records. The JSON reports
`structure_status: "passed"`, `verification_scope: "workspace_structure"`, and
`application_tests: "not_run"`. These describe record format and local paths,
not application behavior or deployment safety.

**Counterexample:** after the seeded counting bug, four application tests fail
while the workspace structure check can still pass. Run project tests
separately. The scripted verifier checks this exact boundary using records
scoped to the word counter.

The `--demo` records describe **Pocket Field Notes**, an invented,
unimplemented note app. The actual runnable word counter is separately under
`practice/word-counter/`; it is not created by `init`.

## Optional copy-install and your own records

No installation is required. To keep the tool elsewhere, use your file manager
to copy only `genc-agentos-0.2.2.pyz` into a directory you choose. Decline an
overwrite prompt. Run it with Python using its quoted path; no PATH or shell
startup change is needed. The practice and guide stay in the extracted release.

From the extracted folder, a new workspace can be previewed and created with:

```sh
python3 genc-agentos-0.2.2.pyz init --dest ./my-project-workspace --project "My Project" --owner "Project Owner" --dry-run
python3 genc-agentos-0.2.2.pyz init --dest ./my-project-workspace --project "My Project" --owner "Project Owner"
python3 genc-agentos-0.2.2.pyz check --dest ./my-project-workspace
```

Destinations are explicit. Use a new directory whose real parent already
exists, or an existing empty directory. The CLI refuses lexical `..`, symlink
boundaries, and occupied destinations; it has no overwrite flag. Use the
physical path if an ancestor is a system symlink, such as a temporary-directory
alias. A second `init` refuses the occupied workspace without changing it.
Repeated `check` calls are read-only and deterministic for identical inputs.
Dry-run checks the destination and prints a creation plan without writing.

For a machine-readable preview, add `--json` to `init --dry-run`:

```sh
python3 genc-agentos-0.2.2.pyz init --dest ./my-project-workspace --project "Café Notes" --owner "Project Owner" --dry-run --json
```

This prints one deterministic JSON object with preview schema version 1,
operation, kit version, project, owner, `dry_run: true`, `writes: false`, and a
sorted `files` list of relative paths and UTF-8 byte counts. It omits the
destination and template contents. `init --json` without `--dry-run` exits 2
without writing. Destination and text validation still apply. A preview does
not reserve the destination, authorize work, or guarantee later creation.
`check --json` remains a separate structure report using report schema version 2.

## Maintain the records

| File | What you maintain |
| --- | --- |
| `BRIEF.md` | Outcome, scope, acceptance, and permissions. |
| `ACTIONS.json` | Owner, scope, concrete next action, status, and evidence links. Keep at least one open or blocked action for the structure check. |
| `DECISIONS.json` | Scoped decision, reason, and evidence. Keep at least one decision. |
| `CORRECTIONS.json` | Original claim, correction, scope, reason, evidence, status, and reciprocal supersession links. Empty is valid; do not invent lessons. |
| `HANDOFF.md` | Current state, next action, boundaries, and resume checklist. |
| `RECOVERY.md` | Stop conditions, reviewed recovery, and manual removal. |
| `evidence/SMOKE.md` | Your actual observations. The note demo's observations are fictional. |
| `agentos.json` | Schema/kit version, project, owner, and six managed document paths. |

Fill visible `[TODO]` entries. Keep generated JSON field names. Action status
is `open`, `blocked`, or `done`; correction status is `active` or `superseded`.
IDs must be unique within each register and record strings must be nonempty.
Empty evidence arrays produce warnings. Blank required Markdown sections and
`[TODO]` text produce structure-check issues.

To supersede `C-001` with `C-002`, both records must have exactly the same
`scope`. Set the old record's `status` to `superseded` and `superseded_by` to
`C-002`. Set the new record's `status` to `active`, `supersedes` to `C-001`, and
`superseded_by` to `null`. Keep the chain acyclic. A correction applies only to
its recorded scope.

Evidence links can be relative local files, optionally with a `#fragment`, or
credential-free HTTPS URLs. Local files must exist inside the workspace without
crossing symlinks. HTTPS links are not fetched or verified and produce warnings;
heading fragments are not verified. Managed paths use forward slashes, without
absolute paths, `.`/`..`, empty components, colons, backslashes, control
characters, trailing dots/spaces, or Windows reserved device names.

## Permissions and limits

`init` writes eight planned files within the selected empty destination and
creates the workspace/evidence directories as needed. File permissions follow
the operating system and current umask: new files request owner read/write
(`0600`) and new directories request owner-only access (`0700`). Existing empty
destination permissions stay as they are. The kit does not encrypt documents or
change security settings. Choose a private location before adding sensitive
information. Templates contain original sanitized text, not owner/client data.

`check` reads the config and six managed documents, and inspects referenced
local evidence paths without reading their contents. It does not traverse
unrelated files. Reads are limited to 1 MiB per document. Malformed JSON,
duplicate keys, invalid schema, nonregular files, and unsafe paths are rejected.
The checker cannot judge whether prose, permissions, claims, or evidence are
true, detect every secret, or authorize an agent action. Concurrent replacement
of a filesystem ancestor is outside the prototype's protection.

Exit codes are `0` for successful preview/creation or passed structure checks,
`1` for valid records needing attention, and `2` for input/filesystem/schema errors.
These describe the workspace tool; project tests report their own results.

## Remove the tool or retire a workspace

There is no deletion command. Review and back up records and project data first.
Use your file manager to remove the exact `.pyz` copy you installed. Remove its
directory only after confirming nothing else there is needed. To retire a
workspace, separately inspect its files, preserve evidence/data, and manually
remove only the explicit workspace you intend to retire. Removing the tool
does not remove workspaces. Preserve any practice backup or bad version needed
to understand the exercise before removing the extracted practice folder.

## Developer checks and license

```sh
python3 -m unittest discover -s tests -v
python3 scripts/build_release.py
```

From a source checkout, the build supplies the packaged app under `dist/`.
To run the exercise verifier against that app:

```sh
python3 scripts/verify_beginner_exercise.py --app ./dist/genc-agentos-0.2.2.pyz --record ./evidence-run.txt
```

Tests use fixtures and temporary directories. Release files are allowlisted;
the surrounding filesystem is not bundled. Actual results accompany the
candidate in `TEST_RESULTS.txt`, `SAMPLE_OUTPUT.txt`, and the beginner findings.
The original bounded prototype is licensed under [MIT](LICENSE), with
`Copyright (c) 2026 Gen C`. See [RIGHTS.md](RIGHTS.md) for included-content and
dependency scope. Gen C is the attribution name; this does not represent an
LLC or separate naming clearance. Nothing here establishes deployment safety,
autonomous learning, or a safety guarantee.
