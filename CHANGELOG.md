# Changes

## 0.2.2 — 2026-10-08

Added `init --dry-run --json` so local callers can inspect the planned relative
paths and UTF-8 byte counts without parsing the human preview. JSON output is
deterministic, omits destination paths and template contents, and writes
nothing. `init --json` without `--dry-run` is refused. Existing destination and
text validation, human preview, and structure-only report behavior remain.

Added Unicode regression coverage for canonical-equivalent paths, full
casefold aliases, ancestor collisions in both orders, and distinct Unicode
document paths. Review also exposed Greek aliases whose casefold outputs had
different normalization; normalizing the folded output now rejects these
duplicate and ancestor paths before reading documents. These checks are not
safety guarantees or evidence of human benefit. Dependencies are unchanged.

## 0.2.1 — 2026-10-08

The workspace checker now says **Workspace structure checks passed.** It
reports application tests separately as **not run**, including when the
exercise's application tests fail. This result does not establish application
behavior or deployment safety.

JSON report schema version 2 replaces `readiness` with `structure_status`
(`passed`, `needs_attention`, or `invalid`) and adds
`verification_scope: "workspace_structure"` and `application_tests: "not_run"`.
The workspace configuration schema remains version 1. Exit codes remain
0 for passing structure checks, 1 for record gaps, and 2 for invalid inputs.

This is the first public experimental release of the bounded original code,
templates, and beginner change-and-recovery exercise under MIT with Gen C
brand attribution. Scripted tests are not human usability or demand evidence.

## 0.2.0 — 2026-10-08 (private candidate)

Added a small fictional word counter and a scripted pass → deliberate failure
→ scoped repair exercise. Its dated private artifacts were preserved before
the 0.2.1 clarity change and are not part of this public release.

## 0.1.0 — 2026-10-08 (private prototype)

Introduced the explicit-destination workspace scaffold and record checker.
Its dated private artifacts are not part of this public release.
