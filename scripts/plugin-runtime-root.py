#!/usr/bin/env python3
"""Print the containing Teamwork checkout root after validating its layout."""

from __future__ import annotations

import stat
from pathlib import Path


REQUIRED_CHECKOUT_FILES = {
    "VERSION",
    "install.sh",
    "policy/teamwork-global.md",
    "scripts/init-project-files.py",
    "scripts/plugin-runtime-root.py",
    "scripts/write-source-pointer.py",
    "skills/teamwork-collaborate/SKILL.md",
}


def require_regular_file(path: Path) -> None:
    try:
        info = path.lstat()
    except OSError as exc:
        raise SystemExit(f"not a Teamwork source checkout: missing {path}") from exc
    if not stat.S_ISREG(info.st_mode):
        raise SystemExit(f"not a Teamwork source checkout: non-regular checkout file {path}")


def validate_checkout_root(root: Path) -> None:
    git_entry = root / ".git"
    if not git_entry.exists():
        raise SystemExit("not a Teamwork source checkout: missing .git")

    for relative in REQUIRED_CHECKOUT_FILES:
        require_regular_file(root / relative)
    skills = root / "skills"
    if not skills.is_dir():
        raise SystemExit("not a Teamwork source checkout: missing skills/")


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    try:
        validate_checkout_root(root)
    except OSError as exc:
        raise SystemExit(f"not a Teamwork source checkout: {exc}") from exc
    print(root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
