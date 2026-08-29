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
README_IMPORT = "@docs/teamwork/README.md"
DOCS_README_RELATIVE = ("docs", "teamwork", "README.md")
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
    if not label or CONTROL_RE.search(label) or "`" in label:
        raise InitError(
            "project label must be non-empty text without control characters or backticks"
        )
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
        "- This project's Teamwork context lives under `docs/teamwork/` at the "
        "repository root, with `docs/teamwork/README.md` as the reading-side "
        "entry point; the global policy's project-context contract owns it, and "
        "this block only adds project-specific detail.\n"
        f"{MANAGED_END}\n"
    )


def project_constraints_seed() -> str:
    return (
        "## Project-specific constraints\n\n"
        "Fill this in with what only this project knows — its code style "
        "boundaries, directory tidiness expectations, and mechanisms it allows "
        "or forbids. Teamwork does not decide this content.\n\n"
        "- <add a project-specific constraint here>\n"
        "- <add another one here>\n"
    )


def seed_project_constraints(text: str) -> str:
    # `replace_block` strips every leading newline from whatever trails the
    # managed block on a later run (see its `after.lstrip("\n")`), so the
    # seed must sit immediately after the block's own trailing newline with
    # no blank-line separator — anything else would not be a fixed point and
    # would get squeezed away the next time `initialize` regenerates the
    # block, breaking idempotency.
    return text + project_constraints_seed()


def bridge_block(include_agents_import: bool) -> str:
    agents_part = (
        "<!-- A host that reads CLAUDE.md instead of AGENTS.md gets the project "
        "block through this import. -->\n"
        f"{AGENTS_IMPORT}\n"
    ) if include_agents_import else ""
    return (
        f"{BRIDGE_START}\n"
        f"{agents_part}"
        "<!-- The project's Teamwork reading-side entry point, loaded into every "
        "session's context. -->\n"
        f"{README_IMPORT}\n"
        f"{BRIDGE_END}\n"
    )


def text_outside_bridge_block(text: str) -> str:
    """The bridge block's own generated import line is never the user's own
    copy; only content the user actually authored, outside the block, counts
    toward an already-active `@AGENTS.md` import."""
    if text.count(BRIDGE_START) != 1 or text.count(BRIDGE_END) != 1:
        return text
    before, rest = text.split(BRIDGE_START, 1)
    if BRIDGE_END not in rest:
        return text
    _inside, after = rest.split(BRIDGE_END, 1)
    return before + after


def project_docs_readme() -> str:
    return (
        "# Project Teamwork Documents\n\n"
        "This is the project's Teamwork reading side: read it before work that "
        "depends on what this project already decided, concluded, or tried.\n\n"
        "## Project current state\n\n"
        "<!-- What is being worked on now, what has already been settled, and "
        "where it is currently blocked. Keep this current here instead of "
        "narrating it in chat. -->\n\n"
        "## Document index\n\n"
        "<!-- One line per document: a link plus a one-sentence description, "
        "grouped by kind under docs/teamwork/<kind>/. -->\n\n"
        "No documents yet.\n"
    )


def write_project_docs_readme(root: Path) -> None:
    path = root.joinpath(*DOCS_README_RELATIVE)
    if path.exists() or path.is_symlink():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    write_managed_file(path, read_text(path), project_docs_readme())


def replace_block(
    text: str,
    block: str,
    start: str = MANAGED_START,
    end: str = MANAGED_END,
    empty_header: str = "# Repository Guidelines\n\n",
) -> str:
    if text.count(start) != text.count(end) or text.count(start) > 1:
        raise InitError("Teamwork managed block markers are ambiguous")
    if start in text and text.index(end) < text.index(start):
        raise InitError("Teamwork managed block end marker precedes its start marker")
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
    after = replace_block(before, managed_block(label))
    if MANAGED_START not in before:
        # Seed the placeholder once, for this project's own future edits, and
        # never touch it again on later initialize/refresh-context runs.
        after = seed_project_constraints(after)
    write_managed_file(path, before, after)


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
    include_agents_import = not has_agents_import(text_outside_bridge_block(before))
    after = replace_block(
        before, bridge_block(include_agents_import), BRIDGE_START, BRIDGE_END, ""
    )
    return path, before, after


def write_claude_bridge(root: Path) -> None:
    if bridge_links_to_agents(root):
        print(
            f"Teamwork: {root / 'CLAUDE.md'} is a symlink to AGENTS.md, so "
            "docs/teamwork/README.md is not auto-imported for this project."
        )
        return
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
            write_project_docs_readme(root)
            validate(root)
        else:
            validate(root)
    except (InitError, OSError, UnicodeError) as exc:
        print(f"Teamwork project init failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
