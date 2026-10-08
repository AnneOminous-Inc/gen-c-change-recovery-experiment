"""Small explicit schemas and read-only workspace structure checks."""

import json
import unicodedata
from urllib.parse import urlsplit

from .paths import WorkspaceError, local_file, portable_path, read_text

DOCUMENTS = ("brief", "actions", "decisions", "corrections", "handoff", "recovery")
HEADINGS = {
    "brief": ("Outcome", "In scope", "Out of scope", "Acceptance", "Permissions"),
    "handoff": ("Current state", "Next action", "Boundaries", "Resume checklist"),
    "recovery": ("Stop conditions", "Recovery steps", "Removal"),
}
FIELDS = {
    "actions": {"id", "owner", "scope", "next_action", "status", "evidence"},
    "decisions": {"id", "scope", "decision", "reason", "evidence"},
    "corrections": {"id", "scope", "original", "correction", "reason", "evidence", "status", "supersedes", "superseded_by"},
}
MISSING = object()


def _pairs(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise WorkspaceError("duplicate JSON key: " + key)
        obj[key] = value
    return obj


def _constant(value):
    raise WorkspaceError("invalid JSON constant: " + value)


def read_json(root, name):
    try:
        return json.loads(read_text(root, name), object_pairs_hook=_pairs, parse_constant=_constant)
    except json.JSONDecodeError as exc:
        raise WorkspaceError("malformed JSON at line %s column %s; fix syntax" % (exc.lineno, exc.colno))
    except RecursionError:
        raise WorkspaceError("JSON nesting is too deep; simplify the document")


def check(root):
    report = {"schema_version": 2, "verification_scope": "workspace_structure", "structure_status": "invalid", "application_tests": "not_run", "project": None, "owner": None, "checks": [], "issues": []}

    def issue(severity, location, message):
        report["issues"].append({"severity": severity, "location": location, "message": message})

    def error(location, message):
        issue("error", location, message)

    def warning(location, message):
        issue("warning", location, message)

    def string(value, location):
        if not isinstance(value, str) or not value.strip():
            error(location, "expected a nonempty string")
            return False
        if any(unicodedata.category(c) in ("Cc", "Cs") and c not in "\n\t" for c in value):
            error(location, "remove control characters from text")
            return False
        if "[TODO]" in value:
            warning(location, "replace [TODO] with a scoped, reviewable statement")
        return True

    def load(name, json_file=False):
        try:
            return read_json(root, name) if json_file else read_text(root, name)
        except (WorkspaceError, OSError) as exc:
            error(name, str(exc) if isinstance(exc, WorkspaceError) else "unable to read file; check permissions and file type")
            return MISSING

    cfg = load("agentos.json", True)
    if not isinstance(cfg, dict):
        if cfg is not MISSING:
            error("agentos.json", "expected a JSON object")
        return report
    expected = {"schema_version", "kit_version", "project", "owner", "documents"}
    if set(cfg) != expected:
        error("agentos.json", "expected exactly: " + ", ".join(sorted(expected)))
    if type(cfg.get("schema_version")) is not int or cfg.get("schema_version") != 1:
        error("agentos.json.schema_version", "unsupported schema; expected integer 1")
    for field in ("kit_version", "project", "owner"):
        if string(cfg.get(field), "agentos.json." + field) and field != "kit_version":
            report[field] = cfg[field]
    docs = cfg.get("documents")
    if not isinstance(docs, dict) or set(docs) != set(DOCUMENTS):
        error("agentos.json.documents", "provide exactly the six document roles: " + ", ".join(DOCUMENTS))
        return report
    safe_docs = {}
    for role, name in docs.items():
        try:
            portable_path(name)
            safe_docs[role] = name
        except WorkspaceError as exc:
            error("agentos.json.documents." + role, str(exc))
    names = ["agentos.json"] + list(safe_docs.values())
    folded = [unicodedata.normalize("NFC", name).casefold() for name in names]
    if len(set(folded)) != len(folded):
        error("agentos.json.documents", "document paths must be unique, including on case-insensitive filesystems")
    for index, name in enumerate(folded):
        if any(other.startswith(name + "/") for other in folded[index + 1:]) or any(name.startswith(other + "/") for other in folded[index + 1:]):
            error("agentos.json.documents", "a document path cannot be an ancestor of another file")
    if any(i["severity"] == "error" for i in report["issues"]):
        return report
    report["checks"].append("Config schema and portable document paths")

    def evidence(value, location):
        if not isinstance(value, list):
            error(location, "expected an array of evidence links")
            return
        if not value:
            warning(location, "add local evidence for this statement")
        for index, link in enumerate(value):
            loc = "%s[%s]" % (location, index)
            if not string(link, loc):
                continue
            if link.startswith("https://"):
                try:
                    url = urlsplit(link)
                    if not url.hostname or url.username is not None or url.password is not None or any(c.isspace() for c in link):
                        raise ValueError()
                    url.port
                except ValueError:
                    error(loc, "use an HTTPS URL with a host and no credentials")
                    continue
                warning(loc, "external evidence is not fetched or verified; add a local summary")
                continue
            filename, _, fragment = link.partition("#")
            try:
                local_file(root, filename)
                if fragment and any(c.isspace() for c in fragment):
                    raise WorkspaceError("use a fragment without whitespace")
            except (WorkspaceError, OSError) as exc:
                error(loc, str(exc) if isinstance(exc, WorkspaceError) else "unable to inspect evidence; check permissions")

    for role, headings in HEADINGS.items():
        name = safe_docs[role]
        before = len(report["issues"])
        content = load(name)
        if content is MISSING:
            continue
        sections = {}
        current = None
        for line in content.splitlines():
            if line.startswith("## "):
                current = line[3:].strip()
                if current in sections:
                    error(name, "duplicate section heading: " + current)
                sections[current] = []
            elif current:
                sections[current].append(line)
        for heading in headings:
            if heading not in sections:
                error(name, "add required heading: ## " + heading)
            elif not "\n".join(sections[heading]).strip():
                warning(name + "#" + heading, "fill this section before handing off")
        if "[TODO]" in content:
            warning(name, "replace all [TODO] placeholders before handing off")
        if not any(i["severity"] == "error" for i in report["issues"][before:]):
            report["checks"].append(role.capitalize() + " sections and safe file read")

    registers = {}
    for role in ("actions", "decisions", "corrections"):
        name = safe_docs[role]
        before = len(report["issues"])
        data = load(name, True)
        if data is MISSING:
            continue
        if not isinstance(data, list):
            error(name, "expected a JSON array of records")
            continue
        registers[role] = data
        ids = set()
        for index, record in enumerate(data):
            loc = "%s[%s]" % (name, index)
            if not isinstance(record, dict) or set(record) != FIELDS[role]:
                error(loc, "expected exactly these fields: " + ", ".join(sorted(FIELDS[role])))
                continue
            for field in sorted(FIELDS[role] - {"evidence", "supersedes", "superseded_by"}):
                string(record[field], loc + "." + field)
            record_id = record["id"]
            if isinstance(record_id, str):
                if record_id in ids:
                    error(loc + ".id", "duplicate record ID; choose a unique ID")
                ids.add(record_id)
            evidence(record["evidence"], loc + ".evidence")
            if role == "actions" and record["status"] not in ("open", "blocked", "done"):
                error(loc + ".status", "use open, blocked or done")
            if role == "corrections":
                if record["status"] not in ("active", "superseded"):
                    error(loc + ".status", "use active or superseded")
                for field in ("supersedes", "superseded_by"):
                    if record[field] is not None:
                        string(record[field], loc + "." + field)
        if role in ("actions", "decisions") and not data:
            warning(name, "add at least one scoped record")
        if role == "actions" and data and not any(isinstance(r, dict) and r.get("status") in ("open", "blocked") for r in data):
            warning(name, "record the next open or blocked action before handing off")
        if not any(i["severity"] == "error" for i in report["issues"][before:]):
            report["checks"].append(role.capitalize() + " records and evidence paths")

    corrections = registers.get("corrections", [])
    records = {r["id"]: r for r in corrections if isinstance(r, dict) and set(r) == FIELDS["corrections"] and isinstance(r.get("id"), str)}
    before = len(report["issues"])
    for record_id, record in records.items():
        loc = safe_docs["corrections"] + ":" + record_id
        for field, reciprocal in (("supersedes", "superseded_by"), ("superseded_by", "supersedes")):
            ref = record[field]
            if ref is None:
                continue
            if not isinstance(ref, str) or ref not in records:
                error(loc + "." + field, "reference must name an existing correction ID or be null")
                continue
            other = records[ref]
            if other[reciprocal] != record_id:
                error(loc, "supersession must be reciprocal")
            if other["scope"] != record["scope"]:
                error(loc, "supersession must stay within exactly the same scope")
        if record["status"] == "active" and record["superseded_by"] is not None:
            error(loc, "an active correction cannot have superseded_by")
        if record["status"] == "superseded" and record["superseded_by"] is None:
            error(loc, "a superseded correction needs superseded_by")
        seen = set()
        current = record_id
        while isinstance(current, str) and current in records:
            if current in seen:
                error(loc, "supersession cycle; restore an acyclic history")
                break
            seen.add(current)
            current = records[current]["superseded_by"]
    if "corrections" in registers and not any(i["severity"] == "error" for i in report["issues"][before:]):
        report["checks"].append("Correction scope and supersession graph")

    severities = {item["severity"] for item in report["issues"]}
    report["structure_status"] = "invalid" if "error" in severities else "needs_attention" if "warning" in severities else "passed"
    return report


def render(report, next_command=None):
    labels = {"passed": "Workspace structure checks passed.", "needs_attention": "Workspace structure needs attention.", "invalid": "Workspace structure is invalid."}
    lines = ["Gen C AgentOS — workspace records", "Project: " + (report["project"] or "(unavailable)"), "Owner: " + (report["owner"] or "(unavailable)"), labels[report["structure_status"]], "Application tests: not run. Run them separately; this report does not establish application behavior or deployment safety.", ""]
    for passed in report["checks"]:
        lines.append("PASS  " + passed)
    for item in report["issues"]:
        # Escape user-controlled text so terminal control sequences cannot execute.
        lines.append(item["severity"].upper() + "  " + item["location"] + ": " + item["message"])
    lines += ["", "This checks structure and local references; it does not verify outcomes or evidence content.", "Next: read BRIEF.md and HANDOFF.md, resolve record issues, and run your project's tests."]
    if next_command:
        lines += ["To check these records again:", next_command]
    return "\n".join(lines)
