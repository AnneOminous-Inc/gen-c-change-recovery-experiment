# Changes

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
