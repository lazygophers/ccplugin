#!/usr/bin/env python3
"""SKEIN 两层规则记忆 (基于 .skein/spec, 纯 stdlib)。

两层 × 类目:
  core   — .skein/spec/core/<类目>/*.md    每 session 常驻注入 (SessionStart hook → session-start)
  recall — .skein/spec/recall/<类目>/*.md  按需语义召回 (planning 时 recall <query> 粗筛, model 读全文)

类目 (category) 是层内子目录, 自由取名 (git/test/arch/build/style/domain/ops...), 按需建。
索引三份: 每层 <layer>/index.md (层内全规则) + 顶层 index.md (两层聚合概览)。
写盘 (sediment) 由 skein-memory skill 在判定门通过后自动调用 (不逐次询问用户), 写后自动 reindex。

命令:
  memory.py init
  memory.py inject-core                        输出全部 core 规则正文 (调试用)
  memory.py session-start                       SessionStart hook: 直接产 hook JSON 注入 core
  memory.py recall "<query>"                   grep recall/index.md, 输出命中行 (model 再读全文)
  memory.py sediment --layer core|recall --category git --title T \
            --keywords "a,b" --source t01 --body-file /path   写规则 + reindex
  memory.py reindex                            重扫两层重建全部 index
  memory.py list [--layer core|recall]
"""
from __future__ import annotations

import argparse
import time
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Optional, cast

CORE_BUDGET = 8000  # core 全文软预算 (字符, 供 inject-core 手动查看); 超则告警
INDEX_BUDGET_TOKENS = 400  # SessionStart 注入的极简索引 token 硬预算 (每条 1 行, 只 title+类目)
SUBAGENT_BUDGET_TOKENS = 2000  # SubagentStart 注入 core 全文 token 硬预算 (≈CORE_BUDGET 字符)
LAYERS = ("core", "recall")

sys.path.insert(0, str(Path(__file__).parent))  # 同目录 hooklib 可导入 (hook 环境非 Bash PATH)
from hooklib import budget_guard, Debug, debug_enabled  # noqa: E402

# agent 名 → core 类目白名单 (命中类目注全文, 其余仅索引); 空列表/缺项 → fallback 纯索引。
# ponytail: 静态表足够, 无需 per-agent 配置文件; 新增 agent 就地加一行。
AGENT_CATEGORIES: dict[str, list[str]] = {
    "skein-executor": ["script", "git"],
    "skein-checker": ["script"],
    "skein-researcher": ["script", "skill"],
    "skein-finisher": ["script", "git"],
    # setup/dedup/memorier 未列 → 默认 fallback 纯索引
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


def _cell(s: str) -> str:
    """索引表单元格: 空填 '-', 转义 '|' 免破坏 markdown 表格。"""
    return (s or "-").replace("|", "/")


class Memory:
    def __init__(self) -> None:
        self.root = spec_root()

    def layer_dir(self, layer: str) -> Path:
        return self.root / layer

    def _rule_files(self, layer: str) -> list[Path]:
        d = self.layer_dir(layer)
        if not d.exists():
            return []
        return sorted(p for p in d.rglob("*.md") if p.name != "index.md")

    def _next_seq(self, layer: str) -> int:
        # 层内已用最大序号 +1 (非文件计数): 删文件后不回退, 免覆盖已有规则
        used = [int(m.group(1)) for f in self._rule_files(layer)
                if (m := re.search(r"-(\d+)\.md$", f.name))]
        return max(used, default=-1) + 1

    # ---- init ----
    def init(self, _: argparse.Namespace) -> None:
        for layer in LAYERS:
            self.layer_dir(layer).mkdir(parents=True, exist_ok=True)
        self._reindex_all()
        print(f"已初始化 spec 库: {self.root}")

    # ---- core 正文 (供 inject-core / session-start 复用) ----
    def _core_text(self) -> str:
        parts = [_strip_frontmatter(f.read_text()).strip() for f in self._rule_files("core")]
        text = "\n\n".join(p for p in parts if p)
        if len(text) > CORE_BUDGET:
            sys.stderr.write(
                f"core 规则 {len(text)} 字符 > 预算 {CORE_BUDGET} — "
                "常驻注入过重, 考虑降级部分到 recall\n")
        return text

    # ---- inject-core (按需拉全文正文) ----
    def inject_core(self, _: argparse.Namespace) -> None:
        sys.stdout.write(self._core_text())

    # ---- core 极简索引 (每条 1 行: [类目] title) ----
    def _core_index(self) -> str:
        lines: list[str] = []
        for f in self._rule_files("core"):
            meta = _frontmatter(f.read_text())
            lines.append(f"- [{f.parent.name}] {meta.get('title', f.stem)}")
        return "\n".join(lines)

    # ---- session-start (SessionStart hook: 只注入极简索引, 全文按需 inject-core) ----
    def session_start(self, _: argparse.Namespace) -> None:
        idx = self._core_index().strip()
        if not idx:
            return
        ctx = budget_guard(
            "# SKEIN core 规则索引 (仅标题; 需全文跑 `memory.py inject-core`)\n\n" + idx,
            INDEX_BUDGET_TOKENS, "memory:session-start")
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
                "- 动手前: 相关约定先跑 `memory.py recall <关键词>` 拉 recall 层, 别凭记忆重推。\n"
                "- 命中 core 规则 (下列) 即硬约束, 违反视为未完成。\n"
                "- 踩到「后续同类任务会再犯」的坑 / 定下可复用约定: 在回传给 main 的摘要里标一行 `SPEC:` 供 finish sediment 落盘, 别让它随 worktree 销毁蒸发。\n")
        recall_tail = "\n## 需要其他类目全文? 跑 `memory.py recall <关键词>` 或 inject-core\n"
        cats = AGENT_CATEGORIES.get(_read_hook_stdin() or "", [])
        if cats:
            body = self._core_text_by_cat(cats).strip()
            ctx = head + f"\n## core 规则 (命中类目 {cats})\n\n{body}\n\n## 全量 core 索引\n\n{idx}{recall_tail}"
        else:  # 空映射/非 skein agent/stdin 失败 → 纯索引
            ctx = head + f"\n## core 索引 (全量; 需全文跑 recall/inject-core)\n\n{idx}{recall_tail}"
        ctx = budget_guard(ctx, SUBAGENT_BUDGET_TOKENS, "memory:subagent-start")
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "SubagentStart", "additionalContext": ctx}}))

    # ---- recall (按需粗筛) ----
    def recall(self, a: argparse.Namespace) -> None:
        idx = self.layer_dir("recall") / "index.md"
        if not idx.exists():
            print("recall 无命中")
            return
        query = cast(str, a.query)
        terms = [t for t in re.split(r"\s+", query.lower()) if t]
        hits = [ln for ln in idx.read_text().splitlines()
                if ln.startswith("| ") and not ln.startswith("| file")
                and any(t in ln.lower() for t in terms)]
        if hits:
            print("recall 命中 (model 读全文再定用否):")
            print("\n".join(hits))
        else:
            print("recall 无命中")

    # ---- sediment (写盘, 判定门通过后自动调用) ----
    def sediment(self, a: argparse.Namespace) -> None:
        layer = cast(str, a.layer)
        category = cast(Optional[str], getattr(a, "category", None))
        title = cast(str, a.title)
        keywords = cast(Optional[str], getattr(a, "keywords", None))
        source = cast(Optional[str], getattr(a, "source", None))
        body_file = cast(Optional[str], getattr(a, "body_file", None))
        cat = category or "misc"
        d = self.layer_dir(layer) / cat
        d.mkdir(parents=True, exist_ok=True)
        seq = self._next_seq(layer)  # 层内全局序号, 免跨类目撞名
        f = d / f"{source or 'rule'}-{seq:02d}.md"
        body = Path(body_file).read_text() if body_file else ""
        f.write_text(
            "---\n"
            f"title: {title}\n"
            f"layer: {layer}\n"
            f"category: {cat}\n"
            f"keywords: [{keywords or ''}]\n"
            f"source: {source or '-'}\n"
            "authored-by: skein-memory\n"
            f"created: {now()}\n"
            "---\n\n"
            + body.strip() + "\n")
        self._reindex_all()
        print(f"已沉淀 → {f}")

    # ---- reindex ----
    def reindex(self, _: argparse.Namespace) -> None:
        self._reindex_all()
        print(f"已重建索引: {self.root}")

    def _reindex_all(self) -> dict[str, dict[str, int]]:
        counts: dict[str, dict[str, int]] = {}
        for layer in LAYERS:
            counts[layer] = self._reindex_layer(layer)
        self._reindex_top(counts)
        return counts

    def _reindex_layer(self, layer: str) -> dict[str, int]:
        """重建 <layer>/index.md, 返回 {category: 条数}。"""
        d = self.layer_dir(layer)
        d.mkdir(parents=True, exist_ok=True)
        by_cat: dict[str, int] = {}
        rows: list[tuple[str, str, str, str, str]] = []
        for f in self._rule_files(layer):
            txt = f.read_text()
            meta = _frontmatter(txt)
            cat = f.parent.name  # 类目 = 所在目录 (物理事实), 免与 frontmatter 漂移
            rel = f.relative_to(d).as_posix()
            by_cat[cat] = by_cat.get(cat, 0) + 1
            rows.append((cat, rel, _cell(str(meta.get("title", ""))),
                         _cell(str(meta.get("keywords", ""))), _summary(txt)))
        rows.sort()
        body = "\n".join(f"| {rel} | {cat} | {title} | {kw} | {summ} |"
                         for cat, rel, title, kw, summ in rows)
        (d / "index.md").write_text(
            f"# SKEIN {layer} 规则索引\n\n"
            f"类目: {_dist(by_cat)}\n\n"
            "| file | category | title | keywords | summary |\n"
            "|---|---|---|---|---|\n"
            + (body + "\n" if body else ""))
        return by_cat

    def _reindex_top(self, counts: dict[str, dict[str, int]]) -> None:
        lines = ["# SKEIN 规则库总索引\n",
                 "两层: **core** 常驻注入 (SessionStart) · **recall** 按需召回 (planning `recall <query>`)。\n",
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
            print(f"已归档 {moved} 条规则 → {dest}\n回滚: python3 memory.py restore {ts}")
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

    # ---- list ----
    def list_(self, a: argparse.Namespace) -> None:
        layer_opt = cast(Optional[str], getattr(a, "layer", None))
        for layer in ([layer_opt] if layer_opt else list(LAYERS)):
            files = [f.relative_to(self.layer_dir(layer)).as_posix() for f in self._rule_files(layer)]
            print(f"[{layer}] {len(files)} 条: {', '.join(files) or '-'}")


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


def _summary(body: str) -> str:
    s = _strip_frontmatter(body).strip().replace("\n", " ")
    s = re.sub(r"[|]", "/", s)  # 免破坏表格
    return (s[:60] + "…") if len(s) > 60 else s or "-"


def main() -> None:
    p = argparse.ArgumentParser(
        prog="memory.py",
        description="SKEIN 两层规则记忆 (.skein/spec) — core 常驻 + recall 按需召回",
        epilog="用法: planning 时 recall 召回, task finish 时 sediment 沉淀",
    )
    p.add_argument("-d", "--debug", action="store_true",
                   help="rich 美化叙事到 stderr — 展示命令与参数 (stdout 保持机器纯净; 亦可 SKEIN_DEBUG=1)")
    sub = p.add_subparsers(dest="cmd", required=True, metavar="<command>")
    sub.add_parser("init", help="初始化 .skein/spec 库 (幂等)")
    sub.add_parser("inject-core", help="输出 core 层全部规则正文 (常驻注入)")
    sub.add_parser("session-start", help="[hook 用] 每 session 注入 core 规则索引")
    sub.add_parser("subagent-start", help="[hook 用] 每 subagent 注入 core 全文 + spec 纪律")
    sub.add_parser("reindex", help="重建三份 index.md (改盘后同步)")
    r = sub.add_parser("recall", help="按关键词 grep recall 索引, 输出命中行")
    r.add_argument("query", help="任务关键词")
    s = sub.add_parser("sediment", help="沉淀一条规则写盘 + 自动 reindex")
    s.add_argument("--layer", required=True, choices=list(LAYERS), help="core=常驻硬规 / recall=按需召回")
    s.add_argument("--category", help="类目子目录 (git/test/arch/build/style...)")
    s.add_argument("--title", required=True, help="规则标题")
    s.add_argument("--keywords", help="召回关键词, 逗号分隔")
    s.add_argument("--source", help="来源标记 (如 bootstrap)")
    s.add_argument("--body-file", help="规则正文文件路径")
    ls = sub.add_parser("list", help="列已存规则")
    ls.add_argument("--layer", choices=list(LAYERS), help="仅列指定层 (缺省列两层)")
    ar = sub.add_parser("archive", help="[完全重构前] 可逆归档旧规则到 .archive/<ts>/ + reindex 空")
    ar.add_argument("--layer", choices=list(LAYERS), help="仅归档指定层 (缺省两层全归档)")
    rs = sub.add_parser("restore", help="从归档恢复规则 (撞名不覆盖新规则, 加 restored- 前缀并存)")
    rs.add_argument("ts", help="归档时间戳 (archive 输出的目录名)")

    # --debug 可置子命令前后任意位置: 预剥离 argv (argparse 子解析器不认父级 flag)
    cli_debug = any(x in ("-d", "--debug") for x in sys.argv[1:])
    sys.argv[1:] = [x for x in sys.argv[1:] if x not in ("-d", "--debug")]
    a = p.parse_args()
    global DBG
    DBG = Debug(cli_debug or debug_enabled(None))
    DBG.rule(f"memory {a.cmd}")
    DBG.kv({k: v for k, v in vars(a).items() if k not in ("cmd", "debug") and v not in (None, False)},
           title="参数")
    m = Memory()
    {
        "init": m.init, "inject-core": m.inject_core, "recall": m.recall,
        "session-start": m.session_start, "subagent-start": m.subagent_start,
        "sediment": m.sediment, "reindex": m.reindex, "list": m.list_,
        "archive": m.archive, "restore": m.restore,
    }[cast(str, a.cmd)](a)
    DBG.log(f"✓ {a.cmd} 完成", style="bold green")


if __name__ == "__main__":
    main()
