#!/usr/bin/env python3
"""SKEIN 两层规则记忆 (基于 .claude/rules, 纯 stdlib)。

两层 × 类目:
  core   — .claude/rules/core/<类目>/*.md    每 session 常驻注入 (SessionStart hook → session-start)
  recall — .claude/rules/recall/<类目>/*.md  按需语义召回 (planning 时 recall <query> 粗筛, model 读全文)

类目 (category) 是层内子目录, 自由取名 (git/test/arch/build/style/domain/ops...), 按需建。
索引三份: 每层 <layer>/index.md (层内全规则) + 顶层 index.md (两层聚合概览)。
写盘 (sediment) 由 skein-memory skill 在 AskUserQuestion 审批后调用, 写后自动 reindex。

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
import argparse
import datetime
import json
import re
import subprocess
import sys
from pathlib import Path

CORE_BUDGET = 8000  # core 常驻注入软预算 (字符); 超则告警
LAYERS = ("core", "recall")


def now() -> str:
    return datetime.datetime.now().isoformat(timespec="seconds")


def _dist(by_cat: dict) -> str:
    """类目分布串 '类目(条数), ...', 空则 '-'。"""
    return ", ".join(f"{c}({n})" for c, n in sorted(by_cat.items())) or "-"


def rules_root() -> Path:
    try:
        r = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                           capture_output=True, text=True)
        base = Path(r.stdout.strip()) if r.returncode == 0 else Path.cwd()
    except FileNotFoundError:  # 无 git 二进制 → fallback cwd (设计意图: 非 git 也可用)
        base = Path.cwd()
    return base / ".claude" / "rules"


def _cell(s: str) -> str:
    """索引表单元格: 空填 '-', 转义 '|' 免破坏 markdown 表格。"""
    return (s or "-").replace("|", "/")


class Memory:
    def __init__(self):
        self.root = rules_root()

    def layer_dir(self, layer) -> Path:
        return self.root / layer

    def _rule_files(self, layer):
        d = self.layer_dir(layer)
        if not d.exists():
            return []
        return sorted(p for p in d.rglob("*.md") if p.name != "index.md")

    def _next_seq(self, layer) -> int:
        # 层内已用最大序号 +1 (非文件计数): 删文件后不回退, 免覆盖已有规则
        used = [int(m.group(1)) for f in self._rule_files(layer)
                if (m := re.search(r"-(\d+)\.md$", f.name))]
        return max(used, default=-1) + 1

    # ---- init ----
    def init(self, _):
        for layer in LAYERS:
            self.layer_dir(layer).mkdir(parents=True, exist_ok=True)
        self._reindex_all()
        print(f"已初始化规则库: {self.root}")

    # ---- core 正文 (供 inject-core / session-start 复用) ----
    def _core_text(self) -> str:
        parts = [_strip_frontmatter(f.read_text()).strip() for f in self._rule_files("core")]
        text = "\n\n".join(p for p in parts if p)
        if len(text) > CORE_BUDGET:
            sys.stderr.write(
                f"⚠️ core 规则 {len(text)} 字符 > 预算 {CORE_BUDGET} — "
                "常驻注入过重, 考虑降级部分到 recall\n")
        return text

    # ---- inject-core (常驻注入正文) ----
    def inject_core(self, _):
        sys.stdout.write(self._core_text())

    # ---- session-start (SessionStart hook: 直接产 hook JSON, 免 shell 包一层) ----
    def session_start(self, _):
        text = self._core_text().strip()
        if not text:
            return
        ctx = "# SKEIN 常驻规则 (core)\n\n" + text
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "SessionStart", "additionalContext": ctx}}))

    # ---- recall (按需粗筛) ----
    def recall(self, a):
        idx = self.layer_dir("recall") / "index.md"
        if not idx.exists():
            print("recall 无命中")
            return
        terms = [t for t in re.split(r"\s+", a.query.lower()) if t]
        hits = [ln for ln in idx.read_text().splitlines()
                if ln.startswith("| ") and not ln.startswith("| file")
                and any(t in ln.lower() for t in terms)]
        if hits:
            print("recall 命中 (model 读全文再定用否):")
            print("\n".join(hits))
        else:
            print("recall 无命中")

    # ---- sediment (写盘, 审批后调用) ----
    def sediment(self, a):
        cat = a.category or "misc"
        d = self.layer_dir(a.layer) / cat
        d.mkdir(parents=True, exist_ok=True)
        seq = self._next_seq(a.layer)  # 层内全局序号, 免跨类目撞名
        f = d / f"{a.source or 'rule'}-{seq:02d}.md"
        body = Path(a.body_file).read_text() if a.body_file else ""
        f.write_text(
            "---\n"
            f"title: {a.title}\n"
            f"layer: {a.layer}\n"
            f"category: {cat}\n"
            f"keywords: [{a.keywords or ''}]\n"
            f"source: {a.source or '-'}\n"
            "authored-by: skein-memory\n"
            f"created: {now()}\n"
            "---\n\n"
            + body.strip() + "\n")
        self._reindex_all()
        print(f"已沉淀 → {f}")

    # ---- reindex ----
    def reindex(self, _):
        self._reindex_all()
        print(f"已重建索引: {self.root}")

    def _reindex_all(self):
        counts = {}
        for layer in LAYERS:
            counts[layer] = self._reindex_layer(layer)
        self._reindex_top(counts)

    def _reindex_layer(self, layer) -> dict:
        """重建 <layer>/index.md, 返回 {category: 条数}。"""
        d = self.layer_dir(layer)
        d.mkdir(parents=True, exist_ok=True)
        by_cat = {}
        rows = []
        for f in self._rule_files(layer):
            txt = f.read_text()
            meta = _frontmatter(txt)
            cat = f.parent.name  # 类目 = 所在目录 (物理事实), 免与 frontmatter 漂移
            rel = f.relative_to(d).as_posix()
            by_cat[cat] = by_cat.get(cat, 0) + 1
            rows.append((cat, rel, _cell(meta.get("title", "")),
                         _cell(meta.get("keywords", "")), _summary(txt)))
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

    def _reindex_top(self, counts: dict):
        lines = ["# SKEIN 规则库总索引\n",
                 "两层: **core** 常驻注入 (SessionStart) · **recall** 按需召回 (planning `recall <query>`)。\n",
                 "| layer | 条数 | 类目分布 | 索引 |",
                 "|---|---|---|---|"]
        for layer in LAYERS:
            by_cat = counts.get(layer, {})
            total = sum(by_cat.values())
            lines.append(f"| {layer} | {total} | {_dist(by_cat)} | [{layer}/index.md]({layer}/index.md) |")
        (self.root / "index.md").write_text("\n".join(lines) + "\n")

    # ---- list ----
    def list_(self, a):
        for layer in ([a.layer] if a.layer else list(LAYERS)):
            files = [f.relative_to(self.layer_dir(layer)).as_posix() for f in self._rule_files(layer)]
            print(f"[{layer}] {len(files)} 条: {', '.join(files) or '-'}")


def _frontmatter(text: str) -> dict:
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    out = {}
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


def main():
    p = argparse.ArgumentParser(prog="memory.py")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init")
    sub.add_parser("inject-core")
    sub.add_parser("session-start")
    sub.add_parser("reindex")
    r = sub.add_parser("recall"); r.add_argument("query")
    s = sub.add_parser("sediment")
    s.add_argument("--layer", required=True, choices=list(LAYERS))
    s.add_argument("--category")
    s.add_argument("--title", required=True)
    s.add_argument("--keywords")
    s.add_argument("--source")
    s.add_argument("--body-file")
    ls = sub.add_parser("list"); ls.add_argument("--layer", choices=list(LAYERS))

    a = p.parse_args()
    m = Memory()
    {
        "init": m.init, "inject-core": m.inject_core, "recall": m.recall,
        "session-start": m.session_start,
        "sediment": m.sediment, "reindex": m.reindex, "list": m.list_,
    }[a.cmd](a)


if __name__ == "__main__":
    main()
