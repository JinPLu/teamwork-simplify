#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
MODE=fast
if [[ "${1:-}" == "--release" || "${1:-}" == "--full" ]]; then
  MODE=release
elif [[ -n "${1:-}" && "${1:-}" != "--fast" ]]; then
  echo "Usage: ./scripts/validate.sh [--fast|--release]" >&2
  exit 2
fi

bash -n "$ROOT/install.sh" \
  "$ROOT/scripts/init-project.sh" "$ROOT/scripts/install/"*.sh

PYTHONDONTWRITEBYTECODE=1 python3 "$ROOT/scripts/plugin-runtime-root.py" >/dev/null
PYTHONDONTWRITEBYTECODE=1 python3 "$ROOT/scripts/write-source-pointer.py" check

# The suite is behavior-only: every case runs the real installer or the real
# project-init script against a throwaway HOME and reads the filesystem back.
# Wording, word-list, file-count and frontmatter-key assertions were removed in
# 2026-08-29 because a mutation audit showed they passed while the product was
# gutted; a case that cannot be made to fail is not kept here.
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  scripts.tests.test_installer_behavior \
  scripts.tests.test_project_init_behavior \
  scripts.tests.test_doctor_shape_behavior

if [[ "$MODE" == release ]]; then
  python3 - "$ROOT" <<'PY'
import pathlib
import re
import sys

root = pathlib.Path(sys.argv[1])
version = (root / "VERSION").read_text(encoding="utf-8").strip()
if not re.fullmatch(r"\d+\.\d+\.\d+", version):
    raise SystemExit("VERSION must be semver for release")
PY
fi

echo "OK: Teamwork validation ($MODE)"
