#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Teamwork requires python3." >&2
  exit 1
fi

PYTHONDONTWRITEBYTECODE=1 exec python3 "$ROOT/scripts/teamwork.py" "$@"
