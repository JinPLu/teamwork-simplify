#!/usr/bin/env python3
"""Fill <!-- BEGIN GENERATED --> blocks from config/teamwork-facts.yaml."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from teamwork_tooling.simple_yaml import load_simple_yaml  # noqa: E402

FACTS_REL = Path("config/teamwork-facts.yaml")
BEGIN = "<!-- BEGIN GENERATED: {name} -->"
END = "<!-- END GENERATED: {name} -->"
BLOCK_RE = re.compile(
    r"<!-- BEGIN GENERATED: ([a-z0-9-]+) -->\n.*?<!-- END GENERATED: \1 -->",
    re.DOTALL,
)

TARGETS = (
    Path("README.md"),
    Path("README.en.md"),
    Path("CURSOR.md"),
    Path("CLAUDE.md"),
    Path("CODEX.md"),
    Path("docs/architecture.md"),
)


def facts_path(root: Path) -> Path:
    return root / FACTS_REL


def load_facts(root: Path) -> dict:
    return load_simple_yaml(facts_path(root))


def _kinds(facts: dict) -> list[str]:
    kinds = facts["kinds"]
    if not isinstance(kinds, list) or not kinds:
        raise SystemExit("facts.yaml kinds must be a non-empty list")
    return [str(item) for item in kinds]


def render_blocks(facts: dict) -> dict[str, str]:
    kinds = _kinds(facts)
    meanings = facts["kind_meanings"]
    hosts = facts["hosts"]
    checkpoint = facts["checkpoint_path"]
    kind_root = facts["kind_root"]

    meaning_lines = ["The four meanings are:", ""]
    for index, kind in enumerate(kinds):
        row = meanings[kind]
        suffix = ";" if index < len(kinds) - 1 else "."
        meaning_lines.append(
            f"- {row['label']} (`{kind}/`): {row['meaning']}{suffix}"
        )
    kind_meanings = "\n".join(meaning_lines)

    table_zh_rows = ["| 文档 | 它记录什么 |", "| --- | --- |"]
    table_en_rows = ["| Document | What it records |", "| --- | --- |"]
    for kind in kinds:
        row = meanings[kind]
        table_zh_rows.append(f"| {row['emoji']} {row['label']} | {row['meaning_zh']} |")
        table_en_rows.append(
            f"| {row['emoji']} {row['label']} | {row['meaning'][0].upper() + row['meaning'][1:]}. |"
        )

    host_names = sorted(hosts)
    skill_counts = {hosts[host]["skills"] for host in host_names}
    role_counts = {hosts[host]["roles"] for host in host_names}
    if len(skill_counts) == 1 and len(role_counts) == 1:
        (skills_n,) = skill_counts
        (roles_n,) = role_counts
        host_counts = (
            f"Codex, Cursor, and Claude Code install the same footprint: "
            f"{skills_n} Skill and {roles_n} optional roles. No host omits a "
            "role or the Skill."
        )
        host_counts_zh = (
            f"Codex、Cursor 与 Claude Code 安装的内容完全一致：{skills_n} 个 Skill "
            f"与 {roles_n} 个可选角色，没有宿主省略角色或 Skill。"
        )
    else:
        per_host = "; ".join(
            f"{host}: {hosts[host]['skills']} Skill(s), {hosts[host]['roles']} role(s)"
            for host in host_names
        )
        host_counts = f"Host footprint differs: {per_host}."
        host_counts_zh = f"各宿主安装内容不同：{per_host}。"

    persistence_zh = (
        "当原生交互或 `teamwork-collaborate` 到达可复用语义结果、且你已经接受该"
        f"结果时，Root 在同一响应周期把纯 Markdown 写入 `{kind_root}`；进入宿主"
        "界面本身不会落盘，也不必先点名 Skill。Writer 只在不耽误写入时帮忙。每份"
        "文档同时保留一份**当前综合**和按时间追加的**历史**，既方便快速阅读，也"
        f"不会抹掉结论如何变化。默认路径为 `{checkpoint}`，同一稳定身份复用已有"
        "路径。\n\n" + "\n".join(table_zh_rows)
    )
    persistence_en = (
        "When a native interaction or `teamwork-collaborate` reaches a reusable "
        f"semantic result and you accept that result, Root writes plain Markdown "
        f"under `{kind_root}` in the same response cycle. Entering a host surface "
        "is not itself a write, and you do not need to name the Skill first. "
        "Writer helps only when that does not delay the write. Each document "
        "carries both a **current synthesis** and an append-only **chronological "
        "history**, so it is quick to read without hiding how the conclusion "
        f"changed. Default paths are `{checkpoint}`; reuse the path for the same "
        "stable identity.\n\n" + "\n".join(table_en_rows)
    )
    return {
        "kind-meanings": kind_meanings,
        "host-counts": host_counts,
        "host-counts-zh": host_counts_zh,
        "persistence-zh": persistence_zh,
        "persistence-en": persistence_en,
        "kind-root": f"`{kind_root}`",
        "checkpoint-path": f"`{checkpoint}`",
    }


def replace_blocks(text: str, blocks: dict[str, str], rel: Path) -> str:
    names = BLOCK_RE.findall(text)
    if not names:
        return text

    def repl(match: re.Match[str]) -> str:
        name = match.group(1)
        if name not in blocks:
            raise SystemExit(f"unknown generated block {name!r} in {rel}")
        return f"{BEGIN.format(name=name)}\n{blocks[name]}\n{END.format(name=name)}"

    updated = BLOCK_RE.sub(repl, text)
    missing = [name for name in names if name not in blocks]
    if missing:
        raise SystemExit(f"unknown generated blocks in {rel}: {missing}")
    return updated


def iter_targets(root: Path) -> list[Path]:
    return [root / rel for rel in TARGETS]


def apply(root: Path, check: bool) -> int:
    blocks = render_blocks(load_facts(root))
    dirty: list[str] = []
    for path in iter_targets(root):
        before = path.read_text(encoding="utf-8")
        after = replace_blocks(before, blocks, path.relative_to(root))
        if after != before:
            dirty.append(path.relative_to(root).as_posix())
            if not check:
                path.write_text(after, encoding="utf-8")
    if check and dirty:
        print("stale generated docs:", ", ".join(dirty), file=sys.stderr)
        return 1
    if not check and dirty:
        print("updated:", ", ".join(dirty))
    else:
        print("OK: generated docs facts")
    return 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--root", type=Path, default=ROOT)
    result.add_argument(
        "--check",
        action="store_true",
        help="fail when tracked files differ from rendered facts",
    )
    return result


def main() -> int:
    arguments = parser().parse_args()
    root = arguments.root.resolve()
    try:
        return apply(root, arguments.check)
    except (OSError, ValueError, KeyError) as exc:
        print(f"render-teamwork-facts failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
