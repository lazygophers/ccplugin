#!/usr/bin/env python3
"""Scan a repo's .scratch directory and render a task-progress report.

Writes .scratch/progress.html — a single self-contained page, no network,
no build step. Open it directly in a browser.

Design: 晨雾企业台 admin console — light blue-white canvas, white cards, one
blue accent reserved for work you can start right now; hash-routed views so
every tab/menu item behaves like its own page. Numbers still state how they
were counted (see the 口径 note on the overview).

Usage: python3 tracking_progress.py [repo-root]
"""

from __future__ import annotations

import html
import os
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

# Directories under .scratch that never hold task state.
SKIP_DIRS = {"memory", "research", ".ask-me", "node_modules", ".git"}

# Files that are structural, not tasks — never reported as unrecognised.
KNOWN_FILENAMES = {"map.md", "memory.md", "spec.md", "readme.md"}

DONE_WORDS = (
    "resolved done closed completed complete fixed merged shipped wontfix "
    "won't-fix 已完成 完成 已解决 已合并 定稿 已抵达目的地 已交付 已归档"
).split()

ACTIVE_WORDS = (
    "claimed in-progress inprogress wip doing started 进行中 在跑 施工中 认领"
).split()

STALE_DAYS = 14
TIMELINE_LIMIT = 15

# Field lines appear bare (`Status: open`) or bold (`**Status:** open`).
# The value must stay on the same line — `\s` would cross the newline and
# swallow the next paragraph as a status ("Blocked by:" followed by an empty
# value used to read the quote underneath and mint phantom ticket ids).
_SAME_LINE = r"[^\S\n]*"
STATUS_RE = re.compile(
    rf"^\s*\**{_SAME_LINE}(?:Status|状态)\s*\**{_SAME_LINE}[:：][^\S\n]*([^\n]+?)\s*$",
    re.I | re.M,
)
TYPE_RE = re.compile(
    rf"^\s*\**{_SAME_LINE}(?:Type|类型)\s*\**{_SAME_LINE}[:：][^\S\n]*([^\n]+?)\s*$",
    re.I | re.M,
)
BLOCKED_RE = re.compile(
    rf"^\s*\**{_SAME_LINE}(?:Blocked by|Blocked-by|阻塞于|依赖于)\s*\**{_SAME_LINE}"
    r"[:：]?[^\S\n]*([^\n]*?)\s*$",
    re.I | re.M,
)
INLINE_BLOCKED_RE = re.compile(r"[（(](?:阻塞于|blocked by)[:：]?\s*([^）)]+)[）)]", re.I)
H1_RE = re.compile(r"^#\s+(.+?)\s*$", re.M)
CHECKBOX_RE = re.compile(r"^\s*[-*]\s*\[([ xX~/\-])\]\s*(.+?)\s*$")
# Leading ticket id inside a title: "01 — foo", "**I01** foo", "23: foo".
# Group 2 captures the separator + trailing whitespace: a bare number with no
# separator must be ≤2 digits AND space-separated to mint an id — that keeps
# map rows like "04 后续扩展" working while rejecting dates ("2026 年计划"),
# error codes ("404 页面修复") and "3rd-party API" (no whitespace at all).
LEAD_ID_RE = re.compile(r"^\**\s*([A-Za-z]{0,3}\d{1,4})\**((?:\s*[—\-·:：.、)])?\s*)(.*)$")
# Hyphen between prefix and digits stays part of the token, so "ADR-0046" and
# "ADR0046" normalise to the same "ADR46" instead of the hyphen dropping it.
ID_TOKEN_RE = re.compile(r"[A-Za-z]{0,3}-?\d{1,4}")
# Strip markdown emphasis only — `_` is part of identifiers like open_session.
MD_NOISE_RE = re.compile(r"[*`]")

DONE, ACTIVE, OPEN, BLOCKED = "done", "active", "open", "blocked"

# 「未完成」「无法完成」「取消完成」「not done」「unresolved」——
# 状态词前面带否定时，子串命中不算数。
NEGATION_RE = re.compile(r"未|不|没|无|非|勿|取消|无法|不能|暂停|not$|n't$|un$")

STATUS_LABEL = {DONE: "已完成", ACTIVE: "进行中", OPEN: "可开工", BLOCKED: "被阻塞"}

STATUS_CLASS = {DONE: "done", ACTIVE: "active", OPEN: "open", BLOCKED: "blocked"}

ROOT = "(根目录)"

PROGRESS = {OPEN: 0, BLOCKED: 0, ACTIVE: 1, DONE: 2}


@dataclass
class Task:
    effort: str
    tid: str
    title: str
    status: str
    blocked_by: list[str] = field(default_factory=list)
    kind: str = ""
    source: str = ""
    mtime: float = 0.0
    raw_status: str = ""
    from_file: bool = False
    # Derived in analyse(): dependency graph facts.
    deps: list[str] = field(default_factory=list)
    dangling: list[str] = field(default_factory=list)
    unlocks: int = 0
    depth: int = 0

    @property
    def key(self) -> str:
        """Identity for dedupe. Untitled checklist rows never collide."""
        return normalise_id(self.tid) if self.tid else f"@{self.source}:{self.title}"

    @property
    def label(self) -> str:
        return self.tid or "—"


@dataclass
class Effort:
    name: str
    path: Path
    is_map: bool = False
    has_spec: bool = False
    mtime: float = 0.0
    tasks: list[Task] = field(default_factory=list)
    # Derived: [(blocker_key, blocked_key)] edges among this effort's tickets.
    edges: list[tuple[str, str]] = field(default_factory=list)
    cycle_edges: list[tuple[str, str]] = field(default_factory=list)
    unknown_nodes: list[str] = field(default_factory=list)
    # spec 级 research/ 下的文档,页面只列链接不解析状态
    research: list[Path] = field(default_factory=list)


def negated(head: str, i: int) -> bool:
    """「未完成」「not done」:状态词前缀带否定时，子串命中不算数。"""
    before = head[max(0, i - 4) : i].rstrip()
    return bool(NEGATION_RE.search(before))


def classify(text: str) -> str:
    """Map a free-form status string onto done/active/open."""
    head = re.split(r"[·（(，,。]", MD_NOISE_RE.sub("", text or ""), maxsplit=1)[0]
    head = head.strip().lower()
    if not head:
        return OPEN
    for word in DONE_WORDS:
        i = head.find(word)
        if i >= 0 and not negated(head, i):
            return DONE
    for word in ACTIVE_WORDS:
        i = head.find(word)
        if i >= 0 and not negated(head, i):
            return ACTIVE
    return OPEN


def parse_ids(text: str) -> list[str]:
    """Pull ticket ids out of a 'Blocked by' value; '—' and 'none' mean empty."""
    cleaned = MD_NOISE_RE.sub("", text or "")
    # "None (can start immediately)" — parenthetical prose must not yield ids.
    cleaned = re.sub(r"[（(][^）)]*[）)]", "", cleaned).strip()
    if not cleaned or cleaned.lower() in {"—", "-", "–", "无", "none", "n/a", "nil"}:
        return []
    return [normalise_id(t) for t in ID_TOKEN_RE.findall(cleaned)]


def normalise_id(tid: str) -> str:
    """I01, i1 and I1 are the same ticket. T01 and 01 are not.

    The letter prefix is part of the identity: one effort can run two numbering
    schemes side by side (decision tickets `01..13` and impl tickets `T01..T11`),
    and collapsing them would merge unrelated work.
    """
    match = re.match(r"\s*([A-Za-z]*)-?0*(\d+)", tid or "")
    if not match:
        return (tid or "").strip().lower()
    return match.group(1).upper() + match.group(2)


def split_title(title: str) -> tuple[str, str]:
    """Return (id, remaining title) for '01 — foo'; id is '' when absent."""
    text = MD_NOISE_RE.sub("", title).strip()
    match = LEAD_ID_RE.match(text)
    if match and match.group(3):
        tid, gap = match.group(1), match.group(2)
        if tid.isdigit() and (not gap or len(tid) > 2):
            # 裸数字无分隔符:只在 ≤2 位且后随空白时算票号("04 后续扩展");
            # 日期("2026 年计划")、错误码("404 页面修复")、"3rd-party"不算
            return "", text
        return tid, match.group(3).strip()
    return "", text


def status_from_path(path: Path) -> str | None:
    parts = path.parts
    # 只看 .scratch 以下的段:克隆位置里带 open/done 字样的目录不能翻转判定
    if ".scratch" in parts:
        parts = parts[parts.index(".scratch") + 1 :]
    parts = {p.lower() for p in parts}
    if parts & {"done", "closed", "resolved", "completed", "已完成"}:
        return DONE
    if parts & {"open", "todo", "backlog", "待办"}:
        return OPEN
    return None


def parse_issue_file(path: Path, effort: str) -> Task | None:
    """Parse one ticket file. Returns None when no status can be determined."""
    text = path.read_text(encoding="utf-8", errors="replace")
    heading = H1_RE.search(text)
    title = heading.group(1) if heading else path.stem
    tid, rest = split_title(title)
    if not tid:
        tid, _ = split_title(path.stem)
    title = rest or path.stem

    raw = ""
    blocked = BLOCKED_RE.search(text)
    kind = TYPE_RE.search(text)
    status_match = STATUS_RE.search(text)
    if status_match:
        raw = status_match.group(1)
        status = classify(raw)
    else:
        # No Status line: fall back to the directory, then to the mere presence
        # of ticket fields — a `Blocked by:` header means this is a ticket, and
        # a ticket nobody marked done is not done.
        status = status_from_path(path)
        if status is None:
            if not (blocked or kind):
                return None
            status = OPEN
    return Task(
        effort=effort,
        tid=tid or path.stem,
        title=title,
        status=status,
        blocked_by=parse_ids(blocked.group(1)) if blocked else [],
        kind=MD_NOISE_RE.sub("", kind.group(1)).strip() if kind else "",
        source=str(path),
        mtime=path.stat().st_mtime,
        raw_status=raw,
        from_file=True,
    )


def parse_checklist_file(path: Path, effort: str) -> list[Task]:
    """Pull `- [x] ...` checkpoint lines out of memory.md / INDEX files."""
    tasks = []
    mtime = path.stat().st_mtime
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        match = CHECKBOX_RE.match(line)
        if not match:
            continue
        mark, body = match.group(1), match.group(2)
        if mark in "xX":
            status = DONE
        elif mark in "~/-":
            status = ACTIVE
        else:
            status = ACTIVE if any(w in body for w in ACTIVE_WORDS) else OPEN
        inline = INLINE_BLOCKED_RE.search(body)
        tid, rest = split_title(body)
        tasks.append(
            Task(
                effort=effort,
                tid=tid,
                title=(rest or body).strip(),
                status=status,
                blocked_by=parse_ids(inline.group(1)) if inline else [],
                source=str(path),
                mtime=mtime,
            )
        )
    return tasks


def iter_md(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            if name.endswith(".md"):
                yield Path(dirpath) / name


def scan(scratch: Path) -> tuple[list[Effort], list[Path]]:
    efforts: dict[str, Effort] = {}
    unparsed: list[Path] = []

    def effort_for(path: Path) -> Effort:
        rel = path.relative_to(scratch)
        name = rel.parts[0] if len(rel.parts) > 1 else ROOT
        base = scratch / rel.parts[0] if len(rel.parts) > 1 else scratch
        if name not in efforts:
            efforts[name] = Effort(name=name, path=base, mtime=base.stat().st_mtime)
        return efforts[name]

    for path in sorted(iter_md(scratch)):
        name = path.name.lower()
        effort = effort_for(path)
        if name == "map.md":
            effort.is_map = True
            # 地图行也要进任务集:还没建票面文件的条目靠它暴露为「未建票」
            effort.tasks.extend(parse_checklist_file(path, effort.name))
            continue
        if name == "spec.md":
            effort.has_spec = True
            continue
        # Ticket files live anywhere: issues/, impl/, or the effort root.
        if name not in KNOWN_FILENAMES:
            task = parse_issue_file(path, effort.name)
            if task:
                effort.tasks.append(task)
                continue
        found = parse_checklist_file(path, effort.name)
        if found:
            effort.tasks.extend(found)
        elif name not in KNOWN_FILENAMES and not path.stem.startswith("00"):
            # `00-INDEX.md` / `00-graph.md` are task indexes, not tasks.
            unparsed.append(path)

    absorb_root_checklist(efforts)
    for effort in efforts.values():
        # 顶层 .scratch/research/ 是跨项目历史,不进页;只有 spec 级 research/ 展示
        rdir = effort.path / "research"
        if effort.name != ROOT and rdir.is_dir():
            effort.research = sorted(rdir.glob("*.md"))
        effort.tasks = dedupe(effort.tasks)
        # analyse first: it splits blocked_by into real deps and dangling
        # refs, so blocking only counts ids that actually exist.
        analyse(effort)
        resolve_blocking(effort)
        if effort.name != ROOT:
            # spec 更新时间 = 整个文件夹(递归)里文件的最后写入时间
            effort.mtime = max(
                (p.stat().st_mtime for p in effort.path.rglob("*") if p.is_file()),
                default=effort.mtime,
            )
        elif effort.tasks:
            effort.mtime = max(effort.mtime, max(t.mtime for t in effort.tasks))

    # spec 按更新时间倒序,最近动过的排最前
    ordered = sorted(efforts.values(), key=lambda e: (-e.mtime, e.name))
    return [e for e in ordered if e.tasks or e.is_map or e.has_spec], unparsed


def dedupe(tasks: list[Task]) -> list[Task]:
    """One ticket often appears twice: as a file and as a checklist row.

    Keep the file (it carries the link and the blocking edges) but take the
    furthest-along status of the two — a ticket only ever moves forward.
    """
    merged: dict[str, Task] = {}
    for task in tasks:
        seen = merged.get(task.key)
        if seen is None:
            merged[task.key] = task
            continue
        winner = task if (task.from_file and not seen.from_file) else seen
        loser = seen if winner is task else task
        if PROGRESS[loser.status] > PROGRESS[winner.status]:
            winner.status = loser.status
        winner.blocked_by = winner.blocked_by or loser.blocked_by
        merged[task.key] = winner
    return list(merged.values())


def absorb_root_checklist(efforts: dict[str, Effort]) -> None:
    """The root `memory.md` mirrors a spec's tickets; don't count them twice.

    A root checklist row moves into the spec whose ticket files it matches, but
    only when exactly one spec claims that id — an ambiguous match stays put.
    """
    root = efforts.get(ROOT)
    if root is None:
        return
    owners: dict[str, list[Effort]] = {}
    for effort in efforts.values():
        if effort.name == ROOT:
            continue
        for task in effort.tasks:
            if task.from_file:
                owners.setdefault(task.key, []).append(effort)
    kept = []
    for task in root.tasks:
        claimants = owners.get(task.key, [])
        if len(claimants) == 1:
            task.effort = claimants[0].name
            claimants[0].tasks.append(task)
        else:
            kept.append(task)
    root.tasks = kept


def resolve_blocking(effort: Effort) -> None:
    done_ids = {t.key for t in effort.tasks if t.status == DONE}
    for task in effort.tasks:
        if task.status == OPEN and any(d not in done_ids for d in task.deps):
            task.status = BLOCKED


def analyse(effort: Effort) -> None:
    """Turn blocked_by into graph facts: real deps, dangling refs, depths.

    A blocking id nobody owns is *dangling* — usually a document reference
    (`ADR-0046`) that got minted into a ticket id. It does not block anything
    and the report shows it, because a silent wrong edge is worse than a
    visible odd one.
    """
    by_key = {t.key: t for t in effort.tasks if t.tid}
    for task in effort.tasks:
        task.deps = []
        task.dangling = []
        for raw in task.blocked_by:
            target = by_key.get(raw)
            if target is not None and target is not task:
                task.deps.append(target.key)
            elif target is None:
                task.dangling.append(raw)
        task.unlocks = 0

    for task in effort.tasks:
        for dep in task.deps:
            by_key[dep].unlocks += 1

    effort.edges = [(dep, task.key) for task in effort.tasks for dep in task.deps]

    # Depth = longest chain of blockers, cycles cut on revisit.
    depth: dict[str, int] = {}
    state: dict[str, int] = {}

    def visit(key: str) -> int:
        if key in depth:
            return depth[key]
        if state.get(key) == 1:
            return 0  # cycle: cut here, the edge gets flagged below
        state[key] = 1
        deepest = 0
        for dep in by_key[key].deps:
            deepest = max(deepest, visit(dep) + 1)
        state[key] = 2
        depth[key] = deepest
        return deepest

    for key in by_key:
        visit(key)
    for task in effort.tasks:
        task.depth = depth.get(task.key, 0)

    # An edge that does not advance a layer is part of a cycle.
    effort.cycle_edges = [
        (a, b) for a, b in effort.edges if depth.get(a, 0) >= depth.get(b, 0)
    ]
    effort.unknown_nodes = sorted(
        {raw for t in effort.tasks for raw in t.dangling}
    )


# ────────────────────────────── rendering ──────────────────────────────

# Flowchart-only mermaid build (katex/cytoscape stubbed out), inlined into the
# page so it stays self-contained and offline. Rebuild:
#   npm i mermaid@11 esbuild && esbuild entry.mjs --bundle --minify --format=iife \
#     --global-name=mermaid --alias:katex=stub.js --alias:cytoscape=stub.js \
#     [--external every non-flowchart diagram chunk]
MERMAID_JS = (Path(__file__).parent / "mermaid.flow.min.js").read_text(encoding="utf-8")

CSS = """
  :root{
    --ink:#1C2B3A; --ink-2:#5B6E82; --ink-3:#93A5B8;
    --rule:#E3EBF4; --rule-2:#EDF2F8;
    --open:#1D4FD7; --open-fill:#2563EB;
    --active:#B45309; --active-fill:#D97706;
    --blocked:#A16207; --blocked-fill:#D97706;
    --done:#14945B; --done-fill:#16A34A;
    --bg:#F3F7FC; --panel:#FFFFFF; --gap:#F3F7FC; --nav-bg:#FFFFFF; --row-hover:#F8FAFD;
    --underline:rgba(37,99,235,.3); --danger:#D6455D;
    --blue:#2563EB; --blue-2:#1D4FD7; --blue-soft:#EAF0FE;
    --amber-soft:#FBF0DE; --green-soft:#E5F5EC; --gray-soft:#EEF2F7;
    --sh-1:0 1px 2px rgba(28,43,58,.05),0 1px 3px rgba(28,43,58,.06);
    --sh-2:0 10px 28px -10px rgba(28,43,58,.16);
    --sans:-apple-system,BlinkMacSystemFont,"PingFang SC","Noto Sans CJK SC","Hiragino Sans GB",sans-serif;
    --mono:"Maple Mono","JetBrains Mono",ui-monospace,"SF Mono",Menlo,Consolas,monospace;
    color-scheme:light;
  }
  :root[data-theme=dark]{
    --ink:#d7dce1; --ink-2:#9aa4ae; --ink-3:#737d87;
    --rule:#2b3138; --rule-2:#232830;
    --open:#6aa5e3; --open-fill:#2f6fb5;
    --active:#d9a35f; --active-fill:#b5813a;
    --blocked:#c98a80; --blocked-fill:#8f5348;
    --done:#7fae8b; --done-fill:#4a6b52; --bg:#141719;
    --panel:#1a1e22; --gap:#141719; --nav-bg:rgba(20,23,25,.96); --row-hover:#1d2227;
    --underline:rgba(106,165,227,.4); --danger:#e0796c;
    --blue:#60A5FA; --blue-2:#93C5FD; --blue-soft:rgba(47,111,181,.18);
    --amber-soft:rgba(181,129,58,.15); --green-soft:rgba(74,107,82,.2); --gray-soft:rgba(154,164,174,.12);
    --sh-1:none; --sh-2:none;
    color-scheme:dark;
  }
  *{box-sizing:border-box}
  html{scroll-behavior:smooth;scroll-padding-top:118px}
  body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.6 var(--sans);-webkit-font-smoothing:antialiased}
  body::before{content:"";position:fixed;inset:0;pointer-events:none;z-index:0;
    background:radial-gradient(1000px 520px at 18% -10%,rgba(37,99,235,.07),transparent 60%),
               radial-gradient(760px 420px at 90% 0%,rgba(96,165,250,.08),transparent 55%)}
  a{color:var(--open);text-decoration:none;border-bottom:1px solid var(--underline)}
  a:hover{border-bottom-color:var(--open)}
  svg{flex-shrink:0}
  .app{position:relative;z-index:1;display:grid;grid-template-columns:236px minmax(0,1fr);min-height:100vh}
  .side{background:var(--nav-bg);border-right:1px solid var(--rule);display:flex;flex-direction:column;
    position:sticky;top:0;height:100vh;overflow-y:auto;padding:14px 12px;z-index:21}
  .side .workspace{display:flex;align-items:center;gap:10px;padding:6px 8px 14px;border-bottom:1px solid var(--rule);margin-bottom:12px}
  .side .mark{width:32px;height:32px;border-radius:9px;background:linear-gradient(135deg,#3B82F6,#1D4FD7);
    color:#fff;display:grid;place-items:center;font:700 13px var(--mono);box-shadow:0 4px 10px rgba(37,99,235,.35);flex-shrink:0}
  .side .ws{font:600 13.5px var(--sans);line-height:1.35;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .side .ws span{display:block;font:400 11px var(--mono);color:var(--ink-3)}
  .navcap{font:600 10.5px/1 var(--sans);letter-spacing:.08em;color:var(--ink-3);padding:14px 10px 6px;
    display:flex;align-items:center;cursor:pointer;user-select:none;border:0;background:none;width:100%;text-align:left}
  .navcap .chev{width:11px;height:11px;margin-left:auto;transition:transform .18s}
  .navcap.closed .chev{transform:rotate(-90deg)}
  .nav .grp{display:flex;flex-direction:column}
  .navcap.closed+.grp{display:none}
  .nav{display:flex;flex-direction:column}
  .nav a{display:flex;align-items:center;gap:10px;padding:7.5px 10px;border-radius:8px;
    color:var(--ink-2);font:500 13.5px var(--sans);transition:background .14s,color .14s}
  .nav a svg{width:17px;height:17px}
  .nav a:hover{background:var(--row-hover);color:var(--ink)}
  .nav a.on{background:var(--blue-soft);color:var(--blue-2);font-weight:600}
  .nav .cnt{margin-left:auto;font:600 11px var(--mono);color:var(--ink-3);background:var(--gray-soft);
    border-radius:99px;padding:1.5px 7px}
  .nav a.on .cnt{background:rgba(37,99,235,.14);color:var(--blue-2)}
  .nav .proj{padding-left:26px;position:relative}
  .nav .proj::before{content:"";position:absolute;left:16px;top:0;bottom:0;width:1.5px;background:var(--rule)}
  .nav .proj a{padding:5.5px 10px;font-size:13px;min-width:0}
  .nav .proj .nm{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .nav .proj .mini{margin-left:auto;width:40px;height:3px;border-radius:2px;background:var(--gray-soft);
    overflow:hidden;flex-shrink:0;border:1px solid var(--rule-2)}
  .nav .proj .mini i{display:block;height:100%;background:var(--open-fill)}
  .nav .soon{display:flex;align-items:center;gap:10px;padding:7.5px 10px;color:var(--ink-3);font:500 13px var(--sans)}
  .nav .soon .soon-tag{margin-left:auto;font:600 10px var(--mono);color:var(--ink-3);
    border:1px dashed var(--rule);border-radius:99px;padding:2px 7px;white-space:nowrap}
  .side .foot{margin-top:auto;border-top:1px solid var(--rule);padding:12px 8px 4px;display:flex;align-items:center;gap:10px}
  .side .foot .ava{width:30px;height:30px;border-radius:50%;background:linear-gradient(135deg,#60A5FA,#2563EB);
    color:#fff;display:grid;place-items:center;font:600 12px var(--sans);flex-shrink:0}
  .side .foot .who{font:600 12.5px var(--sans);min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .side .foot .who span{display:block;font:400 11px var(--mono);color:var(--ink-3)}
  .right{min-width:0;display:flex;flex-direction:column}
  .top{display:flex;align-items:center;gap:14px;padding:10px 24px;border-bottom:1px solid var(--rule);
    background:var(--nav-bg);position:sticky;top:0;z-index:20}
  .crumb{font:500 13px var(--sans);color:var(--ink-3);white-space:nowrap}
  .crumb b{color:var(--ink);font-weight:600}
  .search{margin-left:auto;display:flex;align-items:center;gap:9px;height:34px;min-width:min(340px,38vw);
    background:var(--row-hover);border:1px solid var(--rule);border-radius:8px;padding:0 12px;
    color:var(--ink-3);font:400 13px var(--sans);cursor:text;transition:border-color .18s,box-shadow .18s}
  .search:focus-within{background:var(--panel);border-color:var(--open);box-shadow:0 0 0 3px rgba(37,99,235,.12)}
  .search svg{opacity:.7}
  .search kbd{font:600 10.5px var(--mono);color:var(--ink-3);background:var(--panel);
    border:1px solid var(--rule);border-radius:5px;padding:2px 5px}
  .search input{all:unset;flex:1;min-width:0;font:400 13px var(--sans);color:var(--ink)}
  .search input::placeholder{color:var(--ink-3)}
  .pagebar{background:var(--nav-bg);border-bottom:1px solid var(--rule);padding:18px 24px 0;position:sticky;top:55px;z-index:19}
  .pagebar .row{display:flex;align-items:center;gap:14px;max-width:1240px;margin:0 auto}
  .pagebar h1{font:700 20px/1.3 var(--sans);letter-spacing:-.3px;margin:0;display:flex;align-items:center;gap:10px}
  .pagebar .scope{font:500 11px var(--mono);color:var(--ink-2);background:var(--row-hover);
    border:1px solid var(--rule);border-radius:99px;padding:3px 10px;font-weight:500;white-space:nowrap}
  .pagebar .acts{margin-left:auto;display:flex;gap:8px}
  .btn{display:inline-flex;align-items:center;gap:7px;height:32px;padding:0 13px;border-radius:8px;
    border:1px solid var(--rule);background:var(--panel);color:var(--ink);font:600 12.5px var(--sans);
    cursor:pointer;transition:box-shadow .15s,border-color .15s}
  .btn:hover{box-shadow:var(--sh-1);border-color:var(--ink-3)}
  .btn.primary{background:var(--open);border-color:var(--open);color:#fff}
  .btn.primary:hover{background:var(--blue-2)}
  .pagebar .tabs{display:flex;gap:20px;max-width:1240px;margin:12px auto 0;overflow-x:auto}
  .pagebar .tabs a{display:flex;align-items:center;gap:7px;padding:9px 0 11px;font:500 13px var(--sans);
    color:var(--ink-2);border-bottom:2px solid transparent;margin-bottom:-1px;transition:color .13s;white-space:nowrap}
  .pagebar .tabs a:hover{color:var(--ink)}
  .pagebar .tabs a.on{color:var(--ink);border-color:var(--open);font-weight:600}
  .pagebar .tabs a .n{font:500 10.5px var(--mono);color:var(--ink-3);background:var(--gray-soft);
    border-radius:99px;padding:1px 6px}
  .pagebody{max-width:1240px;width:100%;margin:0 auto;padding:20px 24px 70px;position:relative;z-index:1}
  /* 入场编排 */
  .rise{opacity:0;transform:translateY(10px);animation:tprise .55s cubic-bezier(.22,.9,.3,1) forwards}
  @keyframes tprise{to{opacity:1;transform:none}}
  .d1{animation-delay:.04s}.d2{animation-delay:.1s}.d3{animation-delay:.16s}.d4{animation-delay:.22s}.d5{animation-delay:.28s}
  @media (prefers-reduced-motion:reduce){.rise{animation:none;opacity:1;transform:none}}
  .focus{display:flex;align-items:center;gap:13px;background:linear-gradient(90deg,var(--blue-soft),rgba(234,240,254,.35));
    border:1px solid var(--rule);border-radius:12px;padding:12px 18px;margin-bottom:16px}
  :root[data-theme=dark] .focus{background:var(--blue-soft)}
  .focus .pulse{width:9px;height:9px;border-radius:50%;background:var(--open-fill);flex-shrink:0;
    box-shadow:0 0 0 0 rgba(37,99,235,.4);animation:pulse 2s infinite}
  @keyframes pulse{70%{box-shadow:0 0 0 9px rgba(37,99,235,0)}100%{box-shadow:0 0 0 0 rgba(37,99,235,0)}}
  .focus .ft{font:600 13.5px/1.55 var(--sans)}
  .focus .ft em{font-style:normal;color:var(--blue-2)}
  .focus .btn{flex-shrink:0;margin-left:auto}
  .kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:16px}
  .kpi{background:var(--panel);border:1px solid var(--rule);border-radius:12px;padding:14px 16px;
    box-shadow:var(--sh-1);transition:transform .2s,box-shadow .2s}
  .kpi:hover{transform:translateY(-2px);box-shadow:var(--sh-2)}
  .kpi .k{display:flex;align-items:center;gap:7px;font:500 12.5px var(--sans);color:var(--ink-2)}
  .kpi .k i{width:8px;height:8px;border-radius:3px}
  .kpi .v{font:700 26px/1.3 var(--sans);letter-spacing:-.5px;margin-top:4px;font-variant-numeric:tabular-nums}
  .kpi .v small{font:500 12px var(--sans);color:var(--ink-3);letter-spacing:0;margin-left:5px;font-weight:500}
  .kpi .meter{height:4px;border-radius:99px;background:var(--gray-soft);margin-top:9px;overflow:hidden}
  .kpi .meter i{display:block;height:100%;border-radius:99px;width:0;animation:metergrow 1s .4s cubic-bezier(.22,.9,.3,1) forwards}
  @keyframes metergrow{to{width:var(--w)}}
  section{padding:26px 0;border-top:1px solid var(--rule)}
  section:first-of-type{border-top:0}
  /* hash 路由视图:每个 tab/菜单项是独立页面,同一时刻只显示一个 */
  .view{display:none}
  .view.on{display:block}
  h2{font:600 16px/1.4 var(--sans);margin:0 0 4px;display:flex;align-items:center;gap:10px;flex-wrap:wrap}
  .sub{font-size:13px;color:var(--ink-2);margin:0 0 16px;max-width:64em}
  .note{font-size:12.5px;line-height:1.7;color:var(--ink-2);margin:14px 0 0;padding:12px 14px;
    background:var(--panel);border:1px solid var(--rule);border-radius:10px}
  .note b{color:var(--ink);font-weight:600}
  .note code{font:12px var(--mono)}
  .badge{font:600 11px var(--mono);color:var(--blue-2);background:var(--blue-soft);border-radius:99px;padding:2px 9px}
  .panel{background:var(--panel);border:1px solid var(--rule);border-radius:12px;box-shadow:var(--sh-1);overflow:hidden}
  .statline{display:flex;flex-wrap:wrap;gap:0 26px;margin:0 0 14px;font-size:13px;color:var(--ink-2)}
  .statline span{font:600 13.5px var(--mono);color:var(--ink)}
  .stack{display:flex;height:30px;width:100%;border:1px solid var(--rule);background:var(--panel);border-radius:8px;overflow:hidden}
  .stack i{display:block;height:100%}
  .stack i+i{border-left:1px solid var(--gap)}
  .ticks{display:flex;width:100%;margin-top:0}
  .tick{position:relative;padding:9px 0 0}
  .tick::before{content:"";position:absolute;left:0;top:0;width:1px;height:7px;background:var(--rule)}
  .tick .k{display:block;font:600 12.5px/1.3 var(--sans);padding-left:8px;white-space:nowrap}
  .tick .v{display:block;font:11px/1.4 var(--mono);color:var(--ink-2);padding-left:8px;white-space:nowrap}
  .tick.low{padding-top:50px}
  .tick.low::before{height:48px}
  .k-done{color:var(--ink-3)} .k-active{color:var(--active)} .k-open{color:var(--open)} .k-blocked{color:var(--blocked)}
  table{width:100%;border-collapse:collapse;font-size:13.5px}
  th{text-align:left;font:500 11px/1.4 var(--mono);color:var(--ink-3);letter-spacing:.05em;padding:9px 12px 9px 0;
    border-bottom:1px solid var(--rule);white-space:nowrap;text-transform:uppercase;background:transparent}
  th.num,td.num{text-align:right;padding-right:14px}
  td{padding:10px 12px 10px 0;border-bottom:1px solid var(--rule-2);vertical-align:middle}
  tr:hover td{background:var(--row-hover)}
  td.lbl{font:600 12px var(--mono);color:var(--ink-2);white-space:nowrap;width:44px}
  td.spec{font:600 12px var(--mono);color:var(--ink-2);white-space:nowrap;width:130px}
  td.t{max-width:0;width:100%}
  td.t a{display:inline-block;max-width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;vertical-align:bottom}
  td.meta{font:12px var(--mono);color:var(--ink-2);white-space:nowrap}
  .st{display:inline-flex;align-items:center;gap:6px;height:21px;padding:0 9px;border-radius:99px;font:600 11.5px/1 var(--sans);white-space:nowrap}
  .st::before{content:"";width:6px;height:6px;border-radius:50%;background:currentColor;opacity:.85}
  .st-open{color:var(--open);background:var(--blue-soft)}
  .st-active{color:var(--active);background:var(--amber-soft)}
  .st-blocked{color:var(--blocked);background:var(--amber-soft)}
  .st-done{color:var(--done);background:var(--green-soft)}
  tr.r-done td.t a{color:var(--ink-2)}
  tr.r-done td.lbl{color:var(--ink-3)}
  .unlocks{font:600 13px var(--mono);color:var(--open)}
  .unlocks-0{font:13px var(--mono);color:var(--ink-3);font-weight:400}
  .spec-head{display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin:26px 0 6px;padding:12px 16px;
    background:var(--panel);border:1px solid var(--rule);border-radius:12px 12px 0 0;border-bottom:0}
  .spec-head h3{font:600 15px/1.3 var(--sans);margin:0;display:flex;align-items:center}
  .spec-head h3:focus-within button.copy-btn{outline:2px solid var(--open);outline-offset:3px}
  .spec-head h3 a{color:inherit;border-bottom:1px dotted var(--rule)}
  .spec-head h3 a:hover{color:var(--open);border-bottom-color:var(--open)}
  .share-wrap{position:relative;display:inline-block;margin-left:8px}
  .share-btn{font:600 11px/1 var(--mono);color:var(--ink-3);background:none;border:1px solid var(--rule);border-radius:99px;padding:3px 9px;cursor:pointer}
  .share-btn:hover{color:var(--open);border-color:var(--open)}
  .share-menu{display:none;position:absolute;top:calc(100% + 4px);left:0;background:var(--panel);border:1px solid var(--rule);border-radius:8px;padding:4px;z-index:40;min-width:130px;box-shadow:var(--sh-2)}
  .share-wrap.open .share-menu,.share-wrap:focus-within .share-menu{display:flex;flex-direction:column}
  .share-menu button{all:unset;font:600 12px/1 var(--sans);color:var(--ink);padding:7px 10px;border-radius:5px;cursor:pointer;white-space:nowrap}
  .share-menu button:hover{background:var(--row-hover);color:var(--open)}
  .mmd .share-wrap{position:absolute;right:52px;top:0;margin:0}
  .toast{position:fixed;left:50%;bottom:28px;transform:translateX(-50%);background:var(--ink);color:#fff;border:0;border-radius:8px;padding:9px 16px;font:600 13px var(--sans);opacity:0;transition:opacity .2s;z-index:60;pointer-events:none}
  .toast.show{opacity:1}
  .toast.err{background:var(--danger)}
  .copy-btn{font:inherit;line-height:1;color:var(--ink-3);background:none;border:0;padding:0 0 0 5px;cursor:pointer;vertical-align:-1px}
  .copy-btn:hover{color:var(--open)}
  .copy-btn svg{display:block}
  .copy-btn.copied{color:var(--open);font:600 12px/1 var(--sans)}
  .spec-head .kind{font-size:12px;color:var(--ink-2);border:1px solid var(--rule);padding:2px 8px;border-radius:99px;text-decoration:none;background:var(--row-hover)}
  .spec-head a.kind:hover{color:var(--open);border-color:var(--open)}
  .spec-head .cnt{font-size:12px;color:var(--ink-2);margin-left:auto;font-family:var(--mono);white-space:nowrap}
  .spec-head .kind.tbd{color:var(--active);border-color:var(--active);background:var(--amber-soft)}
  .spec-head .kind.ok{color:var(--done);border-color:var(--done);background:var(--green-soft)}
  .tbdmark{font-style:normal;font-size:11px;color:var(--active);border:1px solid var(--active);border-radius:4px;padding:0 3px;margin-left:4px}
  .minibar{display:flex;height:8px;width:100%;margin:0 0 0;background:var(--row-hover);border:1px solid var(--rule-2);border-radius:0 0 0 0;overflow:hidden}
  .minibar i{display:block;height:100%}
  .minibar i+i{border-left:1px solid var(--gap)}
  .minicap{display:flex;justify-content:space-between;gap:10px;font:12px var(--mono);color:var(--ink-2);
    padding:8px 16px;background:var(--panel);border:1px solid var(--rule);border-top:0}
  .mmd{margin:0;text-align:center;font:12px/1.5 var(--mono);overflow-x:auto;position:relative;
    background:var(--panel);border:1px solid var(--rule);border-top:0;padding:14px 8px 18px}
  .minicap+.mmd{border-top:0}
  .mmd svg text,#mmdStage svg text{font-weight:600}
  .mmd svg{max-width:100%}
  .mmd-zoom{position:absolute;right:0;top:0;font:600 11px/1 var(--sans);color:var(--ink-2);background:var(--panel);border:1px solid var(--rule);border-radius:4px;padding:4px 8px;cursor:pointer;z-index:2}
  .mmd-zoom:hover{color:var(--open);border-color:var(--open)}
  .mmd button.mmd-zoom:nth-of-type(1){right:0}
  .mmd button.mmd-zoom:nth-of-type(2){right:58px}
  .mmd button.mmd-zoom:nth-of-type(3){right:122px}
  .mmd-viewer{position:fixed;inset:0;z-index:50;background:color-mix(in srgb,var(--bg) 92%,transparent);backdrop-filter:blur(4px);display:none;align-items:center;justify-content:center;flex-direction:column;gap:10px}
  .mmd-viewer.open{display:flex}
  .mmd-viewer .stage{flex:1;width:100%;overflow:hidden;cursor:grab;touch-action:none}
  .mmd-viewer .stage.dragging{cursor:grabbing}
  .mmd-viewer svg{max-width:none;transform-origin:0 0}
  .mmd-viewer .hint{font:12px var(--sans);color:var(--ink-2);padding:10px 0 14px}
  .mmd-viewer .close{position:absolute;right:18px;top:14px;font:600 12px/1 var(--sans);color:var(--ink-2);background:var(--panel);border:1px solid var(--rule);border-radius:99px;padding:6px 13px;cursor:pointer}
  .mmd-viewer .close:hover{color:var(--open);border-color:var(--open)}
  .mmd path.flowchart-link,.mmd-viewer path.flowchart-link{stroke:var(--ink-3)!important}
  .mmd marker path,.mmd-viewer marker path{fill:var(--ink-3)!important;stroke:var(--ink-3)!important}
  .mmd .edgeLabel,.mmd-viewer .edgeLabel,.mmd .edgeLabel text,.mmd-viewer .edgeLabel text{fill:var(--ink-2)}
  .empty{font-size:13px;color:var(--ink-2);padding:14px 16px;border:1.5px dashed var(--rule);border-radius:10px;display:flex;gap:9px;align-items:center}
  .empty .ok{color:var(--done);font-weight:700}
  .docrow{display:flex;align-items:center;gap:11px;padding:10px 4px;border-bottom:1px solid var(--rule-2);
    color:var(--ink);transition:background .12s}
  .docrow:hover{background:var(--row-hover)}
  .docrow .ico{width:30px;height:30px;border-radius:8px;display:grid;place-items:center;flex-shrink:0;
    font:700 10px var(--mono);background:var(--green-soft);color:var(--done)}
  .docrow .ico.res{background:var(--amber-soft);color:var(--active)}
  .docrow .t{font:600 13.5px var(--sans);line-height:1.35;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .docrow .m{font:400 11.5px var(--mono);color:var(--ink-3)}
  .docrow .sz{margin-left:auto;font:500 11.5px var(--mono);color:var(--ink-3);white-space:nowrap}
  .filelist{list-style:none;margin:14px 0 0;padding:0}
  .filelist li{font:13px var(--mono);padding:8px 0;border-bottom:1px solid var(--rule-2)}
  footer{border-top:1px solid var(--rule);margin-top:34px;padding:20px 0 10px;font-size:12.5px;line-height:1.75;color:var(--ink-2)}
  .theme-btn{position:fixed;right:18px;top:11px;z-index:30;font:600 12px/1 var(--sans);color:var(--ink-2);background:var(--panel);border:1px solid var(--rule);border-radius:99px;padding:7px 13px;cursor:pointer;box-shadow:var(--sh-1)}
  .theme-btn:hover{color:var(--open);border-color:var(--open)}
  .dangling{color:var(--danger)}
  /* 页内文件预览 */
  .pv-wrap{position:fixed;inset:0;z-index:55;background:color-mix(in srgb,var(--bg) 75%,transparent);
    backdrop-filter:blur(4px);display:none;align-items:stretch;justify-content:flex-end}
  .pv-wrap.open{display:flex}
  .pv-card{width:min(880px,94vw);background:var(--panel);border-left:1px solid var(--rule);
    box-shadow:-18px 0 50px rgba(28,43,58,.18);display:flex;flex-direction:column;
    animation:pvslide .28s cubic-bezier(.22,.9,.3,1)}
  @keyframes pvslide{from{transform:translateX(40px);opacity:0}to{transform:none;opacity:1}}
  .pv-head{display:flex;align-items:center;gap:12px;padding:13px 20px;border-bottom:1px solid var(--rule);flex-shrink:0}
  .pv-head .t{font:600 14px var(--mono);min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .pv-head .raw{font:500 12px var(--sans);color:var(--ink-2);white-space:nowrap}
  .pv-head .close{margin-left:auto;font:600 12px/1 var(--sans);color:var(--ink-2);background:var(--panel);
    border:1px solid var(--rule);border-radius:99px;padding:6px 13px;cursor:pointer;flex-shrink:0}
  .pv-head .close:hover{color:var(--open);border-color:var(--open)}
  .pv-body{flex:1;overflow-y:auto;padding:26px 30px 50px;font:14px/1.75 var(--sans);color:var(--ink)}
  .pv-body h1,.pv-body h2,.pv-body h3,.pv-body h4{font:600 20px/1.4 var(--sans);margin:22px 0 8px;letter-spacing:-.2px}
  .pv-body h1{font-size:24px}.pv-body h2{font-size:19px}.pv-body h3{font-size:16px}.pv-body h4{font-size:14px;color:var(--ink-2)}
  .pv-body h1:first-child,.pv-body h2:first-child,.pv-body h3:first-child{margin-top:0}
  .pv-body p{margin:10px 0}
  .pv-body ul,.pv-body ol{margin:10px 0;padding-left:24px}
  .pv-body li{margin:3px 0}
  .pv-body li input[type=checkbox]{margin-right:7px;vertical-align:-1px}
  .pv-body code{font:12.5px var(--mono);background:var(--gray-soft);border:1px solid var(--rule-2);
    border-radius:5px;padding:1px 5px}
  .pv-body pre{background:var(--row-hover);border:1px solid var(--rule);border-radius:10px;
    padding:14px 16px;overflow-x:auto;margin:14px 0}
  .pv-body pre code{background:none;border:0;padding:0;font-size:12.5px;line-height:1.6}
  .pv-body blockquote{margin:12px 0;padding:2px 14px;border-left:3px solid var(--rule-2);color:var(--ink-2)}
  .pv-body table{width:auto;max-width:100%;border-collapse:collapse;margin:14px 0;font-size:13px}
  .pv-body th{border:1px solid var(--rule);border-bottom-width:2px;padding:7px 12px;background:var(--row-hover)}
  .pv-body td{border:1px solid var(--rule);padding:6px 12px}
  .pv-body hr{border:0;border-top:1px solid var(--rule);margin:20px 0}
  .pv-body a{color:var(--open)}
  @media (max-width:960px){.app{grid-template-columns:1fr}.side{display:none}.kpis{grid-template-columns:repeat(2,1fr)}
    .pagebar{top:0}.search{min-width:0;flex:1}}
"""

def esc(s: str) -> str:
    return html.escape(s, quote=True)


def clip(text: str, n: int) -> str:
    text = text.replace('"', "'")
    return text if len(text) <= n else text[: n - 1] + "…"


def rel(source: str, scratch: Path) -> str:
    return os.path.relpath(source, scratch)


def scan_index(scratch: Path) -> tuple[list[Path], list[Path]]:
    """入口目录索引:顶层 memory/ 与 research/ 的 markdown,按改动时间倒序。

    两处目录都是历史账本,只列文件名不解析状态;目录不存在就返回空列表。
    """
    def ls(d: Path) -> list[Path]:
        if not d.is_dir():
            return []
        return sorted(d.glob("*.md"), key=lambda p: -p.stat().st_mtime)

    return ls(scratch / "memory"), ls(scratch / "research")


def copy_btn(name: str, what: str = "spec 名称") -> str:
    """Small icon button next to an id/name; copies `name` on click."""
    icon = (
        "<svg width='12' height='12' viewBox='0 0 16 16' fill='none' "
        "stroke='currentColor' stroke-width='1.5' stroke-linejoin='round'>"
        "<rect x='5' y='5' width='8' height='8' rx='1.5'></rect>"
        "<path d='M11 5V3.5A1.5 1.5 0 0 0 9.5 2h-6A1.5 1.5 0 0 0 2 3.5v6A1.5 1.5 0 0 0 3.5 11H5'></path></svg>"
    )
    return (
        f"<button type='button' class='copy-btn' data-copy-spec='{esc(name)}' "
        f"aria-label='复制{esc(what)} {esc(name)}' title='复制{esc(what)}'>{icon}</button>"
    )


def task_link(task: Task, scratch: Path) -> str:
    if task.source:
        return (
            f'<a href="{esc(rel(task.source, scratch))}" target="_blank" '
            f'rel="noopener">{esc(task.title)}</a>'
        )
    return esc(task.title)


def stacked_bar(total: int, counts: dict[str, int], height_css: str) -> tuple[str, str]:
    """One stacked band; returns (band html, tick html). Widths are data-driven."""
    fills = {
        DONE: "var(--done-fill)",
        ACTIVE: "var(--active-fill)",
        OPEN: "var(--open-fill)",
        BLOCKED: "var(--blocked-fill)",
    }
    order = [DONE, ACTIVE, OPEN, BLOCKED]
    band, ticks = [], []
    for status in order:
        n = counts.get(status, 0)
        if not n:
            continue
        pct = round(n * 100 / total, 2)
        band.append(f'<i style="width:{pct}%;background:{fills[status]}"></i>')
        low = ' low' if pct < 6 else ""
        ticks.append(
            f'<div class="tick{low}" style="width:{pct}%">'
            f'<span class="k k-{STATUS_CLASS[status]}">{STATUS_LABEL[status]} {n}</span>'
            f'<span class="v">{round(pct)}%</span></div>'
        )
    return "".join(band), "".join(ticks)


def mermaid_graph(effort: "Effort") -> str:
    """Mermaid flowchart of this effort's tickets: every ticket is a node
    (isolated ones included), blocking edges are arrows. '' when no ticket
    has an id. Colours are a safe base; the page repaints them per theme."""
    nodes = {t.key: t for t in effort.tasks if t.tid}
    if not nodes:
        return ""
    ids = {k: f"n{i}" for i, k in enumerate(nodes)}
    # mermaid's parser rejects var(--x) in linkStyle/classDef, so hex only here.
    lines = [
        "graph TD",
        "classDef done fill:#7ba888",
        "classDef active fill:#c08a3e",
        "classDef open fill:#2f6fb5",
        "classDef blocked fill:#c9968c",
        "classDef tbd stroke-dasharray:5 5",
    ]
    for key, t in nodes.items():
        label = f"{clip(t.tid, 12)} · {mmd_label(t.title)}"
        lines.append(f'{ids[key]}["{label}"]:::{STATUS_CLASS[t.status]}')
        if not t.from_file:
            lines.append(f"class {ids[key]} tbd")
    cyc = {frozenset(e) for e in effort.cycle_edges}
    edge_i = 0
    for a, b in effort.edges:
        if a not in ids or b not in ids:
            continue
        arrow = "-.->" if frozenset((a, b)) in cyc else "-->"
        lines.append(f"{ids[a]} {arrow} {ids[b]}")
        if arrow == "-.->":
            lines.append(f"linkStyle {edge_i} stroke:#b5813a")
        edge_i += 1
    return "\n".join(lines)


def mmd_label(text: str, n: int = 40) -> str:
    """Title safe for a quoted mermaid node label: quotes/brackets/newlines out."""
    for bad, good in (('"', "'"), ("[", "（"), ("]", "）"), ("\n", " ")):
        text = text.replace(bad, good)
    return clip(text, n)


def headline(efforts: list[Effort]) -> str:
    tasks = [t for e in efforts for t in e.tasks]
    total = len(tasks)
    open_now = sorted(
        (t for t in tasks if t.status == OPEN),
        key=lambda t: (-t.unlocks, t.effort, t.tid),
    )
    if not total:
        return "没有扫到任何票。"
    if not open_now:
        return (
            f"{total} 张票，<em>没有一张现在能开工</em>——"
            "要么全做完了，要么都卡在别的票后面。"
        )
    head = open_now[0]
    if head.unlocks:
        tail = (
            f"；先做 <em>{esc(head.effort)} {esc(head.label)}</em>，"
            f"它一张解锁 {head.unlocks} 张。"
        )
    else:
        tail = "，做完都不会解锁别的票。"
    return f"{total} 张票里，<em>{len(open_now)} 张现在就能开工</em>{tail}"


def minify_html(doc: str) -> str:
    """输出压缩:保护 pre/script/style 内部,标签间空白与注释全去掉。"""
    parts = re.split(
        r"(<pre[^>]*>.*?</pre>|<script[^>]*>.*?</script>|<style>.*?</style>)",
        doc, flags=re.S,
    )
    out = []
    for i, seg in enumerate(parts):
        if i % 2 == 1:
            out.append(seg)
            continue
        seg = re.sub(r"<!--.*?-->", "", seg, flags=re.S)
        seg = re.sub(r">\s+<", "><", seg)
        seg = re.sub(r"\s{2,}", " ", seg)
        out.append(seg.strip())
    return "".join(out)


def render(efforts: list[Effort], unparsed: list[Path], scratch: Path) -> str:
    all_tasks = [t for e in efforts for t in e.tasks]
    c = {s: 0 for s in STATUS_LABEL}
    for t in all_tasks:
        c[t.status] += 1
    total = len(all_tasks)
    now = time.time()
    project = scratch.parent.name
    pct = round(c[DONE] * 100 / total) if total else 0

    band, ticks = stacked_bar(total, c, "") if total else ("", "")

    stale = [
        e
        for e in efforts
        if any(t.status != DONE for t in e.tasks)
        and (now - e.mtime) > STALE_DAYS * 86400
    ]
    recent = sorted(
        (t for t in all_tasks if t.status == DONE),
        key=lambda t: (not t.from_file, -t.mtime),
    )[:TIMELINE_LIMIT]
    open_now = sorted(
        (t for t in all_tasks if t.status == OPEN),
        key=lambda t: (-t.unlocks, t.effort, t.tid),
    )
    mem_files, res_files = scan_index(scratch)

    # 页内预览:把 md 原文嵌进页面——file:// 下 fetch 本地文件会被 CORS 拦,
    # 只能在生成期读。按相对路径去重,总字节封顶,超限的文件回退为新标签打开。
    pv_files: dict[str, str] = {}
    pv_budget = 2_000_000

    def add_pv(*paths) -> None:
        nonlocal pv_budget
        for p in paths:
            key = rel(str(p), scratch)
            if key in pv_files or pv_budget <= 0:
                continue
            try:
                text = p.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if len(text) > pv_budget:
                continue
            pv_files[key] = text
            pv_budget -= len(text)

    add_pv(*mem_files, *res_files)
    for e in efforts:
        add_pv(e.path / "spec.md", e.path / "map.md", *e.research)
        add_pv(*[Path(s) for s in (t.source for t in e.tasks if t.from_file and t.source)])
    add_pv(*unparsed)

    def human_size(p: Path) -> str:
        n = p.stat().st_size
        return f"{n / 1024:.1f}K" if n >= 1024 else f"{n}B"

    def day_mark(p: Path) -> str:
        """2026-10-22 → 10·22；不带日期前缀的文件用改动时间。"""
        m = re.match(r"(\d{4})-(\d{2})-(\d{2})", p.stem)
        if m:
            return f"{m.group(2)}·{m.group(3)}"
        return time.strftime("%m·%d", time.localtime(p.stat().st_mtime))

    tabs = [("<a class='on' href='#/overview'>概览</a>")]
    tabs.append(f"<a href='#/now'>可开工<span class='n'>{len(open_now)}</span></a>")
    tabs.append(f"<a href='#/specs'>功能台<span class='n'>{len(efforts)}</span></a>")
    if mem_files:
        tabs.append(f"<a href='#/memory'>决策档案<span class='n'>{len(mem_files)}</span></a>")
    if res_files:
        tabs.append(f"<a href='#/research'>调研<span class='n'>{len(res_files)}</span></a>")
    if stale:
        tabs.append(f"<a href='#/stale'>久未动<span class='n'>{len(stale)}</span></a>")
    if recent:
        tabs.append(f"<a href='#/recent'>最近完成<span class='n'>{len(recent)}</span></a>")
    if unparsed:
        tabs.append(f"<a href='#/unknown'>未能识别<span class='n'>{len(unparsed)}</span></a>")
    nav_extra = "".join(tabs)

    icon_grid = "<svg viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='1.8'><rect x='3' y='3' width='7' height='9' rx='1.5'/><rect x='14' y='3' width='7' height='5' rx='1.5'/><rect x='14' y='12' width='7' height='9' rx='1.5'/><rect x='3' y='16' width='7' height='5' rx='1.5'/></svg>"
    icon_target = "<svg viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='1.8'><circle cx='12' cy='12' r='9'/><circle cx='12' cy='12' r='4'/></svg>"
    icon_board = "<svg viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='1.8'><path d='M8 6h13M8 12h13M8 18h13'/><circle cx='4' cy='6' r='1'/><circle cx='4' cy='12' r='1'/><circle cx='4' cy='18' r='1'/></svg>"
    icon_clock = "<svg viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='1.8'><path d='M12 8v4l2.5 2.5'/><circle cx='12' cy='12' r='9'/></svg>"
    icon_search = "<svg viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='1.8'><circle cx='11' cy='11' r='7'/><path d='m21 21-4.3-4.3'/></svg>"
    icon_alert = "<svg viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='1.8'><path d='M12 9v4M12 17h.01'/><circle cx='12' cy='12' r='9'/></svg>"

    side_proj = "".join(
        f"<a href='#/spec-{esc(e.name)}'><span class='nm'>{esc(e.name)}</span>"
        f"<span class='mini'><i style='width:{round(sum(1 for t in e.tasks if t.status == DONE) * 100 / len(e.tasks)) if e.tasks else 0}%'></i></span></a>"
        for e in efforts
    )

    chev = "<svg class='chev' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2.2'><path d='m6 9 6 6 6-6'/></svg>"

    def navgroup(cap: str, items: str) -> str:
        """一级分组头(可折叠) + 二级条目容器。"""
        if not items:
            return ""
        return (
            f"<button type='button' class='navcap' data-navcap>{cap}{chev}</button>"
            f"<div class='grp'>{items}</div>"
        )

    out = [
        "<!DOCTYPE html><html lang='zh-Hans'><head><meta charset='utf-8'>",
        "<meta name='viewport' content='width=device-width,initial-scale=1'>",
        f"<title>{esc(project)}·.scratch 总览</title>",
        f"<style>{CSS}</style>",
        "<script>try{var t=localStorage.getItem('tp-theme');if(t)document.documentElement.dataset.theme=t}catch(e){}</script>",
        "</head><body>",
        "<button class='theme-btn' type='button' id='themeToggle' aria-label='切换深浅色'>深色</button>",
        "<div class='app'>",
        "<aside class='side'>",
        f"<div class='workspace'><div class='mark'>sc</div><div class='ws'>{esc(project)}<span>.scratch 工作区</span></div></div>",
        "<nav class='nav'>",
        navgroup(
            "工作台",
            f"<a class='on' href='#/overview'>{icon_grid}总览<span class='cnt'>{total}</span></a>"
            f"<a href='#/now'>{icon_target}可开工<span class='cnt'>{len(open_now)}</span></a>",
        ),
        navgroup(
            "功能台",
            f"<a href='#/specs'>{icon_board}全部功能<span class='cnt'>{len(efforts)}</span></a>"
            + (f"<div class='proj'>{side_proj}</div>" if efforts else ""),
        ),
        navgroup(
            "档案库",
            "".join(
                [
                    f"<a href='#/memory'>{icon_clock}决策档案<span class='cnt'>{len(mem_files)}</span></a>"
                    if mem_files
                    else "",
                    f"<a href='#/research'>{icon_search}调研<span class='cnt'>{len(res_files)}</span></a>"
                    if res_files
                    else "",
                    f"<a href='#/unknown'>{icon_alert}未能识别<span class='cnt'>{len(unparsed)}</span></a>"
                    if unparsed
                    else "",
                ]
            ),
        ),
        "<div class='navcap' style='cursor:default'>即将上线</div>",
        "<div class='soon'>更多模块<span class='soon-tag'>规划中</span></div>",
        "</nav>",
        f"<div class='foot'><div class='ava'>{esc(project[:1].upper())}</div><div class='who'>{esc(project)}<span>本地模式 · file:// 直开</span></div></div>",
        "</aside>",
        "<div class='right'>",
        "<header class='top'>",
        "<span class='crumb'><b>.scratch</b> / 总览</span>",
        "<label class='search'>",
        "<svg width='14' height='14' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2'><circle cx='11' cy='11' r='7'/><path d='m21 21-4.3-4.3'/></svg>",
        "<input id='tpFilter' type='text' placeholder='过滤票号、标题、spec…' aria-label='过滤行'>",
        "<kbd>输入即滤</kbd>",
        "</label>",
        "</header>",
        "<div class='pagebar'>",
        "<div class='row'>",
        f"<h1>.scratch 总览 <span class='scope'>{total} 票 · {pct}%</span></h1>",
        f"<div class='acts'><a class='btn' href='#/now'>可开工 {len(open_now)}</a></div>" if total else "",
        "</div>",
        f"<nav class='tabs'>{nav_extra}</nav>",
        "</div>",
        "<div class='pagebody'>",
        "<div class='mmd-viewer' id='mmdViewer'><button class='close' type='button' id='mmdClose'>关闭</button>"
        "<div class='stage' id='mmdStage'></div>"
        "<p class='hint'>滚轮缩放 · 拖拽平移 · 双击复位 · ESC 退出</p></div>",
        f"<div class='focus rise d1'><span class='pulse'></span><div class='ft'>{headline(efforts)}</div>"
        f"<a class='btn' href='#/now'>看可开工的票</a></div>" if total else "",
        "<section class='view on' id='overview' data-route='overview' style='border-top:0;padding-top:0'>",
        "<div class='kpis rise d2'>",
        f"<div class='kpi'><div class='k'><i style='background:var(--done-fill)'></i>已完成</div>"
        f"<div class='v'><span data-n='{c[DONE]}'>0</span><small>/ {total} 票</small></div>"
        f"<div class='meter'><i style='--w:{pct}%;background:var(--done-fill)'></i></div></div>",
        f"<div class='kpi'><div class='k'><i style='background:var(--active-fill)'></i>进行中</div>"
        f"<div class='v'><span data-n='{c[ACTIVE]}'>0</span></div>"
        f"<div class='meter'><i style='--w:{round(c[ACTIVE] * 100 / total) if total else 0}%;background:var(--active-fill)'></i></div></div>",
        f"<div class='kpi'><div class='k'><i style='background:var(--open-fill)'></i>可开工</div>"
        f"<div class='v'><span data-n='{c[OPEN]}'>0</span></div>"
        f"<div class='meter'><i style='--w:{round(c[OPEN] * 100 / total) if total else 0}%;background:var(--open-fill)'></i></div></div>",
        f"<div class='kpi'><div class='k'><i style='background:var(--blocked-fill)'></i>被阻塞</div>"
        f"<div class='v'><span data-n='{c[BLOCKED]}'>0</span></div>"
        f"<div class='meter'><i style='--w:{round(c[BLOCKED] * 100 / total) if total else 0}%;background:var(--blocked-fill)'></i></div></div>",
        "</div>",
        f"<p class='statline rise d3'>spec <span>{len(efforts)}</span> 个 · 票 <span>{total}</span> 张 · "
        f"总进度 <span>{pct}%</span>（{c[DONE]} ÷ {total}） · 生成于 {time.strftime('%Y-%m-%d %H:%M')} · "
        f"扫描 <code>{esc(str(scratch))}</code> 下 {len(efforts)} 个 spec 目录的票面文件与 "
        f"<code>memory.md</code> 勾选行。一次快照，无历史记录——本页所有数字都由这一次扫描直接数出来。</p>",
        f"<div class='stack rise d3'>{band}</div><div class='ticks rise d3'>{ticks}</div>",
        "<p class='note rise d4'>",
        "<b>进度 = 已完成 ÷ 总票数</b>，被阻塞的票也算在分母里——所以这个百分比是"
        "「全部要做的事完成了多少」，不是「手头能推进的事完成了多少」。<br>",
        "<b>四种状态是一条单向的路</b>：被阻塞 → 可开工 → 进行中 → 已完成，票只前进不后退。<br>",
        "<b>未建票</b> = 只在 map.md / 清单上有一行、还没有票面文件的条目；「票已建齐」= 每一条都有对应票面文件。<br>",
        "<b>一张票 = 一个票面文件，或 <code>memory.md</code> 里的一行勾选</b>。两种来源同等计数，"
        "所以「已完成」里可能包含「写 spec.md」这类过程记录，不等于功能数。",
        "</p></section>",
    ]

    # 功能台首页:每个 spec 一行,点名字进该 spec 的独立视图
    out += [
        "<section class='view' id='specs' data-route='specs'>",
        "<h2>功能台</h2>",
        "<p class='sub'>每个 spec 一行：票数按状态拆开，进度 = 该 spec 的已完成 ÷ 该 spec 总票数。"
        "「可开工」列非零说明这个 spec 现在就有活能干；点 spec 名进它的独立页面。</p>",
        "<table><thead><tr><th style='width:150px'>spec</th>"
        "<th class='num'>可开工</th><th class='num'>进行中</th><th class='num'>已完成</th>"
        "<th class='num'>被阻塞</th><th class='num'>ticket</th><th class='num'>未建</th>"
        "<th class='num'>进度</th></tr></thead><tbody>",
    ]
    spec_rows = sorted(
        efforts,
        key=lambda e: (
            -sum(1 for t in e.tasks if t.status == OPEN),
            e.name,
        ),
    )
    for effort in spec_rows:
        ec = {s: 0 for s in STATUS_LABEL}
        for t in effort.tasks:
            ec[t.status] += 1
        tbd = sum(1 for t in effort.tasks if not t.from_file)
        et = len(effort.tasks)
        epct = round(ec[DONE] * 100 / et) if et else 0
        out.append(
            f"<tr><td class='spec'><a href='#/spec-{esc(effort.name)}'>{esc(effort.name)}</a>{copy_btn(effort.name)}</td>"
            f"<td class='num'>{ec[OPEN] or '·'}</td>"
            f"<td class='num'>{ec[ACTIVE] or '·'}</td>"
            f"<td class='num'>{ec[DONE] or '·'}</td>"
            f"<td class='num'>{ec[BLOCKED] or '·'}</td>"
            f"<td class='num'>{et}</td>"
            f"<td class='num'>{tbd or '·'}</td>"
            f"<td class='num'>{epct}%</td></tr>"
        )
    out.append("</tbody></table></section>")

    out += [
        "<section class='view' id='now' data-route='now'>",
        f"<h2>可开工的票 · {len(open_now)} 张</h2>",
        "<p class='sub'>未完成、没有前置票挡着、也没人在做的票。按「直接解锁」从多到少排——"
        "解锁得多的票，做完能让更多票动起来。</p>",
    ]
    if open_now:
        out += [
            "<table><thead><tr><th style='width:130px'>spec</th><th style='width:44px'>ticket</th>"
            "<th>标题</th><th style='width:70px'>类型</th><th class='num'>解锁</th></tr></thead>",
        ]
        out += [
            "<tbody>"
            + "".join(
                f"<tr><td class='spec'>{esc(t.effort)}{copy_btn(t.effort)}</td>"
                f"<td class='lbl'>{esc(t.label)}{copy_btn(f'{t.effort}#{t.tid}', '票号') if t.tid else ''}</td>"
                f"<td class='t'>{task_link(t, scratch)}</td>"
                f"<td class='meta'>{esc(t.kind) or '—'}</td>"
                f"<td class='num {'unlocks' if t.unlocks else 'unlocks-0'}'>"
                f"{t.unlocks or '·'}</td></tr>"
                for t in open_now
            )
            + "</tbody></table>",
        ]
    else:
        out.append("<p class='empty'>没有可直接开工的票——要么全做完了，要么都卡在别的票后面。</p>")
    out.append("</section>")

    # 每个 spec 一个独立视图(hash 路由 spec-<名>),代替原来的「按 spec 明细」长列表
    for effort in efforts:
        out.append(f"<div class='view' id='view-spec-{esc(effort.name)}' data-route='spec-{esc(effort.name)}'>")
        ec = {s: 0 for s in STATUS_LABEL}
        for t in effort.tasks:
            ec[t.status] += 1
        et = len(effort.tasks)
        epct = round(ec[DONE] * 100 / et) if et else 0
        minibar, _ = stacked_bar(et, ec, "") if et else ("", "")
        name_html = esc(effort.name)
        kinds = []
        if effort.is_map:
            kinds.append(
                f"<a class='kind' href='{esc(rel(str(effort.path / 'map.md'), scratch))}' "
                f"target='_blank' rel='noopener'>wayfinder 地图</a>"
            )
        if effort.has_spec:
            kinds.append(
                f"<a class='kind' href='{esc(rel(str(effort.path / 'spec.md'), scratch))}' "
                f"target='_blank' rel='noopener'>spec</a>"
            )
        # 未建票 = 只有 map.md/清单行、还没有票面文件的条目
        tbd = sum(1 for t in effort.tasks if not t.from_file)
        if et and tbd:
            kinds.append(f"<span class='kind tbd'>未建票 {tbd}</span>")
        elif et:
            kinds.append("<span class='kind ok'>票已建齐</span>")
        out += [
            "<div class='spec-head'>",
            f"<h3>{name_html}{copy_btn(effort.name)}"
            f"<span class='share-wrap'><button type='button' class='share-btn'>分享</button>"
            f"<span class='share-menu'>"
            f"<button type='button' data-share='progress' data-spec='{esc(effort.name)}'>进度(文字)</button>"
            f"<button type='button' data-share='deps-img' data-spec='{esc(effort.name)}'>依赖图(图片)</button>"
            f"<button type='button' data-share='deps-md' data-spec='{esc(effort.name)}'>依赖(源码)</button>"
            f"</span></span></h3>",
            *kinds,
            f"<span class='cnt'>{et} 张 · {ec[DONE]} 已完成</span></div>",
            f"<div class='minibar'>{minibar}</div>",
            f"<div class='minicap'><span>{STATUS_LABEL[DONE]} {ec[DONE]}</span>"
            f"{('<span>未建票 %d</span>' % tbd) if tbd else ''}"
            f"<span>{epct}%({ec[DONE]} ÷ {et})</span></div>" if et else "",
        ]
        mmd = mermaid_graph(effort)
        if mmd:
            out.append(f"<pre class='mmd' data-spec='{esc(effort.name)}'>{esc(mmd)}</pre>")
        if et:
            out += [
                f"<table><thead><tr><th style='width:44px'>ticket</th>"
                f"<th>标题<span class='share-wrap'><button type='button' class='share-btn'>分享</button>"
                f"<span class='share-menu'>"
                f"<button type='button' data-share='table-md' data-spec='{esc(effort.name)}'>表格(文字)</button>"
                f"<button type='button' data-share='table-img' data-spec='{esc(effort.name)}'>表格(图片)</button>"
                f"</span></span></th>"
                f"<th style='width:64px'>状态</th><th style='width:110px'>阻塞于</th>"
                "<th class='num'>解锁</th></tr></thead><tbody>",
            ]
            for t in effort.tasks:
                mark = "<i class='tbdmark'>未建</i>" if not t.from_file else ""
                meta = []
                if t.dangling:
                    meta.append(
                        "<s class='dangling'>"
                        + " ".join(esc(d) for d in t.dangling)
                        + "</s>"
                    )
                if t.deps:
                    meta.append(" ".join(f"<a href='#'>{esc(d)}</a>" for d in t.deps))
                blocked_cell = (
                    "、".join(meta) if meta else "—"
                )
                out.append(
                    f"<tr class='r-{STATUS_CLASS[t.status]}'>"
                    f"<td class='lbl'>{esc(t.label)}{mark}{copy_btn(f'{t.effort}#{t.tid}', '票号') if t.tid else ''}</td>"
                    f"<td class='t'>{task_link(t, scratch)}</td>"
                    f"<td><span class='st st-{STATUS_CLASS[t.status]}'>"
                    f"{STATUS_LABEL[t.status]}</span></td>"
                    f"<td class='meta'>{blocked_cell}</td>"
                    f"<td class='num {'unlocks' if t.unlocks else 'unlocks-0'}'>"
                    f"{t.unlocks or '·'}</td></tr>"
                )
            out.append("</tbody></table>")
        else:
            out.append("<p class='empty'>只有 spec / 地图，没扫到票。</p>")
        if effort.research:
            links = "、".join(
                f"<a href='{esc(rel(str(p), scratch))}' target='_blank' rel='noopener'>"
                f"{esc(re.sub(r'^\\d+-', '', p.stem).replace('-', ' '))}</a>"
                for p in effort.research
            )
            out.append(
                f"<p class='research'>research {len(effort.research)} 篇：{links}</p>"
            )
        out.append("</div>")

    if stale:
        rows = sorted(stale, key=lambda e: e.mtime)
        out += ["<section class='view' id='stale' data-route='stale'>", "<h2>久未动</h2>",
                f"<p class='sub'>超过 {STALE_DAYS} 天没有任何文件改动、且还有未完成票的 spec。</p>"]
        out += [
            "<table><thead><tr><th>spec</th><th class='num'>未完成</th>"
            "<th class='num'>最后改动</th></tr></thead><tbody>",
            "".join(
                f"<tr><td class='spec'>{esc(e.name)}{copy_btn(e.name)}</td>"
                f"<td class='num'>{sum(1 for t in e.tasks if t.status != DONE)} 张</td>"
                f"<td class='num'>{int((now - e.mtime) / 86400)} 天前</td></tr>"
                for e in rows
            ),
            "</tbody></table>",
            "</section>",
        ]

    if recent:
        out += [
            "<section class='view' id='recent' data-route='recent'>",
            f"<h2>最近完成 · {len(recent)} 条</h2>",
            "<p class='sub'>按源文件修改时间倒序，最多 "
            f"{TIMELINE_LIMIT} 条。票面文件排在勾选行前面——勾选行共用同一个文件时间，"
            "彼此之间没有先后。</p>",
            "<table><thead><tr><th style='width:110px'>日期</th><th style='width:130px'>spec</th>"
            "<th>标题</th></tr></thead><tbody>",
            "".join(
                f"<tr class='r-done'><td class='lbl'>"
                f"{time.strftime('%Y-%m-%d', time.localtime(t.mtime))}</td>"
                f"<td class='spec'>{esc(t.effort)}{copy_btn(t.effort)}</td>"
                f"<td class='t'>{task_link(t, scratch)}</td></tr>"
                for t in recent
            ),
            "</tbody></table>",
            "</section>",
        ]

    if mem_files:
        out += [
            "<section class='view' id='memory' data-route='memory'>",
            "<h2>决策档案 <span class='badge'>memory/</span></h2>",
            "<p class='sub'>按天追加的决策账本，历史存档——只列文件，不解析状态、不计进度。点开是 markdown 原文。</p>",
            "<div class='panel'>",
            "<table><thead><tr><th style='width:80px'>日期</th><th>文件</th>"
            "<th class='num' style='width:90px'>大小</th></tr></thead><tbody>",
            "".join(
                f"<tr><td class='lbl'>{day_mark(p)}</td>"
                f"<td class='t'><a href='{esc(rel(str(p), scratch))}' target='_blank' rel='noopener'>"
                f"{esc(p.name)}</a></td>"
                f"<td class='num'>{human_size(p)}</td></tr>"
                for p in mem_files
            ),
            "</tbody></table></div></section>",
        ]
    if res_files:
        out += [
            "<section class='view' id='research' data-route='research'>",
            "<h2>调研 <span class='badge'>research/</span></h2>",
            "<p class='sub'>顶层 research/ 的调研报告，只读参考，不参与进度统计。</p>",
            "<div class='panel'>",
            "<table><thead><tr><th style='width:80px'>日期</th><th>文件</th>"
            "<th class='num' style='width:90px'>大小</th></tr></thead><tbody>",
            "".join(
                f"<tr><td class='lbl'>{day_mark(p)}</td>"
                f"<td class='t'><a href='{esc(rel(str(p), scratch))}' target='_blank' rel='noopener'>"
                f"{esc(p.name)}</a></td>"
                f"<td class='num'>{human_size(p)}</td></tr>"
                for p in res_files
            ),
            "</tbody></table></div></section>",
        ]

    if unparsed:
        out += [
            "<section class='view' id='unknown' data-route='unknown'>",
            "<h2>未能识别的文件</h2>",
            "<p class='sub'>扫描时读不出任务状态的 markdown 文件。如果里面其实有真任务，"
            "说明这个工具漏了一种写法——那是工具的问题，不是你的。</p>",
            "<ul class='filelist'>",
            "".join(
                f"<li><a href='{esc(rel(str(p), scratch))}' target='_blank' rel='noopener'>{esc(rel(str(p), scratch))}</a></li>"
                for p in unparsed
            ),
            "</ul>",
            "</section>",
        ]
    out += [
        "<footer>口径：进度 = 已完成 ÷ 总票数，被阻塞计入分母 · 一次快照，无历史统计 · "
        f"{esc('tracking_progress.py')} 生成，file:// 直开</footer>",
        "</div></div></div>",
    ]

    import json as _json
    share = {
        e.name: {
            "is_map": e.is_map,
            "tasks": [
                {"tid": t.tid, "title": t.title, "st": STATUS_CLASS[t.status],
                 "deps": t.deps, "f": 0 if t.from_file else 1}
                for t in e.tasks
            ],
            "mmd": mermaid_graph(e),
        }
        for e in efforts
    }
    out.append(
        "<script id='tp-data' type='application/json'>"
        + _json.dumps(share, ensure_ascii=False).replace("<", "\\u003c")
        + "</script>"
    )
    out.append(
        "<script id='tp-files' type='application/json'>"
        + _json.dumps(pv_files, ensure_ascii=False).replace("<", "\\u003c")
        + "</script>"
    )

    out += [
        "<script>document.querySelectorAll('[data-copy-spec]').forEach(button => button.addEventListener('click', async () => {"
        "if (button.classList.contains('copied')) return;"
        "try { await navigator.clipboard.writeText(button.dataset.copySpec); button.classList.add('copied'); button.textContent = '已复制'; } "
        "catch { button.textContent = '失败'; }"
        "setTimeout(function(){ button.classList.remove('copied'); button.innerHTML = button.dataset.icon; }, 1600);"
        "}));"
        "document.querySelectorAll('[data-copy-spec]').forEach(button => button.dataset.icon = button.innerHTML);</script>",
        # 分享:spec 头 / ticket 表 / mermaid 图,点击即复制进剪贴板,toast 通知成败
        "<div class='pv-wrap' id='pvWrap'><div class='pv-card'>"
        "<div class='pv-head'><span class='t' id='pvTitle'></span>"
        "<a class='raw' id='pvRaw' target='_blank' rel='noopener'>新标签打开</a>"
        "<button class='close' type='button' id='pvClose'>关闭</button></div>"
        "<div class='pv-body' id='pvBody'></div></div></div>",
        "<div class='toast' id='tpToast'></div>",
        "<script>(function(){"
        "var TPDATA={};try{TPDATA=JSON.parse(document.getElementById('tp-data').textContent)}catch(e){}"
        "var STZH={done:'已完成',active:'进行中',open:'可开工',blocked:'被阻塞'};"
        "var STC={done:'#7ba888',active:'#c08a3e',open:'#6aa5e3',blocked:'#c98a80'};"
        r"function escMd(s){return String(s).replace(/\|/g,'\\|').replace(/\n/g,' ')}"
        "function clip(s,n){s=String(s);return s.length>n?s.slice(0,n-1)+'…':s}"
        "function progMd(name){var d=TPDATA[name];if(!d)return '';"
        "var c={done:0,active:0,open:0,blocked:0};"
        "d.tasks.forEach(function(t){c[t.st]++});"
        "var n=d.tasks.length,pct=n?Math.round(c.done*100/n):0;"
        "var L=['### '+name+(d.is_map?'(wayfinder 地图)':'')+' · 进度','','"
        "共 '+n+' 张:已完成 '+c.done+' · 进行中 '+c.active+' · 可开工 '+c.open+' · 被阻塞 '+c.blocked+'(进度 '+pct+'%)'"
        "+(d.tasks.some(function(t){return t.f})?' · 另有未建票 '+d.tasks.filter(function(t){return t.f}).length+' 张':'')+'','"
        "| 票 | 标题 | 状态 | 阻塞于 |','|---|---|---|---|'];"
        "d.tasks.forEach(function(t){L.push('| '+t.tid+' | '+escMd(t.title)+' | '+STZH[t.st]+' | '+(t.deps.length?t.deps.join('、'):'—')+' |')});"
        r"return L.join('\n')}"
        "function tableMd(name){var d=TPDATA[name];if(!d)return '';"
        "var L=['### '+name+' · 票表','','| 票 | 标题 | 状态 | 阻塞于 |','|---|---|---|---|'];"
        "d.tasks.forEach(function(t){L.push('| '+t.tid+' | '+escMd(t.title)+' | '+STZH[t.st]+' | '+(t.deps.length?t.deps.join('、'):'—')+' |')});"
        r"return L.join('\n')}"
        "function depsMd(name){var d=TPDATA[name];if(!d)return '';"
        "var L=['### '+name+' · 依赖','','```mermaid'];"
        "L.push(d.mmd||'graph TD');L.push('```');"
        "var rel=d.tasks.filter(function(t){return t.deps.length});"
        "if(rel.length){L.push('');L.push('阻塞关系:');"
        "rel.forEach(function(t){L.push('- '+t.tid+' 被 '+t.deps.join('、')+' 阻塞')})}"
        r"return L.join('\n')}"
        "function toast(msg,err){var t=document.getElementById('tpToast');"
        "t.textContent=msg;t.classList.toggle('err',true===err);t.classList.add('show');"
        "clearTimeout(t._h);t._h=setTimeout(function(){t.classList.remove('show')},1800)}"
        "function copyText(txt,label){navigator.clipboard.writeText(txt).then("
        "function(){toast('已复制'+label)},function(){toast('复制失败',true)})}"
        r"function svgPngBlob(svg,cb){var r={width:+svg.getAttribute('width')||svg.getBoundingClientRect().width,height:+svg.getAttribute('height')||svg.getBoundingClientRect().height};"
        "var s=new XMLSerializer().serializeToString(svg);"
        "var url=URL.createObjectURL(new Blob([s],{type:'image/svg+xml;charset=utf-8'}));"
        "var img=new Image();"
        "img.onload=function(){var c=document.createElement('canvas');"
        "c.width=Math.max(1,Math.round(r.width*2));c.height=Math.max(1,Math.round(r.height*2));"
        "var x=c.getContext('2d');"
        "x.fillStyle=getComputedStyle(document.documentElement).getPropertyValue('--bg').trim()||'#141719';"
        "x.fillRect(0,0,c.width,c.height);x.drawImage(img,0,0,c.width,c.height);"
        "URL.revokeObjectURL(url);c.toBlob(function(b){cb(b)},'image/png')};"
        "img.onerror=function(){URL.revokeObjectURL(url);cb(null)};img.src=url}"
        "function copyDepsImg(name){"
        "var pre=document.querySelector(\"pre.mmd[data-spec='\"+name.replace(/'/g,'')+\"']\");"
        "var svg=pre&&pre.querySelector('svg');"
        "if(!svg){toast('没有依赖图',true);return}"
        "var vb=svg.viewBox&&svg.viewBox.baseVal;"
        "var clone=svg.cloneNode(true);clone.removeAttribute('style');"
        "if(vb&&vb.width){clone.setAttribute('width',vb.width);clone.setAttribute('height',vb.height)}"
        "svgPngBlob(clone,function(b){"
        "if(!b){toast('复制失败',true);return}"
        "try{navigator.clipboard.write([new ClipboardItem({'image/png':b})]).then("
        "function(){toast('已复制依赖图')},function(){toast('复制失败',true)})"
        "}catch(e){toast('复制失败',true)}})}"
        "function clipCard(name){var d=TPDATA[name];if(!d)return null;"
        "var W=1080,RH=40,HH=48,TH=68,pad=24;"
        "var H=TH+HH+d.tasks.length*RH+pad*2;"
        "var c=document.createElement('canvas');c.width=W;c.height=H;"
        "var x=c.getContext('2d');"
        "x.fillStyle='#141719';x.fillRect(0,0,W,H);"
        "x.fillStyle='#e8ecef';"
        "x.font='600 26px \"Maple Mono\",\"JetBrains Mono\",ui-monospace,monospace';"
        "x.fillText(clip(name,40),pad,TH-20);"
        "var y=TH;x.fillStyle='#1c2126';x.fillRect(pad,y,W-pad*2,HH);"
        "x.fillStyle='#8b96a2';x.font='600 15px -apple-system,BlinkMacSystemFont,sans-serif';"
        "x.fillText('票',pad+16,y+30);x.fillText('标题',pad+100,y+30);"
        "x.fillText('状态',pad+600,y+30);x.fillText('阻塞于',pad+740,y+30);"
        "d.tasks.forEach(function(t,i){var yy=y+HH+i*RH;"
        "if(i%2){x.fillStyle='rgba(255,255,255,.03)';x.fillRect(pad,yy,W-pad*2,RH)}"
        "x.fillStyle='#e8ecef';x.font='15px -apple-system,BlinkMacSystemFont,sans-serif';"
        "x.fillText(t.tid,pad+16,yy+26);x.fillText(clip(t.title,36),pad+100,yy+26);"
        "x.fillStyle=STC[t.st]||'#e8ecef';x.font='600 15px -apple-system,BlinkMacSystemFont,sans-serif';"
        "x.fillText(STZH[t.st],pad+600,yy+26);"
        "x.fillStyle='#8b96a2';x.font='15px -apple-system,BlinkMacSystemFont,sans-serif';"
        "x.fillText(t.deps.length?t.deps.join('、'):'—',pad+740,yy+26)});"
        "return c}"
        "function copyTableImg(name){var c=clipCard(name);"
        "if(!c){toast('没有票',true);return}"
        "c.toBlob(function(b){"
        "try{navigator.clipboard.write([new ClipboardItem({'image/png':b})]).then("
        "function(){toast('已复制表格图片')},function(){toast('复制失败',true)})"
        "}catch(e){toast('复制失败',true)}},'image/png')}"
        "function wireShare(){"
        "document.querySelectorAll('[data-share]:not([data-wired])').forEach(function(b){"
        "b.dataset.wired=1;"
        "b.addEventListener('click',function(e){e.stopPropagation();"
        "var w=b.dataset.share,s=b.dataset.spec;"
        "if(w==='progress')copyText(progMd(s),'进度');"
        "else if(w==='deps-md')copyText(depsMd(s),'依赖');"
        "else if(w==='deps-img')copyDepsImg(s);"
        "else if(w==='table-md')copyText(tableMd(s),'表格文字');"
        "else if(w==='table-img')copyTableImg(s)})})}"
        "function wireHover(){"
"document.querySelectorAll('.share-wrap:not([data-hw])').forEach(function(w){"
"w.dataset.hw=1;"
"w.addEventListener('mouseenter',function(){clearTimeout(w._t);w.classList.add('open')});"
"w.addEventListener('mouseleave',function(){w._t=setTimeout(function(){"
"w.classList.remove('open')},350)})})}"
"wireHover();"
"if(document.readyState!='loading')wireShare();"
"else document.addEventListener('DOMContentLoaded',wireShare);"
"window._copyDepsImg=copyDepsImg;"
        "})();</script>",

        "<script>(function(){var root=document.documentElement,btn=document.getElementById('themeToggle');"
        "function set(t){root.dataset.theme=t;btn.textContent=t==='dark'?'亮色':'深色';"
        "if(window.paintMmd)window.paintMmd();"
        "try{localStorage.setItem('tp-theme',t)}catch(e){}}"
        "set(root.dataset.theme||'light');"
        "btn.addEventListener('click',function(){set(root.dataset.theme==='dark'?'light':'dark')});})();</script>",
        # KPI 数字滚动 + ⌘K/输入即滤:过滤所有表格行和依赖图标题
        "<script>(function(){"
        "document.querySelectorAll('.kpi [data-n]').forEach(function(el){"
        "var n=+el.dataset.n,t0=performance.now();"
        "requestAnimationFrame(function tick(t){"
        "var p=Math.min((t-t0-350)/800,1);"
        "if(p>=0)el.textContent=Math.round(n*(1-Math.pow(1-p,3)));"
        "if(p<1)requestAnimationFrame(tick)});});"
        "var box=document.getElementById('tpFilter');if(box){"
        "var rows=[].slice.call(document.querySelectorAll('tbody tr'));"
        "box.addEventListener('input',function(){"
        "var q=box.value.trim().toLowerCase();"
        "rows.forEach(function(r){"
        "r.style.display=!q||r.textContent.toLowerCase().indexOf(q)>=0?'':'none'})});"
        "document.addEventListener('keydown',function(e){"
        "if((e.metaKey||e.ctrlKey)&&e.key.toLowerCase()==='k'){e.preventDefault();box.focus()}})}})();</script>",
        # hash 路由:每个 tab/菜单项是独立视图;#/路由切换,浏览器前进后退可用,未知路由回落总览
        "<script>(function(){"
        "var views={};document.querySelectorAll('.view').forEach(function(v){views[v.dataset.route]=v});"
        "var links=[].slice.call(document.querySelectorAll('.pagebar .tabs a[href^=\\'#/\\'],.nav a[href^=\\'#/\\']'));"
        "function setActive(route){"
        "links.forEach(function(a){a.classList.toggle('on',a.getAttribute('href')==='#/'+route)})}"
        "function show(route){"
        "if(!views[route])route='overview';"
        "Object.keys(views).forEach(function(k){views[k].classList.toggle('on',k===route)});"
        "setActive(route);window.scrollTo(0,0)}"
        "function current(){return location.hash.replace(/^#\\//,'')||'overview'}"
        "window.addEventListener('hashchange',function(){show(current())});"
        "show(current());"
        "})();</script>",
        # 侧栏一级分组折叠
        "<script>document.querySelectorAll('[data-navcap]').forEach(function(h){"
        "h.addEventListener('click',function(){h.classList.toggle('closed')})});</script>",
        # 页内预览:点任何嵌入了原文的 md 链接,右侧抽屉渲染;没有嵌入的回退新标签
        r"<script>(function(){"
        r"var PV={};try{PV=JSON.parse(document.getElementById('tp-files').textContent)}catch(e){}"
        r"var wrap=document.getElementById('pvWrap'),body=document.getElementById('pvBody'),"
        r"title=document.getElementById('pvTitle'),raw=document.getElementById('pvRaw');"
        r"function escHtml(s){return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/\"/g,'&quot;')}"
        r"function inline(s){return s"
        r".replace(/`([^`]+)`/g,'<code>$1</code>')"
        r".replace(/\*\*([^*]+)\*\*/g,'<b>$1</b>')"
        r".replace(/\[([^\]]+)\]\(([^)\s]+)\)/g,function(m,t,u){return '<a href=\"'+u+'\" target=\"_blank\" rel=\"noopener\">'+t+'</a>'})}"
        r"function renderMd(src){"
        r"var L=escHtml(src).split('\n'),out=[],i=0;"
        r"function cells(r){r=r.replace(/^\s*\|/,'').replace(/\|\s*$/,'');"
        r"return r.split('|').map(function(c){return inline(c.trim())})}"
        r"while(i<L.length){var s=L[i];"
        r"if(/^```/.test(s)){var buf=[];i++;while(i<L.length&&!/^```/.test(L[i])){buf.push(L[i]);i++}i++;"
        r"out.push('<pre><code>'+buf.join('\n')+'</code></pre>');continue}"
        r"var h=s.match(/^(#{1,4})\s+(.*)/);"
        r"if(h){out.push('<h'+h[1].length+'>'+inline(h[2])+'</h'+h[1].length+'>');i++;continue}"
        r"if(/^\s*(-{3,}|\*{3,})\s*$/.test(s)){out.push('<hr>');i++;continue}"
        r"if(/^>/.test(s)){var b=[];while(i<L.length&&/^>/.test(L[i])){b.push(L[i].replace(/^>\s?/,''));i++}"
        r"out.push('<blockquote>'+inline(b.join(' '))+'</blockquote>');continue}"
        r"if(s.indexOf('|')>=0&&i+1<L.length&&/^\s*\|?[\s:|-]+\|?\s*$/.test(L[i+1])&&L[i+1].indexOf('-')>=0){"
        r"var rows=[];while(i<L.length&&L[i].indexOf('|')>=0){rows.push(L[i]);i++}"
        r"var t='<table><thead><tr>'+cells(rows[0]).map(function(c){return '<th>'+c+'</th>'}).join('')+'</tr></thead><tbody>';"
        r"for(var r=2;r<rows.length;r++){t+='<tr>'+cells(rows[r]).map(function(c){return '<td>'+c+'</td>'}).join('')+'</tr>'}"
        r"out.push(t+'</tbody></table>');continue}"
        r"var ml=s.match(/^(\s*)([-*]|\d+\.)\s+(.*)/);"
        r"if(ml){var ol=/\d/.test(ml[2]),tag=ol?'ol':'ul',items=[];"
        r"while(i<L.length){var m2=L[i].match(/^(\s*)([-*]|\d+\.)\s+(.*)/);"
        r"if(!m2||(/\d/.test(m2[2]))!==ol)break;"
        r"var cb=m2[3].match(/^\[([ xX~/\-])\]\s+(.*)/);"
        r"if(cb){var ck=/[xX]/.test(cb[1])?' checked':'';"
        r"items.push('<li><input type=\"checkbox\" disabled'+ck+'> '+inline(cb[2])+'</li>')}"
        r"else items.push('<li>'+inline(m2[3])+'</li>');i++}"
        r"out.push('<'+tag+'>'+items.join('')+'</'+tag+'>');continue}"
        r"if(!s.trim()){i++;continue}"
        r"var para=[s];i++;"
        r"while(i<L.length&&L[i].trim()&&!/^(#{1,4}\s|```|>|\s*([-*]|\d+\.)\s)/.test(L[i])&&L[i].indexOf('|')<0){para.push(L[i]);i++}"
        r"out.push('<p>'+inline(para.join('<br>'))+'</p>')}"
        r"return out.join('\n')}"
        r"function openPv(k){title.textContent=k;raw.href=k;"
        r"body.innerHTML=renderMd(PV[k]||'(空文件)');body.scrollTop=0;wrap.classList.add('open')}"
        r"function closePv(){wrap.classList.remove('open')}"
        r"document.getElementById('pvClose').addEventListener('click',closePv);"
        r"wrap.addEventListener('click',function(e){if(e.target===wrap)closePv()});"
        r"document.addEventListener('keydown',function(e){if(e.key==='Escape')closePv()});"
        r"document.addEventListener('click',function(e){"
        r"var a=e.target.closest?e.target.closest('a'):null;if(!a)return;"
        r"var href=a.getAttribute('href')||'';"
        r"if(a.target==='_blank'&&PV.hasOwnProperty(href)&&!e.metaKey&&!e.ctrlKey){"
        r"e.preventDefault();openPv(href)}});"
        r"})();</script>",
        "<script>" + MERMAID_JS + "</script>",
        "<script>(function(){ if (!window.mermaid) return;"
        "var m = window.mermaid.default || window.mermaid;"
        # mermaid bakes classDef colours into inline style="fill:... !important",
        # so the page repaints nodes itself — and again on theme switch.
        "window.paintMmd = function(){"
        "var light = document.documentElement.dataset.theme === 'light';"
        "var F = light ? {done:'#d7dce0', active:'#c08a3e', open:'#2f6fb5', blocked:'#9ba5af'}"
        "              : {done:'#3b444d', active:'#b5813a', open:'#2f6fb5', blocked:'#66707a'};"
        "document.querySelectorAll('.mmd g.node').forEach(function(g){"
        "var cls = g.getAttribute('class') || '';"
        "Object.keys(F).forEach(function(k){"
        "if (cls.indexOf(k) < 0) return;"
        "g.querySelectorAll('rect,polygon').forEach(function(r){ r.setAttribute('style', 'fill:'+F[k]); });"
        "g.querySelectorAll('text').forEach(function(t){"
        "t.setAttribute('style', 'fill:'+(light?'#16191c':'#ffffff')+';font-weight:600;font-size:14px'); });"
        "});});};"
        # per-diagram buttons: copy the mermaid source / open the zoom viewer.
        # sources must be captured before run() replaces the pre's content,
        # buttons must be injected after — so capture now, inject in then().
        "var viewer = document.getElementById('mmdViewer'), stage = document.getElementById('mmdStage');"
        "var pres = document.querySelectorAll('pre.mmd');"
        "for (var i = 0; i < pres.length; i++) pres[i].dataset.src = pres[i].textContent;"
        "function addButtons(){"
        "document.querySelectorAll('pre.mmd').forEach(function(pre){"
        "function mk(label, fn){ var b = document.createElement('button');"
        "b.type = 'button'; b.className = 'mmd-zoom'; b.textContent = label;"
        "b.addEventListener('click', fn); pre.appendChild(b); }"
        "mk('复制', function(e){ e.stopPropagation(); var b = e.currentTarget;"
        "navigator.clipboard.writeText(pre.dataset.src).then(function(){"
        "b.textContent = '已复制'; setTimeout(function(){ b.textContent = '复制'; }, 1600);"
        "}, function(){ b.textContent = '失败'; setTimeout(function(){ b.textContent = '复制'; }, 1600); }); });"
        "mk('放大', function(){ openViewer(pre); });"
        "if(pre.dataset.spec)mk('复制图',function(e){e.stopPropagation();"
        "window._copyDepsImg&&window._copyDepsImg(pre.dataset.spec)});"
        "});}"
        "var svg = null, tx = 0, ty = 0, sc = 1;"
        "function apply(){ if (svg) svg.style.transform = 'translate('+tx+'px,'+ty+'px) scale('+sc+')'; }"
        "function fit(){ if (!svg) return;"
        "var r = svg.getBoundingClientRect(), w = stage.clientWidth, h = stage.clientHeight;"
        "sc = Math.min(1, Math.min(w/r.width, h/r.height) * 0.92) || 1;"
        "tx = (w - r.width*sc)/2; ty = (h - r.height*sc)/2; apply(); }"
        "function openViewer(pre){ var el = pre.querySelector('svg'); if (!el) return;"
        "viewer.dataset.spec = pre.dataset.spec || '';"
        "stage.innerHTML = ''; svg = el.cloneNode(true); svg.removeAttribute('style');"
        "stage.appendChild(svg); viewer.classList.add('open'); fit(); }"
        "function closeViewer(){ viewer.classList.remove('open'); svg = null; stage.innerHTML = ''; }"
        "document.getElementById('mmdClose').addEventListener('click', closeViewer);"
        "document.addEventListener('keydown', function(e){ if (e.key === 'Escape') closeViewer(); else if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'c' && viewer.classList.contains('open') && viewer.dataset.spec){ e.preventDefault(); window._copyDepsImg && window._copyDepsImg(viewer.dataset.spec); } });"
        "stage.addEventListener('wheel', function(e){ e.preventDefault();"
        "sc = Math.max(0.2, Math.min(8, sc * (e.deltaY < 0 ? 1.15 : 0.87))); apply(); }, {passive:false});"
        "stage.addEventListener('dblclick', fit);"
        "stage.addEventListener('pointerdown', function(e){"
        "var px = e.clientX - tx, py = e.clientY - ty;"
        "stage.classList.add('dragging'); stage.setPointerCapture(e.pointerId);"
        "function move(ev){ tx = ev.clientX - px; ty = ev.clientY - py; apply(); }"
        "function up(){ stage.classList.remove('dragging');"
        "stage.removeEventListener('pointermove', move); stage.removeEventListener('pointerup', up); }"
        "stage.addEventListener('pointermove', move); stage.addEventListener('pointerup', up); });"
        "m.initialize({startOnLoad:false, securityLevel:'strict', htmlLabels:false,"
        "themeVariables:{fontSize:'14px',"
        "fontFamily:'\\\"Maple Mono\\\",\\\"JetBrains Mono\\\",ui-monospace,monospace'}});"
        "m.run({querySelector:'pre.mmd'}).then(function(){ window.paintMmd(); addButtons(); })"
        ".catch(function(e){ console.warn('mermaid 渲染失败，依赖图显示源码', e); });"
        "})();</script>",
        "</body></html>",
    ]
    return "".join(out)


def main(argv: list[str]) -> int:
    root = Path(argv[1]).resolve() if len(argv) > 1 else Path.cwd()
    scratch = root / ".scratch"
    if not scratch.is_dir():
        print(f"没有 {scratch}，这个项目还没有 .scratch 目录。", file=sys.stderr)
        return 1

    efforts, unparsed = scan(scratch)
    out_path = scratch / "progress.html"
    out_path.write_text(minify_html(render(efforts, unparsed, scratch)), encoding="utf-8")
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
