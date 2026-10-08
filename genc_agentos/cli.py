"""Command line entry point. All work is explicit and local."""

import argparse
import json
import os
import shlex
import sys
import unicodedata

from . import __version__
from .paths import WorkspaceError, create_files, destination
from .templates import build_files
from .validate import check, render


def safe_output(text):
    return "".join(c if unicodedata.category(c) not in ("Cc", "Cs") or c in "\n\t" else "\\u%04x" % ord(c) for c in text)


def command_text(*arguments):
    """Quote a full follow-up command; never execute project commands."""
    runner = ["py", "-3"] if os.name == "nt" else ["python3"]
    if sys.argv[0].lower().endswith(".pyz"):
        runner.append(sys.argv[0])
    else:
        runner.extend(("-m", "genc_agentos"))
    parts = runner + list(arguments)
    if os.name == "nt":
        # PowerShell single quotes keep spaces, quotes and metacharacters literal.
        return "& " + " ".join("'" + part.replace("'", "''") + "'" for part in parts)
    return shlex.join(parts)


def parser():
    result = argparse.ArgumentParser(prog="gen-c-agentos", description="Scaffold and check an opt-in local workspace. No network or automatic agent execution.")
    result.add_argument("--version", action="version", version="%(prog)s " + __version__)
    commands = result.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init", help="create original templates in a new or empty directory")
    init.add_argument("--dest", required=True, metavar="PATH", help="explicit workspace destination; parent must exist")
    init.add_argument("--project", help="short scoped project name")
    init.add_argument("--owner", help="person or role responsible for the next action")
    init.add_argument("--demo", action="store_true", help="use fictional Pocket Field Notes example")
    init.add_argument("--dry-run", action="store_true", help="validate the destination and show the plan without writing")
    init.add_argument("--json", action="store_true", help="print a machine-readable preview; requires --dry-run")
    validate = commands.add_parser("check", help="check workspace record structure; application tests are separate")
    validate.add_argument("--dest", required=True, metavar="PATH")
    validate.add_argument("--json", action="store_true", help="print a portable machine-readable report")
    return result


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if args.command == "init" and args.json and not args.dry_run:
            raise WorkspaceError("init --json requires --dry-run; no files were written")
        root = destination(args.dest, must_exist=args.command == "check")
        if args.command == "init":
            project = args.project if args.project is not None else "Pocket Field Notes" if args.demo else "[TODO] Project name"
            owner = args.owner if args.owner is not None else "Demo Operator" if args.demo else "[TODO] Accountable owner"
            for name, value in (("project", project), ("owner", owner)):
                if not value.strip() or any(unicodedata.category(c) in ("Cc", "Cs") for c in value) or len(value) > 200:
                    raise WorkspaceError(name + " must be 1–200 characters without control characters")
            files = build_files(project, owner, args.demo)
            if args.json:
                plan = {
                    "schema_version": 1, "operation": "init", "kit_version": __version__,
                    "dry_run": True, "writes": False, "project": project, "owner": owner,
                    "files": [{"path": name, "bytes": len(content.encode("utf-8"))}
                              for name, content in sorted(files.items())],
                }
                print(json.dumps(plan, ensure_ascii=True, indent=2))
                return 0
            print("Gen C AgentOS " + __version__)
            print("Dry run — no files written." if args.dry_run else "Creating opt-in workspace.")
            for name in files:
                print("CREATE  " + name)
            if not args.dry_run:
                try:
                    create_files(root, files)
                except (OSError, WorkspaceError):
                    print("Creation stopped. No existing files were overwritten. Inspect any partial scaffold before retrying.", file=sys.stderr)
                    raise
            if args.dry_run:
                options = ["init", "--dest", args.dest]
                if args.demo:
                    options.append("--demo")
                if args.project is not None:
                    options.extend(("--project", args.project))
                if args.owner is not None:
                    options.extend(("--owner", args.owner))
                print("Next: create the planned files with this command:")
                print(safe_output(command_text(*options)))
            else:
                print("Next: check the workspace records with this command:")
                print(safe_output(command_text("check", "--dest", args.dest)))
                print("The checker does not run or test your project. Read BRIEF.md and HANDOFF.md before editing.")
            return 0
        report = check(root)
        print(json.dumps(report, ensure_ascii=True, indent=2) if args.json else safe_output(render(report, command_text("check", "--dest", args.dest))))
        return {"passed": 0, "needs_attention": 1, "invalid": 2}[report["structure_status"]]
    except WorkspaceError as exc:
        print("Error: " + safe_output(str(exc)), file=sys.stderr)
        return 2
    except OSError:
        print("Error: filesystem operation failed; check permissions, free space and the destination type.", file=sys.stderr)
        return 2
    except (ValueError, RecursionError):
        print("Error: input is too large or malformed; simplify it and check the schema.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
