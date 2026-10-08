"""Follow-up commands are runnable and preserve the operator's arguments."""

import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from genc_agentos.cli import command_text
from test_release import builder


class FollowUpCommandsTests(unittest.TestCase):
    def test_packaged_follow_up_commands_execute_from_the_same_folder(self):
        with tempfile.TemporaryDirectory(prefix="agentos-next-command-") as temporary:
            base = Path(temporary).resolve()
            app = base / "agent tools.pyz"
            builder.build_zipapp(app)
            env = os.environ.copy()
            env.pop("PYTHONPATH", None)
            original = subprocess.run(
                [sys.executable, app.name, "init", "--dest", "workspace with spaces", "--demo", "--project", "Tiny $project", "--owner", "Practice Operator", "--dry-run"],
                cwd=base, env=env, text=True, capture_output=True, timeout=15,
            )
            self.assertEqual(original.returncode, 0, original.stderr)
            follow_up = original.stdout.strip().splitlines()[-1]
            arguments = shlex.split(follow_up)
            self.assertEqual(arguments[0], "python3")
            arguments[0] = sys.executable
            created = subprocess.run(arguments, cwd=base, env=env, text=True, capture_output=True, timeout=15)
            self.assertEqual(created.returncode, 0, created.stderr)
            command = next(line for line in created.stdout.splitlines() if line.startswith("python3 "))
            check_args = shlex.split(command)
            check_args[0] = sys.executable
            checked = subprocess.run(check_args, cwd=base, env=env, text=True, capture_output=True, timeout=15)
            self.assertEqual(checked.returncode, 0, checked.stderr)
            self.assertIn("Workspace structure checks passed.", checked.stdout)
            self.assertIn("application tests: not run", checked.stdout.lower())
            self.assertNotRegex(checked.stdout, r"(?i)\bready\b")
            self.assertNotIn("YOUR_WORKSPACE", created.stdout + checked.stdout)

    def test_windows_command_quotes_powershell_arguments_without_expansion(self):
        with patch("genc_agentos.cli.os.name", "nt"), patch("genc_agentos.cli.sys.argv", ["tools with spaces.pyz"]):
            result = command_text("init", "--dest", "folder & $name", "--project", "Operator's `project`")
        self.assertEqual(result, "& 'py' '-3' 'tools with spaces.pyz' 'init' '--dest' 'folder & $name' '--project' 'Operator''s `project`'")


if __name__ == "__main__":
    unittest.main()
