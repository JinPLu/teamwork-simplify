"""Load a restricted YAML subset without a third-party parser."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


def load_simple_yaml(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    lines: list[str] = []
    for raw in text.splitlines():
        stripped = _strip_comment(raw).rstrip()
        if stripped.strip():
            lines.append(stripped)
    value, index = _parse_map(lines, 0, 0)
    if index != len(lines):
        raise ValueError(f"unparsed YAML at {path}:{index + 1}")
    return value


def _strip_comment(line: str) -> str:
    in_single = False
    in_double = False
    escaped = False
    for i, char in enumerate(line):
        if in_double:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_double = False
            continue
        if in_single:
            if char == "'":
                in_single = False
            continue
        if char == '"':
            in_double = True
        elif char == "'":
            in_single = True
        elif char == "#":
            return line[:i]
    return line


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _parse_scalar(raw: str) -> Any:
    value = raw.strip()
    if not value:
        return ""
    if value in {"null", "~", "Null", "NULL"}:
        return None
    if value in {"true", "True", "TRUE"}:
        return True
    if value in {"false", "False", "FALSE"}:
        return False
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    if value[0] in {'"', "'"}:
        if value[0] == '"':
            return json.loads(value)
        if len(value) >= 2 and value[-1] == "'":
            return value[1:-1].replace("''", "'")
    return value


def _parse_map(lines: list[str], index: int, min_indent: int) -> tuple[dict[str, Any], int]:
    result: dict[str, Any] = {}
    while index < len(lines):
        line = lines[index]
        indent = _indent(line)
        if indent < min_indent:
            break
        if indent != min_indent:
            raise ValueError(f"bad YAML indent: {line}")
        if line.lstrip().startswith("- "):
            raise ValueError(f"expected mapping key: {line}")
        key, sep, rest = line.strip().partition(":")
        if not sep:
            raise ValueError(f"expected ':' in YAML mapping: {line}")
        key = key.strip()
        rest = rest.strip()
        index += 1
        if rest:
            result[key] = _parse_scalar(rest)
            continue
        if index >= len(lines) or _indent(lines[index]) <= min_indent:
            result[key] = {}
            continue
        child_indent = _indent(lines[index])
        if lines[index].lstrip().startswith("- "):
            result[key], index = _parse_list(lines, index, child_indent)
        else:
            result[key], index = _parse_map(lines, index, child_indent)
    return result, index


def _parse_list(lines: list[str], index: int, min_indent: int) -> tuple[list[Any], int]:
    result: list[Any] = []
    while index < len(lines):
        line = lines[index]
        indent = _indent(line)
        if indent < min_indent:
            break
        stripped = line.lstrip()
        if not stripped.startswith("- "):
            break
        rest = stripped[2:].strip()
        index += 1
        if rest:
            result.append(_parse_scalar(rest))
            continue
        if index >= len(lines) or _indent(lines[index]) <= min_indent:
            result.append({})
            continue
        child_indent = _indent(lines[index])
        if lines[index].lstrip().startswith("- "):
            nested, index = _parse_list(lines, index, child_indent)
            result.append(nested)
        else:
            nested, index = _parse_map(lines, index, child_indent)
            result.append(nested)
    return result, index
