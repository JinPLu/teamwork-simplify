#!/usr/bin/env python3
"""Create or refresh Teamwork's small project-local agent instruction block."""

from __future__ import annotations

import argparse
import os
import re
import stat
import sys
from pathlib import Path


MANAGED_START = "<!-- TEAMWORK_PROJECT_START -->"
MANAGED_END = "<!-- TEAMWORK_PROJECT_END -->"
BRIDGE_START = "<!-- TEAMWORK_CLAUDE_BRIDGE_START -->"
BRIDGE_END = "<!-- TEAMWORK_CLAUDE_BRIDGE_END -->"
AGENTS_IMPORT = "@AGENTS.md"
CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")
CODE_SPAN_RE = re.compile(r"`[^`]*`")


class InitError(RuntimeError):
    pass


def checked_project_root(raw: str) -> Path:
    if not raw or CONTROL_RE.search(raw):
        raise InitError("project root must be non-empty text without control characters")
    root = Path(os.path.abspath(os.path.expanduser(raw)))
    if not root.is_dir():
        raise InitError(f"project root is not a directory: {root}")
    return root


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    info = path.lstat()
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise InitError(f"target must be a regular non-symlink file: {path}")
    return path.read_text(encoding="utf-8")


def project_label(root: Path, explicit: str | None) -> str:
    label = (explicit or root.name).strip()
    if not label or CONTROL_RE.search(label):
        raise InitError("project label must be non-empty text without control characters")
    return label


def managed_block(label: str) -> str:
    return (
        f"{MANAGED_START}\n"
        "## Teamwork Project Instructions\n\n"
        f"- Project label: `{label}`.\n"
        "- Teamwork adds no required project-local workflow or state. It creates "
        "no empty directory, schema, or mandatory stage chain. Native host modes "
        "stay in charge. Follow this project's normal instructions and invoke a "
        "named Skill only when its trigger matches.\n"
        "- User-accepted reusable results live under `docs/teamwork/<kind>/` as "
        "one of `discussions`, `plans`, `records`, or `experiments`. Chat, host "
        "plans, and todos are not cross-session memory.\n"
        f"{MANAGED_END}\n"
    )


def bridge_block() -> str:
    return (
        f"{BRIDGE_START}\n"
        "<!-- A host that reads CLAUDE.md instead of AGENTS.md gets the project "
        "block through this import. -->\n"
        f"{AGENTS_IMPORT}\n"
        f"{BRIDGE_END}\n"
    )


def replace_block(
    text: str,
    block: str,
    start: str = MANAGED_START,
    end: str = MANAGED_END,
    empty_header: str = "# Repository Guidelines\n\n",
) -> str:
    if text.count(start) != text.count(end) or text.count(start) > 1:
        raise InitError("Teamwork managed block markers are ambiguous")
    if start in text:
        before, rest = text.split(start, 1)
        _old, after = rest.split(end, 1)
        return before + block + after.lstrip("\n")
    if not text:
        return empty_header + block
    return text + ("\n" if text.endswith("\n") else "\n\n") + block


def write_managed_file(path: Path, text: str, after: str) -> None:
    if after == text:
        return
    temporary = path.with_name(f".{path.name}.teamwork-tmp")
    if temporary.exists() or temporary.is_symlink():
        raise InitError(f"temporary path already exists: {temporary}")
    try:
        temporary.write_text(after, encoding="utf-8")
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def write_agents(root: Path, label: str) -> None:
    path = root / "AGENTS.md"
    before = read_text(path)
    write_managed_file(path, before, replace_block(before, managed_block(label)))


def bridge_links_to_agents(root: Path) -> bool:
    """True when CLAUDE.md is a symlink that already resolves to AGENTS.md."""
    path = root / "CLAUDE.md"
    if not path.is_symlink():
        return False
    try:
        target = path.resolve(strict=True)
    except OSError as exc:
        raise InitError(f"CLAUDE.md is a broken symlink: {path}") from exc
    if target != (root / "AGENTS.md").resolve():
        raise InitError(f"CLAUDE.md is a symlink outside Teamwork ownership: {path}")
    return True


def has_agents_import(text: str) -> bool:
    """True when an import of AGENTS.md is already active outside code."""
    fenced = False
    for line in text.splitlines():
        if line.strip().startswith("```"):
            fenced = not fenced
            continue
        if fenced:
            continue
        if AGENTS_IMPORT in CODE_SPAN_RE.sub("", line):
            return True
    return False


def bridge_plan(root: Path) -> tuple[Path, str, str] | None:
    """Return (path, before, after) for the bridge, or None when nothing to do."""
    if bridge_links_to_agents(root):
        return None
    path = root / "CLAUDE.md"
    before = read_text(path)
    if BRIDGE_START not in before and has_agents_import(before):
        return None
    return path, before, replace_block(
        before, bridge_block(), BRIDGE_START, BRIDGE_END, ""
    )


def write_claude_bridge(root: Path) -> None:
    planned = bridge_plan(root)
    if planned is None:
        return
    write_managed_file(*planned)


def validate(root: Path) -> None:
    text = read_text(root / "AGENTS.md")
    if text.count(MANAGED_START) != 1 or text.count(MANAGED_END) != 1:
        raise InitError("AGENTS.md Teamwork managed block is missing or ambiguous")
    if bridge_links_to_agents(root):
        return
    bridge = read_text(root / "CLAUDE.md")
    if bridge.count(BRIDGE_START) != bridge.count(BRIDGE_END) or bridge.count(BRIDGE_START) > 1:
        raise InitError("CLAUDE.md Teamwork bridge markers are ambiguous")
    if not has_agents_import(bridge):
        raise InitError("CLAUDE.md does not import AGENTS.md")


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--project-root", default=os.getcwd())
    sub = result.add_subparsers(dest="action", required=True)
    sub.add_parser("print-root")
    sub.add_parser("preflight")
    initialize = sub.add_parser("initialize")
    initialize.add_argument("--project-label")
    initialize.add_argument("--full-bootstrap", action="store_true")
    refresh = sub.add_parser("refresh-context")
    refresh.add_argument("--project-label")
    sub.add_parser("validate")
    return result


def main() -> int:
    arguments = parser().parse_args()
    try:
        root = checked_project_root(arguments.project_root)
        if arguments.action == "print-root":
            print(root)
        elif arguments.action == "preflight":
            text = read_text(root / "AGENTS.md")
            replace_block(text, managed_block(project_label(root, None)))
            bridge_plan(root)
        elif arguments.action in {"initialize", "refresh-context"}:
            write_agents(root, project_label(root, arguments.project_label))
            write_claude_bridge(root)
            validate(root)
        else:
            validate(root)
    except (InitError, OSError, UnicodeError) as exc:
        print(f"Teamwork project init failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
