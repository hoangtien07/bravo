"""Small YAML compatibility helper for BRAVO data artifacts.

Production/dev should use PyYAML. The fallback parser exists so static readiness checks can
run in stripped-down environments (for example the bundled Codex Python used in this
workspace) where PyYAML is not installed. It intentionally supports only the YAML subset
used by BRAVO artifact files: mappings, list items, nested mappings, inline lists and
plain/quoted scalars.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any


def safe_load_text(text: str) -> Any:
    try:
        import yaml  # type: ignore

        return yaml.safe_load(text)
    except ModuleNotFoundError:
        return _MiniYaml(text).parse()


def safe_load_file(path: str | Path) -> Any:
    return safe_load_text(Path(path).read_text(encoding="utf-8"))


def _strip_comment(line: str) -> str:
    in_single = False
    in_double = False
    out: list[str] = []
    for ch in line:
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        if ch == "#" and not in_single and not in_double:
            break
        out.append(ch)
    return "".join(out).rstrip()


def _split_key_value(text: str) -> tuple[str, str] | None:
    in_single = False
    in_double = False
    for i, ch in enumerate(text):
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        elif ch == ":" and not in_single and not in_double:
            return text[:i].strip(), text[i + 1:].strip()
    return None


def _split_inline_list(value: str) -> list[str]:
    body = value.strip()[1:-1].strip()
    if not body:
        return []
    parts: list[str] = []
    buf: list[str] = []
    in_single = False
    in_double = False
    for ch in body:
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        if ch == "," and not in_single and not in_double:
            parts.append("".join(buf).strip())
            buf.clear()
        else:
            buf.append(ch)
    if buf:
        parts.append("".join(buf).strip())
    return parts


def _scalar(value: str) -> Any:
    value = value.strip()
    if value == "":
        return None
    if value.startswith("[") and value.endswith("]"):
        return [_scalar(part) for part in _split_inline_list(value)]
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    low = value.lower()
    if low in {"true", "false"}:
        return low == "true"
    if low in {"null", "~"}:
        return None
    try:
        return int(value)
    except ValueError:
        return value


class _MiniYaml:
    def __init__(self, text: str):
        self.lines: list[tuple[int, str]] = []
        for raw in text.splitlines():
            stripped = _strip_comment(raw)
            if not stripped.strip():
                continue
            indent = len(stripped) - len(stripped.lstrip(" "))
            self.lines.append((indent, stripped.strip()))
        self.i = 0

    def parse(self) -> Any:
        if not self.lines:
            return None
        return self._parse_block(self.lines[0][0])

    def _parse_block(self, indent: int) -> Any:
        if self.i >= len(self.lines):
            return {}
        _cur_indent, content = self.lines[self.i]
        if content.startswith("- "):
            return self._parse_list(indent)
        return self._parse_map(indent)

    def _parse_map(self, indent: int) -> dict[str, Any]:
        out: dict[str, Any] = {}
        while self.i < len(self.lines):
            cur_indent, content = self.lines[self.i]
            if cur_indent < indent or content.startswith("- "):
                break
            if cur_indent > indent:
                raise ValueError(f"Unexpected indentation near: {content}")
            kv = _split_key_value(content)
            if kv is None:
                raise ValueError(f"Expected key: value near: {content}")
            key, value = kv
            self.i += 1
            if value:
                out[key] = _scalar(value)
            elif self.i < len(self.lines) and self.lines[self.i][0] > cur_indent:
                out[key] = self._parse_block(self.lines[self.i][0])
            else:
                out[key] = None
        return out

    def _parse_list(self, indent: int) -> list[Any]:
        out: list[Any] = []
        while self.i < len(self.lines):
            cur_indent, content = self.lines[self.i]
            if cur_indent < indent or not content.startswith("- "):
                break
            if cur_indent > indent:
                raise ValueError(f"Unexpected list indentation near: {content}")
            rest = content[2:].strip()
            self.i += 1
            if not rest:
                if self.i < len(self.lines) and self.lines[self.i][0] > cur_indent:
                    out.append(self._parse_block(self.lines[self.i][0]))
                else:
                    out.append(None)
                continue
            kv = _split_key_value(rest)
            if kv is None:
                out.append(_scalar(rest))
                continue
            key, value = kv
            item: dict[str, Any] = {}
            if value:
                item[key] = _scalar(value)
            elif self.i < len(self.lines) and self.lines[self.i][0] > cur_indent:
                item[key] = self._parse_block(self.lines[self.i][0])
            else:
                item[key] = None
            if self.i < len(self.lines) and self.lines[self.i][0] > cur_indent:
                nested = self._parse_map(self.lines[self.i][0])
                item.update(nested)
            out.append(item)
        return out
