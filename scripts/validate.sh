#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

MODE="fast"
if [[ "${1:-}" == "--release" || "${1:-}" == "--full" ]]; then
  MODE="release"
elif [[ -n "${1:-}" && "${1:-}" != "--fast" ]]; then
  echo "Usage: ./scripts/validate.sh [--fast|--release]" >&2
  exit 2
fi

bash -n "$ROOT/install.sh" "$ROOT/scripts/validate.sh"

PYTHONDONTWRITEBYTECODE=1 python3 - "$ROOT" <<'PY'
import pathlib
import re
import sys

root = pathlib.Path(sys.argv[1])
version = (root / "VERSION").read_text(encoding="utf-8").strip()
if not re.fullmatch(r"\d+\.\d+\.\d+", version):
    raise SystemExit(f"VERSION must be semver, got: {version!r}")

skill_dir = root / "skills" / "teamwork-collaborate"
files = sorted(p.relative_to(skill_dir).as_posix() for p in skill_dir.rglob("*") if p.is_file())
if files != ["SKILL.md"]:
    raise SystemExit(f"teamwork-collaborate must contain only SKILL.md, got: {files}")

text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
if not match:
    raise SystemExit("SKILL.md is missing YAML frontmatter")
fields = {}
for line in match.group(1).splitlines():
    if ":" not in line:
        raise SystemExit(f"invalid frontmatter line: {line!r}")
    key, value = line.split(":", 1)
    fields[key.strip()] = value.strip()
if set(fields) != {"name", "description"}:
    raise SystemExit(f"SKILL.md frontmatter must have only name and description, got: {sorted(fields)}")
if fields["name"] != "teamwork-collaborate":
    raise SystemExit(f"unexpected skill name: {fields['name']!r}")
if not fields["description"].startswith("Use when "):
    raise SystemExit("SKILL.md description must start with 'Use when '")
PY

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest scripts.tests.test_teamwork_behavior

echo "OK: Teamwork validation ($MODE)"
