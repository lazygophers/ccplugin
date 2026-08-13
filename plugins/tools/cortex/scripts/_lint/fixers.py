"""cortex lint autofix 实现 (仅 R2 frontmatter / R4 mkdir 可逆).

不可逆操作 (R1 死链 / R3 命名 / R5 孤儿 / R6 反写 / R7 目录混淆) 仅标记不动.
"""
from __future__ import annotations

import datetime as _dt
from pathlib import Path

from . import (
    FRONTMATTER_RE,
    Violation,
    parse_frontmatter,
    serialize_frontmatter,
)


def fix_R2(vault_root: Path, v: Violation) -> bool:
    """补齐缺失字段. v.hint 含建议值. 返回是否落盘."""
    p = vault_root / v.file
    if not p.is_file():
        return False
    text = p.read_text(encoding="utf-8")
    fm, _end = parse_frontmatter(text)
    data = dict(fm) if fm else {}

    # 按 hint 补齐
    for k, val in v.hint.items():
        if not data.get(k):
            data[k] = val

    # created 兜底 (mtime)
    if not data.get("created"):
        try:
            mt = p.stat().st_mtime
            data["created"] = _dt.date.fromtimestamp(mt).isoformat()
        except OSError:
            pass

    new_fm = serialize_frontmatter(data)
    m = FRONTMATTER_RE.match(text)
    if m:
        new_text = new_fm + text[m.end():]
    else:
        new_text = new_fm + text
    if new_text != text:
        p.write_text(new_text, encoding="utf-8")
        return True
    return False


def fix_R4(vault_root: Path, v: Violation) -> bool:
    """mkdir -p 缺失目录. 同时放一个 .gitkeep 防空目录被忽略."""
    missing = v.hint.get("mkdir", [])
    changed = False
    for d in missing:
        target = vault_root / d
        if not target.exists():
            target.mkdir(parents=True, exist_ok=True)
            (target / ".gitkeep").touch()
            changed = True
    return changed


FIXABLE = {"R2", "R4"}


def apply_fix(vault_root: Path, v: Violation) -> bool:
    if v.rule == "R2":
        return fix_R2(vault_root, v)
    if v.rule == "R4":
        return fix_R4(vault_root, v)
    return False
