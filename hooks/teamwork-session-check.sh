#!/usr/bin/env bash
# Claude Code SessionStart hook: report Teamwork errors, and nothing else.
#
# A check that prints on every session start is read once and ignored after
# that, so this stays silent unless doctor found an error. It always exits 0:
# a session must never fail to start because a health check had an opinion.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOCTOR="$ROOT/scripts/doctor.py"
PROJECT="${CLAUDE_PROJECT_DIR:-$PWD}"

[[ -f "$DOCTOR" && -d "$PROJECT" ]] || exit 0

REPORT=""
if ! REPORT="$(python3 "$DOCTOR" --project "$PROJECT" --json 2>/dev/null)"; then
  : # doctor exits non-zero when it found errors; the report is still on stdout
fi
[[ -n "$REPORT" ]] || exit 0

printf '%s' "$REPORT" | python3 -c '
import json
import sys

report = json.load(sys.stdin)
errors = [dict(item, where="install") for item in report["global"] if item["severity"] == "error"]
for project in report["projects"]:
    errors += [
        dict(item, where=project["path"])
        for item in project["findings"]
        if item["severity"] == "error"
    ]
if not errors:
    raise SystemExit(0)

print(f"Teamwork doctor: {len(errors)} error(s). Full report: ./install.sh doctor")
for item in errors[:8]:
    print("  [" + item["check"] + "] " + item["where"] + ": " + item["message"])
if len(errors) > 8:
    print(f"  ... and {len(errors) - 8} more")
' || true

exit 0
