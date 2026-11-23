"""Shared test harness running the real CLI against throwaway HOME directories."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
POLICY_START = "<!-- TEAMWORK_GLOBAL_START -->"
POLICY_END = "<!-- TEAMWORK_GLOBAL_END -->"
CHECKOUT_IGNORE = shutil.ignore_patterns(".git", "__pycache__", "*.pyc", ".DS_Store", "docs", ".claude")


def snapshot(root: Path) -> dict[str, str | bytes]:
    """Map relative paths under root to 'dir', 'link:<target>', or raw file bytes."""
    result: dict[str, str | bytes] = {}
    if not root.exists():
        return result
    for current, dirs, files in os.walk(root, followlinks=False):
        here = Path(current)
        for name in list(dirs):
            path = here / name
            rel = path.relative_to(root).as_posix()
            if path.is_symlink():
                dirs.remove(name)
                result[rel] = "link:" + os.readlink(path)
            else:
                result[rel] = "dir"
        for name in files:
            path = here / name
            rel = path.relative_to(root).as_posix()
            if path.is_symlink():
                result[rel] = "link:" + os.readlink(path)
            else:
                result[rel] = path.read_bytes()
    return result


def split_managed(text: str, start: str = POLICY_START, end: str = POLICY_END) -> tuple[str, str, str]:
    before, rest = text.split(start, 1)
    inside, after = rest.split(end, 1)
    return before, inside, after


class TeamworkCase(unittest.TestCase):
    def setUp(self) -> None:
        self.home = self.temp_dir("home")
        self.workdir = self.temp_dir("cwd")

    def temp_dir(self, label: str) -> Path:
        holder = tempfile.TemporaryDirectory(prefix=f"teamwork-{label}-")
        self.addCleanup(holder.cleanup)
        return Path(holder.name).resolve()

    def cli(
        self,
        *args: str,
        checkout: Path | None = None,
        env_extra: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        env = {
            "HOME": str(self.home),
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "TMPDIR": os.environ.get("TMPDIR", "/tmp"),
            "LANG": "C",
            "PYTHONDONTWRITEBYTECODE": "1",
        }
        if env_extra:
            env.update(env_extra)
        return subprocess.run(
            ["bash", str(Path(checkout or ROOT) / "install.sh"), *args],
            capture_output=True,
            text=True,
            cwd=str(self.workdir),
            env=env,
        )

    def cli_ok(self, *args: str, **kwargs: object) -> subprocess.CompletedProcess[str]:
        done = self.cli(*args, **kwargs)  # type: ignore[arg-type]
        self.assertEqual(
            done.returncode,
            0,
            f"install.sh {' '.join(args)} failed ({done.returncode})\nstdout:\n{done.stdout}\nstderr:\n{done.stderr}",
        )
        return done

    def doctor_json(self, *extra_args: str) -> tuple[int, dict]:
        done = self.cli("doctor", "--json", *extra_args)
        self.assertIn(
            done.returncode,
            (0, 1),
            f"doctor crashed\nstdout:\n{done.stdout}\nstderr:\n{done.stderr}",
        )
        return done.returncode, json.loads(done.stdout)

    def checkout_copy(self, version: str) -> Path:
        dest = self.temp_dir("checkout") / "teamwork"
        shutil.copytree(ROOT, dest, ignore=CHECKOUT_IGNORE, symlinks=True)
        (dest / "VERSION").write_text(version + "\n", encoding="utf-8")
        return dest

    def write(self, path: Path, text: str) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path
