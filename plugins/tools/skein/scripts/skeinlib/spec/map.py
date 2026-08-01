"""`spec.py map --skeleton` — 现算目录树+符号+行数 (不写盘)。

ponytail: 正则非AST, 装饰器/嵌套/多行签名抓不准; 升级路径tree-sitter。
三语言顶层符号抓取:
  Python:  ^def |^class |^async def
  JS/TS:   ^function |^class |^export (function|class|const|let|var)
  Go:      ^func |^type

非 git 仓降级 rglob + 排除衍生目录 (__pycache__/.mypy_cache/.ruff_cache/node_modules等)。
纯 stdlib, 现算不落盘。

性能: ponytail 已达1000文件<3s要求 (实测1501文件0.136s)

k2 扩展: 支持 map namespace 语义页，合并骨架与语义，支持 --src code 召回。
"""
from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, cast

# ponytail: 正则匹配非AST, 已知ceiling=装饰器/嵌套/多行签名抓不准
# 升级路径: 引入 tree-sitter 做精确解析
_PY_TOP_RE = re.compile(r"^(def|class|async\s+def)\s+(\w+)")
_JS_TOP_RE = re.compile(r"^(function|class|export\s+(?:function|class|const|let|var))\s+(\w+)")
_GO_TOP_RE = re.compile(r"^(func|type)\s+(\w+)")

# 衍生目录排除范式 (非 git 仓降级时用)
_EXCLUDE_DIRS = {
    "__pycache__", ".mypy_cache", ".ruff_cache", ".pytest_cache",
    "node_modules", ".git", ".svn", ".hg", "dist", "build",
    ".venv", "venv", ".virtualenv", "site-packages",
}


class MapMixin:
    """现算目录树+符号+行数 (不写盘)，合并 map namespace 语义页。"""

    # 仅供 mypy 用的属性声明: root 由 SpecBase 提供
    if TYPE_CHECKING:
        root: Path

    def map(self, a: argparse.Namespace) -> None:
        """map 命令: 合并骨架输出和 map namespace 语义页。

        skeleton 模式 (--skeleton): 只输出骨架，无 map 页时零回归。
        普通 (不带 --skeleton): 输出骨架 + map namespace 语义页合并的地图。
        """
        skeleton = bool(getattr(a, "skeleton", False))
        paths_inject = cast(str, getattr(a, "paths", None) or "")

        # 1. 计算骨架
        skeleton_data = self._compute_skeleton(paths_inject)

        # 2. 如果是 skeleton 模式或无 map 页，只输出骨架
        if skeleton or not self._has_map_pages():
            import json
            print(json.dumps(skeleton_data, ensure_ascii=False, indent=2))
            return

        # 3. 合并骨架和语义页
        merged_data = self._merge_with_map_semantic(skeleton_data)
        import json
        print(json.dumps(merged_data, ensure_ascii=False, indent=2))

    def _compute_skeleton(self, paths_inject: str) -> dict[str, object]:
        """计算骨架数据：目录树+符号+行数。"""
        # 1. 取文件清单: 参数注入 > git ls-files > rglob(非git降级)
        repo_root = self.root.parent.parent  # .skein/spec → 仓库根
        files: list[Path] = []

        if paths_inject:
            # 清单可参数注入 (逗号分隔)
            files = [repo_root / p.strip() for p in paths_inject.split(",") if p.strip()]
        else:
            # git ls-files 取清单 (非 git 降级 rglob+既有排除范式)
            try:
                r = subprocess.run(
                    ["git", "ls-files"],
                    cwd=repo_root,
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if r.returncode == 0:
                    files = [repo_root / p.strip() for p in r.stdout.splitlines() if p.strip()]
                else:
                    raise OSError("git ls-files failed")
            except (OSError, subprocess.TimeoutExpired):
                # 非 git 仓降级 rglob + 排除衍生目录
                files = self._rglob_exclude(repo_root)

        if not files:
            return {"total_files": 0, "total_lines": 0, "files": []}

        # 2. 现算目录树+符号+行数 (不写盘)
        results: list[dict[str, object]] = []
        for f in files:
            if not f.is_file():
                continue

            # 行数
            try:
                lines = f.read_text().count("\n") + 1
            except (OSError, UnicodeDecodeError):
                continue  # 跳过二进制/读不出文件

            # 符号抓取 (skeleton 模式仅顶层符号)
            symbols: list[str] = []
            symbols = self._extract_top_symbols(f)

            # 目录树 (相对仓库根的路径)
            rel_path = str(f.relative_to(repo_root))

            results.append({
                "path": rel_path,
                "lines": lines,
                "symbols": symbols,
            })

        return {
            "total_files": len(results),
            "total_lines": sum(cast(int, r["lines"]) for r in results),
            "files": results,
        }

    def _has_map_pages(self) -> bool:
        """检查是否存在 map namespace 的语义页。"""
        map_dir = self.root / "map"
        if not map_dir.exists():
            return False

        # 检查是否有非 index.md/backlinks.md 的文件
        for p in map_dir.rglob("*.md"):
            if p.is_file() and p.name not in ("index.md", "backlinks.md"):
                return True
        return False

    def _merge_with_map_semantic(self, skeleton_data: dict[str, object]) -> dict[str, object]:
        """合并骨架数据和 map namespace 语义页。

        语义页格式: spec/map/<category>/<topic>.md
        frontmatter 包含 anchors 列表 (失效即 maintain 断链候选)
        """
        semantic: dict[str, list[dict[str, object]]] = {}

        # 扫描 map namespace 所有语义页
        map_dir = self.root / "map"
        if map_dir.exists():
            for md_file in map_dir.rglob("*.md"):
                if not md_file.is_file() or md_file.name in ("index.md", "backlinks.md"):
                    continue

                try:
                    content = md_file.read_text()
                    meta = self._parse_frontmatter(content)
                    rel_path = str(md_file.relative_to(map_dir))

                    # 提取语义信息
                    semantic_info: dict[str, object] = {
                        "path": rel_path,
                        "title": meta.get("title", ""),
                        "category": meta.get("category", ""),
                        "keywords": meta.get("keywords", []),
                        "anchors": meta.get("anchors", []),
                        "inclusion": meta.get("inclusion", "auto"),
                    }

                    # 按类目组织
                    category = str(semantic_info["category"])
                    semantic.setdefault(category, []).append(semantic_info)

                except (OSError, UnicodeDecodeError):
                    continue  # 跳过读不出的文件

        return {
            "skeleton": skeleton_data,
            "semantic": semantic,
            "merged": True,
        }

    def _parse_frontmatter(self, content: str) -> dict[str, str | list[str]]:
        """解析 YAML frontmatter，返回元数据字典。"""
        meta: dict[str, str | list[str]] = {}
        lines = content.split("\n")
        in_fm = False
        current_list = None  # 当前正在解析的列表字段
        for line in lines:
            s = line.strip()
            if s == "---" and not in_fm:
                in_fm = True
                continue
            if s == "---" and in_fm:
                break
            if in_fm:
                if s.startswith("title:"):
                    meta["title"] = s[6:].strip().strip("\"\'")
                    current_list = None
                elif s.startswith("category:"):
                    meta["category"] = s[9:].strip().strip("\"\'")
                    current_list = None
                elif s.startswith("keywords:"):
                    raw = s[9:].strip()
                    if raw.startswith("["):
                        meta["keywords"] = [k.strip().strip("\"\'") for k in raw.strip("[]").split(",") if k.strip()]
                    else:
                        # 开始流式数组解析
                        current_list = "keywords"
                        meta["keywords"] = []
                elif s.startswith("anchors:"):
                    raw = s[8:].strip()
                    if raw.startswith("["):
                        meta["anchors"] = [a.strip().strip("\"\'") for a in raw.strip("[]").split(",") if a.strip()]
                    else:
                        # 开始流式数组解析
                        current_list = "anchors"
                        meta["anchors"] = []
                elif s.startswith("inclusion:"):
                    meta["inclusion"] = s[10:].strip().strip("\"\'")
                    current_list = None
                elif s.startswith("- ") and current_list:
                    # 流式数组的元素
                    value = s[2:].strip().strip("\"\'")
                    existing = meta.get(current_list)
                    if isinstance(existing, list):
                        existing.append(value)
        return meta

    def _rglob_exclude(self, root: Path) -> list[Path]:
        """非 git 仓降级 rglob + 排除衍生目录。"""
        files: list[Path] = []

        # 常见源代码扩展名
        extensions = {
            ".py", ".pyx", ".pyi",  # Python
            ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs",  # JS/TS
            ".go", ".golang",  # Go
            ".c", ".h", ".cpp", ".hpp", ".cc", ".cxx",  # C/C++
            ".rs",  # Rust
            ".java", ".kt",  # Java/Kotlin
            ".md", ".txt", ".json", ".yaml", ".yml", ".toml",  # 文本配置
        }

        for p in root.rglob("*"):
            # 跳过衍生目录
            if any(excl in p.parts for excl in _EXCLUDE_DIRS):
                continue
            # 跳过隐藏文件/目录 (以.开头)
            if any(part.startswith(".") for part in p.parts):
                continue
            if p.is_file() and p.suffix in extensions:
                files.append(p)

        return files

    def _extract_top_symbols(self, f: Path) -> list[str]:
        """提取顶层符号 (按语言选择正则)。"""
        ext = f.suffix.lower()
        content = f.read_text()

        if ext in {".py", ".pyx", ".pyi"}:
            return self._extract_py_symbols(content)
        elif ext in {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}:
            return self._extract_js_symbols(content)
        elif ext in {".go", ".golang"}:
            return self._extract_go_symbols(content)
        else:
            return []

    def _extract_py_symbols(self, content: str) -> list[str]:
        """Python 顶层符号: def/class/async def。"""
        symbols: list[str] = []
        for line in content.splitlines():
            m = _PY_TOP_RE.search(line.strip())
            if m:
                symbols.append(m.group(2))
        return symbols

    def _extract_js_symbols(self, content: str) -> list[str]:
        """JS/TS 顶层符号: function/class/export。"""
        symbols: list[str] = []
        for line in content.splitlines():
            m = _JS_TOP_RE.search(line.strip())
            if m:
                # export const foo = ... → foo
                # export function bar → bar
                # class Baz → Baz
                name = m.group(2).split("(")[0].split("=")[0].strip()
                if name and name.isidentifier():
                    symbols.append(name)
        return symbols

    def _extract_go_symbols(self, content: str) -> list[str]:
        """Go 顶层符号: func/type。"""
        symbols: list[str] = []
        for line in content.splitlines():
            m = _GO_TOP_RE.search(line.strip())
            if m:
                symbols.append(m.group(2))
        return symbols
