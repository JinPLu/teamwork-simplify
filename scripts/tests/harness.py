"""Shared fixtures for Teamwork behavior tests.

Every test in this suite runs the real installer or the real project-init
script against a throwaway HOME and a throwaway project directory, then reads
the resulting filesystem back. Nothing here asserts on wording: the helpers
only run processes and describe bytes.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

CLAUDE_POLICY_START = "<!-- TEAMWORK_CLAUDE_GLOBAL_START -->"
CLAUDE_POLICY_END = "<!-- TEAMWORK_CLAUDE_GLOBAL_END -->"
CODEX_POLICY_START = "<!-- TEAMWORK_CODEX_GLOBAL_START -->"
CODEX_POLICY_END = "<!-- TEAMWORK_CODEX_GLOBAL_END -->"
PROJECT_START = "<!-- TEAMWORK_PROJECT_START -->"
PROJECT_END = "<!-- TEAMWORK_PROJECT_END -->"

# Written on every install, and deliberately carries an install timestamp, so
# it is excluded from byte-identity comparisons across runs.
POINTER_RELATIVE = ".teamwork/install.json"

CHECKOUT_IGNORE = shutil.ignore_patterns(".git", "__pycache__", "*.pyc", ".DS_Store")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot(root: Path, skip: tuple[str, ...] = ()) -> dict[str, str]:
    """Describe a tree by content, not by mtime: path -> kind + content hash."""
    root = Path(root)
    skipped = set(skip)
    result: dict[str, str] = {}
    for current, directories, files in os.walk(root, followlinks=False):
        here = Path(current)
        for name in list(directories):
            path = here / name
            relative = str(path.relative_to(root))
            if relative in skipped:
                directories.remove(name)
                continue
            if path.is_symlink():
                directories.remove(name)
                result[relative] = "link:" + os.readlink(path)
            else:
                result[relative] = "dir"
        for name in files:
            path = here / name
            relative = str(path.relative_to(root))
            if relative in skipped:
                continue
            if path.is_symlink():
                result[relative] = "link:" + os.readlink(path)
            else:
                result[relative] = "file:" + digest(path)
    return result


def split_managed(text: str, start: str, end: str) -> tuple[str, str, str]:
    """Return (before, inside, after) for exactly one managed block."""
    before, rest = text.split(start, 1)
    inside, after = rest.split(end, 1)
    return before, inside, after


class TeamworkCase(unittest.TestCase):
    """Base case that owns a throwaway HOME and throwaway working directories."""

    def setUp(self) -> None:
        self.home = self.temp_dir("home")
        self.workdir = self.temp_dir("cwd")

    def temp_dir(self, label: str) -> Path:
        holder = tempfile.TemporaryDirectory(prefix=f"teamwork-{label}-")
        self.addCleanup(holder.cleanup)
        return Path(holder.name).resolve()

    # ---- running the real scripts ------------------------------------------

    def install(
        self,
        *args: str,
        checkout: Path | None = None,
        cwd: Path | None = None,
        env_extra: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        environment = {
            "HOME": str(self.home),
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "TMPDIR": os.environ.get("TMPDIR", "/tmp"),
            "LANG": "C",
            "PYTHONDONTWRITEBYTECODE": "1",
        }
        if env_extra:
            environment.update(env_extra)
        return subprocess.run(
            ["bash", str(Path(checkout or ROOT) / "install.sh"), *args],
            capture_output=True,
            text=True,
            cwd=str(cwd or self.workdir),
            env=environment,
        )

    def install_ok(self, *args: str, **kwargs: object) -> subprocess.CompletedProcess[str]:
        done = self.install(*args, **kwargs)  # type: ignore[arg-type]
        self.assertEqual(
            done.returncode,
            0,
            f"install.sh {' '.join(args)} failed\nstdout:\n{done.stdout}\nstderr:\n{done.stderr}",
        )
        return done

    def checkout_copy(self, name: str, version: str) -> Path:
        """A second working copy of this checkout, stamped with its own VERSION."""
        destination = self.temp_dir(name) / "teamwork"
        shutil.copytree(ROOT, destination, ignore=CHECKOUT_IGNORE, symlinks=True)
        (destination / "VERSION").write_text(version + "\n", encoding="utf-8")
        return destination

    # ---- fixture writers ----------------------------------------------------

    def write(self, path: Path, text: str) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def write_skill(self, root: Path, name: str, frontmatter_name: str, body: str) -> Path:
        entry = root / name
        self.write(
            entry / "SKILL.md",
            f"---\nname: {frontmatter_name}\ndescription: {body.splitlines()[0]}\n---\n\n{body}\n",
        )
        return entry

    def write_agent(self, root: Path, name: str, first_line: str) -> Path:
        return self.write(
            root / f"{name}.md",
            f"---\nname: {name}\ndescription: fixture\ntools: Read\nmodel: sonnet\neffort: high\n---\n{first_line}\n",
        )
