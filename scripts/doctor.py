#!/usr/bin/env python3
"""Read-only checks for installed Teamwork content and project context access."""

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
from urllib.parse import unquote, urlsplit

REPO_ROOT = Path(__file__).resolve().parent.parent
COMMON_SH = REPO_ROOT / "scripts" / "install" / "common.sh"
POLICY_SH = REPO_ROOT / "scripts" / "install" / "policy.sh"
INIT_PROJECT_FILES = REPO_ROOT / "scripts" / "init-project-files.py"
MANAGED_START = "<!-- TEAMWORK_PROJECT_START -->"
MANAGED_END = "<!-- TEAMWORK_PROJECT_END -->"
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
PROJECT_LABEL = re.compile(r"^-\s+Project label:\s*`([^`]+)`", re.MULTILINE)
MARKDOWN_LINK = re.compile(
    r'\[[^\]]*\]\(\s*(?:<([^>]+)>|([^\s)]+))(?:\s+"[^"\n]*")?\s*\)'
)
CODEX_HOME_PATH = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
SKILL_ROOTS = (
    Path.home() / ".claude" / "skills",
    Path.home() / ".agents" / "skills",
    Path.home() / ".cursor" / "skills",
    CODEX_HOME_PATH / "skills",
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


def installer_skill_names() -> set[str]:
    text = read_text(COMMON_SH)
    match = re.search(r"^SKILLS=\(([^)]*)\)", text, re.MULTILINE)
    if not match or not match.group(1).strip():
        raise DoctorError(f"could not read the Teamwork skill list from {COMMON_SH}")
    return set(match.group(1).split())


def load_project_init_module():
    spec = importlib.util.spec_from_file_location(
        "teamwork_init_project_files", INIT_PROJECT_FILES
    )
    if spec is None or spec.loader is None:
        raise DoctorError(f"cannot load {INIT_PROJECT_FILES}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for name in ("has_import", "managed_block", "AGENTS_IMPORT"):
        if not hasattr(module, name):
            raise DoctorError(
                f"{INIT_PROJECT_FILES} no longer exposes {name}; host reachability and the "
                "managed block's own text are decided there and are not reimplemented here"
            )
    return module


def managed_policy_status(platform: str) -> str:
    # Paths are positional arguments, never interpolated into shell code.
    completed = subprocess.run(
        [
            "bash",
            "-c",
            'ROOT="$1"; source "$2"; source "$3"; teamwork_managed_policy_status "$4"',
            "bash",
            str(REPO_ROOT),
            str(COMMON_SH),
            str(POLICY_SH),
            platform,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        return "unknown"
    return completed.stdout.strip() or "unknown"


def has_managed_block(path: Path) -> bool:
    return any(marker in read_text(path) for marker in (MANAGED_START, MANAGED_END))


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


def index_references(text: str) -> list[str]:
    """Local inline Markdown links, excluding code examples and remote URLs."""
    references = []
    fence = None
    for line in text.splitlines():
        mark = re.match(r"^\s*(`{3,}|~{3,})", line)
        if mark:
            token = mark.group(1)
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
            continue
        if fence:
            continue
        line = re.sub(r"(`+).*?\1", "", line)
        for match in MARKDOWN_LINK.finditer(line):
            raw = match.group(1) or match.group(2)
            parsed = urlsplit(raw)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            path = unquote(parsed.path)
            if Path(path).suffix.lower() == ".md" and path not in references:
                references.append(path)
    return references


def check_persistence(project: Path) -> list[dict]:
    root = project.joinpath(*DOCS_RELATIVE)
    if not root.is_dir():
        return []
    index = root / INDEX_NAME
    if not index.is_file():
        if any(path.is_file() for path in root.rglob("*.md")):
            return [
                finding(
                    "error",
                    "index-missing",
                    f"{root} contains records but has no {INDEX_NAME}",
                )
            ]
        return []
    findings = []
    for reference in index_references(read_text(index)):
        # Existing indexes sometimes use repository-relative links.
        target = (
            project / reference
            if reference.startswith("docs/teamwork/")
            else root / reference
        )
        if not target.is_file():
            findings.append(
                finding(
                    "error",
                    "index-dead-entry",
                    f"{index} links to missing document {reference}",
                )
            )
    return findings


def check_project(project: Path, project_init) -> list[dict]:
    findings = check_persistence(project)
    agents = project / "AGENTS.md"
    claude = project / "CLAUDE.md"
    claude_text = read_text(claude)
    carrying = [path for path in (agents, claude) if has_managed_block(path)]
    root = project.joinpath(*DOCS_RELATIVE)
    if (
        not carrying
        and root.is_dir()
        and any(path.is_file() for path in root.rglob("*.md"))
    ):
        findings.append(
            finding(
                "error",
                "block-missing",
                "Project records exist but no Teamwork project block declares their entry.",
            )
        )
    for path in carrying:
        text = read_text(path)
        try:
            project_init.replace_block(text, "")  # Validate markers without writing.
        except project_init.InitError as exc:
            findings.append(finding("error", "block-malformed", f"{path}: {exc}"))
            continue
        body = text.split(MANAGED_START, 1)[1].split(MANAGED_END, 1)[0]
        label = PROJECT_LABEL.search(body)
        expected = project_init.managed_block(label.group(1)) if label else ""
        actual = MANAGED_START + body + MANAGED_END + "\n"
        if actual != expected:
            findings.append(
                finding(
                    "error",
                    "block-stale",
                    f"{path} carries an older Teamwork project block; refresh init-project.",
                )
            )

    if has_managed_block(agents):
        try:
            reachable = (
                (claude.resolve(strict=True) == agents.resolve())
                if claude.is_symlink()
                else (
                    claude.is_file()
                    and project_init.has_import(claude_text, project_init.AGENTS_IMPORT)
                )
            )
        except (OSError, RuntimeError):
            reachable = False
        if not reachable:
            findings.append(
                finding(
                    "error",
                    "host-unreachable",
                    "CLAUDE.md does not reach AGENTS.md through an import or symlink.",
                )
            )
    if claude.is_file() and not claude.is_symlink():
        try:
            project_init.replace_block(
                claude_text, "", project_init.BRIDGE_START, project_init.BRIDGE_END
            )
        except project_init.InitError as exc:
            findings.append(finding("error", "bridge-malformed", f"{claude}: {exc}"))
        else:
            if project_init.BRIDGE_START in claude_text:
                body = claude_text.split(project_init.BRIDGE_START, 1)[1].split(
                    project_init.BRIDGE_END, 1
                )[0]
                if project_init.has_import(body, project_init.README_IMPORT):
                    findings.append(
                        finding(
                            "warn",
                            "bridge-stale",
                            "The old managed Claude bridge still auto-imports the index; refresh init-project.",
                        )
                    )
            outside = project_init.text_outside_bridge_block(claude_text)
            if project_init.has_import(outside, project_init.README_IMPORT):
                findings.append(
                    finding(
                        "info",
                        "user-index-import",
                        "A user-owned CLAUDE.md import still loads the index automatically.",
                    )
                )
    return findings


def repo_version() -> str:
    return read_text(REPO_ROOT / "VERSION").strip() or "unknown"


def installed_root(root: Path) -> bool:
    return any(
        (root / marker).is_file()
        for marker in (".teamwork-version", ".teamwork-profile")
    )


def check_global(version: str) -> list[dict]:
    findings = []
    skills = installer_skill_names()
    for root in SKILL_ROOTS:
        if not installed_root(root):
            continue
        if not all(
            (root / marker).is_file()
            for marker in (".teamwork-version", ".teamwork-profile")
        ):
            findings.append(
                finding(
                    "error",
                    "install-markers",
                    f"{root} has incomplete installation markers",
                    path=str(root),
                )
            )
        installed = read_text(root / ".teamwork-version").strip()
        findings.append(
            finding(
                "info" if installed == version else "error",
                "version" if installed == version else "version-drift",
                f"{root} is at {installed or 'unknown'}; checkout is at {version}",
                path=str(root),
            )
        )
        for skill in sorted(skills):
            source, destination = REPO_ROOT / "skills" / skill, root / skill
            expected = {p.relative_to(source) for p in source.rglob("*") if p.is_file()}
            actual = {
                p.relative_to(destination)
                for p in destination.rglob("*")
                if p.is_file()
            }
            changed = sorted(
                str(name)
                for name in expected | actual
                if name not in expected
                or name not in actual
                or (source / name).read_bytes() != (destination / name).read_bytes()
            )
            if changed:
                findings.append(
                    finding(
                        "error",
                        "skill-content-drift",
                        f"{destination} differs from source: {', '.join(changed)}",
                        path=str(destination),
                    )
                )

    for platform, destination, roots in (
        ("claude", Path.home() / ".claude" / "CLAUDE.md", [SKILL_ROOTS[0]]),
        ("codex", CODEX_HOME_PATH / "AGENTS.md", [SKILL_ROOTS[1], SKILL_ROOTS[3]]),
    ):
        status = managed_policy_status(platform)
        if status == "missing":
            enabled = any(installed_root(root) for root in roots)
            findings.append(
                finding(
                    "error" if enabled else "info",
                    "policy-missing" if enabled else "host-disabled",
                    f"{platform}: {'installed Skill has no policy block' if enabled else 'Teamwork is not enabled'}",
                    path=str(destination),
                )
            )
        else:
            findings.append(
                finding(
                    "info" if status == "current" else "error",
                    "policy-" + ("malformed" if status == "malformed" else "block"),
                    f"{platform} managed policy block is {status}",
                    path=str(destination),
                )
            )
    findings.append(
        finding(
            "info",
            "cursor-unverifiable",
            "This installer cannot read Cursor User Rules; verify activation in Cursor.",
        )
    )
    return findings


def sort_findings(findings: list[dict]) -> list[dict]:
    return sorted(
        findings, key=lambda item: (SEVERITY_ORDER[item["severity"]], item["check"])
    )


def worst(findings: list[dict]) -> int:
    return min((SEVERITY_ORDER[item["severity"]] for item in findings), default=3)


def render(report: dict) -> str:
    lines: list[str] = []
    lines.append(
        f"Teamwork doctor - checkout {report['checkout']} at {report['version']}"
    )
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
            lines.append(
                f"    {item['severity']:<5}  {item['check']:<26}  {item['message']}"
            )
    clean = [
        project["path"] for project in report["projects"] if not project["findings"]
    ]
    if clean:
        lines.append("")
        lines.append("  clean: " + ", ".join(clean))
    lines.append("")
    lines.append(
        f"  totals: {counts['error']} error, {counts['warn']} warn, {counts['info']} info"
    )
    return "\n".join(lines)


def build_report(project_filter: Path | None) -> dict:
    project_init = load_project_init_module()
    version = repo_version()

    if project_filter is not None:
        projects = [project_filter.resolve()] if is_project(project_filter) else []
    else:
        projects = discover_projects(Path.home() / "Documents", [REPO_ROOT])

    project_reports = []
    for project in projects:
        findings = sort_findings(
            check_project(
                project,
                project_init,
            )
        )
        project_reports.append({"path": str(project), "findings": findings})
    project_reports.sort(key=lambda item: (worst(item["findings"]), item["path"]))

    global_findings = sort_findings(check_global(version))

    every = global_findings + [
        item for project in project_reports for item in project["findings"]
    ]
    return {
        "version": version,
        "checkout": str(REPO_ROOT),
        "closed_kinds": [],
        "document_fields": [],
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
    parser.add_argument(
        "--json", action="store_true", help="emit the structured report"
    )
    parser.add_argument("--project", help="check only this project directory")
    arguments = parser.parse_args()

    project_filter = None
    if arguments.project:
        project_filter = Path(os.path.abspath(os.path.expanduser(arguments.project)))
        if not project_filter.is_dir():
            print(
                f"Teamwork doctor: not a directory: {project_filter}", file=sys.stderr
            )
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
        print(render(report))
    return 1 if report["summary"]["error"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
