"""sediment 写盘 — 规则作为一个 `## <标题>` 章节**追加**进主题文件。

粒度: 目录 = 类目, 文件 = 主题, 文件内 `## <标题>` = 一条规则。同主题规则必须并入同一文件
(禁一规则一文件, 否则索引膨胀而召回质量不升)。frontmatter 只写 title/category/keywords/
status/inclusion (+ fileMatch 的 globs、可选 anchors), **不写时间字段** —— 新旧判定一律走
文件系统 mtime, 存进 frontmatter 只会与事实漂移。
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import TYPE_CHECKING, Optional, cast

from skeinlib.errors import SkeinError
from skeinlib.spec.text import _frontmatter, _slug, _strip_frontmatter


class WriteMixin:
    # 仅供 mypy 用的属性声明: root/layer_dir/_scan_namespaces/_rules/_rule_files 由兄弟类
    # SpecBase 提供, _reindex_all 由兄弟 mixin IndexMixin 提供 (组装成 Spec 时混入)。
    # TYPE_CHECKING 块运行时永不执行, 零行为改动, 只消除单看本 mixin 时的 attr-defined 噪声。
    if TYPE_CHECKING:
        root: Path
        def layer_dir(self, layer: str) -> Path: ...
        def _scan_namespaces(self) -> list[str]: ...
        def _rules(self, layer: str) -> list[tuple[Path, str, str]]: ...
        def _rule_files(self, layer: str) -> list[Path]: ...
        def _reindex_all(self) -> dict[str, dict[str, int]]: ...

    # ---- namespace/inclusion 取参 (sediment/archive 共用) ----
    def _require_namespace(self, a: argparse.Namespace, *, with_inclusion: bool) -> tuple[str, Optional[str]]:
        """返回 (namespace, inclusion|None)。namespace 是自由字符串 (非白名单, design.md §2)。

        曾有个 `--layer` 废弃通道把旧的 core/recall/external 三值映射到 (namespace, inclusion),
        已整条删除 —— 两套词汇并存期间光是内部互译 shim 就漂移出过多处 bug (最后一次是看板 spec
        树对新 namespace 全盲)。现在只有一套: namespace × inclusion。
        """
        namespace = cast(Optional[str], getattr(a, "namespace", None))
        inclusion = cast(Optional[str], getattr(a, "inclusion", None)) if with_inclusion else None
        if namespace is None:
            raise SkeinError("需要 --namespace (自由字符串, 常见 rules/product/map/external)")
        return namespace, (inclusion or "auto") if with_inclusion else None
    # ---- sediment (写盘: 规则作为一个章节追加进主题文件, 判定门通过后自动调用) ----
    def sediment(self, a: argparse.Namespace) -> None:
        namespace, inclusion_opt = self._require_namespace(a, with_inclusion=True)
        inclusion = cast(str, inclusion_opt)
        title = cast(str, a.title)
        keywords = cast(Optional[str], getattr(a, "keywords", None)) or ""
        status = cast(Optional[str], getattr(a, "status", None)) or "active"
        body_file = cast(Optional[str], getattr(a, "body_file", None))
        cat = cast(Optional[str], getattr(a, "category", None)) or "misc"
        globs = cast(Optional[str], getattr(a, "globs", None))
        anchors = cast(Optional[str], getattr(a, "anchors", None))
        # --topic 缺省 → 归入类目同名主题文件 (调用方应按语义指定主题, 免所有规则挤一个文件)
        topic = _slug(cast(Optional[str], getattr(a, "topic", None)) or cat)
        d = self.layer_dir(namespace) / cat
        d.mkdir(parents=True, exist_ok=True)
        f = d / f"{topic}.md"
        body = (Path(body_file).read_text() if body_file else "").strip()
        self._append_rule(f, namespace, cat, topic, title, body, keywords, status,
                          inclusion, globs, anchors)
        self._reindex_all()
        print(f"已沉淀 → {f.relative_to(self.root).as_posix()}#{title}")
    def _append_rule(self, f: Path, namespace: str, cat: str, topic: str, title: str,
                     body: str, keywords: str, status: str,
                     inclusion: str = "auto", globs: Optional[str] = None,
                     anchors: Optional[str] = None) -> None:
        """把一条规则作为 `## <title>` 章节追加进主题文件 (不存在则建)。

        frontmatter: title/category/keywords/status 五字段 + inclusion (显式加载策略) +
        legacy `layer` 字段 (core/recall 二值, 由 inclusion 反推, 供旧代码路径 `_inclusion()`
        fallback / `degrade()` 兼容读取, s6 迁移完再删) + 可选 globs/anchors (fileMatch 用)。"""
        old_body, kws, st = "", [k.strip() for k in keywords.split(",") if k.strip()], status
        old_globs, old_anchors = globs, anchors
        if f.exists():
            txt = f.read_text()
            meta = _frontmatter(txt)
            old_body = _strip_frontmatter(txt).strip()
            kws = list(dict.fromkeys([k.strip() for k in str(meta.get("keywords", "")).split(",")
                                      if k.strip()] + kws))
            # ponytail: status 是文件级 (主题级) 字段 — 追加时只在显式非 active 时覆盖;
            # 单条规则要独立 status → 拆到自己的主题文件。
            st = status if status != "active" else str(meta.get("status", "active"))
            old_globs = globs if globs is not None else (str(meta.get("globs", "")) or None)
            old_anchors = anchors if anchors is not None else (str(meta.get("anchors", "")) or None)
        extra = ""
        if old_globs:
            extra += f"globs: {old_globs}\n"
        if old_anchors:
            extra += f"anchors: {old_anchors}\n"
        f.write_text(
            "---\n"
            f"title: {topic}\n"
            f"category: {cat}\n"
            f"keywords: [{','.join(kws)}]\n"
            f"status: {st}\n"
            f"inclusion: {inclusion}\n"
            + extra +
            "---\n\n"
            + (old_body + "\n\n" if old_body else "")
            + f"## {title}\n\n{body}\n")
    # ---- list ----
    def list_(self, a: argparse.Namespace) -> None:
        ns_opt = cast(Optional[str], getattr(a, "namespace", None))
        # 目录扫描而非常量白名单 — 与 reindex/maintain 一致, 否则手建 namespace 不进 list (design.md §2)
        for ns in ([ns_opt] if ns_opt else self._scan_namespaces()):
            d = self.layer_dir(ns)
            rules = [f"{f.relative_to(d).as_posix()}#{t}" for f, t, _ in self._rules(ns)]
            print(f"[{ns}] {len(rules)} 条规则 / {len(self._rule_files(ns))} 个主题: "
                  f"{', '.join(rules) or '-'}")
