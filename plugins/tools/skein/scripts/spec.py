#!/usr/bin/env python3
"""SKEIN 三层规则记忆 (基于 .skein/spec, 纯 stdlib)。

三层 × 类目:
  core     — .skein/spec/core/<类目>/*.md        每 session 常驻注入 (SessionStart hook → session-start)
  recall   — .skein/spec/recall/<类目>/*.md      按需语义召回 (planning 时 recall <query> 粗筛, model 读全文)
  external — .skein/spec/external/<类目>/*.md    外部参考 (纯手动 CLI 检索, 不入 hook; recall 跨层命中)

粒度约定 (硬规):
  文件夹 = 类目 (category), 层内子目录, 自由取名 (git/test/arch/build/style/domain/ops...)。
  文件   = 主题 (topic), 文件名即主题; 一个文件承载围绕该主题的**多条规则**。
  章节   = 单条规则, body 内 `## <规则标题>` 一节一条。禁一条规则一个文件 (碎片化)。
  规则 id = <layer>/<category>/<topic>.md#<规则标题>; 关联用 `[[topic#规则标题]]` wikilink。
索引/FTS/反链全部按**章节粒度**建。frontmatter 只留 title/layer/category/keywords/status
(时间类字段一律不写 — 注入上下文无意义且费 token; 新旧判定走 git/文件系统 mtime)。

命令:
  spec.py init
  spec.py inject-core                        输出全部 core 规则正文 (调试用)
  spec.py session-start                       SessionStart hook: 直接产 hook JSON 注入 core
  spec.py recall "<query>"                   FTS5 BM25 跨层排序 recall+external (无索引/MATCH 失败 → grep fallback)
  spec.py sediment --layer core|recall|external --category git --topic merge --title T \
            --keywords "a,b" --body-file /path   规则追加进主题文件 + reindex
  spec.py restructure --map plan.json [--dry-run]  按 {目标主题文件: [源文件,...]} 合并碎片文件
  spec.py reindex                            重扫三层重建全部 index
  spec.py list [--layer core|recall|external]
  spec.py maintain [--layer core|recall|external] [--apply]  全量体检 (超预算/stale/断链/keywords重复/废弃/孤立)
                                                  无 --apply 只报告; --apply 自动修复 (断链只报告)
  spec.py degrade <file|--auto>                   core→recall 单文件降级 (layer 改 + git mv + reindex + 审计)
                                                  external 是终点层不参与; --auto 循环降到 core < core_budget()
                                                  (config.yaml spec_core_budget, 默认 1000) 即停
"""
from __future__ import annotations

import argparse
import time
import json
import re
import subprocess  # spec_root() git rev-parse + _git_mv 用 (热路径必需, 保留顶载)
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, cast
# sqlite3 改局部 import (仅 _recall_fts / _rebuild_fts 用), 不拖 session-start/inject-core 等热路径 (perf-research §6.2)

INDEX_BUDGET_TOKENS = 400  # SessionStart 注入的极简索引 token 硬预算 (每条 1 行, 只 title+类目)
SUBAGENT_BUDGET_TOKENS = 2000  # SubagentStart 注入 core 全文 token 硬预算 (≈core_budget() 字符)
LAYERS = ("core", "recall", "external")
STALE_DAYS = 180  # maintain stale 判据: created 年龄超此天数且无近期 updated → 候选
KEYWORDS_DUP_THRESHOLD = 3  # maintain keywords 高重复判据: 同 keywords 组 ≥ 此数 → 合并候选
AUDIT_RETENTION_DAYS = 7  # .audit-log 保留窗口; 每次写前清掉 7 天前旧行 (按行首 ts 判)

sys.path.insert(0, str(Path(__file__).parent))  # 同目录 hooklib 可导入 (hook 环境非 Bash PATH)
from hooklib import budget_guard, Debug, debug_enabled  # noqa: E402

# agent 名 → core 类目白名单 (命中类目注全文, 其余仅索引); 空列表/缺项 → fallback 纯索引。
# ponytail: 静态表足够, 无需 per-agent 配置文件; 新增 agent 就地加一行。
AGENT_CATEGORIES: dict[str, list[str]] = {
    "skein-executor": ["script", "git"],
    "skein-checker": ["script"],
    "skein-researcher": ["script", "skill"],
    "skein-finisher": ["script", "git"],
    # setup/dedup/specer 未列 → 默认 fallback 纯索引
}

# --debug 叙事器 (默认关): main() 按 --debug/SKEIN_DEBUG 重建; 全走 stderr, stdout 保持机器纯净。
DBG = Debug(False)


def now() -> int:
    return int(time.time())  # Unix epoch 秒 — 与 skein.py 一致, 所有落盘时间字段统一时间戳


def _read_hook_stdin() -> Optional[str]:
    """读 hook stdin JSON 取 agent_type; stdin 空/非 JSON/缺字段 → None (容错 fallback)。"""
    raw = sys.stdin.read().strip() if not sys.stdin.isatty() else ""
    if not raw:
        return None
    try:
        return cast(Optional[str], json.loads(raw).get("agent_type"))
    except (json.JSONDecodeError, AttributeError):
        return None


def _dist(by_cat: dict[str, int]) -> str:
    """类目分布串 '类目(条数), ...', 空则 '-'。"""
    return ", ".join(f"{c}({n})" for c, n in sorted(by_cat.items())) or "-"


def spec_root() -> Path:
    try:
        r = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                           capture_output=True, text=True)
        base = Path(r.stdout.strip()) if r.returncode == 0 else Path.cwd()
    except FileNotFoundError:  # 无 git 二进制 → fallback cwd (设计意图: 非 git 也可用)
        base = Path.cwd()
    return base / ".skein" / "spec"


def core_budget() -> int:
    """core 全文软预算 (字符): 读 .skein/config.yaml spec_core_budget (复用 skein._yaml_load);
    缺失/非正整数 → 默认 1000。懒求值, 每次调读盘, 支持热改。"""
    try:
        from skein import _yaml_load  # 局部 import 免循环依赖
        cfg_path = spec_root().parent / "config.yaml"
        if cfg_path.exists():
            v = _yaml_load(cfg_path.read_text()).get("spec_core_budget")
            if isinstance(v, int) and v > 0:
                return v
    except Exception:
        pass
    return 1000


def _cell(s: str) -> str:
    """索引表单元格: 空填 '-', 转义 '|' 免破坏 markdown 表格。"""
    return (s or "-").replace("|", "/")


class Spec:
    def __init__(self) -> None:
        self.root = spec_root()

    def layer_dir(self, layer: str) -> Path:
        return self.root / layer

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
        for layer in LAYERS:
            for f in self._rule_files(layer):
                out.setdefault(f, int(f.stat().st_mtime))
        return out

    def _age_days(self, f: Path, mtimes: dict[Path, int], now_ts: int) -> int:
        return max(0, (now_ts - mtimes.get(f, now_ts)) // 86400)

    # ---- init ----
    def init(self, _: argparse.Namespace) -> None:
        for layer in LAYERS:
            self.layer_dir(layer).mkdir(parents=True, exist_ok=True)
        self._reindex_all()
        print(f"已初始化 spec 库: {self.root}")

    # ---- core 正文 (供 inject-core / session-start 复用) ----
    def _core_text_raw(self) -> str:
        parts = [_strip_frontmatter(f.read_text()).strip() for f in self._rule_files("core")]
        return "\n\n".join(p for p in parts if p)

    def _core_text(self) -> str:
        text = self._core_text_raw()
        budget = core_budget()
        if len(text) > budget:
            sys.stderr.write(
                f"core 规则 {len(text)} 字符 > 预算 {budget} — "
                "常驻注入过重, 考虑降级部分到 recall\n")
        return text

    # ---- inject-core (按需拉全文正文) ----
    def inject_core(self, _: argparse.Namespace) -> None:
        sys.stdout.write(self._core_text())

    # ---- core 极简索引 (章节粒度, 每条规则 1 行: [类目] 主题 · title) ----
    def _core_index(self) -> str:
        return "\n".join(f"- [{f.parent.name}/{f.stem}] {title}"
                         for f, title, _ in self._rules("core") if title)

    # ---- session-start (SessionStart hook: 只注入极简索引, 全文按需 inject-core) ----
    def session_start(self, _: argparse.Namespace) -> None:
        idx = self._core_index().strip()
        if not idx:
            return
        ctx = budget_guard(
            "# SKEIN core 规则索引 (仅标题; 需全文跑 `spec.py inject-core`)\n\n" + idx,
            INDEX_BUDGET_TOKENS, "spec:session-start")
        # maintain 提示: core 超预算 或 最老规则 > 180 天 → 1 行提醒 (不挤 INDEX 预算)
        core_text = self._core_text_raw()
        now_ts = now()
        # hook 热路径: 不跑 git log (use_git=False), 文件系统 mtime 够判"该体检了"
        mt = self._mtimes(use_git=False)
        oldest = max((self._age_days(f, mt, now_ts) for f in self._rule_files("core")), default=0)
        if len(core_text) > core_budget() or oldest > STALE_DAYS:
            ctx += f"\n⚠️ core 超 budget / 有 > {STALE_DAYS}天老规则, 跑 `spec.py maintain` 体检"
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "SessionStart", "additionalContext": ctx}}))

    # ---- core 按类目过滤全文 (命中类目注全文, 其余仅进索引) ----
    def _core_text_by_cat(self, cats: list[str]) -> str:
        parts = [_strip_frontmatter(f.read_text()).strip()
                 for f in self._rule_files("core") if f.parent.name in cats]
        return "\n\n".join(p for p in parts if p)

    # ---- subagent-start (SubagentStart hook: 读 stdin.agent_type 决定注入范围) ----
    def subagent_start(self, _: argparse.Namespace) -> None:
        # matcher 已放开到全 subagent — 非 SKEIN 项目 (无 .skein/spec) 静默不注入, 免污染其他插件的 agent
        if not self.root.exists():
            return
        idx = self._core_index().strip()
        if not idx:
            return
        head = ("# SKEIN spec 纪律 (执行期强制)\n"
                "- 动手前: 相关约定先跑 `spec.py recall <关键词>` 拉 recall 层, 别凭记忆重推。\n"
                "- 命中 core 规则 (下列) 即硬约束, 违反视为未完成。\n"
                "- 踩到「后续同类任务会再犯」的坑 / 定下可复用约定: 在回传给 main 的摘要里标一行 `SPEC:` 供 finish sediment 落盘, 别让它随 worktree 销毁蒸发。\n")
        recall_tail = "\n## 需要其他类目全文? 跑 `spec.py recall <关键词>` 或 inject-core\n"
        cats = AGENT_CATEGORIES.get(_read_hook_stdin() or "", [])
        if cats:
            body = self._core_text_by_cat(cats).strip()
            ctx = head + f"\n## core 规则 (命中类目 {cats})\n\n{body}\n\n## 全量 core 索引\n\n{idx}{recall_tail}"
        else:  # 空映射/非 skein agent/stdin 失败 → 全 core 正文 + 索引 (对齐 help: 每 subagent 注 core 全文)
            body = self._core_text().strip()
            ctx = head + f"\n## core 规则 (全量)\n\n{body}\n\n## core 索引\n\n{idx}{recall_tail}"
        ctx = budget_guard(ctx, SUBAGENT_BUDGET_TOKENS, "spec:subagent-start")
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "SubagentStart", "additionalContext": ctx}}))

    # ---- recall (按需粗筛: FTS5 BM25 优先, grep fallback) ----
    def recall(self, a: argparse.Namespace) -> None:
        query = cast(str, a.query)
        fts_hits = self._recall_fts(query)
        if fts_hits is not None:
            if fts_hits:
                print("recall 命中 (FTS5 BM25, model 读全文再定用否):")
                print("\n".join(fts_hits))
            else:
                print("recall 无命中")
            return
        # fallback: 无 .recall.db 或 MATCH 语法失败 → 子串 grep recall/index.md
        hits = self._recall_grep(query)
        if hits:
            print("recall 命中 (grep fallback, model 读全文再定用否):")
            print("\n".join(hits))
        else:
            print("recall 无命中")

    def _recall_fts(self, query: str) -> Optional[list[str]]:
        """FTS5 BM25 召回; 返回命中行 (None=不可用降级 grep, []=无命中)。

        每个 token 双引号包起 + OR: 兼容中文 unicode61 分词弱 (任一词命中即召回)。
        含双引号的 token 会破坏 MATCH 语法 → 提前降级 grep (不调 MATCH)。
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
                rows = con.execute(
                    "SELECT rel, category, title, keywords, body, layer FROM rules "
                    "WHERE rules MATCH ? ORDER BY bm25(rules) LIMIT 10", (ftsq,)).fetchall()
            finally:
                con.close()
        except sqlite3.OperationalError:
            return None  # MATCH 语法敏感字符 → 降级 grep
        return [f"| [{layer}] {rel} | {cat} | {title} | {kw} | - | {_summary(body)} |"
                for rel, cat, title, kw, body, layer in rows]

    def _recall_grep(self, query: str) -> list[str]:
        """子串 grep recall+external 的 index.md (FTS5 不可用时的 fallback); 命中行带 [layer] 前缀。"""
        terms = [t for t in re.split(r"\s+", query.lower()) if t]
        hits: list[str] = []
        for layer in ("recall", "external"):
            idx = self.layer_dir(layer) / "index.md"
            if not idx.exists():
                continue
            for ln in idx.read_text().splitlines():
                if ln.startswith("| ") and not ln.startswith("| file") \
                        and any(t in ln.lower() for t in terms):
                    hits.append(f"[{layer}] {ln}")
        return hits

    # ---- sediment (写盘: 规则作为一个章节追加进主题文件, 判定门通过后自动调用) ----
    def sediment(self, a: argparse.Namespace) -> None:
        layer = cast(str, a.layer)
        title = cast(str, a.title)
        keywords = cast(Optional[str], getattr(a, "keywords", None)) or ""
        status = cast(Optional[str], getattr(a, "status", None)) or "active"
        body_file = cast(Optional[str], getattr(a, "body_file", None))
        cat = cast(Optional[str], getattr(a, "category", None)) or "misc"
        # --topic 缺省 → 归入类目同名主题文件 (调用方应按语义指定主题, 免所有规则挤一个文件)
        topic = _slug(cast(Optional[str], getattr(a, "topic", None)) or cat)
        d = self.layer_dir(layer) / cat
        d.mkdir(parents=True, exist_ok=True)
        f = d / f"{topic}.md"
        body = (Path(body_file).read_text() if body_file else "").strip()
        self._append_rule(f, layer, cat, topic, title, body, keywords, status)
        self._reindex_all()
        print(f"已沉淀 → {f.relative_to(self.root).as_posix()}#{title}")

    def _append_rule(self, f: Path, layer: str, cat: str, topic: str, title: str,
                     body: str, keywords: str, status: str) -> None:
        """把一条规则作为 `## <title>` 章节追加进主题文件 (不存在则建, frontmatter 只留 5 字段)。"""
        old_body, kws, st = "", [k.strip() for k in keywords.split(",") if k.strip()], status
        if f.exists():
            txt = f.read_text()
            meta = _frontmatter(txt)
            old_body = _strip_frontmatter(txt).strip()
            kws = list(dict.fromkeys([k.strip() for k in str(meta.get("keywords", "")).split(",")
                                      if k.strip()] + kws))
            # ponytail: status 是文件级 (主题级) 字段 — 追加时只在显式非 active 时覆盖;
            # 单条规则要独立 status → 拆到自己的主题文件。
            st = status if status != "active" else str(meta.get("status", "active"))
        f.write_text(
            "---\n"
            f"title: {topic}\n"
            f"layer: {layer}\n"
            f"category: {cat}\n"
            f"keywords: [{','.join(kws)}]\n"
            f"status: {st}\n"
            "---\n\n"
            + (old_body + "\n\n" if old_body else "")
            + f"## {title}\n\n{body}\n")

    # ---- reindex ----
    def reindex(self, _: argparse.Namespace) -> None:
        self._reindex_all()
        print(f"已重建索引: {self.root}")

    def _reindex_all(self) -> dict[str, dict[str, int]]:
        counts: dict[str, dict[str, int]] = {}
        for layer in LAYERS:
            counts[layer] = self._reindex_layer(layer)
        self._reindex_top(counts)
        self._rebuild_fts()
        self._rebuild_backlinks_md(self._rebuild_backlinks())
        return counts

    def _rebuild_backlinks(self) -> dict[str, list[str]]:
        """扫全库章节 body 的 [[slug]] → {目标 slug: [来源规则 id,...]}。A-MEM-lite 反链表。

        目标 slug 归一为 `topic` (整篇主题) 或 `topic#规则标题` (单条规则); 来源恒为规则 id
        (<layer>/<cat>/<topic>.md#<标题>) — 关联落到章节粒度, 检索时可直接跳到那一条。"""
        backlinks: dict[str, list[str]] = {}
        for layer in LAYERS:
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
        for layer in LAYERS:
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
        """重建 FTS5 BM25 索引 (recall + external 跨层; core 常驻不入索引)。sqlite3 stdlib, 无新依赖。

        schema 含 layer 列, recall 输出带 [layer] 前缀供 model 定位 .skein/spec/<layer>/...。
        CREATE IF NOT EXISTS 不改已存表 schema → reindex 时先 DROP 再 CREATE (幂等迁移)。"""
        db = self.root / ".recall.db"
        import sqlite3  # 局部: 仅 reindex/sediment 重建索引链用
        con = sqlite3.connect(db)
        try:
            con.execute("DROP TABLE IF EXISTS rules")
            con.execute("CREATE VIRTUAL TABLE rules USING fts5(rel, category, title, keywords, body, layer)")
            for layer in ("recall", "external"):  # 跨层索引 (core 常驻, 不入)
                for f, title, body in self._rules(layer):  # 一行 = 一条规则 (章节), 非一个文件
                    kw = str(_frontmatter(f.read_text()).get("keywords", ""))
                    con.execute(
                        "INSERT INTO rules(rel, category, title, keywords, body, layer) VALUES (?,?,?,?,?,?)",
                        (f"{f.parent.name}/{f.stem}.md#{title}", f.parent.name, title, kw, body, layer))
            con.commit()
        finally:
            con.close()

    def _reindex_layer(self, layer: str) -> dict[str, int]:
        """重建 <layer>/index.md (章节粒度: 一行 = 一条规则), 返回 {category: 规则条数}。"""
        d = self.layer_dir(layer)
        d.mkdir(parents=True, exist_ok=True)
        by_cat: dict[str, int] = {}
        rows: list[tuple[str, str, str, str, str, str]] = []
        for f, title, body in self._rules(layer):
            meta = _frontmatter(f.read_text())
            cat = f.parent.name  # 类目 = 所在目录 (物理事实), 免与 frontmatter 漂移
            rel = f"{f.relative_to(d).as_posix()}#{title}"  # 规则 id, 可直接定位到章节
            by_cat[cat] = by_cat.get(cat, 0) + 1
            links = ",".join(sorted({t for m in re.finditer(r"\[\[([^\]]+)\]\]", body)
                                     if (t := _link_target(m.group(1)))}))
            # .get 容错旧 spec 缺 status (缺字段视为 active, 不报错不迁移)
            rows.append((cat, rel, _cell(title), _cell(str(meta.get("keywords", ""))),
                         _cell(str(meta.get("status", "active"))) + (f" / →{_cell(links)}" if links else ""),
                         _summary(body)))
        rows.sort()
        table = "\n".join(f"| {rel} | {cat} | {title} | {kw} | {status} | {summ} |"
                          for cat, rel, title, kw, status, summ in rows)
        (d / "index.md").write_text(
            f"# SKEIN {layer} 规则索引 (章节粒度: 一行一条规则)\n\n"
            f"类目: {_dist(by_cat)} · 关联见 [backlinks.md](backlinks.md)\n\n"
            "| rule (topic.md#标题) | category | title | keywords | status/出链 | summary |\n"
            "|---|---|---|---|---|---|\n"
            + (table + "\n" if table else ""))
        return by_cat

    def _reindex_top(self, counts: dict[str, dict[str, int]]) -> None:
        lines = ["# SKEIN 规则库总索引\n",
                 "三层: **core** 常驻注入 (SessionStart) · **recall** 按需召回 (planning `recall <query>`) · "
                 "**external** 外部参考 (纯手动 CLI 检索, 不入 hook)。\n",
                 "| layer | 条数 | 类目分布 | 索引 |",
                 "|---|---|---|---|"]
        for layer in LAYERS:
            by_cat = counts.get(layer, {})
            total = sum(by_cat.values())
            lines.append(f"| {layer} | {total} | {_dist(by_cat)} | [{layer}/index.md]({layer}/index.md) |")
        (self.root / "index.md").write_text("\n".join(lines) + "\n")

    # ---- archive (完全重构前可逆清库: 移旧规则到 .archive/<ts>/, reindex 空) ----
    def archive(self, a: argparse.Namespace) -> None:
        layer_opt = cast(Optional[str], getattr(a, "layer", None))
        layers = [layer_opt] if layer_opt else list(LAYERS)
        ts = str(now())
        dest = self.root / ".archive" / ts
        moved = 0
        for layer in layers:
            for f in self._rule_files(layer):  # rglob 不含 .archive (在 root 下非 layer 下)
                tgt = dest / f.relative_to(self.root)  # 保 <layer>/<category>/ 结构
                tgt.parent.mkdir(parents=True, exist_ok=True)
                f.rename(tgt)  # 同 fs move, 不复制
                moved += 1
        self._reindex_all()
        if moved:
            print(f"已归档 {moved} 条规则 → {dest}\n回滚: python3 spec.py restore {ts}")
        else:
            print("无规则可归档 (库已空)")

    # ---- restore (从归档恢复; 撞名的旧规则加 restored- 前缀不覆盖重构后新规则) ----
    def restore(self, a: argparse.Namespace) -> None:
        ts = cast(str, a.ts)
        src = self.root / ".archive" / ts
        if not src.exists():
            raise SystemExit(f"归档不存在: {src} (查可用: ls {self.root / '.archive'})")
        moved = 0
        for f in sorted(src.rglob("*.md")):
            if f.name == "index.md":
                continue
            tgt = self.root / f.relative_to(src)
            tgt.parent.mkdir(parents=True, exist_ok=True)
            if tgt.exists():  # 重构后同路径已有新规则 → 不覆盖, 换名并存
                tgt = tgt.with_name(f"restored-{f.name}")
            f.rename(tgt)
            moved += 1
        self._reindex_all()
        print(f"已恢复 {moved} 条 ← {src}")

    # ---- maintain (全量体检: 超预算/stale/断链/keywords重复/废弃; 无 --apply 只报告) ----
    def _scan_findings(self, layers: list[str]) -> list[dict[str, Any]]:
        """全量扫描 → 结构化 findings (kind/text + 修复所需上下文); maintain 报告 & --apply 共用。"""
        # 合法 wikilink 目标 = 主题 stem (整篇) ∪ stem#规则标题 (单条)
        all_slugs = {f.stem for layer in LAYERS for f in self._rule_files(layer)} | \
                    {f"{f.stem}#{t}" for layer in LAYERS for f, t, _ in self._rules(layer)}
        backlinks = self._rebuild_backlinks()  # 一次扫, 判据 6 复用
        now_ts = now()
        mtimes = self._mtimes()
        findings: list[dict[str, Any]] = []

        # 判据 1: 超预算 (仅 core 全文)
        if "core" in layers:
            core_text = self._core_text_raw()
            budget = core_budget()
            if len(core_text) > budget:
                sized = sorted(
                    ((len(_strip_frontmatter(f.read_text()).strip()), f.parent.name, f.stem, f)
                     for f in self._rule_files("core")), reverse=True)
                cands = ", ".join(f"{cat}/{stem}({sz})" for sz, cat, stem, _ in sized[:3])
                findings.append({"kind": "overbudget", "size": len(core_text),
                                 "text": f"[超预算] core {len(core_text)} > {budget} 字符 — 考虑降级: {cands}"})

        for layer in layers:
            for f in self._rule_files(layer):
                txt = f.read_text()
                meta = _frontmatter(txt)
                rel = f"{layer}/{f.parent.name}/{f.stem}"
                status = meta.get("status", "active")

                # 判据 2: stale — 最近修改 (git 提交时间, 无则 fs mtime) 超 STALE_DAYS
                age = self._age_days(f, mtimes, now_ts)
                if age > STALE_DAYS:
                    findings.append({"kind": "stale", "file": f, "rel": rel, "status": status,
                                     "text": f"[stale] {rel} (最近改动 {_months(age)},{age}天前, status {status})"})

                # 判据 3: broken wikilink — body 的 [[slug]] 目标不在库内 (断链只报告, 需人判断修哪头)
                body = _strip_frontmatter(txt)
                for m in re.finditer(r"\[\[([^\]]+)\]\]", body):
                    slug = m.group(1).strip()
                    tgt = _link_target(slug)
                    if tgt and tgt not in all_slugs:
                        findings.append({"kind": "broken_link", "rel": rel, "slug": slug,
                                         "text": f"[断链] {rel}: [[{slug}]] ✗ 目标缺失"})

                # 判据 4: 废弃/superseded → archive
                if status in ("deprecated", "superseded"):
                    findings.append({"kind": "deprecated", "file": f, "rel": rel, "status": status,
                                     "text": f"[废弃] {rel} (status {status}) — 建议 archive"})

                # 判据 6: 孤立 — 整篇无入度 (stem 及其任一章节都不在 backlinks) + active + 超 STALE_DAYS
                linked = f.stem in backlinks or any(f"{f.stem}#{t}" in backlinks
                                                    for t, _ in _sections(txt))
                if status == "active" and not linked and age > STALE_DAYS:
                    findings.append({"kind": "orphan", "file": f, "rel": rel,
                                     "text": f"[孤立] {rel} 无入度+active+超{STALE_DAYS}天 — 候选归档/降级"})

            # 判据 5: keywords 高重复 — 同 keywords 组 ≥3 条 → 保留最新, 余 archive
            groups: dict[str, list[Path]] = {}
            for f in self._rule_files(layer):
                kw = _frontmatter(f.read_text()).get("keywords", "").strip()
                if not kw:
                    continue
                key = ",".join(sorted(k for k in kw.split(",") if k.strip()))
                groups.setdefault(key, []).append(f)
            for kw_key, hits in sorted(groups.items()):
                if len(hits) >= KEYWORDS_DUP_THRESHOLD:
                    rels = [f"{layer}/{f.parent.name}/{f.stem}" for f in hits]
                    findings.append({"kind": "keywords_dup", "kw": kw_key, "files": hits,
                                     "text": f'[重复 keywords] "{kw_key}" ×{len(hits)}: {", ".join(rels)}'})
        return findings

    def maintain(self, a: argparse.Namespace) -> None:
        layer_opt = cast(Optional[str], getattr(a, "layer", None))
        layers = [layer_opt] if layer_opt else list(LAYERS)
        apply = bool(getattr(a, "apply", False))
        findings = self._scan_findings(layers)

        if not apply:
            print("maintain 体检 (.skein/spec):")
            if findings:
                print("\n".join(fd["text"] for fd in findings))
            else:
                print("全清 (无超预算/stale/断链/重复/废弃/孤立)")
            return

        # --apply: 自动修复可修项 (断链只报告, 需人判断)
        broken = [fd for fd in findings if fd["kind"] == "broken_link"]
        actions: list[str] = []

        # 超预算 → 循环降级 core→recall
        if any(fd["kind"] == "overbudget" for fd in findings):
            before = len(self._core_text_raw())
            degraded = self._degrade_core_to_budget()
            after = len(self._core_text_raw())
            for rel in degraded:
                actions.append(f"降级 core→recall: {rel}")
            actions.append(f"core 超预算修复: {before}→{after} 字符 (降 {len(degraded)} 条)")

        # 归档批: stale + 废弃 + keywords 重复(保留最新) 合并一次 .archive/<ts>/
        archive_reasons: dict[Path, tuple[str, str]] = {}
        for fd in findings:
            if fd["kind"] == "stale":
                f = cast(Path, fd["file"])
                archive_reasons[f] = ("prune-stale", f"stale({fd['rel']},超{STALE_DAYS}天)")
            elif fd["kind"] == "deprecated":
                f = cast(Path, fd["file"])
                archive_reasons[f] = ("prune-deprecated", f"废弃(status={fd['status']})")
            elif fd["kind"] == "orphan":
                f = cast(Path, fd["file"])
                # ponytail: stale 必然 orphan, 但 stale 判据更强更具体 → stale 优先, orphan 不覆盖已占 key
                if f not in archive_reasons:
                    archive_reasons[f] = ("prune-orphan", "孤立(无入度+active+stale)")
        for fd in findings:
            if fd["kind"] == "keywords_dup":
                files = cast(list[Path], fd["files"])
                # 保留最新 (最近改动者, git 提交时间优先), 其余归档
                mt = self._mtimes()
                newest = max(files, key=lambda f: mt.get(f, 0))
                for f in files:
                    if f != newest and f not in archive_reasons:
                        archive_reasons[f] = (
                            "prune-dup", f'keywords重复(组"{fd["kw"]}":{len(files)}条,保留最新)')
        # ponytail: 跳过被上文 degrade 移走的 (overbudget+stale 同一最大文件场景);
        # 它已成 recall 层, 旧 core/ Path 在 findings 里过期, 下轮 maintain 再扫到。
        archive_reasons = {f: r for f, r in archive_reasons.items() if f.exists()}
        if archive_reasons:
            self._archive_batch(list(archive_reasons.keys()), archive_reasons)
            for f, (act, _reason) in archive_reasons.items():
                actions.append(f"归档 ({act}): {f.relative_to(self.root).as_posix()}")

        print("maintain --apply 已执行:")
        if actions:
            print("\n".join(actions))
        else:
            print("无自动可修项")
        if broken:
            print("\n仍需人工 (断链 — 需判断修哪头/补目标):")
            print("\n".join(fd["text"] for fd in broken))

    # ---- 审计日志 (.audit-log 追加写 + 7天轮转) ----
    def _write_audit(self, action: str, file: str, before: str, after: str, reason: str) -> None:
        """追加审计行 + 写前清 7 天前旧行 (按行首 iso ts 判)。格式: iso_ts|action|file|before->(after)|reason"""
        log = self.root / ".audit-log"
        cutoff = now() - AUDIT_RETENTION_DAYS * 86400
        kept: list[str] = []
        if log.exists():
            for ln in log.read_text().splitlines():
                head = ln.split("|", 1)[0]
                try:
                    if datetime.fromisoformat(head).timestamp() < cutoff:
                        continue  # 超 7 天 → 丢
                except ValueError:
                    pass  # 非 iso 头 (旧格式/手写) → 保留不误删
                kept.append(ln)
        iso_ts = datetime.fromtimestamp(now()).isoformat(timespec="seconds")
        kept.append(f"{iso_ts}|{action}|{file}|{before}->({after})|{reason}")
        log.write_text("\n".join(kept) + "\n")

    # ---- 单文件降级核心 (degrade 子命令 + maintain --apply 复用) ----
    def _degrade_one(self, f: Path, reason: str) -> str:
        """core→recall 单文件: git mv (fallback rename) + frontmatter layer + reindex + 审计。返回 recall 相对路径。"""
        if not f.exists():
            raise SystemExit(f"降级失败: 文件不存在 {f}")
        rel_before = f.relative_to(self.root).as_posix()
        cat = f.parent.name
        dest_dir = self.layer_dir("recall") / cat
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / f.name
        self._git_mv(f, dest)
        self._rewrite_layer(dest, "recall")
        rel_after = dest.relative_to(self.root).as_posix()
        self._write_audit("degrade", rel_before, rel_before, rel_after, reason)
        self._reindex_all()
        return rel_after

    def _degrade_core_to_budget(self) -> list[str]:
        """循环降 top-1 最大 core 文件 → recall, 直到 core < core_budget() 或无 core 文件。返回降级路径列表。"""
        degraded: list[str] = []
        while True:
            core_text = self._core_text_raw()
            budget = core_budget()
            if len(core_text) <= budget:
                break
            files = self._rule_files("core")
            if not files:
                break
            top = max(files, key=lambda f: len(_strip_frontmatter(f.read_text()).strip()))
            reason = f"core超预算({len(core_text)}>{budget})"
            degraded.append(self._degrade_one(top, reason))
        return degraded

    def _git_mv(self, src: Path, dest: Path) -> None:
        """git mv (保留历史); 未跟踪/无 git → fallback rename (同 fs 移动)。"""
        r = subprocess.run(["git", "mv", str(src), str(dest)],
                           capture_output=True, text=True, cwd=self.root)
        if r.returncode != 0:
            dest.parent.mkdir(parents=True, exist_ok=True)
            src.rename(dest)

    def _rewrite_layer(self, f: Path, new_layer: str) -> None:
        """改 frontmatter 的 layer: 行为新值 (原地正则替换首处)。"""
        txt = f.read_text()
        new = re.sub(r"^layer:\s*\S+", f"layer: {new_layer}", txt, count=1, flags=re.MULTILINE)
        if new != txt:
            f.write_text(new)

    def _archive_batch(self, files: list[Path], reasons: dict[Path, tuple[str, str]]) -> int:
        """批量归档多文件到同一 .archive/<ts>/ (保 <layer>/<cat>/ 结构) + reindex + 审计。"""
        ts = str(now())
        dest_base = self.root / ".archive" / ts
        moved = 0
        for f in files:
            rel_before = f.relative_to(self.root).as_posix()
            dest = dest_base / f.relative_to(self.root)
            dest.parent.mkdir(parents=True, exist_ok=True)
            f.rename(dest)
            act, reason = reasons.get(f, ("archive", ""))
            self._write_audit(act, rel_before, rel_before, f".archive/{ts}/{rel_before}", reason)
            moved += 1
        if moved:
            self._reindex_all()
        return moved

    # ---- degrade 子命令 ----
    def degrade(self, a: argparse.Namespace) -> None:
        if getattr(a, "auto", False):
            before = len(self._core_text_raw())
            degraded = self._degrade_core_to_budget()
            after = len(self._core_text_raw())
            if degraded:
                print(f"自动降级 {len(degraded)} 条 core→recall (core {before}→{after} 字符):")
                for rel in degraded:
                    print(f"  - {rel}")
            else:
                print(f"无需降级 (core {after} ≤ {core_budget()})")
            return
        target = cast(str, a.file)
        # external 是终点层 (非 core), degrade 仅 core→recall 单向 → 显式拒, 免用户误以为可降级
        if target.replace("\\", "/").lstrip().startswith("external/"):
            raise SystemExit("external 是终点层, degrade 仅 core→recall 单向 (external 不参与降级)")
        f = self._resolve_core_file(target)
        meta = _frontmatter(f.read_text())
        if meta.get("layer", "core") != "core":
            raise SystemExit(f"非 core 文件 (layer={meta.get('layer')}), 仅 core 可降级: {target}")
        rel = self._degrade_one(f, "手动降级")
        print(f"已降级 core→recall → {rel}")

    def _resolve_core_file(self, target: str) -> Path:
        """归一化降级目标路径: 补 .md, 补 core/ 前缀; 需含类目 (<cat>/<name>)。"""
        t = target.replace("\\", "/").strip("/")
        if not t.endswith(".md"):
            t += ".md"
        # 去 layer 前缀 (无论 core/recall) 再补 core/
        for pref in (f"{lw}/" for lw in LAYERS):
            if t.startswith(pref):
                t = t[len(pref):]
                break
        t = "core/" + t
        if t.count("/") < 2:  # core/<cat>/<name>.md 至少 2 个斜杠
            raise SystemExit(f"需 <category>/<name> 形式 (如 impl/foo): {target}")
        f = self.root / t
        if not f.exists():
            raise SystemExit(f"文件不存在: {target} → {f.relative_to(self.root)}")
        return f

    # ---- restructure (碎片文件 → 主题文件合并; 源文件进 .archive/<ts>/ 可回滚) ----
    def restructure(self, a: argparse.Namespace) -> None:
        """--map 是 {目标主题文件相对路径: [源文件相对路径,...]} 的 JSON (主题归类由调用方语义判定)。

        每个源文件的每条规则 (章节, 旧库为整篇) 按序追加进目标主题文件, 标题保留原 title。
        """
        plan = json.loads(Path(cast(str, a.map)).read_text())
        dry = bool(getattr(a, "dry_run", False))
        srcs_all: list[Path] = []
        for target, srcs in plan.items():
            t = self.root / target
            layer, cat = t.relative_to(self.root).parts[0], t.parent.name
            if layer not in LAYERS:
                raise SystemExit(f"目标路径层非法: {target} (需 <layer>/<category>/<topic>.md)")
            for s in srcs:
                sp = self.root / s
                if not sp.exists():
                    raise SystemExit(f"源文件不存在: {s}")
                txt = sp.read_text()
                meta = _frontmatter(txt)
                # 一个源文件 = 一条规则: 标题取 frontmatter title, 整篇正文降级为 `###` 子节
                # (源文件内的 `## 铁律`/`## 反例表` 是规则的组成部分, 不是独立规则)
                if not dry:
                    self._append_rule(t, layer, cat, t.stem,
                                      str(meta.get("title", "")) or sp.stem,
                                      _clean_body(_strip_frontmatter(txt)),
                                      str(meta.get("keywords", "")),
                                      str(meta.get("status", "active")))
                if sp != t:  # 源即目标 (原地升格) → 不归档自己
                    srcs_all.append(sp)
            print(f"{'[dry] ' if dry else ''}{target} ← {len(srcs)} 个源文件")
        if dry:
            print(f"[dry-run] 共 {len(plan)} 个主题文件 / {len(srcs_all)} 个源文件, 未落盘")
            return
        moved = self._archive_batch(srcs_all, {f: ("restructure", "合并进主题文件") for f in srcs_all})
        self._reindex_all()
        print(f"已重构: {len(plan)} 个主题文件, 源 {moved} 个已归档 (可 restore 回滚)")

    # ---- list ----
    def list_(self, a: argparse.Namespace) -> None:
        layer_opt = cast(Optional[str], getattr(a, "layer", None))
        for layer in ([layer_opt] if layer_opt else list(LAYERS)):
            d = self.layer_dir(layer)
            rules = [f"{f.relative_to(d).as_posix()}#{t}" for f, t, _ in self._rules(layer)]
            print(f"[{layer}] {len(rules)} 条规则 / {len(self._rule_files(layer))} 个主题: "
                  f"{', '.join(rules) or '-'}")


def _months(days: Optional[int]) -> str:
    """天数 → 'N月' 概览 (粗算 30 天/月); None → '-'。"""
    return f"{int(days) // 30}月" if days is not None else "-"


def _sections(text: str) -> list[tuple[str, str]]:
    """主题文件 → [(规则标题, 规则正文)], 按 body 内 `## ` 切。

    无 `##` → 整篇算一条 (frontmatter title 为标题), 兼容尚未合并的旧单规则文件。
    `## ` 之前的引言不算规则 (主题说明), 不入索引。"""
    body = _strip_frontmatter(text)
    parts = re.split(r"^##\s+(.+?)\s*$", body, flags=re.M)
    if len(parts) < 3:
        t, b = _frontmatter(text).get("title", ""), body.strip()
        return [(t, b)] if (t or b) else []
    return [(parts[i].strip(), parts[i + 1].strip()) for i in range(1, len(parts), 2)]


def _slug(s: str) -> str:
    """标题 → 文件名 slug: 空白/路径/markdown 敏感字符 → '-'; 中文原样保留。空 → 'misc'。"""
    s = re.sub(r"[\s/\\:*?\"'<>|#\[\]]+", "-", s.strip())
    return re.sub(r"-{2,}", "-", s).strip("-.")[:60] or "misc"


def _link_target(raw: str) -> str:
    """`[[core/git/merge.md#标题|别名]]` → 归一 `merge#标题`; 无锚点 → `merge` (整篇主题)。"""
    stem, _, anchor = raw.split("|")[0].strip().partition("#")
    stem = stem.split("/")[-1].strip()
    if stem.endswith(".md"):
        stem = stem[:-3]
    anchor = anchor.strip()
    return f"{stem}#{anchor}" if anchor else stem


def _frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    out: dict[str, str] = {}
    for ln in text[3:end].splitlines():
        if ":" in ln:
            k, _, v = ln.partition(":")
            out[k.strip()] = v.strip().strip("[]")
    return out


def _strip_frontmatter(text: str) -> str:
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            return text[end + 4:]
    return text


def _clean_body(body: str) -> str:
    """合并前清洗规则正文: 剥掉正文里泄漏的 frontmatter 块, 一二级标题降为 `###`
    (免与主题文件的 `## 规则标题` 层级冲突把一条规则劈成多条)。"""
    body = re.sub(r"^---\n.*?\n---\n?", "", body.strip(), flags=re.S)
    return re.sub(r"^(#{1,2})\s+", "### ", body, flags=re.M).strip()


def _summary(body: str) -> str:
    s = _strip_frontmatter(body).strip().replace("\n", " ")
    s = re.sub(r"[|]", "/", s)  # 免破坏表格
    return (s[:60] + "…") if len(s) > 60 else s or "-"


def main() -> None:
    p = argparse.ArgumentParser(
        prog="spec.py",
        description="SKEIN 三层规则记忆 (.skein/spec) — core 常驻 + recall/external 按需召回",
        epilog="用法: planning 时 recall 召回, task finish 时 sediment 沉淀",
    )
    p.add_argument("-d", "--debug", action="store_true",
                   help="rich 美化叙事到 stderr — 展示命令与参数 (stdout 保持机器纯净; 亦可 SKEIN_DEBUG=1)")
    sub = p.add_subparsers(dest="cmd", required=True, metavar="<command>")
    sub.add_parser("init", help="初始化 .skein/spec 库 (幂等)")
    sub.add_parser("inject-core", help="输出 core 层全部规则正文 (常驻注入)")
    sub.add_parser("session-start", help="[hook 用] 每 session 注入 core 规则索引")
    sub.add_parser("subagent-start", help="[hook 用] 每 subagent 注入 core 全文 + spec 纪律")
    sub.add_parser("reindex", help="重建各层 index.md + 顶层总索引 (改盘后同步)")
    r = sub.add_parser("recall", help="按关键词 FTS5 BM25 排序 recall (无 .recall.db/MATCH 失败 → grep fallback)")
    r.add_argument("query", help="任务关键词")
    s = sub.add_parser("sediment", help="沉淀一条规则 (追加为主题文件的一个章节) + 自动 reindex")
    s.add_argument("--layer", required=True, choices=list(LAYERS),
                   help="core=常驻硬规 / recall=按需召回 / external=外部参考 (不入 hook)")
    s.add_argument("--category", help="类目子目录 = 文件夹 (git/test/arch/build/style...)")
    s.add_argument("--topic", help="主题 = 文件名, 同主题规则并入同一文件 (缺省 = 类目同名主题)")
    s.add_argument("--title", required=True, help="规则标题 (主题文件内的 `## ` 章节名)")
    s.add_argument("--keywords", help="召回关键词, 逗号分隔 (并入主题文件已有 keywords)")
    s.add_argument("--source", help="[已废弃, 忽略] 来源标记")
    s.add_argument("--status", choices=["active", "deprecated", "superseded"], default="active",
                   help="主题状态 (缺省 active; deprecated=弃用 / superseded=被替代)")
    s.add_argument("--body-file", help="规则正文文件路径; 关联写 `[[主题#规则标题]]` wikilink")
    ls = sub.add_parser("list", help="列已存规则")
    ls.add_argument("--layer", choices=list(LAYERS), help="仅列指定层 (缺省列三层)")
    mt = sub.add_parser("maintain", help="全量体检 (超预算/stale/断链/keywords重复/废弃/孤立); --apply 自动修复 (断链只报告)")
    mt.add_argument("--layer", choices=list(LAYERS), help="仅体检指定层 (缺省三层全扫)")
    mt.add_argument("--apply", action="store_true",
                   help="自动修复可修项: 超预算→降级 / stale→归档 / keywords重复→归档(保留最新) / 废弃→归档 / 孤立→归档; 断链仍只报告")
    dg = sub.add_parser("degrade", help="core→recall 单文件降级 (layer 改 + git mv + reindex + 审计)")
    dg.add_argument("file", nargs="?", help="相对 .skein/spec/ 路径 (core/<cat>/<name>.md 或 <cat>/<name>); --auto 时省略")
    dg.add_argument("--auto", action="store_true", help="自动模式: 循环降 top-1 最大文件到 core < core_budget() 即停")
    ar = sub.add_parser("archive", help="[完全重构前] 可逆归档旧规则到 .archive/<ts>/ + reindex 空")
    ar.add_argument("--layer", choices=list(LAYERS), help="仅归档指定层 (缺省三层全归档)")
    rs = sub.add_parser("restore", help="从归档恢复规则 (撞名不覆盖新规则, 加 restored- 前缀并存)")
    rs.add_argument("ts", help="归档时间戳 (archive 输出的目录名)")
    rc = sub.add_parser("restructure", help="按映射把碎片文件合并进主题文件 (源进 .archive/, 可 restore 回滚)")
    rc.add_argument("--map", required=True, help='JSON 文件: {"core/git/merge.md": ["core/git/rule-01.md", ...]}')
    rc.add_argument("--dry-run", action="store_true", help="只打印计划不落盘")

    # --debug 可置子命令前后任意位置: 预剥离 argv (argparse 子解析器不认父级 flag)
    cli_debug = any(x in ("-d", "--debug") for x in sys.argv[1:])
    sys.argv[1:] = [x for x in sys.argv[1:] if x not in ("-d", "--debug")]
    a = p.parse_args()
    global DBG
    DBG = Debug(cli_debug or debug_enabled(None))
    DBG.rule(f"spec {a.cmd}")
    DBG.kv({k: v for k, v in vars(a).items() if k not in ("cmd", "debug") and v not in (None, False)},
           title="参数")
    m = Spec()
    {
        "init": m.init, "inject-core": m.inject_core, "recall": m.recall,
        "session-start": m.session_start, "subagent-start": m.subagent_start,
        "sediment": m.sediment, "reindex": m.reindex, "list": m.list_,
        "maintain": m.maintain, "degrade": m.degrade,
        "archive": m.archive, "restore": m.restore, "restructure": m.restructure,
    }[cast(str, a.cmd)](a)
    DBG.log(f"✓ {a.cmd} 完成", style="bold green")


if __name__ == "__main__":
    main()
