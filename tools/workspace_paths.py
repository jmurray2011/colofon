"""Resolve consumer-owned inputs without allowing workspace escapes."""

import os
import re
import subprocess


class WorkspacePathError(ValueError):
    """An input path violates the configured workspace boundary."""


def _inside(root, path):
    try:
        common = os.path.commonpath((os.path.normcase(root), os.path.normcase(path)))
        return common == os.path.normcase(root)
    except ValueError:
        return False


def confined_file(path, workspace, label="input"):
    """Return a resolved regular file path contained by workspace."""
    root = os.path.realpath(os.path.abspath(workspace))
    resolved = os.path.realpath(os.path.abspath(path))
    if not _inside(root, resolved):
        raise WorkspacePathError(f"{label} resolves outside the project root")
    if not os.path.isfile(resolved):
        raise WorkspacePathError(f"{label} not found: {path}")
    return resolved


def relative_file(value, base, workspace, label="input"):
    """Resolve a relative file reference from base, confined to workspace."""
    if not isinstance(value, str) or not value:
        raise WorkspacePathError(f"{label} must be a non-empty relative path")
    if os.path.isabs(value):
        raise WorkspacePathError(f"{label} must be relative to its source file")
    return confined_file(os.path.join(base, value), workspace, label)


def package_name(value, label="brand"):
    """Validate a Typst package name before placing it in generated source."""
    if not isinstance(value, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", value):
        raise WorkspacePathError(
            f"{label} must contain only lowercase letters, digits, and hyphens"
        )
    return value


def project_root_for(path, fallback):
    """Use the input's Git worktree when available, otherwise fallback."""
    directory = os.path.dirname(os.path.abspath(path))
    try:
        result = subprocess.run(
            ["git", "-C", directory, "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=False,
        )
    except FileNotFoundError:
        return os.path.abspath(fallback)
    if result.returncode == 0 and result.stdout.strip():
        return os.path.abspath(result.stdout.strip())
    return os.path.abspath(fallback)
