"""索引重建 + sqlite5 FTS + 召回。

每个 namespace 一份 `index.md` (章节粒度, 一行一条规则, 带 inclusion / anchors 列) + 顶层
聚合索引 + `backlinks.md` 反链表。FTS 表在 `.recall.db`, **先 DROP 再 CREATE** (幂等迁移,
不留旧 schema)。

`recall` 优先走 FTS5 BM25; 库不存在 / MATCH 语法失败 (查询含双引号) → 降级 grep index.md。
降级是刻意的: 召回不到规则只是少点上下文, 炸掉却会打断 planning。
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import TYPE_CHECKING, Optional, cast

from skeinlib.spec.text import _cell, _dist, _frontmatter, _link_target, _summary


class IndexMixin:
    # 仅供 mypy 用的属性声明: root/layer_dir/_scan_namespaces/_rules/_inclusion 由兄弟类
    # SpecBase 提供 (组装成 Spec 时混入), TYPE_CHECKING 块运行时永不执行, 零行为改动,
    # 只消除单看本 mixin 时的 attr-defined 噪声。
    if TYPE_CHECKING:
        root: Path
        def layer_dir(self, layer: str) -> Path: ...
        def _scan_namespaces(self) -> list[str]: ...
        def _rules(self, layer: str) -> list[tuple[Path, str, str]]: ...
        def _inclusion(self, f: Path) -> str: ...

    # ---- recall (按需粗筛: FTS5 BM25 优先, grep fallback) ----
    def recall(self, a: argparse.Namespace) -> None:
        query = cast(str, a.query)
        src = cast(Optional[str], getattr(a, "src", None)) or "all"
        fts_hits = self._recall_fts(query, src)
        if fts_hits is not None:
            if fts_hits:
                print("recall 命中 (FTS5 BM25, model 读全文再定用否):")
                print("\n".join(fts_hits))
            else:
                print("recall 无命中")
            return
        # fallback: 无 .recall.db 或 MATCH 语法失败 → 子串 grep index.md
        hits = self._recall_grep(query, src)
        if hits:
            print("recall 命中 (grep fallback, model 读全文再定用否):")
            print("\n".join(hits))
        else:
            print("recall 无命中")
    def _recall_fts(self, query: str, src: str = "all") -> Optional[list[str]]:
        """FTS5 BM25 召回; 返回命中行 (None=不可用降级 grep, []=无命中)。

        每个 token 双引号包起 + OR: 兼容中文 unicode61 分词弱 (任一词命中即召回)。
        含双引号的 token 会破坏 MATCH 语法 → 提前降级 grep (不调 MATCH)。
        src != "all" → 按 namespace 列过滤 (--src rules|product|map)。
        """
        db = self.root / ".recall.db"
        if not db.exists():
            return None
        tokens = [t for t in re.split(r"\s+", query.strip()) if t]
        if not tokens or any('"' in t for t in tokens):
            return None
        ftsq = " OR ".join(f'"{t}"' for t in tokens)
        import sqlite3  # 局部: 仅 recall + reindex 链用, 不拖 session-start/inject-core
        try:
            con = sqlite3.connect(db)
            try:
                if src != "all":
                    rows = con.execute(
                        "SELECT rel, category, title, keywords, body, namespace FROM rules "
                        "WHERE namespace = ? AND rules MATCH ? ORDER BY bm25(rules) LIMIT 10",
                        (src, ftsq)).fetchall()
                else:
                    rows = con.execute(
                        "SELECT rel, category, title, keywords, body, namespace FROM rules "
                        "WHERE rules MATCH ? ORDER BY bm25(rules) LIMIT 10", (ftsq,)).fetchall()
            finally:
                con.close()
        except sqlite3.OperationalError:
            return None  # MATCH 语法敏感字符 → 降级 grep
        # bracket 用 namespace (非 legacy layer compat 列) — 与 _recall_grep 的 [{ns}] 前缀一致,
        # 且 layer compat 列对 manual/fileMatch inclusion 为空串, 会丢标识 (曾致 external namespace 显示 "[]")
        return [f"| [{ns}] {rel} | {cat} | {title} | {kw} | - | {_summary(body)} |"
                for rel, cat, title, kw, body, ns in rows]
    def _recall_grep(self, query: str, src: str = "all") -> list[str]:
        """子串 grep index.md (FTS5 不可用时的 fallback); 命中行带 [namespace] 前缀。
        src != "all" → 仅扫指定 namespace, 否则扫全 namespace (含手建的)。"""
        terms = [t for t in re.split(r"\s+", query.lower()) if t]
        hits: list[str] = []
        namespaces = [src] if src != "all" else self._scan_namespaces()
        for ns in namespaces:
            idx = self.layer_dir(ns) / "index.md"
            if not idx.exists():
                continue
            for ln in idx.read_text().splitlines():
                if ln.startswith("| ") and not ln.startswith("| file") \
                        and any(t in ln.lower() for t in terms):
                    hits.append(f"[{ns}] {ln}")
        return hits
    # ---- reindex ----
    def reindex(self, _: argparse.Namespace) -> None:
        self._reindex_all()
        print(f"已重建索引: {self.root}")
    def _reindex_all(self) -> dict[str, dict[str, int]]:
        counts: dict[str, dict[str, int]] = {}
        # 目录扫描 (无常量白名单): 手建 spec/<ns>/<cat>/x.md 后 reindex 就能识别并产 spec/<ns>/index.md
        for ns in self._scan_namespaces():
            counts[ns] = self._reindex_layer(ns)
        self._reindex_top(counts)
        self._rebuild_fts()
        self._rebuild_spec_meta()
        self._rebuild_backlinks_md(self._rebuild_backlinks())
        return counts
    def _rebuild_backlinks(self) -> dict[str, list[str]]:
        """扫全库章节 body 的 [[slug]] → {目标 slug: [来源规则 id,...]}。A-MEM-lite 反链表。

        目标 slug 归一为 `topic` (整篇主题) 或 `topic#规则标题` (单条规则); 来源恒为规则 id
        (<layer>/<cat>/<topic>.md#<标题>) — 关联落到章节粒度, 检索时可直接跳到那一条。"""
        backlinks: dict[str, list[str]] = {}
        for layer in self._scan_namespaces():
            for f, title, body in self._rules(layer):
                src = f"{layer}/{f.parent.name}/{f.stem}.md#{title}"
                for m in re.finditer(r"\[\[([^\]]+)\]\]", body):
                    tgt = _link_target(m.group(1))
                    if tgt:
                        backlinks.setdefault(tgt, []).append(src)
        return backlinks
    def _rebuild_backlinks_md(self, backlinks: dict[str, list[str]]) -> None:
        """每层写 <layer>/backlinks.md: 本层每条规则一章节, 列入链 (谁引用我) + 出链 (我引用谁)。
        两向都写 — 检索时正查反查同一张表。无章节 = 该规则孤立 (maintain 判据 6 兜底)。"""
        for layer in self._scan_namespaces():
            lines = [f"# SKEIN {layer} 关联表 (A-MEM-lite 正反链)", "",
                     "章节粒度: 规则 id = `<类目>/<主题>.md#<规则标题>`; "
                     "`←` 入链 (谁引用本条) / `→` 出链 (本条引用谁)。无条目 = 孤立候选。", ""]
            for f, title, body in self._rules(layer):
                rid = f"{f.parent.name}/{f.stem}.md#{title}"
                ins = sorted(set(backlinks.get(f"{f.stem}#{title}", [])
                                 + backlinks.get(f.stem, [])))
                outs = sorted({t for m in re.finditer(r"\[\[([^\]]+)\]\]", body)
                               if (t := _link_target(m.group(1)))})
                if not ins and not outs:
                    continue
                lines.append(f"## {rid}")
                lines.extend(f"- ← {r}" for r in ins)
                lines.extend(f"- → [[{t}]]" for t in outs)
                lines.append("")
            (self.layer_dir(layer) / "backlinks.md").write_text("\n".join(lines))
    def _rebuild_fts(self) -> None:
        """重建 FTS5 BM25 索引 (全 namespace, 含 always 页 —— 注入与检索是两件事, 不该耦合;
        recall 命令要能查到全库)。sqlite3 stdlib, 无新依赖。

        表列 = rel/category/title/keywords/body/namespace/inclusion/anchors。曾有个由 inclusion
        反推的 layer 列, 只写不读 (`_recall_fts` 只 SELECT namespace) — 已删。recall 输出的
        `[namespace]` 前缀供 model 定位 .skein/spec/<namespace>/...。
        先 DROP 再 CREATE (幂等迁移, 非 CREATE IF NOT EXISTS 免留旧 schema)。"""
        db = self.root / ".recall.db"
        import sqlite3  # 局部: 仅 reindex/sediment 重建索引链用
        con = sqlite3.connect(db)
        try:
            con.execute("DROP TABLE IF EXISTS rules")
            con.execute(
                "CREATE VIRTUAL TABLE rules USING fts5("
                "rel, category, title, keywords, body, namespace, inclusion, anchors)")
            for ns in self._scan_namespaces():  # 全 namespace 入索引 (含 always 页)
                for f, title, body in self._rules(ns):  # 一行 = 一条规则 (章节), 非一个文件
                    meta = _frontmatter(f.read_text())
                    inc = self._inclusion(f)
                    con.execute(
                        "INSERT INTO rules(rel, category, title, keywords, body, namespace, inclusion, anchors) "
                        "VALUES (?,?,?,?,?,?,?,?)",
                        (f"{f.parent.name}/{f.stem}.md#{title}", f.parent.name, title,
                         str(meta.get("keywords", "")), body, ns, inc,
                         str(meta.get("anchors", ""))))
            con.commit()
        finally:
            con.close()

    def _rebuild_spec_meta(self) -> None:
        """重建 spec_meta 表 (文件粒度元数据: path/title/namespace/category/keywords/inclusion/mtime)。

        每个文件一行（非章节），path 为 PK。复用 boardsource._spec_build_cache 解析逻辑：
        - 遍历所有 spec 文件（跳 index.md/backlinks.md）
        - 解析 frontmatter (title/category/keywords)
        - 解析正文首个 H1 标题
        - title 优先级: H1 > frontmatter title > 文件名
        - keywords 存 JSON 字符串
        """
        db = self.root / ".recall.db"
        import sqlite3
        import json
        con = sqlite3.connect(db)
        try:
            # DROP + CREATE (幂等迁移)
            con.execute("DROP TABLE IF EXISTS spec_meta")
            con.execute(
                "CREATE TABLE spec_meta ("
                "path TEXT PRIMARY KEY, "
                "title TEXT, "
                "namespace TEXT, "
                "category TEXT, "
                "keywords TEXT, "
                "inclusion TEXT, "
                "mtime REAL"
                ")")

            # 扫描所有 spec 文件
            for ns in self._scan_namespaces():
                ns_dir = self.layer_dir(ns)
                if not ns_dir.exists():
                    continue
                for p in sorted(ns_dir.rglob("*.md")):
                    if not p.is_file() or p.name in ("index.md", "backlinks.md"):
                        continue

                    try:
                        txt = p.read_text(encoding="utf-8", errors="replace")
                    except Exception:
                        continue

                    rel = str(p.relative_to(self.root))
                    mtime = p.stat().st_mtime

                    # 解析 frontmatter
                    fm_title, category, keywords = "", "", []
                    in_fm = False
                    lines = txt.split("\n")
                    fm_end = 0
                    for li, line in enumerate(lines):
                        s = line.strip()
                        if s == "---" and not in_fm:
                            in_fm = True
                            continue
                        if s == "---" and in_fm:
                            fm_end = li + 1
                            break
                        if in_fm:
                            if s.startswith("title:"):
                                fm_title = s[6:].strip().strip("\"\'")
                            elif s.startswith("category:"):
                                category = s[9:].strip().strip("\"\'")
                            elif s.startswith("keywords:"):
                                raw = s[9:].strip()
                                if raw.startswith("["):
                                    keywords = [k.strip().strip("\"\'") for k in raw.strip("[]").split(",") if k.strip()]

                    # 解析 H1 标题
                    h1_title = ""
                    for line in lines[fm_end:]:
                        s = line.strip()
                        if s.startswith("# ") and not s.startswith("## "):
                            h1_title = s[2:].strip()
                            break

                    # title 优先级: H1 > frontmatter title > 文件名
                    title = h1_title or fm_title or p.stem

                    # inclusion = 与 path 相同 (兼容前端字段名)
                    inclusion = rel

                    # keywords 转 JSON 字符串
                    keywords_json = json.dumps(keywords, ensure_ascii=False)

                    con.execute(
                        "INSERT INTO spec_meta(path, title, namespace, category, keywords, inclusion, mtime) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (rel, title, ns, category, keywords_json, inclusion, mtime))

            con.commit()
        finally:
            con.close()
    def _reindex_layer(self, layer: str) -> dict[str, int]:
        """重建 <namespace>/index.md (章节粒度: 一行 = 一条规则), 返回 {category: 规则条数}。
        行加 inclusion (加载策略) 与 anchors (fileMatch 触发路径, 未设留空) 两列。"""
        d = self.layer_dir(layer)
        d.mkdir(parents=True, exist_ok=True)
        by_cat: dict[str, int] = {}
        rows: list[tuple[str, str, str, str, str, str, str, str]] = []
        for f, title, body in self._rules(layer):
            meta = _frontmatter(f.read_text())
            cat = f.parent.name  # 类目 = 所在目录 (物理事实), 免与 frontmatter 漂移
            rel = f"{f.relative_to(d).as_posix()}#{title}"  # 规则 id, 可直接定位到章节
            by_cat[cat] = by_cat.get(cat, 0) + 1
            links = ",".join(sorted({t for m in re.finditer(r"\[\[([^\]]+)\]\]", body)
                                     if (t := _link_target(m.group(1)))}))
            # .get 容错旧 spec 缺 status (缺字段视为 active, 不报错不迁移)
            rows.append((cat, rel, _cell(title), _cell(str(meta.get("keywords", ""))),
                         _cell(self._inclusion(f)), _cell(str(meta.get("anchors", ""))),
                         _cell(str(meta.get("status", "active"))) + (f" / →{_cell(links)}" if links else ""),
                         _summary(body)))
        rows.sort()
        table = "\n".join(f"| {rel} | {cat} | {title} | {kw} | {inc} | {anc} | {status} | {summ} |"
                          for cat, rel, title, kw, inc, anc, status, summ in rows)
        (d / "index.md").write_text(
            f"# SKEIN {layer} 规则索引 (章节粒度: 一行一条规则)\n\n"
            f"类目: {_dist(by_cat)} · 关联见 [backlinks.md](backlinks.md)\n\n"
            "| rule (topic.md#标题) | category | title | keywords | inclusion | anchors | status/出链 | summary |\n"
            "|---|---|---|---|---|---|---|---|\n"
            + (table + "\n" if table else ""))
        return by_cat
    def _reindex_top(self, counts: dict[str, dict[str, int]]) -> None:
        lines = ["# SKEIN 规则库总索引\n",
                 "三层: **core** 常驻注入 (SessionStart) · **recall** 按需召回 (planning `recall <query>`) · "
                 "**external** 外部参考 (纯手动 CLI 检索, 不入 hook)。\n",
                 "| layer | 条数 | 类目分布 | 索引 |",
                 "|---|---|---|---|"]
        for layer in counts:  # 实扫结果 (_scan_namespaces) — 未知 namespace 也上总索引
            by_cat = counts.get(layer, {})
            total = sum(by_cat.values())
            lines.append(f"| {layer} | {total} | {_dist(by_cat)} | [{layer}/index.md]({layer}/index.md) |")
        (self.root / "index.md").write_text("\n".join(lines) + "\n")
