"""`SpecBase` — 库根路径 / namespace 扫描 / inclusion 判定 / 规则文件遍历。

`_scan_namespaces()` 用**目录扫描**而非常量白名单: 手建 `spec/<ns>/<cat>/x.md` 后 reindex
就能识别 (design.md §2「新增 namespace 零配置」)。`NAMESPACES` 常量只在 `init` 建目录时用作
默认清单。曾经有处硬编码了 `("core","recall")`, 于是看板对新 namespace 全盲。

`_inclusion()` 读 frontmatter 显式字段; 缺失时按旧 `layer` 字段兼容一轮 (core→always,
其余→auto) —— 这是给未迁移的存量文件的**读侧**上坡道, 不是两套词汇并存。写侧只写 inclusion。
"""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

from skeinlib.spec.model import INCLUSIONS, NAMESPACES, spec_root
from skeinlib.spec.text import _frontmatter, _sections


class SpecBase:
    # 仅供 mypy 用的属性声明: `_reindex_all` 由兄弟 mixin IndexMixin 提供 (组装成 Spec 时
    # 混入), TYPE_CHECKING 块运行时永不执行, 零行为改动, 只消除单看本类时的 attr-defined 噪声。
    if TYPE_CHECKING:
        def _reindex_all(self) -> dict[str, dict[str, int]]: ...

    def __init__(self) -> None:
        self.root = spec_root()
    def layer_dir(self, layer: str) -> Path:
        return self.root / layer
    def _scan_namespaces(self) -> list[str]:
        """实际可用 namespace = 目录扫描 (物理事实), 非白名单。用户手建 spec/<ns>/... 即被识别,
        新增 namespace 零配置。NAMESPACES 常量仅作 init 建目录的默认清单, 库已存在时以此扫描结果为准
        (根不存在/空库 → 回退 NAMESPACES, 保 init 前调用不炸)。排除 `.` 开头目录 (.archive 等衍生物)。"""
        if not self.root.exists():
            return list(NAMESPACES)
        found = sorted(p.name for p in self.root.iterdir() if p.is_dir() and not p.name.startswith("."))
        return found or list(NAMESPACES)
    def _rule_files(self, layer: str) -> list[Path]:
        d = self.layer_dir(layer)
        if not d.exists():
            return []
        # index.md/backlinks.md 是衍生索引非规则, 扫规则时排除 (免反链表自我递归引用)
        return sorted(p for p in d.rglob("*.md")
                      if p.name not in ("index.md", "backlinks.md"))
    def _rules(self, layer: str) -> list[tuple[Path, str, str]]:
        """层内全部规则 (章节粒度): [(主题文件, 规则标题, 规则正文)]。"""
        return [(f, t, b) for f in self._rule_files(layer) for t, b in _sections(f.read_text())]
    def _mtimes(self, use_git: bool = True) -> dict[Path, int]:
        """各规则文件最近修改时间 (epoch)。git 提交时间优先 (一次 git log 全量解析),
        未跟踪/无 git/use_git=False → 文件系统 mtime。取代已废弃的 frontmatter created/updated。"""
        out: dict[Path, int] = {}
        if use_git:
            r = subprocess.run(["git", "log", "--format=@%ct", "--name-only", "--", "."],
                               capture_output=True, text=True, cwd=self.root)
            if r.returncode == 0:
                repo = self.root.parent.parent  # .skein/spec → 仓库根 (git log 路径相对仓库根)
                ts = 0
                for ln in r.stdout.splitlines():
                    if ln.startswith("@"):
                        ts = int(ln[1:])
                    elif ln.strip():
                        out.setdefault(repo / ln.strip(), ts)  # log 倒序 → 首次见即最新
        for layer in self._scan_namespaces():
            for f in self._rule_files(layer):
                out.setdefault(f, int(f.stat().st_mtime))
        return out
    def _age_days(self, f: Path, mtimes: dict[Path, int], now_ts: int) -> int:
        return max(0, (now_ts - mtimes.get(f, now_ts)) // 86400)
    # ---- init ----
    def init(self, _: argparse.Namespace) -> None:
        for ns in NAMESPACES:
            self.layer_dir(ns).mkdir(parents=True, exist_ok=True)
        self._reindex_all()
        print(f"已初始化 spec 库: {self.root}")
    # ---- inclusion 判定 (加载路径与目录/namespace 无关, 只看 frontmatter inclusion) ----
    def _inclusion(self, f: Path) -> str:
        """有效 inclusion: frontmatter 显式声明优先; 缺失时按旧 `layer` 字段兼容一轮
        (core→always / 其余→auto), 免旧库未迁移 inclusion 字段就丢了常驻注入。"""
        meta = _frontmatter(f.read_text())
        inc = str(meta.get("inclusion", "")).strip()
        if inc in INCLUSIONS:
            return inc
        return "always" if meta.get("layer") == "core" else "auto"
    def _always_files(self) -> list[Path]:
        """全 namespace 扫描 (非仅 core 目录), 筛 inclusion==always。"""
        return sorted(f for ns in self._scan_namespaces() for f in self._rule_files(ns)
                      if self._inclusion(f) == "always")
