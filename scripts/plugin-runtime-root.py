#!/usr/bin/env python3
"""Print the containing Teamwork checkout root after validating its layout."""

from __future__ import annotations

import json
import stat
from pathlib import Path
from typing import Any


SUPPORTED_AGENT_HOSTS = frozenset({"codex", "cursor", "claude"})
REQUIRED_CHECKOUT_FILES = {
    "VERSION",
    "install.sh",
    "policy/teamwork-global.md",
    "config/teamwork-topology.json",
    "scripts/init-project-files.py",
    "scripts/plugin-runtime-root.py",
    "scripts/write-source-pointer.py",
}


def load_json(path: Path) -> dict[str, Any]:
    require_regular_file(path)
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"not a Teamwork source checkout: {path} is not an object")
    return value


def require_regular_file(path: Path) -> None:
    try:
        info = path.lstat()
    except OSError as exc:
        raise SystemExit(f"not a Teamwork source checkout: missing {path}") from exc
    if not stat.S_ISREG(info.st_mode):
        raise SystemExit(f"not a Teamwork source checkout: non-regular checkout file {path}")


def _relative_file(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise SystemExit(f"not a Teamwork source checkout: invalid {label}")
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise SystemExit(f"not a Teamwork source checkout: invalid {label}")
    return path.as_posix()


def validate_topology_layout(root: Path) -> None:
    topology = load_json(root / "config" / "teamwork-topology.json")
    skills = topology.get("public_skills")
    agents = topology.get("agents")
    if not isinstance(skills, list) or not skills or not isinstance(agents, list) or not agents:
        raise SystemExit("not a Teamwork source checkout: incomplete topology inventory")
    for row in skills:
        if not isinstance(row, dict):
            raise SystemExit("not a Teamwork source checkout: invalid skill topology")
        if "hosts" in row:
            hosts = row["hosts"]
            if not isinstance(hosts, list) or not hosts:
                raise SystemExit("not a Teamwork source checkout: invalid skill host topology")
            if any(not isinstance(item, str) or item not in SUPPORTED_AGENT_HOSTS for item in hosts):
                raise SystemExit("not a Teamwork source checkout: invalid skill host topology")
        require_regular_file(root / _relative_file(row.get("path"), "skill path"))
    for row in agents:
        if not isinstance(row, dict) or not isinstance(row.get("templates"), dict):
            raise SystemExit("not a Teamwork source checkout: invalid agent topology")
        templates = row["templates"]
        hosts = set(templates)
        # Validate each declared host file. Do not require {codex,cursor,claude}
        # on every agent: Codex is the supported minimum when present, and a
        # host may be omitted when the topology row intentionally drops it.
        if not hosts or not hosts.issubset(SUPPORTED_AGENT_HOSTS):
            raise SystemExit("not a Teamwork source checkout: invalid agent host topology")
        for host, relative in templates.items():
            require_regular_file(root / _relative_file(relative, f"{host} agent template"))


def validate_checkout_root(root: Path) -> None:
    git_entry = root / ".git"
    if not git_entry.exists():
        raise SystemExit("not a Teamwork source checkout: missing .git")

    for relative in REQUIRED_CHECKOUT_FILES:
        require_regular_file(root / relative)
    skills = root / "skills"
    if not skills.is_dir():
        raise SystemExit("not a Teamwork source checkout: missing skills/")
    validate_topology_layout(root)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    try:
        validate_checkout_root(root)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SystemExit(f"not a Teamwork source checkout: {exc}") from exc
    print(root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
