#!/usr/bin/env python3
"""Derive docs/teamwork/INDEX.md from checkpoint files.

The index is rebuildable and is never a source of truth. --doctor reports
only; it is not a CI gate. --append-history is the append path: the model
supplies only the new entry text.
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
KINDS = (
    "discussions",
    "plans",
    "records",
    "experiments",
)
FOREIGN_PREFIXES: tuple[str, ...] = ()
DATE_PREFIX = re.compile(r"^(\d{4}-\d{2}-\d{2})-(.+)$")
SYNTHESIS_HEADINGS = (
    "Current synthesis",
    "Current stage",
    "Current execution plan",
    "Current project understanding",
    "当前项目理解",
    "当前综合",
)
SKIP_NAMES = frozenset({"INDEX.md", "index.json"})
STATUS_VALUES = frozenset({"active", "superseded", "archived"})


def default_docs_root(repo_root: Path) -> Path:
    return repo_root / "docs" / "teamwork"


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}, text
    meta: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        meta[key.strip()] = value.strip()
    body = text[end + 5 :]
    return meta, body


def first_heading(body: str) -> str:
    for line in body.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return ""


def first_sentence(text: str) -> str:
    collapsed = " ".join(text.split())
    if not collapsed:
        return ""
    for separator in ("。", ". ", "！", "？", "! ", "? "):
        index = collapsed.find(separator)
        if index > 0:
            end = index + (1 if separator.startswith(("。", "！", "？")) else 2)
            return collapsed[:end].strip()
    return collapsed


def synthesis_sentence(body: str) -> str:
    lowered = body
    for heading in SYNTHESIS_HEADINGS:
        marker = f"## {heading}"
        start = lowered.find(marker)
        if start < 0:
            continue
        rest = body[start + len(marker) :]
        nxt = rest.find("\n## ")
        section = rest if nxt < 0 else rest[:nxt]
        paragraphs = [part.strip() for part in section.split("\n\n") if part.strip()]
        for paragraph in paragraphs:
            if paragraph.startswith("#") or paragraph.startswith("<"):
                continue
            sentence = first_sentence(paragraph.lstrip("\n"))
            if sentence:
                return sentence
    for line in body.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and not stripped.startswith("---"):
            return first_sentence(stripped)
    return ""


def identity_slug(path: Path) -> str:
    stem = path.stem
    match = DATE_PREFIX.match(stem)
    return match.group(2) if match else stem


def filename_created(path: Path) -> str:
    match = DATE_PREFIX.match(path.stem)
    return match.group(1) if match else ""


def is_foreign(path: Path) -> bool:
    slug = identity_slug(path)
    return any(slug.startswith(prefix) for prefix in FOREIGN_PREFIXES)


def kind_of(docs_root: Path, path: Path) -> str | None:
    try:
        relative = path.relative_to(docs_root)
    except ValueError:
        return None
    parts = relative.parts
    if not parts:
        return None
    if parts[0] == "_archived" and len(parts) >= 2 and parts[1] in KINDS:
        return parts[1]
    if parts[0] in KINDS:
        return parts[0]
    return None


def iter_checkpoint_files(docs_root: Path) -> list[Path]:
    files: list[Path] = []
    if not docs_root.is_dir():
        return files
    for path in sorted(docs_root.rglob("*.md")):
        if path.name in SKIP_NAMES:
            continue
        if kind_of(docs_root, path) is None:
            continue
        files.append(path)
    return files


class Document:
    def __init__(self, docs_root: Path, path: Path) -> None:
        self.path = path
        self.rel = path.relative_to(docs_root).as_posix()
        self.kind = kind_of(docs_root, path) or ""
        text = path.read_text(encoding="utf-8")
        self.meta, self.body = parse_frontmatter(text)
        self.status = (self.meta.get("status") or "active").strip() or "active"
        self.created = self.meta.get("created", "").strip()
        self.updated = self.meta.get("updated", "").strip()
        self.superseded_by = self.meta.get("superseded-by", "").strip()
        self.title = first_heading(self.body)
        self.summary = synthesis_sentence(self.body)
        self.slug = identity_slug(path)
        self.foreign = is_foreign(path)
        self.text = text

    def index_line(self) -> str:
        title = self.title or self.path.stem
        summary = self.summary or title
        return f"- [`{title}`]({self.rel}) — {summary} (`{self.status}`)"


def load_documents(docs_root: Path) -> list[Document]:
    return [Document(docs_root, path) for path in iter_checkpoint_files(docs_root)]


def render_index(docs_root: Path, documents: list[Document]) -> str:
    lines = [
        "# Teamwork document index",
        "",
        "Derived from checkpoint files. Rebuild with `python3 scripts/teamwork-index.py`.",
        "Not a source of truth. Archived files live under Optional; do not treat",
        "this file as a workflow gate.",
        "",
    ]
    readme = docs_root / "README.md"
    mainline = docs_root / "mainline.md"
    entries = []
    if readme.is_file():
        entries.append("[README](README.md)")
    if mainline.is_file():
        entries.append("[mainline](mainline.md)")
    if entries:
        lines.append("Entry: " + " · ".join(entries))
        lines.append("")

    by_kind: dict[str, list[Document]] = {kind: [] for kind in KINDS}
    optional: dict[str, list[Document]] = {kind: [] for kind in KINDS}
    foreign: list[Document] = []
    for doc in documents:
        if doc.foreign:
            foreign.append(doc)
        if doc.status == "archived":
            optional.setdefault(doc.kind, []).append(doc)
        else:
            by_kind.setdefault(doc.kind, []).append(doc)

    for kind in KINDS:
        lines.append(f"## {kind}")
        lines.append("")
        rows = by_kind.get(kind, [])
        if not rows:
            lines.append("(none)")
        else:
            for doc in rows:
                lines.append(doc.index_line())
        lines.append("")

    lines.extend(
        [
            "## Optional",
            "",
            "Archived files, including other-project memories. Listed for retrieval;",
            "they are not current mainline.",
            "",
        ]
    )
    for kind in KINDS:
        rows = optional.get(kind, [])
        if not rows:
            continue
        lines.append(f"### {kind}")
        lines.append("")
        for doc in rows:
            if doc.foreign:
                continue
            lines.append(doc.index_line())
        lines.append("")
    if foreign:
        lines.append("### Other-project memories")
        lines.append("")
        for doc in foreign:
            lines.append(doc.index_line())
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_derived(docs_root: Path, documents: list[Document] | None = None) -> None:
    docs_root.mkdir(parents=True, exist_ok=True)
    documents = documents if documents is not None else load_documents(docs_root)
    (docs_root / "INDEX.md").write_text(render_index(docs_root, documents), encoding="utf-8")


def check_derived(docs_root: Path) -> int:
    documents = load_documents(docs_root)
    expected_index = render_index(docs_root, documents)
    index_path = docs_root / "INDEX.md"
    actual_index = index_path.read_text(encoding="utf-8") if index_path.is_file() else ""
    dirty = []
    if actual_index != expected_index:
        dirty.append(index_path.as_posix())
    if dirty:
        print("stale derived files:", ", ".join(dirty), file=sys.stderr)
        return 1
    print("OK: teamwork index")
    return 0


def resolve_superseded_target(docs_root: Path, doc: Document) -> Path | None:
    raw = doc.superseded_by
    if not raw:
        return None
    candidate = Path(raw)
    if candidate.is_absolute():
        return candidate if candidate.is_file() else None
    relative = (docs_root / raw).resolve()
    if relative.is_file():
        return relative
    sibling = (doc.path.parent / raw).resolve()
    if sibling.is_file():
        return sibling
    return None


def changelog_latest_date(repo_root: Path) -> str:
    path = repo_root / "CHANGELOG.md"
    if not path.is_file():
        return ""
    match = re.search(r"^## \d+\.\d+\.\d+ - (\d{4}-\d{2}-\d{2})", path.read_text(encoding="utf-8"), re.M)
    return match.group(1) if match else ""


def mainline_latest_date(docs_root: Path) -> str:
    path = docs_root / "mainline.md"
    if not path.is_file():
        return ""
    text = path.read_text(encoding="utf-8")
    dates = re.findall(r"^### (\d{4}-\d{2}-\d{2})", text, re.M)
    return dates[-1] if dates else ""


def doctor(repo_root: Path, docs_root: Path) -> int:
    documents = load_documents(docs_root)
    findings: list[str] = []
    product = changelog_latest_date(repo_root)
    mainline = mainline_latest_date(docs_root)
    if product and mainline and product > mainline:
        findings.append(
            f"stale mainline: last history {mainline}; CHANGELOG latest {product}"
        )
    elif product and not mainline:
        findings.append(f"stale mainline: no history date; CHANGELOG latest {product}")

    index_text = (docs_root / "INDEX.md").read_text(encoding="utf-8") if (docs_root / "INDEX.md").is_file() else ""
    for doc in documents:
        if doc.rel not in index_text:
            findings.append(f"missing-from-index: {doc.rel}")

    by_kind_slug: dict[tuple[str, str], list[str]] = {}
    for doc in documents:
        by_kind_slug.setdefault((doc.kind, doc.slug), []).append(doc.rel)
        if doc.status not in STATUS_VALUES:
            findings.append(f"unknown-status: {doc.rel} ({doc.status!r})")
        if doc.status == "superseded" and not doc.superseded_by:
            findings.append(f"broken superseded-by: {doc.rel} (empty)")
        if doc.superseded_by:
            target = resolve_superseded_target(docs_root, doc)
            if target is None:
                findings.append(
                    f"broken superseded-by: {doc.rel} -> {doc.superseded_by}"
                )
            else:
                back = target.read_text(encoding="utf-8")
                if doc.path.name not in back and doc.rel not in back:
                    findings.append(
                        f"broken superseded-by: {doc.rel} has no backlink from {target}"
                    )
    for (kind, slug), paths in sorted(by_kind_slug.items()):
        if len(paths) > 1:
            findings.append(f"duplicate slug: {kind}/{slug} -> {', '.join(paths)}")

    print("# teamwork-index doctor")
    print("Report only; not a CI gate.")
    if not findings:
        print("No findings.")
        return 0
    for item in findings:
        print(f"- {item}")
    return 0


def history_stamp() -> str:
    now = dt.datetime.now().astimezone()
    return now.strftime("%Y-%m-%d %H:%M %z")


def append_history(path: Path, entry: str) -> None:
    text = path.read_text(encoding="utf-8")
    entry = entry.strip("\n")
    if not entry.strip():
        raise SystemExit("append-history entry is empty")
    if "## History" not in text:
        raise SystemExit(f"no ## History section in {path}")
    if not entry.lstrip().startswith("### "):
        first = entry.splitlines()[0].strip()
        label = first[:80] if first else "update"
        entry = f"### {history_stamp()} — {label}\n\n{entry}"
    updated = text.rstrip() + "\n\n" + entry + "\n"
    meta, body = parse_frontmatter(updated)
    if meta:
        today = dt.date.today().isoformat()
        lines = ["---"]
        seen_updated = False
        for raw in text.splitlines()[1:]:
            if raw == "---":
                break
            if raw.startswith("updated:"):
                lines.append(f"updated: {today}")
                seen_updated = True
            else:
                lines.append(raw)
        if not seen_updated:
            lines.append(f"updated: {today}")
        rest_start = updated.find("\n---\n", 4)
        body_out = updated[rest_start + 5 :] if rest_start >= 0 else body
        updated = "\n".join(lines) + "\n---\n" + body_out.lstrip("\n")
        if not updated.endswith("\n"):
            updated += "\n"
    path.write_text(updated, encoding="utf-8")
    print(f"appended history: {path}")


def frontmatter_block(status: str, created: str, extra: dict[str, str] | None = None) -> str:
    lines = [
        "---",
        f"status: {status}",
        "superseded-by:",
        f"created: {created}",
        f"updated: {created}",
    ]
    if extra:
        for key, value in extra.items():
            lines.append(f"{key}: {value}")
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def backfill(docs_root: Path, force: bool = False) -> int:
    changed = 0
    skipped = 0
    for path in iter_checkpoint_files(docs_root):
        text = path.read_text(encoding="utf-8")
        meta, _body = parse_frontmatter(text)
        if meta.get("status"):
            continue
        if not force and not DATE_PREFIX.match(path.stem):
            skipped += 1
            continue
        created = filename_created(path)
        status = "archived"
        prefix = frontmatter_block(status, created)
        path.write_text(prefix + text.lstrip("\n"), encoding="utf-8")
        changed += 1
    print(f"backfilled frontmatter: {changed}")
    if skipped:
        print(f"skipped slug-only files without status: {skipped} (pass --force to archive)")
    return 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--repo-root", type=Path, default=ROOT)
    result.add_argument("--docs-root", type=Path)
    result.add_argument("--check", action="store_true", help="fail if INDEX.md is stale")
    result.add_argument(
        "--doctor",
        action="store_true",
        help="report stale mainline, missing index rows, broken supersede links, duplicate slugs",
    )
    result.add_argument(
        "--append-history",
        metavar="PATH",
        help="append a History entry; pass the entry as a following argument or on stdin",
    )
    result.add_argument(
        "--backfill",
        action="store_true",
        help="add archived frontmatter to date-prefixed historical files that lack status",
    )
    result.add_argument(
        "--force",
        action="store_true",
        help="with --backfill, also archive slug-only files that lack status",
    )
    result.add_argument(
        "entry",
        nargs="?",
        help="History entry text for --append-history; stdin if omitted",
    )
    return result


def main() -> int:
    arguments = parser().parse_args()
    repo_root = arguments.repo_root.resolve()
    docs_root = (arguments.docs_root or default_docs_root(repo_root)).resolve()
    try:
        if arguments.append_history:
            path = Path(arguments.append_history)
            if not path.is_absolute():
                path = (repo_root / path).resolve()
            entry = arguments.entry if arguments.entry is not None else sys.stdin.read()
            append_history(path, entry)
            return 0
        if arguments.backfill:
            backfill(docs_root, force=arguments.force)
            write_derived(docs_root)
            return 0
        if arguments.doctor:
            return doctor(repo_root, docs_root)
        if arguments.check:
            return check_derived(docs_root)
        write_derived(docs_root)
        print(f"wrote {docs_root / 'INDEX.md'}")
        return 0
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"teamwork-index failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
