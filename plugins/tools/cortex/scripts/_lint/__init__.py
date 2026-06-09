"""cortex lint 内部模块.

提供 Violation 数据类 + frontmatter 解析工具.

不依赖第三方包 (pyyaml 若可用则用; 否则 fallback 简易解析).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

try:
    import yaml  # type: ignore
    _HAS_YAML = True
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore
    _HAS_YAML = False


# 路径名 ↔ level 权威映射 (权威源: cortex-schema-memory/references/levels.md)
LEVEL_DIR_MAP = {
    "L0-core": "L0",
    "L1-long": "L1",
    "L2-mid": "L2",
    "L3-short": "L3",
    "L4-inbox": "L4",
}

VAULT_REQUIRED_DIRS = [
    "memory/L0-core",
    "memory/L1-long",
    "memory/L2-mid",
    "memory/L3-short",
    "memory/L4-inbox",
    "项目",
    "领域",
    "脚本",
]

KEBAB_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
WIKILINK_RE = re.compile(r"\[\[([^\]\|#]+?)(?:#[^\]\|]+)?(?:\|[^\]]+)?\]\]")
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


@dataclass
class Violation:
    file: str
    rule: str         # R1..R7
    level: str        # "error" | "warn"
    msg: str
    line: Optional[int] = None
    # autofix 提示: fixer 可读取
    hint: dict = field(default_factory=dict)

    def format(self) -> str:
        loc = f"{self.file}:{self.line}" if self.line else self.file
        return f"{loc}:{self.rule}:{self.level}:{self.msg}"


def parse_frontmatter(text: str) -> tuple[Optional[dict[str, Any]], int]:
    """解析 markdown 顶部 frontmatter. 返回 (data | None, end_line).

    end_line = frontmatter 结束行 (1-based). data=None 表示无 frontmatter.
    """
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None, 0
    block = m.group(1)
    end_line = block.count("\n") + 2  # --- + block + ---
    if _HAS_YAML:
        try:
            data = yaml.safe_load(block) or {}
            if not isinstance(data, dict):
                return None, end_line
            return data, end_line
        except Exception:
            return _fallback_parse(block), end_line
    return _fallback_parse(block), end_line


def _fallback_parse(block: str) -> dict[str, Any]:
    """简易 frontmatter 解析: 只支持 `key: value` 与 `key: [a, b]` 形式."""
    out: dict[str, Any] = {}
    for raw in block.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        v = v.strip()
        if v.startswith("[") and v.endswith("]"):
            inner = v[1:-1].strip()
            out[k.strip()] = [s.strip().strip("'\"") for s in inner.split(",") if s.strip()]
        elif v == "":
            out[k.strip()] = ""
        else:
            out[k.strip()] = v.strip("'\"")
    return out


def serialize_frontmatter(data: dict[str, Any]) -> str:
    """重新序列化 frontmatter. 优先 pyyaml, 否则手工渲染."""
    if _HAS_YAML:
        body = yaml.safe_dump(data, allow_unicode=True, sort_keys=False).rstrip()
    else:
        lines = []
        for k, v in data.items():
            if isinstance(v, list):
                inner = ", ".join(str(x) for x in v)
                lines.append(f"{k}: [{inner}]")
            else:
                lines.append(f"{k}: {v}")
        body = "\n".join(lines)
    return f"---\n{body}\n---\n"


def find_md_files(root: Path) -> list[Path]:
    return [p for p in root.rglob("*.md") if p.is_file()]


def vault_root_of(target: Path) -> Path:
    """识别 vault 根. 若 target 含 .wiki/ 则用之, 否则 target 本身视作 vault 根."""
    wiki = target / ".wiki"
    if wiki.is_dir():
        return wiki
    return target
