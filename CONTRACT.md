# Gen C AgentOS records CLI specification — 0.2.1

The small records CLI supports the Gen C Change and Recovery Experiment.
It checks workspace structure and local references; it does not run application
tests or establish application behavior, completion, or deployment safety.
Python 3.9+ and the standard library are the only runtime requirements.

## Commands

From a source checkout:

```sh
python3 -m genc_agentos --version
python3 -m genc_agentos init --dest ./workspace --demo --dry-run
python3 -m genc_agentos init --dest ./workspace --demo
python3 -m genc_agentos check --dest ./workspace
python3 -m genc_agentos check --dest ./workspace --json
```

The extracted release replaces `python3 -m genc_agentos` with
`python3 genc-agentos-0.2.1.pyz`. `init` also accepts `--project NAME` and
`--owner NAME` instead of `--demo`. Put names containing spaces in quotes.

An explicit destination is required. Init accepts a missing directory whose
real parent exists, or an existing empty directory. Occupied directories are
refused; there is no force/overwrite option. Dry-run prints the file plan without
writes. Repeated init refuses existing data. Check is read-only and deterministic
for identical inputs. Exit codes are `0` for successful preview/creation or a
passed structure check, `1` for valid structure needing attention, and `2` for
input, filesystem, or schema errors. Project tests have separate results.

## Source interface

`genc_agentos/templates.py` exposes `VERSION = __version__` (0.2.1) and
`build_files(project: str, owner: str, demo: bool = False) -> dict[str, str]`.
Mapping keys are portable relative POSIX paths; values are UTF-8 text. All
template keys are implementation constants, not user-controlled paths.

## Workspace schema

`agentos.json` has exactly `schema_version` (1), `kit_version` (string),
`project` and `owner` (nonempty strings), and `documents` (object). The documents
object has exactly `brief`, `actions`, `decisions`, `corrections`, `handoff`, and
`recovery`, each mapping to a unique portable relative file path.

- `BRIEF.md`: headings `## Outcome`, `## In scope`, `## Out of scope`,
  `## Acceptance`, and `## Permissions`. Blank sections or `[TODO]` are issues.
- `ACTIONS.json`: array; records have exactly `id`, `owner`, `scope`,
  `next_action`, `status`, and `evidence`. Status is `open`, `blocked`, or `done`.
  At least one open or blocked next action is required for the structure check.
- `DECISIONS.json`: array; records have exactly `id`, `scope`, `decision`,
  `reason`, and `evidence`. At least one decision is required.
- `CORRECTIONS.json`: array; records have exactly `id`, `scope`, `original`,
  `correction`, `reason`, `evidence`, `status`, `supersedes`, and `superseded_by`.
  Status is `active` or `superseded`; references are null or record IDs.
  Supersession is reciprocal, acyclic, and restricted to identical scope. An
  active record cannot have `superseded_by`. Empty corrections are valid;
  do not invent lessons.
- `HANDOFF.md`: headings `## Current state`, `## Next action`, `## Boundaries`,
  and `## Resume checklist`. Blank sections or `[TODO]` are issues.
- `RECOVERY.md`: headings `## Stop conditions`, `## Recovery steps`, and
  `## Removal`.
- `evidence/SMOKE.md`: fictional evidence in the note demo; default templates
  have a `[TODO]` placeholder.

Record strings are nonempty and IDs are unique within each register. Evidence
is an array of relative local paths, optionally with a `#fragment`, or HTTPS
URLs without embedded credentials. Missing/empty evidence produces a warning;
a missing local evidence file produces an error. HTTPS links are never fetched
or verified and produce warnings. Heading fragments are not verified.

## File boundaries

Reject lexical `..` in destinations and symlinks in the destination or existing
ancestors. Use a physical path for a system alias such as a temporary-directory
alias; the parent must be a real directory. Managed/evidence paths reject
absolute paths, backslashes, colons, control characters, empty/dot/dot-dot
components, trailing dots/spaces, and reserved Windows device names.

Check rejects symlinks in referenced local paths, nonregular files, duplicate
JSON keys, and reads exceeding 1 MiB per document. Unrelated workspace files
are neither traversed nor read. Init requests file mode `0600` and directory
mode `0700`, subject to the operating system and umask; it does not change an
existing empty destination's permissions. There are no hooks, telemetry,
network calls, secret access, external accounts, or automatic agent actions.

Concurrent ancestor replacement is outside the prototype's protection. There
is no deletion command. Review and back up records and project data before
manually removing the specific files you intend to retire.

## Reports

Human output identifies the project/owner when parsed, describes structure
status, lists passed checks and issues with remedies, and suggests a next
command. A successful check says exactly:

```text
Workspace structure checks passed.
Application tests: not run.
```

The second line continues with an instruction to run tests separately; the
report does not establish application behavior or deployment safety.

JSON reports use a separate report schema version **2**, with:

- `schema_version`: `2`
- `verification_scope`: `"workspace_structure"`
- `structure_status`: `"passed"`, `"needs_attention"`, or `"invalid"`
- `application_tests`: `"not_run"`
- `project`, `owner`: parsed values or null
- `checks`: array of passed-check names
- `issues`: objects with `severity`, `location`, and `message`

The successful structure status can remain `"passed"` while the practice
application's tests fail. The experiment deliberately demonstrates this
counterexample. Workspace data and reports do not serialize absolute paths.

## Distribution

The [repository](https://github.com/AnneOminous-Inc/gen-c-change-recovery-experiment)
contains allowlisted original source, templates, tests, practice files, and
documentation. The v0.2.1 release adds a standalone zipapp and extracted-source
ZIP. See [README.md](README.md) for download, source usage, removal, and limits,
and [LICENSE](LICENSE) for MIT terms. No third-party packages or Python runtime
are bundled. This experiment does not claim novel tooling, measured human
usability, demand, productivity gains, or a safety guarantee.
