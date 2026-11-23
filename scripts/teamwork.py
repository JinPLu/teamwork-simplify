#!/usr/bin/env python3
"""Install, refresh, uninstall, or inspect Teamwork across agent hosts."""

from __future__ import annotations

import sys

sys.dont_write_bytecode = True

import json
import os
import re
import shutil
import stat
import subprocess
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urlsplit

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_NAME = "teamwork-collaborate"
SKILL_SOURCE = REPO_ROOT / "skills" / SKILL_NAME
POLICY_SOURCE = REPO_ROOT / "policy" / "teamwork-global.md"
VERSION_FILE = REPO_ROOT / "VERSION"
SKILL_VERSION_MARKER = ".teamwork-version"

POLICY_START = "<!-- TEAMWORK_GLOBAL_START -->"
POLICY_END = "<!-- TEAMWORK_GLOBAL_END -->"

HOST_ORDER = ("antigravity", "codex", "claude", "cursor")
HOST_ALIASES = {
    "agy": "antigravity",
    "antigravity": "antigravity",
    "codex": "codex",
    "claude": "claude",
    "cursor": "cursor",
}

SEVERITY_ORDER = {"error": 0, "warn": 1, "info": 2}
PRUNED_SCAN_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    "venv",
    ".venv",
    "env",
    "site-packages",
    "target",
    "build",
    "dist",
    "artifacts",
    "outputs",
    "backups",
    "backup",
    "_Archive",
    "archive",
    "Library",
}
EPHEMERAL_LINK_SEGMENTS = {
    "outputs",
    "artifacts",
    "log",
    "logs",
    "tmp",
    "runs",
    "build",
    "dist",
}
MAX_SCAN_DEPTH = 4
MARKDOWN_LINK_RE = re.compile(
    r'\[[^\]]*\]\(\s*(?:<([^>]+)>|([^\s)]+))(?:\s+"[^"\n]*")?\s*\)'
)

USAGE_TEXT = """Usage:
  ./install.sh [--copy|--link] [--force] <host>...
  ./install.sh [--copy|--link] [--force] all|refresh
  ./install.sh uninstall <host>...|all
  ./install.sh policy [--clipboard]
  ./install.sh doctor [--project PATH] [--json]

Hosts:
  antigravity, agy   ~/.gemini/config/skills + ~/.gemini/GEMINI.md
  codex              ~/.agents/skills + $CODEX_HOME/AGENTS.md
  claude             ~/.claude/skills + ~/.claude/CLAUDE.md
  cursor             ~/.cursor/skills (activate policy via `policy --clipboard`)

Commands:
  <host>...          Install or update Teamwork on the named host(s)
  all                Install or update Teamwork on all four hosts
  refresh            Update only hosts where Teamwork is already installed
  uninstall          Remove Teamwork's Skill and managed policy block
  policy             Print (or copy with --clipboard) the canonical policy block
  doctor             Read-only check of host installations and project links

Options:
  --copy             Copy Skill files (default for new installs)
  --link             Symlink the Skill directory to this checkout
  --force            Replace an existing unmarked teamwork-collaborate Skill entry
"""


class TeamworkError(RuntimeError):
    """Operational or validation failure (exits 1)."""


class UsageError(RuntimeError):
    """Invalid command-line invocation (exits 2)."""


@dataclass(frozen=True)
class HostSpec:
    name: str
    skill_root: Path
    policy_path: Path | None


def host_specs() -> dict[str, HostSpec]:
    home = Path.home()
    gemini_home = Path(os.environ.get("GEMINI_HOME", home / ".gemini"))
    codex_home = Path(os.environ.get("CODEX_HOME", home / ".codex"))
    claude_home = Path(os.environ.get("CLAUDE_CONFIG_DIR", home / ".claude"))
    return {
        "antigravity": HostSpec(
            name="antigravity",
            skill_root=gemini_home / "config" / "skills",
            policy_path=gemini_home / "GEMINI.md",
        ),
        "codex": HostSpec(
            name="codex",
            skill_root=home / ".agents" / "skills",
            policy_path=codex_home / "AGENTS.md",
        ),
        "claude": HostSpec(
            name="claude",
            skill_root=claude_home / "skills",
            policy_path=claude_home / "CLAUDE.md",
        ),
        "cursor": HostSpec(
            name="cursor",
            skill_root=home / ".cursor" / "skills",
            policy_path=None,
        ),
    }


def repo_version() -> str:
    try:
        return VERSION_FILE.read_text(encoding="utf-8").strip() or "unknown"
    except OSError as exc:
        raise TeamworkError(f"cannot read {VERSION_FILE}: {exc}") from exc


def canonical_policy_block() -> str:
    if not POLICY_SOURCE.is_file():
        raise TeamworkError(f"missing policy source: {POLICY_SOURCE}")
    body = POLICY_SOURCE.read_text(encoding="utf-8").strip()
    if not body:
        raise TeamworkError(f"policy source is empty: {POLICY_SOURCE}")
    return f"{POLICY_START}\n{body}\n{POLICY_END}\n"


def check_writable_target(path: Path, label: str) -> None:
    if path.is_symlink():
        raise TeamworkError(f"{label} must not be a symlink: {path}")
    if path.exists():
        info = path.lstat()
        if not stat.S_ISREG(info.st_mode):
            raise TeamworkError(f"{label} is not a regular file: {path}")
        if not os.access(path, os.R_OK | os.W_OK):
            raise TeamworkError(f"{label} is not readable and writable: {path}")
        return

    parent = path.parent
    while not parent.exists() and parent != parent.parent:
        parent = parent.parent
    if not parent.is_dir():
        raise TeamworkError(f"{label} parent is not a directory: {parent}")
    if not os.access(parent, os.W_OK | os.X_OK):
        raise TeamworkError(f"{label} parent is not writable: {parent}")


def check_writable_dir(directory: Path, label: str) -> None:
    if directory.is_symlink():
        raise TeamworkError(f"{label} must not be a symlink: {directory}")
    if directory.exists():
        if not directory.is_dir():
            raise TeamworkError(f"{label} is not a directory: {directory}")
        if not os.access(directory, os.W_OK | os.X_OK):
            raise TeamworkError(f"{label} is not writable: {directory}")
        return

    parent = directory.parent
    while not parent.exists() and parent != parent.parent:
        parent = parent.parent
    if not parent.is_dir() or not os.access(parent, os.W_OK | os.X_OK):
        raise TeamworkError(f"{label} ancestor is not writable: {parent}")


def atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not path.is_symlink():
        try:
            if path.read_text(encoding="utf-8") == content:
                return
        except (OSError, UnicodeDecodeError):
            pass
    tmp = path.with_name(f".{path.name}.teamwork-tmp")
    if tmp.exists() or tmp.is_symlink():
        raise TeamworkError(f"temporary file already exists: {tmp}")
    try:
        tmp.write_text(content, encoding="utf-8")
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


# ---- Policy block parsing & editing ----------------------------------------


def locate_policy_markers(text: str, label: str) -> tuple[list[str], int, int] | None:
    lines = text.splitlines(keepends=True)
    starts = [i for i, line in enumerate(lines) if line.rstrip("\r\n") == POLICY_START]
    ends = [i for i, line in enumerate(lines) if line.rstrip("\r\n") == POLICY_END]
    raw_starts = text.count(POLICY_START)
    raw_ends = text.count(POLICY_END)
    if (
        raw_starts != len(starts)
        or raw_ends != len(ends)
        or len(starts) != len(ends)
        or len(starts) > 1
    ):
        raise TeamworkError(f"malformed Teamwork policy markers in {label}")
    if not starts:
        return None
    if starts[0] > ends[0]:
        raise TeamworkError(f"Teamwork policy end marker precedes start marker in {label}")
    return lines, starts[0], ends[0]


def upsert_policy_block(text: str, block: str, label: str) -> str:
    located = locate_policy_markers(text, label)
    if located is None:
        if not text.strip():
            return block
        return text.rstrip("\r\n") + "\n\n" + block

    lines, start_idx, end_idx = located
    before = "".join(lines[:start_idx]).rstrip("\r\n")
    after = "".join(lines[end_idx + 1 :]).lstrip("\r\n")
    if not before and not after:
        return block
    if before and not after:
        return before + "\n\n" + block
    if not before and after:
        return block + "\n" + after
    return before + "\n\n" + block + "\n" + after


def remove_policy_block(text: str, label: str) -> tuple[str, bool]:
    located = locate_policy_markers(text, label)
    if located is None:
        return text, False
    lines, start_idx, end_idx = located
    before = "".join(lines[:start_idx]).rstrip("\r\n")
    after = "".join(lines[end_idx + 1 :]).lstrip("\r\n")
    if not before and not after:
        return "", True
    if before and not after:
        return before + "\n", True
    if not before and after:
        return after, True
    return before + "\n\n" + after, True


def inspect_policy_status(path: Path, expected_block: str) -> str:
    if path.is_symlink() or (path.exists() and not path.is_file()):
        return "malformed"
    if not path.is_file():
        return "missing"
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return "malformed"
    try:
        located = locate_policy_markers(text, str(path))
    except TeamworkError:
        return "malformed"
    if located is None:
        return "missing"
    lines, start_idx, end_idx = located
    actual = "".join(lines[start_idx : end_idx + 1])
    if not actual.endswith("\n"):
        actual += "\n"
    return "current" if actual == expected_block else "drift"


# ---- Skill ownership & installation ----------------------------------------


def frontmatter_skill_name(skill_md: Path) -> str | None:
    try:
        lines = skill_md.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return None
    if not lines or lines[0].strip() != "---":
        return None
    for line in lines[1:]:
        stripped = line.strip()
        if stripped == "---":
            break
        if stripped.startswith("name:"):
            return stripped.split(":", 1)[1].strip()
    return None


def is_owned_skill_symlink(dest: Path) -> bool:
    if not dest.is_symlink():
        return False
    suffix = f"/skills/{SKILL_NAME}"
    try:
        raw = os.readlink(dest).rstrip("/")
    except OSError:
        return False
    if raw.endswith(suffix):
        return True
    try:
        resolved = str(dest.resolve()).rstrip("/")
    except OSError:
        return False
    return resolved.endswith(suffix)


def is_owned_skill_dir(dest: Path) -> bool:
    if dest.is_symlink():
        return is_owned_skill_symlink(dest)
    if not dest.is_dir():
        return False
    marker = dest / SKILL_VERSION_MARKER
    skill_md = dest / "SKILL.md"
    if not marker.is_file() or marker.is_symlink():
        return False
    if not skill_md.is_file() or skill_md.is_symlink():
        return False
    if frontmatter_skill_name(skill_md) != SKILL_NAME:
        return False
    expected_files = {
        *(p.relative_to(SKILL_SOURCE) for p in SKILL_SOURCE.rglob("*") if p.is_file()),
        Path(SKILL_VERSION_MARKER),
    }
    for entry in dest.rglob("*"):
        if entry.is_symlink():
            return False
        if entry.is_file() and entry.relative_to(dest) not in expected_files:
            return False
    return True


def preflight_skill_dest(dest: Path, force: bool) -> None:
    check_writable_dir(dest.parent, f"skill root {dest.parent}")
    if not dest.exists() and not dest.is_symlink():
        return
    if force:
        if dest.is_dir() and not dest.is_symlink():
            for current, dirs, _files in os.walk(dest, followlinks=False):
                here = Path(current)
                if not os.access(here, os.W_OK | os.X_OK):
                    raise TeamworkError(f"cannot replace non-writable directory: {here}")
                for d in dirs:
                    sub = here / d
                    if not sub.is_symlink() and not os.access(sub, os.W_OK | os.X_OK):
                        raise TeamworkError(f"cannot replace non-writable directory: {sub}")
        return
    if not is_owned_skill_dir(dest):
        raise TeamworkError(
            f"refusing to replace unrecognized skill entry at {dest} "
            "(pass --force to replace it)"
        )
    if dest.is_dir() and not dest.is_symlink() and not os.access(dest, os.W_OK | os.X_OK):
        raise TeamworkError(f"installed skill directory is not writable: {dest}")


def install_skill(dest: Path, mode: str, version: str) -> None:
    if not SKILL_SOURCE.is_dir() or not (SKILL_SOURCE / "SKILL.md").is_file():
        raise TeamworkError(f"missing skill source: {SKILL_SOURCE}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.is_symlink() or dest.is_file():
        dest.unlink()
    elif dest.is_dir():
        shutil.rmtree(dest)

    if mode == "link":
        dest.symlink_to(SKILL_SOURCE)
    elif mode == "copy":
        shutil.copytree(SKILL_SOURCE, dest)
        (dest / SKILL_VERSION_MARKER).write_text(version + "\n", encoding="utf-8")
    else:
        raise UsageError(f"unknown install mode: {mode}")


def host_is_installed(spec: HostSpec) -> bool:
    dest = spec.skill_root / SKILL_NAME
    if dest.exists() or dest.is_symlink():
        return True
    if spec.policy_path is not None and spec.policy_path.is_file() and not spec.policy_path.is_symlink():
        try:
            text = spec.policy_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return False
        return POLICY_START in text or POLICY_END in text
    return False


def preflight_install_host(spec: HostSpec, force: bool) -> None:
    if not SKILL_SOURCE.is_dir() or not (SKILL_SOURCE / "SKILL.md").is_file():
        raise TeamworkError(f"missing skill source: {SKILL_SOURCE}")
    _ = canonical_policy_block()
    preflight_skill_dest(spec.skill_root / SKILL_NAME, force=force)
    if spec.policy_path is not None:
        check_writable_target(spec.policy_path, f"{spec.name} global policy")
        if spec.policy_path.is_file():
            text = spec.policy_path.read_text(encoding="utf-8")
            locate_policy_markers(text, str(spec.policy_path))


def execute_install_host(spec: HostSpec, mode: str, version: str, block: str) -> None:
    dest = spec.skill_root / SKILL_NAME
    install_skill(dest, mode=mode, version=version)
    print(f"{spec.name}: installed Skill at {dest} ({mode})")
    if spec.policy_path is not None:
        before = (
            spec.policy_path.read_text(encoding="utf-8")
            if spec.policy_path.is_file()
            else ""
        )
        after = upsert_policy_block(before, block, str(spec.policy_path))
        atomic_write_text(spec.policy_path, after)
        if inspect_policy_status(spec.policy_path, block) != "current":
            raise TeamworkError(f"{spec.name}: policy verification failed at {spec.policy_path}")
        print(f"{spec.name}: updated global policy in {spec.policy_path}")
    else:
        print(
            "cursor: update Cursor User Rules manually via `./install.sh policy --clipboard`"
        )


def preflight_uninstall_host(spec: HostSpec) -> None:
    dest = spec.skill_root / SKILL_NAME
    if dest.exists() or dest.is_symlink():
        check_writable_dir(dest.parent, f"skill root {dest.parent}")
        if not is_owned_skill_dir(dest):
            raise TeamworkError(f"refusing to remove unrecognized skill entry at {dest}")
    if spec.policy_path is not None and (spec.policy_path.exists() or spec.policy_path.is_symlink()):
        check_writable_target(spec.policy_path, f"{spec.name} global policy")
        text = spec.policy_path.read_text(encoding="utf-8")
        locate_policy_markers(text, str(spec.policy_path))


def execute_uninstall_host(spec: HostSpec) -> None:
    removed_any = False
    dest = spec.skill_root / SKILL_NAME
    if dest.is_symlink() or dest.is_file():
        dest.unlink()
        removed_any = True
        print(f"{spec.name}: removed Skill link {dest}")
    elif dest.is_dir():
        shutil.rmtree(dest)
        removed_any = True
        print(f"{spec.name}: removed Skill directory {dest}")

    if spec.policy_path is not None and spec.policy_path.is_file():
        before = spec.policy_path.read_text(encoding="utf-8")
        after, removed_block = remove_policy_block(before, str(spec.policy_path))
        if removed_block:
            removed_any = True
            if after:
                atomic_write_text(spec.policy_path, after)
                print(f"{spec.name}: removed Teamwork policy block from {spec.policy_path}")
            else:
                spec.policy_path.unlink()
                print(f"{spec.name}: removed empty policy file {spec.policy_path}")

    if not removed_any:
        print(f"{spec.name}: nothing installed")


# ---- Policy output / clipboard ---------------------------------------------


def run_policy(to_clipboard: bool) -> int:
    block = canonical_policy_block()
    if not to_clipboard:
        sys.stdout.write(block)
        return 0

    clipboard_commands = (
        ["pbcopy"],
        ["wl-copy"],
        ["xclip", "-selection", "clipboard"],
        ["xsel", "--clipboard", "--input"],
        ["clip.exe"],
    )
    copied = False
    for cmd in clipboard_commands:
        if shutil.which(cmd[0]):
            done = subprocess.run(cmd, input=block, text=True, check=False)
            if done.returncode == 0:
                copied = True
                break
    if copied:
        print("Copied canonical Teamwork global policy block to clipboard.")
    else:
        print("No clipboard utility found; printing canonical policy block:", file=sys.stderr)
        sys.stdout.write(block)
    print("Paste into Cursor Settings -> Rules -> User Rules (replacing any previous Teamwork block).")
    return 0


# ---- Doctor diagnostics ----------------------------------------------------


def finding(severity: str, check: str, message: str, **extra: object) -> dict:
    item = {"severity": severity, "check": check, "message": message}
    item.update(extra)
    return item


def sort_findings(items: list[dict]) -> list[dict]:
    return sorted(items, key=lambda x: (SEVERITY_ORDER[x["severity"]], x["check"], x["message"]))


def check_installed_skill(dest: Path, version: str, host: str) -> dict:
    if not dest.exists() and not dest.is_symlink():
        return finding(
            "error",
            "skill-missing",
            f"{host}: policy block is present but Skill is missing at {dest}",
            host=host,
            path=str(dest),
        )
    if not is_owned_skill_dir(dest):
        return finding(
            "error",
            "skill-unrecognized",
            f"{host}: {dest} is not a recognized Teamwork installation",
            host=host,
            path=str(dest),
        )
    expected_files = {
        p.relative_to(SKILL_SOURCE): p.read_bytes()
        for p in SKILL_SOURCE.rglob("*")
        if p.is_file()
    }
    actual_files = {
        p.relative_to(dest): p.read_bytes()
        for p in dest.rglob("*")
        if p.is_file() and p.name != SKILL_VERSION_MARKER
    }
    if expected_files != actual_files:
        return finding(
            "error",
            "skill-drift",
            f"{host}: installed Skill at {dest} differs from checkout",
            host=host,
            path=str(dest),
        )
    if not dest.is_symlink():
        installed_ver = (dest / SKILL_VERSION_MARKER).read_text(encoding="utf-8").strip()
        if installed_ver != version:
            return finding(
                "error",
                "version-drift",
                f"{host}: Skill at {dest} is {installed_ver or 'unknown'}, checkout is {version}",
                host=host,
                path=str(dest),
            )
    mode = "link" if dest.is_symlink() else "copy"
    return finding(
        "info",
        "skill-ok",
        f"{host}: Skill current ({version}, {mode})",
        host=host,
        path=str(dest),
    )


def check_global_hosts(version: str, expected_block: str) -> list[dict]:
    results: list[dict] = []
    for name in HOST_ORDER:
        spec = host_specs()[name]
        dest = spec.skill_root / SKILL_NAME
        skill_exists = dest.exists() or dest.is_symlink()

        if spec.policy_path is None:
            if not skill_exists:
                results.append(
                    finding("info", "host-disabled", f"{name}: not installed", host=name)
                )
            else:
                results.append(check_installed_skill(dest, version, name))
                results.append(
                    finding(
                        "info",
                        "cursor-manual-policy",
                        "cursor: verify User Rules manually (`./install.sh policy --clipboard`)",
                        host="cursor",
                    )
                )
            continue

        p_status = inspect_policy_status(spec.policy_path, expected_block)
        if not skill_exists and p_status == "missing":
            results.append(
                finding("info", "host-disabled", f"{name}: not installed", host=name)
            )
            continue

        results.append(check_installed_skill(dest, version, name))
        if p_status == "current":
            results.append(
                finding(
                    "info",
                    "policy-ok",
                    f"{name}: global policy current in {spec.policy_path}",
                    host=name,
                    path=str(spec.policy_path),
                )
            )
        elif p_status == "missing":
            results.append(
                finding(
                    "error",
                    "policy-missing",
                    f"{name}: Skill is installed without global policy in {spec.policy_path}",
                    host=name,
                    path=str(spec.policy_path),
                )
            )
        elif p_status == "malformed":
            results.append(
                finding(
                    "error",
                    "policy-malformed",
                    f"{name}: malformed Teamwork policy markers in {spec.policy_path}",
                    host=name,
                    path=str(spec.policy_path),
                )
            )
        else:
            results.append(
                finding(
                    "error",
                    "policy-drift",
                    f"{name}: global policy differs from checkout in {spec.policy_path}",
                    host=name,
                    path=str(spec.policy_path),
                )
            )
    return sort_findings(results)


def extract_local_md_links(text: str) -> list[str]:
    refs: list[str] = []
    fence: str | None = None
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
        cleaned = re.sub(r"(`+).*?\1", "", line)
        for match in MARKDOWN_LINK_RE.finditer(cleaned):
            raw = match.group(1) or match.group(2)
            parsed = urlsplit(raw)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            rel = unquote(parsed.path)
            if Path(rel).suffix.lower() == ".md" and rel not in refs:
                refs.append(rel)
    return refs


def link_targets_ephemeral_area(project: Path, resolved_target: Path) -> bool:
    try:
        rel = resolved_target.relative_to(project.resolve())
    except ValueError:
        return True
    return any(part in EPHEMERAL_LINK_SEGMENTS for part in rel.parts[:-1])


def check_project(project: Path) -> list[dict]:
    tw_root = project / "docs" / "teamwork"
    if not tw_root.is_dir():
        return []
    entry = tw_root / "README.md"
    if not entry.is_file():
        if any(p.is_file() for p in tw_root.rglob("*.md")):
            return [
                finding(
                    "error",
                    "entry-missing",
                    f"{tw_root} contains documents without README.md",
                    path=str(tw_root),
                )
            ]
        return []

    try:
        text = entry.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return [
            finding("error", "entry-unreadable", f"cannot read {entry}", path=str(entry))
        ]

    findings: list[dict] = []
    for ref in extract_local_md_links(text):
        candidate = project / ref if ref.startswith("docs/teamwork/") else tw_root / ref
        if candidate.is_file():
            continue
        resolved = Path(os.path.normpath(candidate))
        if link_targets_ephemeral_area(project, resolved):
            findings.append(
                finding(
                    "warn",
                    "missing-artifact-link",
                    f"{entry} links to missing runtime/external path {ref}",
                    path=str(entry),
                )
            )
        else:
            findings.append(
                finding(
                    "error",
                    "dead-link",
                    f"{entry} links to missing document {ref}",
                    path=str(entry),
                )
            )
    return sort_findings(findings)


def discover_projects(scan_root: Path) -> list[Path]:
    found: list[Path] = []
    seen: set[Path] = set()

    def add(candidate: Path) -> None:
        resolved = candidate.resolve()
        if resolved not in seen:
            seen.add(resolved)
            found.append(resolved)

    add(REPO_ROOT)
    if scan_root.is_dir():
        base_depth = len(scan_root.parts)
        for current, dirs, _files in os.walk(scan_root, followlinks=False):
            here = Path(current)
            depth = len(here.parts) - base_depth
            dirs[:] = [
                d
                for d in dirs
                if not d.startswith(".")
                and d not in PRUNED_SCAN_DIRS
                and depth < MAX_SCAN_DEPTH
            ]
            if (here / "docs" / "teamwork").is_dir():
                add(here)
    return sorted(found, key=str)


def render_doctor(report: dict) -> str:
    lines = [f"Teamwork doctor — {report['checkout']} ({report['version']})", "", "GLOBAL"]
    for item in report["global"]:
        lines.append(f"  {item['severity']:<5}  {item['check']:<22}  {item['message']}")
    lines.append("")
    counts = report["summary"]
    lines.append(
        f"PROJECTS ({counts['projects']} checked, {counts['projects_with_errors']} with errors)"
    )
    for proj in report["projects"]:
        if not proj["findings"]:
            continue
        lines.append("")
        lines.append(f"  {proj['path']}")
        for item in proj["findings"]:
            lines.append(f"    {item['severity']:<5}  {item['check']:<22}  {item['message']}")
    clean = [p["path"] for p in report["projects"] if not p["findings"]]
    if clean:
        lines.append("")
        lines.append("  clean: " + ", ".join(clean))
    lines.append("")
    lines.append(
        f"  totals: {counts['error']} error, {counts['warn']} warn, {counts['info']} info"
    )
    return "\n".join(lines)


def run_doctor(project_arg: str | None, as_json: bool) -> int:
    version = repo_version()
    expected_block = canonical_policy_block()

    if project_arg is not None:
        project_path = Path(os.path.abspath(os.path.expanduser(project_arg)))
        if not project_path.is_dir():
            raise UsageError(f"not a directory: {project_path}")
        projects = [project_path.resolve()]
    else:
        projects = discover_projects(Path.home() / "Documents")

    global_findings = check_global_hosts(version, expected_block)
    project_reports = [
        {"path": str(proj), "findings": check_project(proj)} for proj in projects
    ]
    project_reports.sort(
        key=lambda item: (
            min((SEVERITY_ORDER[f["severity"]] for f in item["findings"]), default=3),
            item["path"],
        )
    )
    all_findings = global_findings + [
        f for proj in project_reports for f in proj["findings"]
    ]
    report = {
        "version": version,
        "checkout": str(REPO_ROOT),
        "global": global_findings,
        "projects": project_reports,
        "summary": {
            "projects": len(project_reports),
            "projects_with_errors": sum(
                1
                for proj in project_reports
                if any(f["severity"] == "error" for f in proj["findings"])
            ),
            "error": sum(1 for f in all_findings if f["severity"] == "error"),
            "warn": sum(1 for f in all_findings if f["severity"] == "warn"),
            "info": sum(1 for f in all_findings if f["severity"] == "info"),
        },
    }
    if as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(render_doctor(report))
    return 1 if report["summary"]["error"] else 0


# ---- CLI argument parsing & dispatch ---------------------------------------


def resolve_host_targets(tokens: list[str]) -> list[str]:
    if not tokens:
        raise UsageError("specify at least one host (agy, codex, claude, cursor) or all")
    if "all" in tokens:
        if len(tokens) > 1:
            raise UsageError("`all` cannot be combined with individual host names")
        return list(HOST_ORDER)
    selected: list[str] = []
    for token in tokens:
        canonical = HOST_ALIASES.get(token)
        if canonical is None:
            raise UsageError(f"unknown target: {token}")
        if canonical not in selected:
            selected.append(canonical)
    return selected


def parse_and_run(argv: list[str]) -> int:
    if not argv:
        raise UsageError("missing command or host target")
    if argv in (["-h"], ["--help"]):
        sys.stdout.write(USAGE_TEXT)
        return 0

    head = argv[0]
    if head == "doctor":
        as_json = False
        project_arg: str | None = None
        i = 1
        while i < len(argv):
            arg = argv[i]
            if arg == "--json":
                as_json = True
                i += 1
            elif arg == "--project":
                if i + 1 >= len(argv):
                    raise UsageError("--project requires a directory path")
                project_arg = argv[i + 1]
                i += 2
            elif arg in ("-h", "--help"):
                sys.stdout.write(USAGE_TEXT)
                return 0
            else:
                raise UsageError(f"unknown doctor option: {arg}")
        return run_doctor(project_arg=project_arg, as_json=as_json)

    if head == "policy":
        to_clipboard = False
        for arg in argv[1:]:
            if arg == "--clipboard":
                to_clipboard = True
            elif arg in ("-h", "--help"):
                sys.stdout.write(USAGE_TEXT)
                return 0
            else:
                raise UsageError(f"unknown policy option: {arg}")
        return run_policy(to_clipboard=to_clipboard)

    if head == "uninstall":
        rest = argv[1:]
        if rest in (["-h"], ["--help"]):
            sys.stdout.write(USAGE_TEXT)
            return 0
        targets = resolve_host_targets(rest)
        specs = host_specs()
        for name in targets:
            preflight_uninstall_host(specs[name])
        for name in targets:
            execute_uninstall_host(specs[name])
        return 0

    explicit_mode: str | None = None
    force = False
    tokens: list[str] = []
    for arg in argv:
        if arg == "--copy":
            if explicit_mode == "link":
                raise UsageError("cannot combine --copy and --link")
            explicit_mode = "copy"
        elif arg == "--link":
            if explicit_mode == "copy":
                raise UsageError("cannot combine --copy and --link")
            explicit_mode = "link"
        elif arg == "--force":
            force = True
        elif arg in ("-h", "--help"):
            sys.stdout.write(USAGE_TEXT)
            return 0
        elif arg.startswith("-"):
            raise UsageError(f"unknown option: {arg}")
        else:
            tokens.append(arg)

    if not tokens:
        raise UsageError("specify a host target (agy, codex, claude, cursor), all, or refresh")

    specs = host_specs()
    version = repo_version()
    block = canonical_policy_block()

    if tokens == ["refresh"]:
        installed = [name for name in HOST_ORDER if host_is_installed(specs[name])]
        if not installed:
            raise TeamworkError(
                "no Teamwork host installations found; run `./install.sh <host>` first"
            )
        for name in installed:
            preflight_install_host(specs[name], force=force)
        for name in installed:
            dest = specs[name].skill_root / SKILL_NAME
            mode = explicit_mode or ("link" if dest.is_symlink() else "copy")
            execute_install_host(specs[name], mode=mode, version=version, block=block)
        return 0

    if "refresh" in tokens:
        raise UsageError("`refresh` cannot be combined with other targets")
    if any(t in ("doctor", "policy", "uninstall") for t in tokens):
        raise UsageError("subcommands (doctor, policy, uninstall) must appear first")

    targets = resolve_host_targets(tokens)
    mode = explicit_mode or os.environ.get("TEAMWORK_INSTALL_MODE", "copy")
    if mode not in ("copy", "link"):
        raise UsageError(f"invalid TEAMWORK_INSTALL_MODE: {mode}")

    for name in targets:
        preflight_install_host(specs[name], force=force)
    for name in targets:
        execute_install_host(specs[name], mode=mode, version=version, block=block)
    return 0


def main() -> int:
    try:
        return parse_and_run(sys.argv[1:])
    except UsageError as exc:
        print(f"Error: {exc}\n", file=sys.stderr)
        sys.stderr.write(USAGE_TEXT)
        return 2
    except TeamworkError as exc:
        print(f"Teamwork error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
