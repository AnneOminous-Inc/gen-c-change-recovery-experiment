"""Conservative filesystem boundaries; no traversal or directory scanning."""

import os
import re
import stat
import unicodedata
from pathlib import Path

MAX_BYTES = 1024 * 1024
DEVICE = re.compile(r"^(con|prn|aux|nul|com[0-9¹²³]|lpt[0-9¹²³])(?:\.|$)", re.I)


class WorkspaceError(Exception):
    """A problem the caller can fix without a traceback."""


def portable_path(value):
    if not isinstance(value, str) or not value:
        raise WorkspaceError("use a nonempty portable relative file path")
    if value.startswith("/") or "\\" in value or ":" in value:
        raise WorkspaceError("use a relative POSIX path, without a drive or backslash")
    if any(unicodedata.category(c) in ("Cc", "Cs") or c in '<>\"|?*' for c in value):
        raise WorkspaceError("path contains characters that are not portable")
    parts = value.split("/")
    for part in parts:
        if part in ("", ".", "..") or part.endswith((".", " ")) or DEVICE.match(part):
            raise WorkspaceError("path contains traversal, empty or nonportable components")
    return parts


def no_symlinks(path):
    """Inspect existing components without following a symlink."""
    for part in list(reversed(path.parents)) + [path]:
        try:
            mode = part.lstat().st_mode
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(mode):
            raise WorkspaceError("symlink boundary refused; choose the physical directory path")


def destination(value, must_exist=False):
    if not value or any(unicodedata.category(c) in ("Cc", "Cs") for c in value):
        raise WorkspaceError("destination must be nonempty and contain no control characters")
    raw = Path(value)
    if ".." in raw.parts:
        raise WorkspaceError("destination must not contain '..' traversal components")
    path = Path(os.path.abspath(str(raw)))
    no_symlinks(path)
    if must_exist:
        if not path.is_dir():
            raise WorkspaceError("destination must be an existing workspace directory")
    else:
        if not path.parent.is_dir():
            raise WorkspaceError("destination parent must already exist as a real directory")
        if path.exists():
            if not path.is_dir():
                raise WorkspaceError("destination is not a directory")
            if next(path.iterdir(), None) is not None:
                raise WorkspaceError("destination is occupied; choose a new or empty directory (no overwrite)")
    return path


def local_file(root, relative):
    parts = portable_path(relative)
    path = root.joinpath(*parts)
    no_symlinks(path)
    try:
        mode = path.lstat().st_mode
    except FileNotFoundError:
        raise WorkspaceError("file is missing; restore it or fix the relative reference")
    if not stat.S_ISREG(mode):
        raise WorkspaceError("expected a regular file")
    return path


def read_text(root, relative):
    path = local_file(root, relative)
    # O_NOFOLLOW prevents a final-component symlink swap on supporting systems.
    fd = os.open(str(path), os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0))
    try:
        metadata = os.fstat(fd)
        if not stat.S_ISREG(metadata.st_mode):
            raise WorkspaceError("expected a regular file")
        if metadata.st_size > MAX_BYTES:
            raise WorkspaceError("file exceeds the 1 MiB read limit")
        with os.fdopen(fd, "rb") as handle:
            fd = None
            data = handle.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise WorkspaceError("file exceeds the 1 MiB read limit")
        return data.decode("utf-8")
    except UnicodeDecodeError:
        raise WorkspaceError("file must contain UTF-8 text")
    finally:
        if fd is not None:
            os.close(fd)


def create_files(root, files):
    """Only create; never overwrite, roll back or delete user files."""
    for name in files:
        portable_path(name)
    if not root.exists():
        root.mkdir(mode=0o700)
    for name, content in files.items():
        path = root.joinpath(*portable_path(name))
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        no_symlinks(path)
        fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600)
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
