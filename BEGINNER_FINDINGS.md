# What this experiment tests, and what remains unknown

Gen C Change and Recovery Experiment v0.2.2 is a scripted local exercise with a
fictional word counter. It is not a human usability study, demand measurement,
or comparison against an existing agent/checkpoint workflow. The records CLI
is a secondary structural checker.

## Evidence status

The **v0.2.2 packaged exercise passed**: 19 commands recorded seven passing
application tests, four deliberate failures, and seven passing tests after a
scoped repair. The wanted help edit and operator notes remained intact.
See `BEGINNER_EXERCISE_RESULTS.txt` for the actual command transcript.

**Full suite: 52 tests passed** in 22.290 seconds on Python 3.9.6/macOS,
with exit code 0. See `TEST_RESULTS.txt` for actual current-tree output.
The JSON preview matches actual created-file UTF-8 byte counts; Unicode
regressions cover aliases and ancestor boundaries, including a Greek casefold
normalization gap found and repaired during review.

| Step | Observed packaged result | What it establishes |
| --- | --- | --- |
| Preview/create | Dry-run wrote nothing; repeated init refused an occupied destination without changing it. | The exercised file boundaries held. |
| Working app | Seven behavior tests passed and the command printed `Words: 4`. | Tested whitespace-counting behavior worked in the recorded runtime. |
| Wanted edit | The revised argparse help sentence appeared before the regression. | An intentional edit existed in the same file as the bug. |
| Seeded regression | Four tests failed after `split()` became `split(" ")`; the simple example still printed `Words: 4`. | One happy-path example missed this particular bug. |
| Structure check | Valid records passed structural checks during application test failure. | `Workspace structure checks passed.` and JSON `structure_status: "passed"`, `verification_scope: "workspace_structure"`, `application_tests: "not_run"` describe record structure only. |
| Recovery preview | Replacing the entire file with the baseline would lose the wanted help edit; that replacement was rejected without applying it. | The backup covered more than the intended repair. |
| Scoped repair | Repairing only the count line preserved the wanted help edit and operator notes, with seven tests passing again. | Recovered bytes matched the pre-regression source; backup/bad copies and notes remained intact. |

The runner uses resolved temporary directories and allowlisted inputs. It
records baseline, pre-regression, broken, and recovered SHA-256 values, and
preserves backup/failed source copies for inspection during the run. The user's
practice source is not changed by the automated exercise. A human still has to
explain the diff and interpret failures; the script does not measure that work.

## Improvements and observed friction

The records CLI supplies complete follow-up commands for the chosen destination.
The exercise requires separate project tests, because the structural checker
does not execute or understand application code. v0.2.1 replaces broad success
language with the precise sentence `Workspace structure checks passed.` and
reports that application tests were not run.

The beginner path checks an existing Python runtime, explains the current
terminal folder and quotes, and runs without a global installation. It covers
one tiny project's behavior, intended edit, deliberate regression, failing
layer, and scoped repair. The operator still needs a terminal and plain-text
editor, must keep Python indentation, and must preserve backups without
replacing an existing file. These are remaining sources of friction, not
measured human failure rates.

## What the exercise does not solve

- Choosing a project, tool, budget, or suitable scope for a particular person.
- Inferring an arbitrary agent's next changes or planning a repair for unknown
  regressions. The seeded bug is known and one line; real changes can be ambiguous.
- Proving record claims, evidence truth, application correctness, completion, or
  deployment safety from a structural pass.
- Maintaining accurate project records or interpreting a failure automatically.
  The runner's setup is scripted and bypasses this human work.
- Moving a web preview to a deployed, maintainable app, migrating a database,
  controlling provider cost, or providing ongoing support.

Generic planning, scaffolding, progress, and recovery workflows can overlap
with existing tools. This experiment claims no novelty, superiority, human
comprehension result, completion rate, demand, productivity gain, autonomous
learning, or safety guarantee.

## Next evidence and platform limits

Test a narrow hypothesis with actual beginners: can a person explain the
intended file/input/output, predict the seeded failure, identify the failed
layer, and repair it while keeping the wanted edit? A comparison against an
existing agent/checkpoint workflow would need the same app, task, tests, and
constraints. Neither human validation nor that comparison has been conducted.

Native Windows/Linux execution remains unverified. Portable paths and command
quoting need separate native confirmation. Local code repair does not restore
database, deployment, external-action, or unrelated-file state. Concurrent
filesystem ancestor replacement is outside the CLI's protection. Missing
Python 3.9+ remains a stop; the experiment does not install it globally.
