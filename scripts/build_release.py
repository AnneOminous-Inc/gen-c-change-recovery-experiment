"""Build the experimental release from explicit original files."""

import hashlib
from pathlib import Path
import sys
import tempfile
import zipapp
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from genc_agentos import __version__
from genc_agentos.templates import build_files

PACKAGE_FILES = (
    "genc_agentos/__init__.py",
    "genc_agentos/__main__.py",
    "genc_agentos/cli.py",
    "genc_agentos/paths.py",
    "genc_agentos/validate.py",
    "genc_agentos/templates.py",
)
RELEASE_FILES = PACKAGE_FILES + (
    "README.md", "LICENSE", "RIGHTS.md", "CONTRACT.md", "CHANGELOG.md", "TEST_RESULTS.txt",
    "SAMPLE_OUTPUT.txt", "scripts/build_release.py", "tests/test_cli.py",
    "tests/test_release.py", "tests/test_next_commands.py",
    "tests/test_beginner_exercise.py", "scripts/verify_beginner_exercise.py",
    "practice/word-counter/counter.py", "practice/word-counter/test_counter.py",
    "practice/word-counter/CHANGE.md", "BEGINNER_GUIDE.md", "BEGINNER_FINDINGS.md",
    "BEGINNER_EXERCISE_RESULTS.txt", ".gitignore",
)


def build_zipapp(target):
    """Build the exact standalone launcher; also exercised by release tests."""
    with tempfile.TemporaryDirectory(prefix="agentos-build-") as temporary:
        stage = Path(temporary)
        for name in PACKAGE_FILES:
            staged_file = stage / name
            staged_file.parent.mkdir(parents=True, exist_ok=True)
            staged_file.write_bytes((ROOT / name).read_bytes())
        (stage / "__main__.py").write_text(
            "from genc_agentos.cli import main\nraise SystemExit(main())\n",
            encoding="utf-8",
        )
        (stage / "LICENSE").write_bytes((ROOT / "LICENSE").read_bytes())
        zipapp.create_archive(stage, target, compressed=True)
    target.chmod(0o600)


def main():
    for name in RELEASE_FILES:
        path = ROOT / name
        if not path.is_file() or path.is_symlink():
            raise SystemExit("Missing or unsafe allowlisted release file: " + name)
    output = ROOT / "dist"
    if output.is_symlink():
        raise SystemExit("Refusing symlink dist directory")
    output.mkdir(exist_ok=True)
    app_name = "genc-agentos-" + __version__ + ".pyz"
    archive_name = "genc-agentos-" + __version__ + ".zip"
    app = output / app_name
    archive = output / archive_name
    checksums = output / ("genc-agentos-" + __version__ + "-SHA256SUMS.txt")
    for path in (app, archive, checksums):
        if path.is_symlink():
            raise SystemExit("Refusing symlink build target: " + path.name)
    build_zipapp(app)
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as release:
        release.write(app, app_name)
        for name in RELEASE_FILES:
            release.write(ROOT / name, name)
        for name, content in build_files("Pocket Field Notes", "Demo Operator", True).items():
            release.writestr("demo/" + name, content.encode("utf-8"))
    archive.chmod(0o600)
    sums = []
    for path in (app, archive):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        sums.append(digest + "  " + path.name)
        print("Built dist/" + path.name + " (%s bytes)" % path.stat().st_size)
    checksums.write_text("\n".join(sums) + "\n", encoding="utf-8")
    checksums.chmod(0o600)
    print("Wrote dist/" + checksums.name)


if __name__ == "__main__":
    main()
