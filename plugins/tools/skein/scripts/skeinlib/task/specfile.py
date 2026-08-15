"""prd.md 的 TaskSpec 读写 — YAML frontmatter 承载 desc/boundary/estimate/acceptance。

prd.md 是 TaskSpec 四要素的**唯一真值** (task.json 不落这些字段); frontmatter 下方可自由写
需求散文 (人读, 不参与校验)。写路径只经本模块, 禁手改 (结构坏 = confirm 硬门全瞎)。
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from skeinlib.utils.errors import SkeinError

# TaskSpec 四字段 — 注入 task dict 的键, 也是 store.save 需剥离的键
SPEC_KEYS = ("desc", "boundary", "estimate", "acceptance")


def prd_path(tasks_dir: Path, tid: str) -> Path:
    """定位 task 的 prd.md; 不存在 raise SkeinError。"""
    prd = tasks_dir / tid / "prd.md"
    if not prd.exists():
        raise SkeinError(f"{tid} 无 prd.md — 先 skein task create 再操作 spec")
    return prd


def load_spec(tasks_dir: Path, tid: str) -> dict[str, Any]:
    """读 prd.md frontmatter → spec dict (缺文件/无 frontmatter 返回空 dict, 不抛)。"""
    prd = tasks_dir / tid / "prd.md"
    if not prd.exists():
        return {}
    text = prd.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end < 0:
        return {}
    block = text[4:end] if text[3] == "\n" else text[3:end]
    data = yaml.safe_load(block)
    return data if isinstance(data, dict) else {}


def save_spec(tasks_dir: Path, tid: str, spec: dict[str, Any]) -> None:
    """整块重写 prd.md 的 frontmatter, 正文散文区原样保留。"""
    prd = prd_path(tasks_dir, tid)
    text = prd.read_text(encoding="utf-8")
    body = text
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end >= 0:
            body = text[end + 4:]  # 跳过结束 --- 行
    head = yaml.safe_dump({k: spec[k] for k in SPEC_KEYS if k in spec},
                          allow_unicode=True, sort_keys=False, default_flow_style=False)
    prd.write_text(f"---\n{head}---\n{body.lstrip(chr(10))}", encoding="utf-8")


def scaffold_spec(name: str, desc: str = "", estimate: Any = None) -> str:
    """task create 用的 prd.md 初始模板 (frontmatter 骨架 + 空散文区)。"""
    spec: dict[str, Any] = {"desc": desc, "boundary": {"should": [], "should_not": []},
                            "acceptance": []}
    if estimate is not None:
        spec["estimate"] = estimate
    head = yaml.safe_dump(spec, allow_unicode=True, sort_keys=False, default_flow_style=False)
    return (f"---\n{head}---\n"
            f"# {name} — 需求\n\n"
            f"frontmatter 为 TaskSpec 四要素 (`skein task spec` 读写); 下方自由写需求细节。\n")


def validate_spec(tasks_dir: Path, tid: str) -> dict[str, Any]:
    """confirm 硬门: 四要素齐备 (desc 非空 / 边界有内容 / 验收非空 / estimate>0)。
    返回 spec dict 供复用; 不就绪 raise SkeinError。"""
    spec = load_spec(tasks_dir, tid)
    if not spec:
        raise SkeinError(f"{tid} prd.md 缺 frontmatter — TaskSpec 未落盘")
    if not str(spec.get("desc") or "").strip():
        raise SkeinError(f"{tid} 任务描述未填 — `skein task spec {tid} --desc <描述>`")
    b = spec.get("boundary") or {}
    if not (b.get("should") or b.get("should_not")):
        raise SkeinError(f"{tid} 边界未填 — `skein task spec {tid} --should <a;b> --not <c;d>`")
    if not spec.get("acceptance"):
        raise SkeinError(f"{tid} 验收项未填 — `skein task spec {tid} --acceptance <条1;条2>`")
    est = spec.get("estimate")
    if not isinstance(est, (int, float)) or est <= 0:
        raise SkeinError(f"{tid} 预计工时未填 — `skein task estimate {tid} --set <小时>`")
    return spec
