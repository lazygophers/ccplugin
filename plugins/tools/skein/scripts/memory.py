#!/usr/bin/env python3
"""SKEIN 两层规则记忆 (基于 .claude/rules, 纯 stdlib)。

两层:
  core   — .claude/rules/core/*.md   每 session 常驻注入 (SessionStart hook → inject-core)
  recall — .claude/rules/recall/*.md 按需语义召回 (planning 时 recall <query> 粗筛, model 读全文)

每层维护 index.md 做检索目录; recall 检索必读 index (硬同步, 否则新规则漏检)。
写盘 (sediment) 由 skein-memory skill 在 AskUserQuestion 审批后调用。

命令:
  memory.py init
  memory.py inject-core                        输出全部 core 规则正文 (供 hook 注入)
  memory.py recall "<query>"                   grep recall/index.md, 输出命中行 (model 再读全文)
  memory.py sediment --layer core|recall --title T --keywords "a,b" \
            --source t01 --body-file /path      写规则 + 同步 index
  memory.py list [--layer core|recall]
"""
import argparse
import datetime
import re
import subprocess
import sys
from pathlib import Path

CORE_BUDGET = 8000  # core 常驻注入软预算 (字符); 超则告警


def now() -> str:
    return datetime.datetime.now().isoformat(timespec="seconds")


def rules_root() -> Path:
    r = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                       capture_output=True, text=True)
    base = Path(r.stdout.strip()) if r.returncode == 0 else Path.cwd()
    return base / ".claude" / "rules"


class Memory:
    def __init__(self):
        self.root = rules_root()

    def layer_dir(self, layer) -> Path:
        return self.root / layer

    def _index(self, layer) -> Path:
        return self.layer_dir(layer) / "index.md"

    # ---- init ----
    def init(self, _):
        for layer in ("core", "recall"):
            d = self.layer_dir(layer)
            d.mkdir(parents=True, exist_ok=True)
            idx = self._index(layer)
            if not idx.exists():
                idx.write_text(
                    f"# SKEIN {layer} 规则索引\n\n"
                    "| file | title | keywords | summary |\n"
                    "|---|---|---|---|\n")
        print(f"已初始化规则库: {self.root}")

    # ---- inject-core (常驻注入) ----
    def inject_core(self, _):
        d = self.layer_dir("core")
        if not d.exists():
            return
        parts = []
        for f in sorted(d.glob("*.md")):
            if f.name == "index.md":
                continue
            parts.append(_strip_frontmatter(f.read_text()).strip())
        text = "\n\n".join(p for p in parts if p)
        if len(text) > CORE_BUDGET:
            sys.stderr.write(
                f"⚠️ core 规则 {len(text)} 字符 > 预算 {CORE_BUDGET} — "
                "常驻注入过重, 考虑降级部分到 recall\n")
        sys.stdout.write(text)

    # ---- recall (按需粗筛) ----
    def recall(self, a):
        idx = self._index("recall")
        if not idx.exists():
            return
        terms = [t for t in re.split(r"\s+", a.query.lower()) if t]
        hits = []
        for line in idx.read_text().splitlines():
            if not line.startswith("| ") or line.startswith("| file") or "---" in line:
                continue
            if any(t in line.lower() for t in terms):
                hits.append(line)
        if hits:
            print("recall 命中 (model 读全文再定用否):")
            print("\n".join(hits))
        else:
            print("recall 无命中")

    # ---- sediment (写盘, 审批后调用) ----
    def sediment(self, a):
        layer = a.layer
        d = self.layer_dir(layer)
        d.mkdir(parents=True, exist_ok=True)
        seq = len([p for p in d.glob("*.md") if p.name != "index.md"])
        stem = f"{a.source or 'rule'}-{seq:02d}"
        f = d / f"{stem}.md"
        body = Path(a.body_file).read_text() if a.body_file else ""
        fm = (
            "---\n"
            f"title: {a.title}\n"
            f"layer: {layer}\n"
            f"keywords: [{a.keywords or ''}]\n"
            f"source: {a.source or '-'}\n"
            "authored-by: skein-memory\n"
            f"created: {now()}\n"
            "---\n\n"
        )
        f.write_text(fm + body.strip() + "\n")
        self._sync_index(layer, f.name, a.title, a.keywords or "", _summary(body))
        print(f"已沉淀 → {f}")

    def _sync_index(self, layer, fname, title, keywords, summary):
        idx = self._index(layer)
        if not idx.exists():
            self.init(None)
        row = f"| {fname} | {title} | {keywords} | {summary} |"
        lines = idx.read_text().splitlines()
        # 同名替换, 否则 append
        for i, ln in enumerate(lines):
            if ln.startswith(f"| {fname} |"):
                lines[i] = row
                break
        else:
            lines.append(row)
        idx.write_text("\n".join(lines) + "\n")

    # ---- list ----
    def list_(self, a):
        layers = [a.layer] if a.layer else ["core", "recall"]
        for layer in layers:
            d = self.layer_dir(layer)
            files = sorted(p.name for p in d.glob("*.md") if p.name != "index.md") if d.exists() else []
            print(f"[{layer}] {len(files)} 条: {', '.join(files) or '-'}")


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
    r = sub.add_parser("recall"); r.add_argument("query")
    s = sub.add_parser("sediment")
    s.add_argument("--layer", required=True, choices=["core", "recall"])
    s.add_argument("--title", required=True)
    s.add_argument("--keywords")
    s.add_argument("--source")
    s.add_argument("--body-file")
    ls = sub.add_parser("list"); ls.add_argument("--layer", choices=["core", "recall"])

    a = p.parse_args()
    m = Memory()
    {
        "init": m.init, "inject-core": m.inject_core, "recall": m.recall,
        "sediment": m.sediment, "list": m.list_,
    }[a.cmd](a)


if __name__ == "__main__":
    main()
