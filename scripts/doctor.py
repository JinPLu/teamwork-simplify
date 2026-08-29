#!/usr/bin/env python3
"""Read-only contract-drift check for Teamwork's installed and project surfaces.

Nothing here writes, fixes, or gates: every check reads files and the
installer's own status helpers. It answers one question — where has reality
drifted from the contract in `policy/teamwork-global.md` and from what the
installer declares it installs.
"""

from __future__ import annotations

import sys

sys.dont_write_bytecode = True

import argparse
import importlib.util
import json
import os
import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
POLICY_SOURCE = REPO_ROOT / "policy" / "teamwork-global.md"
COMMON_SH = REPO_ROOT / "scripts" / "install" / "common.sh"
POLICY_SH = REPO_ROOT / "scripts" / "install" / "policy.sh"
INIT_PROJECT_FILES = REPO_ROOT / "scripts" / "init-project-files.py"

MANAGED_START = "<!-- TEAMWORK_PROJECT_START -->"
MANAGED_END = "<!-- TEAMWORK_PROJECT_END -->"

# The contract's persistence root and the one file it allows at that root.
DOCS_RELATIVE = ("docs", "teamwork")
INDEX_NAME = "README.md"

SEVERITY_ORDER = {"error": 0, "warn": 1, "info": 2}

PRUNED_DIRECTORY_NAMES = {
    "node_modules",
    "__pycache__",
    "venv",
    "env",
    "site-packages",
    "target",
    "Library",
}
MAX_SCAN_DEPTH = 5

# The kind table in the policy source: every row ends in the kind directory it
# names. Reading the table's shape, not any sentence around it, keeps the closed
# set single-sourced without depending on the prose that introduces it.
KIND_TABLE_ROW = re.compile(r"^\|.*\|\s*`([a-z][a-z0-9_-]*)/`\s*\|\s*$")

MARKDOWN_LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
BACKTICKED = re.compile(r"`([^`\n]+)`")
KEBAB_IDENTIFIER = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)+$")

SKILL_ROOTS = (
    Path.home() / ".claude" / "skills",
    Path.home() / ".agents" / "skills",
    Path.home() / ".cursor" / "skills",
    Path.home() / ".codex" / "skills",
)


class DoctorError(RuntimeError):
    pass


def finding(severity: str, check: str, message: str, **extra: object) -> dict:
    result = {"severity": severity, "check": check, "message": message}
    result.update(extra)
    return result


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


# --- the contract ----------------------------------------------------------


def closed_kind_set() -> set[str]:
    """The closed kind set, parsed out of the policy source that owns it."""
    text = read_text(POLICY_SOURCE)
    if not text:
        raise DoctorError(f"policy source is unreadable: {POLICY_SOURCE}")
    kinds = {
        match.group(1)
        for match in (KIND_TABLE_ROW.match(line) for line in text.splitlines())
        if match
    }
    if not kinds:
        raise DoctorError(
            f"no kind table row in {POLICY_SOURCE}; the closed set cannot be established"
        )
    return kinds


def installer_skill_names() -> tuple[set[str], set[str]]:
    """(current, retired) Teamwork Skill names, as the installer declares them."""
    text = read_text(COMMON_SH)
    lists: list[set[str]] = []
    for array in ("SKILLS", "RETIRED_SKILLS"):
        match = re.search(rf"^{array}=\(([^)]*)\)", text, re.MULTILINE)
        lists.append(set(match.group(1).split()) if match else set())
    if not lists[0]:
        raise DoctorError(f"could not read the Teamwork skill name list from {COMMON_SH}")
    return lists[0], lists[1]


def load_project_init_module():
    spec = importlib.util.spec_from_file_location(
        "teamwork_init_project_files", INIT_PROJECT_FILES
    )
    if spec is None or spec.loader is None:
        raise DoctorError(f"cannot load {INIT_PROJECT_FILES}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "has_agents_import"):
        raise DoctorError(
            f"{INIT_PROJECT_FILES} no longer exposes has_agents_import(); host reachability "
            "is decided by that function and is not reimplemented here"
        )
    return module


def managed_policy_status(platform: str) -> str:
    """Reuse the installer's own comparison instead of writing a second one."""
    script = (
        f'ROOT={json.dumps(str(REPO_ROOT))}\n'
        f'source {json.dumps(str(COMMON_SH))}\n'
        f'source {json.dumps(str(POLICY_SH))}\n'
        f'teamwork_managed_policy_status {platform}\n'
    )
    completed = subprocess.run(
        ["bash", "-c", script], capture_output=True, text=True, check=False
    )
    if completed.returncode != 0:
        return "unknown"
    return completed.stdout.strip() or "unknown"


# --- project discovery -----------------------------------------------------


def has_managed_block(path: Path) -> bool:
    return MANAGED_START in read_text(path)


def is_project(directory: Path) -> bool:
    if directory.joinpath(*DOCS_RELATIVE).is_dir():
        return True
    return has_managed_block(directory / "AGENTS.md") or has_managed_block(
        directory / "CLAUDE.md"
    )


def discover_projects(scan_root: Path, extra_roots: list[Path]) -> list[Path]:
    found: list[Path] = []
    seen: set[Path] = set()

    def remember(candidate: Path) -> None:
        resolved = candidate.resolve()
        if resolved not in seen:
            seen.add(resolved)
            found.append(resolved)

    for root in extra_roots:
        if root.is_dir() and is_project(root):
            remember(root)

    if scan_root.is_dir():
        base_depth = len(scan_root.parts)
        for current, directories, _files in os.walk(scan_root, followlinks=False):
            here = Path(current)
            depth = len(here.parts) - base_depth
            directories[:] = [
                name
                for name in directories
                if not name.startswith(".")
                and name not in PRUNED_DIRECTORY_NAMES
                and depth < MAX_SCAN_DEPTH
            ]
            if is_project(here):
                remember(here)
    return sorted(found, key=lambda path: str(path))


# --- per-project checks ----------------------------------------------------


def managed_block_text(text: str) -> str:
    if MANAGED_START not in text or MANAGED_END not in text:
        return ""
    body = text.split(MANAGED_START, 1)[1]
    return body.split(MANAGED_END, 1)[0] if MANAGED_END in body else ""


def spelling_variant(kind: str, closed: set[str]) -> str | None:
    if kind + "s" in closed:
        return kind + "s"
    if kind.endswith("s") and kind[:-1] in closed:
        return kind[:-1]
    return None


def documents_on_disk(docs_root: Path, closed: set[str]) -> list[str]:
    """Every document under a contract kind directory, relative to docs/teamwork."""
    documents: list[str] = []
    for kind in sorted(closed):
        directory = docs_root / kind
        if not directory.is_dir():
            continue
        for path in sorted(directory.rglob("*.md")):
            if path.is_file():
                documents.append(str(path.relative_to(docs_root)))
    return documents


def index_references(text: str, closed: set[str]) -> list[str]:
    """Documents the index points at, as paths relative to docs/teamwork.

    Both a repository-relative and an index-relative link name the same file, so
    the `docs/teamwork/` prefix is normalised away; anything whose first segment
    is not a contract kind is pointing somewhere else and is not an index entry.
    """
    references: list[str] = []
    candidates = MARKDOWN_LINK.findall(text) + [
        token.strip() for token in BACKTICKED.findall(text)
    ]
    for raw in candidates:
        reference = raw.split("#", 1)[0].strip()
        if not reference.endswith(".md"):
            continue
        if reference.startswith("./"):
            reference = reference[2:]
        prefix = "/".join(DOCS_RELATIVE) + "/"
        if reference.startswith(prefix):
            reference = reference[len(prefix):]
        if reference.split("/", 1)[0] not in closed:
            continue
        if reference not in references:
            references.append(reference)
    return references


def check_persistence(project: Path, closed: set[str]) -> list[dict]:
    findings: list[dict] = []
    docs_root = project.joinpath(*DOCS_RELATIVE)
    if not docs_root.is_dir():
        return findings

    for entry in sorted(docs_root.iterdir()):
        if entry.name.startswith(".") or entry.is_dir():
            continue
        if entry.name == INDEX_NAME:
            continue
        findings.append(
            finding(
                "error",
                "root-entry-outside-contract",
                f"docs/teamwork/{entry.name} sits at the persistence root, where the "
                f"contract writes nothing but {INDEX_NAME}",
            )
        )

    for entry in sorted(docs_root.iterdir()):
        if not entry.is_dir() or entry.name.startswith("."):
            continue
        if entry.name in closed:
            continue
        variant = spelling_variant(entry.name, closed)
        if variant:
            findings.append(
                finding(
                    "error",
                    "kind-spelling",
                    f"docs/teamwork/{entry.name}/ is the wrong number; the contract kind is "
                    f"`{variant}/`, so the two directories never meet",
                )
            )
        else:
            findings.append(
                finding(
                    "error",
                    "kind-outside-contract",
                    f"docs/teamwork/{entry.name}/ is not in the closed kind set "
                    f"({', '.join(sorted(closed))})",
                )
            )

    index_path = docs_root / INDEX_NAME
    if not index_path.is_file():
        # The contract never requires a docs/teamwork/README.md: it is a
        # navigation convenience the installer's init-project seeds, not a
        # persistence rule. A project that never ran init (or dropped the
        # file) has no human-readable index, and that is not drift.
        return findings

    documents = documents_on_disk(docs_root, closed)
    referenced = index_references(read_text(index_path), closed)
    for reference in referenced:
        if not (docs_root / reference).is_file():
            findings.append(
                finding(
                    "error",
                    "index-dead-entry",
                    f"docs/teamwork/{INDEX_NAME} indexes {reference}, which is not on disk",
                )
            )
    for document in documents:
        if document not in referenced:
            # A document nobody indexed is drift the next write can absorb, so it
            # stays a warning: the session-start hook prints errors only, and a
            # project carrying pre-contract documents must not shout on every
            # start. A dead index entry stays an error — it points at nothing.
            findings.append(
                finding(
                    "warn",
                    "index-unregistered",
                    f"docs/teamwork/{document} is on disk but no index line in "
                    f"{INDEX_NAME} points at it",
                )
            )
    return findings


def check_project(
    project: Path,
    closed: set[str],
    contract: dict,
    current_skills: set[str],
    retired_skills: set[str],
    has_agents_import,
) -> list[dict]:
    findings: list[dict] = []
    agents_path = project / "AGENTS.md"
    claude_path = project / "CLAUDE.md"
    agents_text = read_text(agents_path)
    claude_text = read_text(claude_path)

    block_in_agents = MANAGED_START in agents_text
    block_in_claude = MANAGED_START in claude_text
    has_persistence = project.joinpath(*DOCS_RELATIVE).is_dir()

    if has_persistence and not (block_in_agents or block_in_claude):
        findings.append(
            finding(
                "error",
                "block-missing",
                "docs/teamwork/ exists but no TEAMWORK_PROJECT_START block declares it; "
                "run ./install.sh --project-root <path> init-project",
            )
        )

    findings.extend(check_persistence(project, closed))
    findings.extend(check_shape(project, closed, contract))

    if block_in_agents:
        if claude_path.is_symlink():
            try:
                resolved = claude_path.resolve(strict=True)
            except OSError:
                resolved = None
            if resolved != agents_path.resolve():
                findings.append(
                    finding(
                        "error",
                        "host-unreachable",
                        "CLAUDE.md is a symlink that does not resolve to AGENTS.md, so "
                        "Claude Code loads something else",
                    )
                )
        elif not claude_path.exists():
            findings.append(
                finding(
                    "error",
                    "host-unreachable",
                    "the block lives in AGENTS.md and there is no CLAUDE.md, so Claude Code "
                    "never loads it",
                )
            )
        elif not has_agents_import(claude_text):
            findings.append(
                finding(
                    "error",
                    "host-unreachable",
                    "CLAUDE.md exists but carries no active @AGENTS.md import, so Claude Code "
                    "never loads the block",
                )
            )

    block_body = managed_block_text(agents_text if block_in_agents else claude_text)
    for token in BACKTICKED.findall(block_body):
        identifier = token.strip()
        if not KEBAB_IDENTIFIER.match(identifier):
            continue
        if identifier in current_skills or identifier not in retired_skills:
            continue
        findings.append(
            finding(
                "error",
                "retired-skill-reference",
                f"the project block names the Teamwork Skill `{identifier}`, which this "
                "version no longer installs",
            )
        )

    return findings


# --- document shape --------------------------------------------------------

# The project checks above stop at the directory listing: they see names, not
# contents, which is why a tree of malformed documents reports clean. These look
# inside each document, against the shape the policy source spells out — a
# frontmatter block, a current synthesis, an append-only dated History at the end.

SHAPE_PREFIX = "shape-"
SHAPE_SAMPLES = 3

# The shape block in the policy source is an indented sample document. Its
# frontmatter keys, its History heading level and title, and the level of a dated
# entry are all read out of that sample rather than restated here, so a contract
# edit moves the criteria and a doctor edit does not.
SHAPE_INDENT = " " * 4
SHAPE_FENCE = re.compile(rf"^{SHAPE_INDENT}---\s*$")
SHAPE_KEY = re.compile(rf"^{SHAPE_INDENT}([a-z][a-z0-9_-]*):")
SHAPE_HISTORY = re.compile(rf"^{SHAPE_INDENT}(#{{1,6}})\s+(History)\s*$")
SHAPE_ENTRY = re.compile(rf"^{SHAPE_INDENT}(#{{1,6}})\s+<date\b")

FRONTMATTER_KEY = re.compile(r"^([A-Za-z][A-Za-z0-9_-]*):")
HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
CODE_FENCE = re.compile(r"^\s*(?:```|~~~)")
LEADING_DATE = re.compile(r"^(\d{4}-\d{2}-\d{2})")
DATE_PREFIXED_NAME = re.compile(r"^\d{4}-\d{2}-\d{2}-")
BULLETED_DATE = re.compile(r"^\s*[-*+]\s+\**(\d{4}-\d{2}-\d{2})")

# Phrases that assert something about a past edit which the document itself
# cannot show: whether the body really went untouched is a fact about the diff,
# not about the file on disk. doctor stays read-only and fast, so it lists them
# for a human to check against git rather than running git itself.
UNVERIFIABLE_CLAIM = (
    "正文内容未改动",
    "未改写",
    "原样保留",
    "一字未改",
    "链接目标此前已正确",
    "no semantic change",
    "carried over verbatim",
)


def document_shape_contract() -> dict:
    """Frontmatter fields and History heading levels, parsed from the policy."""
    text = read_text(POLICY_SOURCE)
    if not text:
        raise DoctorError(f"policy source is unreadable: {POLICY_SOURCE}")
    lines = text.splitlines()

    fields: list[str] = []
    open_fence = False
    for line in lines:
        if SHAPE_FENCE.match(line):
            if open_fence:
                break
            open_fence = True
            continue
        if open_fence:
            match = SHAPE_KEY.match(line)
            if match:
                fields.append(match.group(1))
    if not fields:
        raise DoctorError(
            f"no indented frontmatter sample in {POLICY_SOURCE}; the document field set "
            "cannot be established"
        )

    history_level = 0
    history_title = ""
    entry_level = 0
    for line in lines:
        match = SHAPE_HISTORY.match(line)
        if match and not history_level:
            history_level, history_title = len(match.group(1)), match.group(2)
        match = SHAPE_ENTRY.match(line)
        if match and not entry_level:
            entry_level = len(match.group(1))
    if not history_level or not entry_level:
        raise DoctorError(
            f"the document shape sample in {POLICY_SOURCE} no longer shows a History "
            "heading and a dated entry heading; the shape check has no criteria"
        )

    return {
        "fields": fields,
        "history_level": history_level,
        "history_title": history_title,
        "entry_level": entry_level,
    }


def frontmatter(lines: list[str]) -> tuple[list[str] | None, dict[str, str]]:
    """(keys in order, key -> value) for a closed leading `---` block."""
    if not lines or lines[0].strip() != "---":
        return None, {}
    keys: list[str] = []
    values: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return keys, values
        match = FRONTMATTER_KEY.match(line)
        if match:
            keys.append(match.group(1))
            values[match.group(1)] = line.split(":", 1)[1].strip()
    return None, {}


def headings(lines: list[str]) -> list[tuple[int, int, str]]:
    """(line index, level, title) for every ATX heading outside a code fence."""
    found: list[tuple[int, int, str]] = []
    fenced = False
    for number, line in enumerate(lines):
        if CODE_FENCE.match(line):
            fenced = not fenced
            continue
        if fenced:
            continue
        match = HEADING.match(line)
        if match:
            found.append((number, len(match.group(1)), match.group(2)))
    return found


def history_heading_text(contract: dict) -> str:
    return "#" * contract["history_level"] + " " + contract["history_title"]


def check_document(relative: str, path: Path, contract: dict) -> list[dict]:
    findings: list[dict] = []
    where = f"docs/teamwork/{relative}"

    def report(severity: str, check: str, message: str, **extra: object) -> None:
        findings.append(
            finding(severity, check, f"{where}: {message}", document=relative, **extra)
        )

    if DATE_PREFIXED_NAME.match(path.name):
        report(
            "error",
            "shape-filename-date",
            "the file name carries a date prefix; the contract name is the subject "
            "in kebab-case, and the dates live in History",
        )

    lines = read_text(path).splitlines()

    keys, values = frontmatter(lines)
    if keys is None:
        report("error", "shape-frontmatter", "no closed `---` frontmatter block")
    else:
        expected = contract["fields"]
        missing = [field for field in expected if field not in keys]
        extra = [key for key in keys if key not in expected]
        if missing:
            report(
                "error",
                "shape-frontmatter",
                f"frontmatter is missing {', '.join(missing)}",
            )
        if extra:
            report(
                "error",
                "shape-frontmatter",
                f"frontmatter carries {', '.join(extra)}, which the contract does not "
                f"name (its fields are {', '.join(expected)})",
            )

    title = history_heading_text(contract)
    every = headings(lines)
    marks = [
        item
        for item in every
        if item[1] == contract["history_level"] and item[2] == contract["history_title"]
    ]
    if not marks:
        report(
            "error",
            "shape-history-section",
            f"no `{title}` section, so the document keeps no append-only history",
        )
        return findings
    if len(marks) > 1:
        report(
            "error",
            "shape-history-section",
            f"{len(marks)} `{title}` sections; the contract has one",
            line=marks[-1][0] + 1,
        )

    start = marks[-1][0]
    trailing = [
        item
        for item in every
        if item[0] > start and item[1] <= contract["history_level"]
    ]
    if trailing:
        report(
            "error",
            "shape-history-section",
            f"`{'#' * trailing[0][1]} {trailing[0][2]}` follows History; History is the "
            "last section, so an append lands after unrelated prose",
            line=trailing[0][0] + 1,
        )

    body = lines[start + 1 :]
    entries = [
        item
        for item in every
        if item[0] > start and item[1] == contract["entry_level"]
    ]
    dates = [
        match.group(1)
        for match in (LEADING_DATE.match(item[2]) for item in entries)
        if match
    ]
    if not dates:
        bulleted = any(BULLETED_DATE.match(line) for line in body)
        detail = (
            "History entries are dated bullets"
            if bulleted
            else "History carries no dated entry"
        )
        report(
            "warn",
            "shape-history-entry",
            f"{detail}; the contract entry is `{'#' * contract['entry_level']} <date>`",
            line=start + 1,
        )

    updated = values.get("updated", "")
    if dates and LEADING_DATE.match(updated):
        latest = max(dates)
        if updated < latest:
            report(
                "error",
                "shape-updated-stale",
                f"updated is {updated} but the newest History entry is {latest}; a change "
                "was recorded and never carried into the frontmatter",
            )
        elif updated > latest:
            report(
                "warn",
                "shape-updated-ahead",
                f"updated is {updated} but the newest History entry is {latest}; a change "
                "was stamped and never written into History",
            )

    for offset, line in enumerate(body):
        for phrase in UNVERIFIABLE_CLAIM:
            if phrase in line:
                report(
                    "warn",
                    "shape-unverifiable-claim",
                    f"History claims `{phrase}`, which the document cannot show; check it "
                    "against the git diff of that entry",
                    line=start + 2 + offset,
                )
                break

    return findings


def check_shape(project: Path, closed: set[str], contract: dict) -> list[dict]:
    findings: list[dict] = []
    docs_root = project.joinpath(*DOCS_RELATIVE)
    if not docs_root.is_dir():
        return findings
    for kind in sorted(closed):
        directory = docs_root / kind
        if not directory.is_dir():
            continue
        for path in sorted(directory.rglob("*")):
            if not path.is_file() or path.name.startswith("."):
                continue
            relative = str(path.relative_to(docs_root))
            if path.suffix != ".md":
                findings.append(
                    finding(
                        "warn",
                        "shape-non-document",
                        f"docs/teamwork/{relative} is not a `.md` document; the contract "
                        "shape is `<kind>/<slug>.md`",
                        document=relative,
                    )
                )
                continue
            findings.extend(check_document(relative, path, contract))
    return findings


# --- global checks ---------------------------------------------------------


def repo_version() -> str:
    return read_text(REPO_ROOT / "VERSION").strip() or "unknown"


def source_pointer() -> dict:
    path = Path.home() / ".teamwork" / "install.json"
    if not path.is_file():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def check_global(version: str, pointer: dict) -> list[dict]:
    findings: list[dict] = []

    for root in SKILL_ROOTS:
        marker = root / ".teamwork-version"
        if not marker.is_file():
            continue
        installed = read_text(marker).strip()
        if installed != version:
            findings.append(
                finding(
                    "error",
                    "version-drift",
                    f"{root} is at {installed or 'unknown'} while this checkout is at {version}",
                    path=str(root),
                )
            )
        else:
            findings.append(
                finding("info", "version", f"{root} is at {installed}", path=str(root))
            )

    for platform, destination in (
        ("claude", Path.home() / ".claude" / "CLAUDE.md"),
        ("codex", Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")) / "AGENTS.md"),
    ):
        status = managed_policy_status(platform)
        if status == "current":
            findings.append(
                finding(
                    "info",
                    "policy-block",
                    f"{platform} managed policy block is current",
                    path=str(destination),
                )
            )
        else:
            findings.append(
                finding(
                    "error",
                    "policy-block",
                    f"{platform} managed policy block is {status}; "
                    f"run ./install.sh {platform}-policy or ./install.sh {platform}",
                    path=str(destination),
                )
            )

    findings.append(
        finding(
            "info",
            "cursor-unverifiable",
            "Cursor keeps User Rules behind a paste-only surface with no readback, so this "
            "check cannot confirm or deny the Cursor policy block — verify it by hand in "
            "Settings -> Rules -> User Rules",
        )
    )

    recorded = pointer.get("version")
    if recorded and recorded != version:
        findings.append(
            finding(
                "warn",
                "pointer-version",
                f"~/.teamwork/install.json records {recorded} while this checkout is at {version}",
            )
        )

    return findings


# --- reporting -------------------------------------------------------------


def sort_findings(findings: list[dict]) -> list[dict]:
    return sorted(findings, key=lambda item: (SEVERITY_ORDER[item["severity"]], item["check"]))


def worst(findings: list[dict]) -> int:
    return min((SEVERITY_ORDER[item["severity"]] for item in findings), default=3)


def render_shape(findings: list[dict], verbose: bool) -> list[str]:
    """Shape findings collapse to a count plus a few examples unless asked for all.

    A tree of a few hundred documents produces more shape lines than a terminal
    holds, and the count per check is what says whether a defect class is one
    stray file or a habit. `--verbose` and `--json` both carry every line.
    """
    lines: list[str] = []
    order: list[str] = []
    grouped: dict[str, list[dict]] = {}
    for item in findings:
        grouped.setdefault(item["check"], []).append(item)
        if item["check"] not in order:
            order.append(item["check"])
    for check in order:
        group = grouped[check]
        severity = min(group, key=lambda item: SEVERITY_ORDER[item["severity"]])["severity"]
        shown = group if verbose else group[:SHAPE_SAMPLES]
        lines.append(
            f"    {severity:<5}  {check:<26}  {len(group)} finding(s)"
            + ("" if verbose or len(group) <= len(shown) else f", first {len(shown)} shown")
        )
        for item in shown:
            lines.append(f"      {item['severity']:<5}  {item['message']}")
    return lines


def render(report: dict, verbose: bool = False) -> str:
    lines: list[str] = []
    lines.append(f"Teamwork doctor - checkout {report['checkout']} at {report['version']}")
    lines.append("")
    lines.append("GLOBAL")
    for item in report["global"]:
        lines.append(f"  {item['severity']:<5}  {item['check']:<26}  {item['message']}")
    lines.append("")
    counts = report["summary"]
    lines.append(
        f"PROJECTS ({counts['projects']} scanned, {counts['projects_with_errors']} with errors)"
    )
    for project in report["projects"]:
        if not project["findings"]:
            continue
        lines.append("")
        lines.append(f"  {project['path']}")
        for item in project["findings"]:
            if item["check"].startswith(SHAPE_PREFIX):
                continue
            lines.append(f"    {item['severity']:<5}  {item['check']:<26}  {item['message']}")
        lines.extend(
            render_shape(
                [item for item in project["findings"] if item["check"].startswith(SHAPE_PREFIX)],
                verbose,
            )
        )
    clean = [project["path"] for project in report["projects"] if not project["findings"]]
    if clean:
        lines.append("")
        lines.append("  clean: " + ", ".join(clean))
    lines.append("")
    lines.append(
        f"  totals: {counts['error']} error, {counts['warn']} warn, {counts['info']} info"
    )
    return "\n".join(lines)


def build_report(project_filter: Path | None) -> dict:
    closed = closed_kind_set()
    contract = document_shape_contract()
    current_skills, retired_skills = installer_skill_names()
    has_agents_import = load_project_init_module().has_agents_import
    version = repo_version()
    pointer = source_pointer()

    if project_filter is not None:
        projects = [project_filter.resolve()] if is_project(project_filter) else []
    else:
        extra_roots = [Path(pointer["root"])] if pointer.get("root") else []
        projects = discover_projects(Path.home() / "Documents", extra_roots)

    project_reports = []
    for project in projects:
        findings = sort_findings(
            check_project(
                project,
                closed,
                contract,
                current_skills,
                retired_skills,
                has_agents_import,
            )
        )
        project_reports.append({"path": str(project), "findings": findings})
    project_reports.sort(key=lambda item: (worst(item["findings"]), item["path"]))

    global_findings = sort_findings(check_global(version, pointer))

    every = global_findings + [
        item for project in project_reports for item in project["findings"]
    ]
    return {
        "version": version,
        "checkout": str(REPO_ROOT),
        "closed_kinds": sorted(closed),
        "document_fields": contract["fields"],
        "global": global_findings,
        "projects": project_reports,
        "summary": {
            "projects": len(project_reports),
            "projects_with_errors": sum(
                1
                for project in project_reports
                if any(item["severity"] == "error" for item in project["findings"])
            ),
            "error": sum(1 for item in every if item["severity"] == "error"),
            "warn": sum(1 for item in every if item["severity"] == "warn"),
            "info": sum(1 for item in every if item["severity"] == "info"),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit the structured report")
    parser.add_argument("--project", help="check only this project directory")
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="list every document-shape finding instead of a count and a few examples",
    )
    arguments = parser.parse_args()

    project_filter = None
    if arguments.project:
        project_filter = Path(os.path.abspath(os.path.expanduser(arguments.project)))
        if not project_filter.is_dir():
            print(f"Teamwork doctor: not a directory: {project_filter}", file=sys.stderr)
            return 2
        if not is_project(project_filter):
            print(
                f"Teamwork doctor: not a Teamwork project: {project_filter} "
                "(no docs/teamwork/ and no managed block in AGENTS.md or CLAUDE.md)",
                file=sys.stderr,
            )
            return 2

    try:
        report = build_report(project_filter)
    except DoctorError as exc:
        print(f"Teamwork doctor cannot run: {exc}", file=sys.stderr)
        return 2

    if arguments.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(render(report, arguments.verbose))
    return 1 if report["summary"]["error"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
