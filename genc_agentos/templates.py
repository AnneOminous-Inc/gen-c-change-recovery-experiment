"""Original, local-only workspace templates for the private starter kit."""

import json
from typing import Dict
from . import __version__


VERSION = __version__


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def build_files(project: str, owner: str, demo: bool = False) -> Dict[str, str]:
    """Return portable, constant paths and UTF-8 text without filesystem access."""
    documents = {
        "brief": "BRIEF.md",
        "actions": "ACTIONS.json",
        "decisions": "DECISIONS.json",
        "corrections": "CORRECTIONS.json",
        "handoff": "HANDOFF.md",
        "recovery": "RECOVERY.md",
    }
    config = {
        "schema_version": 1,
        "kit_version": VERSION,
        "project": project,
        "owner": owner,
        "documents": documents,
    }

    if demo:
        brief = f"""# Project brief

This is a fictional handoff exercise for {project}. It is not a
claim that a note application has been implemented or tested.

## Outcome

Prepare one bounded implementation handoff for an offline text-note utility.
A solo operator should know the first task, its owner, and its limits.

## In scope

- Specify one command that appends a short note to a chosen local text file.
- Assign the first implementation action and retain local review evidence.
- Carry forward only corrections scoped to local note capture.

## Out of scope

Cloud sync, accounts, analytics, background agents, publishing, paid services,
and changes outside the explicitly selected project workspace.

## Acceptance

- A named owner and an open next action appear in ACTIONS.json.
- A storage decision links to the fictional review evidence.
- The correction chain is reciprocal and has one active record for its scope.
- The handoff identifies what is still unimplemented; no productivity gain is
  asserted.

## Permissions

The fictional operator may draft code and tests inside the chosen project
workspace. First writes must have an explicit destination and refuse occupied
targets. Contacting people, accessing accounts, publishing, changing security
settings, and deleting existing data require separate authorization.
"""
        actions = [
            {
                "id": "A-001",
                "owner": owner,
                "scope": f"{project} / local capture",
                "next_action": "Implement the single local note command and its occupied-target test.",
                "status": "open",
                "evidence": ["BRIEF.md#acceptance", "evidence/SMOKE.md#handoff-review"],
            }
        ]
        decisions = [
            {
                "id": "D-001",
                "scope": f"{project} / local capture",
                "decision": "Use one UTF-8 text file under an explicitly chosen project directory for the first version.",
                "reason": "A local text file keeps the fictional first increment small and inspectable.",
                "evidence": ["evidence/SMOKE.md#storage-review"],
            }
        ]
        corrections = [
            {
                "id": "C-001",
                "scope": f"{project} / local capture",
                "original": "Infer the first note file from the current working directory.",
                "correction": "Require an explicit destination and ask for confirmation before the first write.",
                "reason": "The fictional review identified ambiguity about which directory the operator meant.",
                "evidence": ["evidence/SMOKE.md#correction-review"],
                "status": "superseded",
                "supersedes": None,
                "superseded_by": "C-002",
            },
            {
                "id": "C-002",
                "scope": f"{project} / local capture",
                "original": "Require an explicit destination and ask for confirmation before the first write.",
                "correction": "Require an explicit destination, refuse an occupied target, and provide a dry-run preview before the first write.",
                "reason": "The fictional review refined the boundary into inspectable behavior within the already authorized local task.",
                "evidence": ["evidence/SMOKE.md#correction-review"],
                "status": "active",
                "supersedes": "C-001",
                "superseded_by": None,
            },
        ]
        handoff = f"""# Handoff

## Current state

This fictional fixture records an agreed scope, one storage decision, and a
reviewed correction chain. The note application is still unimplemented.
The starter-kit checker verifies records and local paths; it does not verify
the fictional application's behavior.

## Next action

Read A-001 in ACTIONS.json. Implement the single local note command and the
occupied-target test within the selected workspace, then add actual evidence.

## Boundaries

Read BRIEF.md Permissions before editing. C-002 is active only for
{project} / local capture. C-001 remains historical and must not be
applied as current guidance. No account access, publication, external messages,
network calls, or removal of existing data is authorized by this fixture.

## Resume checklist

1. Run the starter-kit check with an explicit destination.
2. Read the brief, open action, decision, and active correction.
3. Confirm the selected directory and inspect existing files before editing.
4. Perform the single next action; record actual commands and results locally.
5. Update the action and handoff so the next operator can resume safely.
"""
        evidence = """# Fictional smoke evidence

This file is an invented, sanitized demonstration. It contains no client
records, personal conversations, real application test results, or credentials.
The starter-kit test suite is reported separately in the release materials.

## Handoff review

The fictional operator can identify the project outcome, the scope, A-001's
owner, and its next action. The note application remains unimplemented.

## Storage review

The fictional review chose a single local UTF-8 text file so a first increment
could be inspected without a service account or network dependency.

## Correction review

C-001 first removed an implicit working-directory assumption. C-002 then
superseded C-001 with an explicit destination, occupied-target refusal, and a
dry-run preview. Both records retain the identical local-capture scope.
This is a recordkeeping example, not an autonomous learning process.
"""
    else:
        brief = """# Project brief

Fill the TODOs before handing this workspace to a coding agent. The records
are operator-maintained; the starter kit does not perform the project work.

## Outcome

[TODO] Describe one useful outcome and who will use it.

## In scope

[TODO] List the small increment this workspace may implement.

## Out of scope

[TODO] List excluded features, systems, data, and external actions.

## Acceptance

[TODO] State observable checks that would demonstrate the increment is complete.

## Permissions

[TODO] Name the files and actions the operator authorizes. Explicitly document
any approval needed for accounts, messages, publishing, spending, or deletion.
"""
        actions = [
            {
                "id": "A-001",
                "owner": owner,
                "scope": "[TODO] Define the bounded project scope.",
                "next_action": "[TODO] Confirm the brief and choose one concrete next action.",
                "status": "open",
                "evidence": ["evidence/SMOKE.md"],
            }
        ]
        decisions = [
            {
                "id": "D-001",
                "scope": "Workspace setup",
                "decision": "Keep agent permissions scoped to this project.",
                "reason": "An explicit boundary makes the next handoff reviewable.",
                "evidence": ["BRIEF.md#permissions"],
            }
        ]
        corrections = []
        handoff = """# Handoff

## Current state

[TODO] State what exists, what was checked, and what remains uncertain.

## Next action

[TODO] Point to one open or blocked action in ACTIONS.json and its owner.

## Boundaries

[TODO] Restate the allowed scope and the actions needing separate authority.
Read BRIEF.md Permissions and any active correction for this exact scope.

## Resume checklist

1. Run the starter-kit check with an explicit destination.
2. Read the brief, action register, decisions, and active corrections.
3. Inspect current files and confirm the next action's authority.
4. [TODO] Add the project's specific verification step.
5. Update the evidence, action status, and this handoff after work.
"""
        evidence = """# Smoke evidence

[TODO] Record the command or review performed, its observed result, and its
limits. Use local relative links to evidence you are authorized to include.
Do not paste credentials, client records, personal conversations, or private
session history. Do not describe a proposed check as an executed check.
"""

    recovery = """# Recovery and removal

## Stop conditions

Stop work when the checker reports an invalid workspace, the intended owner or
permission boundary is unclear, a referenced path crosses a symlink, or a
proposed operation could overwrite or remove unreviewed data. A workspace
structure report does not authorize any action beyond the brief's permissions.

## Recovery steps

1. Run the starter-kit check with the explicit workspace destination.
2. Review the reported file or field before making changes. Preserve or back
   up your current documents and project data first.
3. Repair only the affected record or path. Confirm evidence exists locally
   and that the active correction applies to exactly the current scope.
4. Keep historical corrections. To supersede one, give both records the same
   scope, set reciprocal supersedes/superseded_by IDs, mark the old record
   superseded and the new record active, and avoid reference cycles.
5. Run check again, then update ACTIONS.json and HANDOFF.md with the observed
   result. If authority is missing, obtain it from the project owner.

## Removal

The kit has no deletion command. First review and back up the entire workspace,
including any files added since creation. Use your operating system's file
manager to select the explicit workspace you intend to retire; manually remove
only files you have confirmed are disposable. Preserve project data and evidence
you still need. Removing the installed zipapp or extracted kit source is a
separate operation and does not remove a scaffolded workspace.
"""

    return {
        "agentos.json": _json(config),
        "BRIEF.md": brief,
        "ACTIONS.json": _json(actions),
        "DECISIONS.json": _json(decisions),
        "CORRECTIONS.json": _json(corrections),
        "HANDOFF.md": handoff,
        "RECOVERY.md": recovery,
        "evidence/SMOKE.md": evidence,
    }
