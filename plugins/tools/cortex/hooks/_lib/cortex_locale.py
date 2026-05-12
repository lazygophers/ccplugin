#!/usr/bin/env python3
"""locale.py — cortex i18n locale loader (stdlib only).

Locale file lookup priority (per prd §4.1):
  1. <vault>/locales/<lang>.yml         — vault-level override
  2. ~/.config/cortex/locales/<lang>.yml — user-level override
  3. <plugin>/locales/<lang>.yml         — plugin builtin

Fallback chain (per key, not per file):
  zh-CN -> zh -> en -> KeyError

Supported YAML subset:
  - nested mappings (2-space indent)
  - scalar strings (quoted or bare; preserves trailing chars)
  - flow lists [a, b, c] (parsed into list)
  - block lists with `- item`
  - line comments starting with `#`
  - block scalar `|` (folded into multi-line string)

Not supported: anchors, aliases, !!tags, multi-document.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any


# ---------- minimal YAML parser ----------


def _parse_scalar(raw: str) -> Any:
    s = raw.strip()
    if not s:
        return ""
    # Strip quotes
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        return s[1:-1]
    # Flow list
    if s.startswith("[") and s.endswith("]"):
        inner = s[1:-1].strip()
        if not inner:
            return []
        return [p.strip().strip('"').strip("'") for p in inner.split(",")]
    # bool / null
    low = s.lower()
    if low in ("true", "yes"):
        return True
    if low in ("false", "no"):
        return False
    if low in ("null", "~", ""):
        return ""
    return s


def _strip_comment(line: str) -> str:
    """Strip trailing # comment but not inside quotes."""
    in_s = False
    in_d = False
    for i, ch in enumerate(line):
        if ch == "'" and not in_d:
            in_s = not in_s
        elif ch == '"' and not in_s:
            in_d = not in_d
        elif ch == "#" and not in_s and not in_d:
            # require whitespace before # to count as comment
            if i == 0 or line[i - 1] in (" ", "\t"):
                return line[:i].rstrip()
    return line.rstrip()


def parse_yaml(text: str) -> dict[str, Any]:
    """Parse subset YAML to dict. Best-effort, never raises on minor issues."""
    raw_lines = text.splitlines()
    # Pre-process: keep original line for indent; strip comments unless inside block scalar
    lines: list[tuple[int, str]] = []  # (indent, content)
    i = 0
    while i < len(raw_lines):
        line = raw_lines[i]
        stripped_full = line.strip()
        if not stripped_full or stripped_full.startswith("#"):
            i += 1
            continue
        line = _strip_comment(line)
        if not line.strip():
            i += 1
            continue
        indent = len(line) - len(line.lstrip(" "))
        lines.append((indent, line.lstrip(" ")))
        i += 1

    root: dict[str, Any] = {}
    # stack of (indent, container, last_key)
    stack: list[tuple[int, Any, str | None]] = [(-1, root, None)]
    idx = 0
    while idx < len(lines):
        indent, content = lines[idx]
        # pop stack until indent > top.indent
        while stack and indent <= stack[-1][0]:
            stack.pop()
        if not stack:
            stack = [(-1, root, None)]
        _, parent, _ = stack[-1]

        # block list item
        if content.startswith("- "):
            item = content[2:].strip()
            if isinstance(parent, list):
                parent.append(_parse_scalar(item))
            idx += 1
            continue

        # key: value
        if ":" not in content:
            idx += 1
            continue
        key, _, val = content.partition(":")
        key = key.strip()
        val = val.strip()

        if val == "":
            # nested map or list — peek next
            next_idx = idx + 1
            if next_idx < len(lines) and lines[next_idx][0] > indent:
                nxt_content = lines[next_idx][1]
                if nxt_content.startswith("- "):
                    new_container: Any = []
                else:
                    new_container = {}
                if isinstance(parent, dict):
                    parent[key] = new_container
                stack.append((indent, new_container, key))
                idx += 1
                continue
            # empty value
            if isinstance(parent, dict):
                parent[key] = ""
            idx += 1
            continue

        if val == "|":
            # block scalar — collect indented lines that follow
            block_lines = []
            min_indent = None
            j = idx + 1
            while j < len(lines):
                ind, body = lines[j]
                if ind <= indent:
                    break
                if min_indent is None:
                    min_indent = ind
                # reconstruct prefix (preserve relative indent)
                block_lines.append(" " * (ind - (min_indent or ind)) + body)
                j += 1
            if isinstance(parent, dict):
                parent[key] = "\n".join(block_lines)
            idx = j
            continue

        # scalar value
        if isinstance(parent, dict):
            parent[key] = _parse_scalar(val)
        idx += 1

    return root


# ---------- locale loader ----------


def _candidate_paths(plugin_root: Path, vault: Path | None, lang: str) -> list[Path]:
    out: list[Path] = []
    if vault:
        out.append(Path(vault) / "locales" / f"{lang}.yml")
    out.append(Path(os.path.expanduser("~/.config/cortex/locales")) / f"{lang}.yml")
    out.append(Path(plugin_root) / "locales" / f"{lang}.yml")
    return out


def _load_one(plugin_root: Path, vault: Path | None, lang: str) -> dict[str, Any]:
    """Merge all three layers (vault > user > plugin) for a single lang."""
    merged: dict[str, Any] = {}
    # Read in reverse priority (lowest first) so highest overwrites
    for p in reversed(_candidate_paths(plugin_root, vault, lang)):
        if not p.is_file():
            continue
        try:
            text = p.read_text(encoding="utf-8")
            data = parse_yaml(text)
            merged = _deep_merge(merged, data)
        except Exception:
            continue
    return merged


def _deep_merge(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    out = dict(a)
    for k, v in b.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def _fallback_chain(lang: str) -> list[str]:
    """zh-CN -> zh -> en; en -> en; ja -> en; xx-YY -> xx -> en."""
    chain = [lang]
    if "-" in lang:
        chain.append(lang.split("-", 1)[0])
    if "en" not in chain:
        chain.append("en")
    return chain


class Locale:
    """Resolved locale view with key-level fallback."""

    def __init__(self, plugin_root: Path, vault: Path | None, lang: str):
        self.plugin_root = Path(plugin_root)
        self.vault = Path(vault) if vault else None
        self.lang = lang
        self._stack: list[dict[str, Any]] = []
        for code in _fallback_chain(lang):
            data = _load_one(self.plugin_root, self.vault, code)
            if data:
                self._stack.append(data)

    def get(self, dotted_key: str, default: Any = None) -> Any:
        for layer in self._stack:
            cur: Any = layer
            ok = True
            for part in dotted_key.split("."):
                if isinstance(cur, dict) and part in cur:
                    cur = cur[part]
                else:
                    ok = False
                    break
            if ok and cur != "" and cur is not None:
                return cur
        return default

    def get_dirs(self) -> dict[str, str]:
        out: dict[str, str] = {}
        for layer in reversed(self._stack):
            d = layer.get("dirs", {}) if isinstance(layer.get("dirs"), dict) else {}
            for k, v in d.items():
                if isinstance(v, str) and v:
                    out[k] = v
        return out

    def get_files(self) -> dict[str, str]:
        out: dict[str, str] = {}
        for layer in reversed(self._stack):
            d = layer.get("files", {}) if isinstance(layer.get("files"), dict) else {}
            for k, v in d.items():
                if isinstance(v, str) and v:
                    out[k] = v
        return out

    def get_prompt(self, key: str, **vars: Any) -> str:
        raw = self.get(f"prompts.{key}", "")
        if not isinstance(raw, str):
            return ""
        if vars:
            try:
                return raw.format(**vars)
            except Exception:
                return raw
        return raw

    def chain(self) -> list[str]:
        return _fallback_chain(self.lang)


def load_locale(plugin_root: str | Path, vault: str | Path | None, lang: str) -> Locale:
    """Public API: build a Locale view for given lang with full fallback chain.

    plugin_root: path to plugins/tools/cortex/
    vault: vault root (may be None for cron / programmatic use)
    lang: e.g. "zh-CN" / "en" / "ja"
    """
    return Locale(Path(plugin_root), Path(vault) if vault else None, lang)


def detect_vault_lang(vault: Path | str) -> str:
    """Resolve lang: vault _meta/version.json > config.lang > zh-CN.

    Env var lookup removed per PRD (config-only). Plugin business code uses
    `~/.cortex/config.json` exclusively for the `lang` field.
    """
    import json

    p = Path(vault) / "_meta" / "version.json"
    if p.is_file():
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            v = data.get("lang") if isinstance(data, dict) else None
            if isinstance(v, str) and v:
                return v
        except Exception:
            pass

    try:
        from cortex_config import load_config
        cfg_lang = load_config().get("lang")
        if isinstance(cfg_lang, str) and cfg_lang:
            return cfg_lang
    except ImportError:
        pass
    return "zh-CN"


# ---------- self-test ----------

if __name__ == "__main__":
    import sys

    plugin_root = Path(__file__).resolve().parents[2]
    lang = sys.argv[1] if len(sys.argv) > 1 else "zh-CN"
    loc = load_locale(plugin_root, None, lang)
    print(f"lang={lang} chain={loc.chain()}")
    print(f"display={loc.get('meta.display')}")
    print(f"dirs={loc.get_dirs()}")
    print(f"search_first={loc.get_prompt('search_first')}")
    print(f"archive_pending={loc.get_prompt('archive_pending', path='log/2026-05/11-foo.md')}")
