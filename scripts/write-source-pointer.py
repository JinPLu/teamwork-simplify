#!/usr/bin/env python3
"""Write or validate ~/.teamwork/install.json, the Teamwork source pointer."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VALID_HOSTS = ("claude", "codex", "cursor")
REQUIRED_KEYS = ("root", "version", "hosts", "installed_at")


class PointerError(ValueError):
    """The pointer object does not match the closed schema."""


def pointer_path(home: Path) -> Path:
    return home / ".teamwork" / "install.json"


def checkout_is_valid(root: Path) -> bool:
    return (
        (root / "VERSION").is_file()
        and (root / "skills").is_dir()
        and (root / "install.sh").is_file()
    )


def validate_pointer_object(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise PointerError("pointer must be a JSON object")
    extra = sorted(set(value) - set(REQUIRED_KEYS))
    if extra:
        raise PointerError(f"unexpected pointer keys: {extra}")
    missing = [key for key in REQUIRED_KEYS if key not in value]
    if missing:
        raise PointerError(f"missing pointer keys: {missing}")

    root = value["root"]
    if not isinstance(root, str) or not root or not Path(root).is_absolute():
        raise PointerError("root must be an absolute path")

    version = value["version"]
    if not isinstance(version, str) or not version.strip():
        raise PointerError("version must be a non-empty string")

    hosts = value["hosts"]
    if not isinstance(hosts, list):
        raise PointerError("hosts must be a list")
    seen: set[str] = set()
    for host in hosts:
        if not isinstance(host, str) or host not in VALID_HOSTS:
            raise PointerError("hosts must be unique known host names")
        if host in seen:
            raise PointerError("hosts must be unique known host names")
        seen.add(host)

    installed_at = value["installed_at"]
    if not isinstance(installed_at, str) or not installed_at.strip():
        raise PointerError("installed_at must be a non-empty string")
    return value


def merge_hosts(existing: list[str], incoming: list[str]) -> list[str]:
    merged: list[str] = []
    for host in existing + incoming:
        if host in VALID_HOSTS and host not in merged:
            merged.append(host)
    return merged


def load_existing_hosts(path: Path) -> list[str]:
    if not path.is_file() or path.is_symlink():
        return []
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if not isinstance(value, dict) or not isinstance(value.get("hosts"), list):
        return []
    return [host for host in value["hosts"] if isinstance(host, str) and host in VALID_HOSTS]


def atomic_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, raw_tmp = tempfile.mkstemp(prefix=f".{path.name}.teamwork-", dir=path.parent)
    temporary = Path(raw_tmp)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        temporary.unlink(missing_ok=True)


def write_pointer(path: Path, root: Path, version: str, hosts: list[str]) -> dict[str, Any]:
    value = {
        "root": str(root.resolve()),
        "version": version,
        "hosts": merge_hosts(load_existing_hosts(path), hosts),
        "installed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    validate_pointer_object(value)
    atomic_write(path, value)
    return value


def pointer_status(path: Path) -> str:
    if path.is_symlink():
        return "invalid"
    if not path.exists():
        return "missing"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        validate_pointer_object(value)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, PointerError):
        return "invalid"
    if not checkout_is_valid(Path(value["root"])):
        return "invalid"
    return "valid"


def self_check() -> None:
    valid = {
        "root": "/tmp/teamwork",
        "version": "7.10.1",
        "hosts": ["codex", "cursor"],
        "installed_at": "2026-08-21T00:00:00Z",
    }
    validate_pointer_object(valid)
    validate_pointer_object(
        {
            "root": "/tmp/teamwork",
            "version": "7.10.1",
            "hosts": [],
            "installed_at": "2026-08-21T00:00:00Z",
        }
    )
    invalid_cases: tuple[object, ...] = (
        [],
        "pointer",
        {},
        {
            "root": "relative",
            "version": "7.10.1",
            "hosts": [],
            "installed_at": "2026-08-21T00:00:00Z",
        },
        {
            "root": "/tmp/teamwork",
            "version": "",
            "hosts": [],
            "installed_at": "2026-08-21T00:00:00Z",
        },
        {
            "root": "/tmp/teamwork",
            "version": "7.10.1",
            "hosts": ["vim"],
            "installed_at": "2026-08-21T00:00:00Z",
        },
        {
            "root": "/tmp/teamwork",
            "version": "7.10.1",
            "hosts": ["codex", "codex"],
            "installed_at": "2026-08-21T00:00:00Z",
        },
        {
            "root": "/tmp/teamwork",
            "version": "7.10.1",
            "hosts": ["codex"],
            "installed_at": "2026-08-21T00:00:00Z",
            "extra": True,
        },
    )
    for case in invalid_cases:
        try:
            validate_pointer_object(case)
        except PointerError:
            continue
        raise SystemExit(f"schema accepted an invalid pointer object: {case!r}")


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument(
        "action",
        choices=("write", "status", "check"),
        nargs="?",
        default="check",
    )
    result.add_argument("--root", type=Path)
    result.add_argument("--version")
    result.add_argument("--home", type=Path, default=Path.home())
    result.add_argument("--host", action="append", dest="hosts", default=[])
    return result


def main() -> int:
    args = parser().parse_args()
    if args.action == "check" or args.action is None:
        self_check()
        return 0

    home = args.home.expanduser()
    path = pointer_path(home)
    if args.action == "status":
        print(pointer_status(path))
        return 0

    if args.root is None or not args.version:
        raise SystemExit("write requires --root and --version")
    for host in args.hosts:
        if host not in VALID_HOSTS:
            raise SystemExit(f"unknown Teamwork host: {host}")
    try:
        write_pointer(path, args.root.expanduser(), args.version, args.hosts)
    except (OSError, PointerError) as exc:
        print(f"ERROR: cannot write Teamwork source pointer at {path}: {exc}", file=sys.stderr)
        return 1
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
