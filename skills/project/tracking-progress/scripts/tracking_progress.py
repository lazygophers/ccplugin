#!/usr/bin/env python3
"""Scan a repo's .scratch directory and render a task-progress report.

Writes .scratch/progress.html — a single self-contained page, no network,
no build step. Open it directly in a browser.

Design: data-publication style after Our World in Data — every number states
how it was counted, finished work greys out, and the one accent colour is
reserved for work you can start right now.

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
SKIP_DIRS = {"memory", "research", ".ask-ui", "node_modules", ".git"}

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
LEAD_ID_RE = re.compile(r"^\**\s*([A-Za-z]{0,3}\d{1,4})\**\s*[—\-·:：.、)]?\s*(.*)$")
ID_TOKEN_RE = re.compile(r"[A-Za-z]{0,3}\d{1,4}")
# Strip markdown emphasis only — `_` is part of identifiers like open_session.
MD_NOISE_RE = re.compile(r"[*`]")

DONE, ACTIVE, OPEN, BLOCKED = "done", "active", "open", "blocked"

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


def classify(text: str) -> str:
    """Map a free-form status string onto done/active/open."""
    head = re.split(r"[·（(，,。]", MD_NOISE_RE.sub("", text or ""), maxsplit=1)[0]
    head = head.strip().lower()
    if not head:
        return OPEN
    for word in DONE_WORDS:
        if word in head:
            return DONE
    for word in ACTIVE_WORDS:
        if word in head:
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
    match = re.match(r"\s*([A-Za-z]*)0*(\d+)", tid or "")
    if not match:
        return (tid or "").strip().lower()
    return match.group(1).upper() + match.group(2)


def split_title(title: str) -> tuple[str, str]:
    """Return (id, remaining title) for '01 — foo'; id is '' when absent."""
    match = LEAD_ID_RE.match(MD_NOISE_RE.sub("", title).strip())
    if match and match.group(2):
        return match.group(1), match.group(2).strip()
    return "", MD_NOISE_RE.sub("", title).strip()


def status_from_path(path: Path) -> str | None:
    parts = {p.lower() for p in path.parts}
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
        stem_id = LEAD_ID_RE.match(path.stem)
        tid = stem_id.group(1) if stem_id and stem_id.group(2) else ""
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
        effort.tasks = dedupe(effort.tasks)
        # analyse first: it splits blocked_by into real deps and dangling
        # refs, so blocking only counts ids that actually exist.
        analyse(effort)
        resolve_blocking(effort)
        if effort.tasks:
            effort.mtime = max(effort.mtime, max(t.mtime for t in effort.tasks))

    ordered = sorted(efforts.values(), key=lambda e: e.name)
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

CSS = """
  :root{
    --ink:#16191c; --ink-2:#4d565f; --ink-3:#6e7781;
    --rule:#dfe3e7; --rule-2:#eef1f3;
    --open:#1d5b9e; --open-fill:#2f6fb5;
    --active:#8a5a15; --active-fill:#c08a3e;
    --blocked:#5b6570; --blocked-fill:#9ba5af;
    --done-fill:#d7dce0; --bg:#ffffff;
    --sans:-apple-system,BlinkMacSystemFont,"PingFang SC","Noto Sans CJK SC","Hiragino Sans GB",sans-serif;
    --serif:Georgia,"Songti SC","Noto Serif CJK SC","STSong",serif;
    --mono:ui-monospace,"SF Mono",Menlo,Consolas,monospace;
  }
  *{box-sizing:border-box}
  html{scroll-behavior:smooth;scroll-padding-top:56px}
  body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.6 var(--sans);-webkit-font-smoothing:antialiased}
  a{color:var(--open);text-decoration:none;border-bottom:1px solid rgba(29,91,158,.28)}
  a:hover{border-bottom-color:var(--open)}
  .wrap{max-width:1180px;margin:0 auto;padding:0 28px}
  nav{position:sticky;top:0;z-index:20;background:rgba(255,255,255,.96);border-bottom:1px solid var(--rule);backdrop-filter:blur(6px)}
  nav .wrap{display:flex;gap:22px;align-items:center;height:44px;overflow-x:auto}
  nav b{font:600 13px/1 var(--sans);color:var(--ink);white-space:nowrap}
  nav a{font-size:13px;color:var(--ink-2);border:0;white-space:nowrap}
  nav a:hover{color:var(--open)}
  header{padding:48px 0 22px}
  h1{font:400 34px/1.28 var(--serif);margin:0 0 12px;letter-spacing:-.2px;max-width:26em}
  h1 em{font-style:normal;color:var(--open)}
  .standfirst{font-size:15px;color:var(--ink-2);margin:0;max-width:52em}
  .standfirst code{font:12.5px var(--mono);color:var(--ink-2)}
  section{padding:30px 0;border-top:1px solid var(--rule)}
  h2{font:600 19px/1.4 var(--sans);margin:0 0 4px}
  .sub{font-size:13px;color:var(--ink-2);margin:0 0 18px;max-width:62em}
  .note{font-size:12.5px;line-height:1.65;color:var(--ink-2);margin:12px 0 0;padding-left:11px;border-left:2px solid var(--rule)}
  .note b{color:var(--ink);font-weight:600}
  .note code{font:12px var(--mono)}
  .statline{display:flex;flex-wrap:wrap;gap:0 30px;margin:0 0 22px;font-size:13.5px;color:var(--ink-2)}
  .statline span{font:600 13.5px var(--mono);color:var(--ink)}
  .stack{display:flex;height:34px;width:100%;border:1px solid var(--rule);background:#fff}
  .stack i{display:block;height:100%}
  .stack i+i{border-left:1px solid #fff}
  .ticks{display:flex;width:100%;margin-top:0}
  .tick{position:relative;padding:9px 0 0}
  .tick::before{content:"";position:absolute;left:0;top:0;width:1px;height:7px;background:var(--rule)}
  .tick .k{display:block;font:600 13px/1.3 var(--sans);padding-left:8px;white-space:nowrap}
  .tick .v{display:block;font:12px/1.4 var(--mono);color:var(--ink-2);padding-left:8px;white-space:nowrap}
  .tick.low{padding-top:50px}
  .tick.low::before{height:48px}
  .k-done{color:var(--ink-3)} .k-active{color:var(--active)} .k-open{color:var(--open)} .k-blocked{color:var(--blocked)}
  table{width:100%;border-collapse:collapse;font-size:14px}
  th{text-align:left;font:600 12px/1.4 var(--sans);color:var(--ink-2);letter-spacing:.04em;padding:0 10px 7px 0;border-bottom:1px solid var(--ink);white-space:nowrap}
  th.num,td.num{text-align:right;padding-right:16px}
  td{padding:7px 10px 7px 0;border-bottom:1px solid var(--rule-2);vertical-align:top}
  tr:hover td{background:#f7f9fa}
  td.lbl{font:12.5px var(--mono);color:var(--ink-2);white-space:nowrap;width:44px}
  td.spec{font:12.5px var(--mono);color:var(--ink-2);white-space:nowrap;width:130px}
  td.t{max-width:0;width:100%}
  td.t a{display:inline-block;max-width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;vertical-align:bottom}
  td.meta{font:12.5px var(--mono);color:var(--ink-2);white-space:nowrap}
  .st{font:12px/1 var(--sans);white-space:nowrap}
  .st::before{content:"";display:inline-block;width:8px;height:8px;margin-right:6px;vertical-align:1px}
  .st-open{color:var(--open);font-weight:600} .st-open::before{background:var(--open-fill)}
  .st-active{color:var(--active);font-weight:600} .st-active::before{background:var(--active-fill)}
  .st-blocked{color:var(--blocked)} .st-blocked::before{background:var(--blocked-fill)}
  .st-done{color:var(--ink-3)} .st-done::before{background:var(--done-fill)}
  tr.r-done td.t a{color:var(--ink-3);border-bottom-color:var(--rule)}
  tr.r-done td.lbl{color:var(--ink-3)}
  .unlocks{font:600 13px var(--mono);color:var(--open)}
  .unlocks-0{font:13px var(--mono);color:var(--ink-3);font-weight:400}
  .spec-head{display:flex;align-items:baseline;gap:14px;flex-wrap:wrap;margin:34px 0 4px;padding-top:14px;border-top:1px solid var(--rule)}
  .spec-head h3{font:600 17px/1.3 var(--mono);margin:0}
  .spec-head .kind{font-size:12px;color:var(--ink-2);border:1px solid var(--rule);padding:1px 6px}
  .spec-head .cnt{font-size:13px;color:var(--ink-2);margin-left:auto;font-family:var(--mono)}
  .minibar{display:flex;height:9px;width:100%;margin:10px 0 3px;background:#fff;border:1px solid var(--rule-2)}
  .minibar i{display:block;height:100%}
  .minibar i+i{border-left:1px solid #fff}
  .minicap{display:flex;justify-content:space-between;font:12px var(--mono);color:var(--ink-2);margin-bottom:12px}
  .waves{margin-top:6px;overflow-x:auto}
  .wave-title{font:600 13px var(--mono);margin:22px 0 2px;color:var(--ink)}
  .waves svg{display:block;height:auto;overflow:visible}
  .colhead{font:600 12px var(--sans);fill:var(--ink)}
  .colsub{font:11.5px var(--sans);fill:var(--ink-2)}
  .n-label{font:12px var(--mono)}
  .n-title{font:12px var(--sans)}
  .empty{font-size:13px;color:var(--ink-2);padding:14px 0 4px;border-bottom:1px solid var(--rule-2)}
  .filelist{list-style:none;margin:14px 0 0;padding:0}
  .filelist li{font:13px var(--mono);padding:8px 0;border-bottom:1px solid var(--rule-2)}
  footer{border-top:1px solid var(--ink);margin-top:40px;padding:22px 0 60px;font-size:12.5px;line-height:1.75;color:var(--ink-2)}
  footer b{color:var(--ink);font-weight:600;display:block;margin-bottom:6px;font-size:13px}
"""

NW, NH, GY, CG, TOP, PAD = 150, 38, 9, 34, 44, 2
NODE_FILL = {OPEN: "#2f6fb5", BLOCKED: "#ffffff", ACTIVE: "#c08a3e"}
NODE_STROKE = {OPEN: "#1d5b9e", BLOCKED: "#9ba5af", ACTIVE: "#8a5a15"}
NODE_TEXT = {OPEN: "#ffffff", BLOCKED: "#16191c", ACTIVE: "#16191c"}


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def clip(text: str, n: int) -> str:
    text = text.replace('"', "'")
    return text if len(text) <= n else text[: n - 1] + "…"


def rel(source: str, scratch: Path) -> str:
    return os.path.relpath(source, scratch)


def task_link(task: Task, scratch: Path) -> str:
    if task.source:
        return f'<a href="{esc(rel(task.source, scratch))}">{esc(task.title)}</a>'
    return esc(task.title)


def wave_svg(effort: Effort, scratch: Path) -> str:
    """Layered dependency diagram: columns by depth, bezier edges, no network.

    Only unfinished tickets are drawn: edges between resolved tickets are
    history, and a graph of done work answers no question the reader has.
    """
    by_key = {t.key: t for t in effort.tasks if t.tid}
    nodes = [t for t in by_key.values() if t.status != DONE]
    if not any(a in {t.key for t in nodes} or b in {t.key for t in nodes}
               for a, b in effort.edges):
        return ""
    nodes = sorted(nodes, key=lambda t: t.depth)

    cols: dict[int, list[Task]] = {}
    for t in nodes:
        cols.setdefault(t.depth, []).append(t)
    for depth in cols:
        cols[depth].sort(key=lambda t: (len(t.tid), t.tid))

    pos = {}
    for ci, depth in enumerate(sorted(cols)):
        for ri, t in enumerate(cols[depth]):
            pos[t.key] = (PAD + ci * (NW + CG), TOP + ri * (NH + GY))

    n_cols = len(cols)
    width = PAD * 2 + n_cols * NW + (n_cols - 1) * CG
    height = TOP + max(len(c) for c in cols.values()) * (NH + GY)
    cycle = set(effort.cycle_edges)

    out = [f'<svg viewBox="0 0 {width} {height + 6}" style="min-width:{width}px">']
    for ci, depth in enumerate(sorted(cols)):
        x = PAD + ci * (NW + CG)
        first = "现在能开工 · " if depth == 0 else f"等前 {depth} 层 · "
        out += [
            f'<text class="colhead" x="{x}" y="14">第 {depth} 波</text>',
            f'<text class="colsub" x="{x}" y="30">{first}{len(cols[depth])} 张</text>',
            f'<line x1="{x}" y1="37" x2="{x + NW}" y2="37" stroke="#dfe3e7"/>',
        ]

    edges_svg = []
    for a, b in effort.edges:
        if a not in pos or b not in pos:
            continue
        x1, y1 = pos[a]
        x2, y2 = pos[b]
        y1, y2 = y1 + NH / 2, y2 + NH / 2
        is_cycle = (a, b) in cycle
        dash = ' stroke-dasharray="4 3" stroke="#8a5a15"' if is_cycle else ""
        width_attr = 1.4 if is_cycle else 1
        edges_svg.append(
            f'<path d="M{x1 + NW} {y1} C{x1 + NW + CG / 2} {y1} {x2 - CG / 2} {y2} '
            f'{x2} {y2}" fill="none" stroke-width="{width_attr}"'
            + (dash or ' stroke="#c2c9cf"')
            + "/>"
        )

    unknown = set(effort.unknown_nodes)
    node_svg = []
    for t in nodes:
        x, y = pos[t.key]
        s = t.status
        node_svg.append(
            f'<g><title>{esc(t.tid + " " + t.title)}</title>'
            f'<rect x="{x}" y="{y}" width="{NW}" height="{NH}" '
            f'fill="{NODE_FILL.get(s, "#fff")}" stroke="{NODE_STROKE.get(s, "#c6ccd2")}"/>'
            f'<text class="n-label" x="{x + 9}" y="{y + 17}" fill="{NODE_TEXT.get(s, "#16191c")}" '
            f'font-weight="600">{esc(t.tid)}</text>'
            f'<text class="n-title" x="{x + 9}" y="{y + 30}" '
            f'fill="{NODE_TEXT.get(s, "#6e7781")}">{esc(clip(t.title, 17))}</text></g>'
        )
    # Cycle edges last so they draw on top of the nodes.
    out += edges_svg + node_svg + [f"</svg>"]
    return "".join(out)


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

    out = [
        "<!DOCTYPE html><html lang='zh-Hans'><head><meta charset='utf-8'>",
        "<meta name='viewport' content='width=device-width,initial-scale=1'>",
        f"<title>任务进度 · {esc(project)}</title>",
        f"<style>{CSS}</style></head><body>",
        "<nav><div class='wrap'>",
        f"<b>任务进度 · {esc(project)}</b>",
        "<a href='#now'>现在能开工</a><a href='#waves'>阻塞与解锁波次</a>"
        "<a href='#specs'>按 spec 明细</a><a href='#stale'>久未动</a>"
        "<a href='#recent'>最近完成</a><a href='#unknown'>未能识别</a>",
        "</div></nav><div class='wrap'>",
        "<header>",
        f"<h1>{headline(efforts)}</h1>",
        "<p class='standfirst'>",
        f"口径：扫描 <code>{esc(str(scratch))}</code> 下 {len(efforts)} 个 spec 目录的票面文件与 "
        f"<code>memory.md</code> 勾选行，生成于 {time.strftime('%Y-%m-%d %H:%M')}。"
        "一次快照，无历史记录——本页所有数字都由这一次扫描直接数出来，没有跨时间的统计。",
        "</p></header>",
        "<section id='overview' style='border-top:0;padding-top:8px'>",
        "<h2>总览</h2>",
        f"<p class='sub'>全部 {total} 张票按状态切成四段，段宽 = 该状态的票数占总数的比例。"
        "标签直接写在各段起点下方。</p>",
        "<div class='statline'>",
        f"<div>spec <span>{len(efforts)}</span> 个</div>",
        f"<div>票 <span>{total}</span> 张</div>",
        f"<div>总进度 <span>{pct}%</span>（{c[DONE]} ÷ {total}）</div>" if total else "",
        "</div>",
        f"<div class='stack'>{band}</div><div class='ticks'>{ticks}</div>",
        "<p class='note'>",
        "<b>进度 = 已完成 ÷ 总票数</b>，被阻塞的票也算在分母里——所以这个百分比是"
        "「全部要做的事完成了多少」，不是「手头能推进的事完成了多少」。<br>",
        "<b>四种状态是一条单向的路</b>：被阻塞 → 可开工 → 进行中 → 已完成，票只前进不后退。<br>",
        "<b>一张票 = 一个票面文件，或 <code>memory.md</code> 里的一行勾选</b>。两种来源同等计数，"
        "所以「已完成」里可能包含「写 spec.md」这类过程记录，不等于功能数。",
        "</p></section>",
    ]

    open_now = sorted(
        (t for t in all_tasks if t.status == OPEN),
        key=lambda t: (-t.unlocks, t.effort, t.tid),
    )
    out += [
        "<section id='now'>",
        f"<h2>现在能开工的 · {len(open_now)} 张</h2>",
        "<p class='sub'>未完成、没有前置票挡着、也没人在做的票。按「直接解锁」从多到少排——"
        "解锁得多的票，做完能让更多票动起来。</p>",
    ]
    if open_now:
        out += [
            "<table><thead><tr><th style='width:130px'>spec</th><th style='width:44px'>票</th>"
            "<th>标题</th><th style='width:70px'>类型</th><th class='num'>解锁</th></tr></thead>",
        ]
        out += [
            "<tbody>"
            + "".join(
                f"<tr><td class='spec'>{esc(t.effort)}</td>"
                f"<td class='lbl'>{esc(t.label)}</td>"
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

    out += [
        "<section id='waves'>",
        "<h2>阻塞与解锁波次</h2>",
        "<p class='sub'>阻塞是一张有向图：箭头 A → B 表示「A 不做完，B 就动不了」。"
        "这里按<b>最长前置链</b>把票排进波次——第 0 波是没有任何前置的票（也就是「现在能开工」），"
        "第 N 波要等前面 N 层全部做完。列头就是标签，图里不再放图例。</p>",
    ]
    graphs = [e for e in efforts if e.edges]
    if graphs:
        for effort in graphs:
            out += [
                f"<p class='wave-title'>{esc(effort.name)}</p>",
                f"<div class='waves'>{wave_svg(effort, scratch)}</div>",
            ]
        notes = [
            "<b>波次 = 到这张票的最长前置链长度</b>。它是最坏情况下的等待深度，不是排期——"
            "同一波的票彼此独立，可以并行。"
        ]
        cycles = sum(len(e.cycle_edges) for e in graphs)
        if cycles:
            names = "、".join(
                f"{esc(e.name)} {' / '.join(f'{a} ↔ {b}' for a, b in e.cycle_edges)}"
                for e in graphs
                if e.cycle_edges
            )
            notes.append(
                f"<b>虚线 = 环</b>：两张票互相阻塞，谁都开不了工，需要人工拆。"
                f"本次扫描命中 <b>{cycles} 处</b>（{names}）。"
            )
        unknown = [(e.name, e.unknown_nodes) for e in graphs if e.unknown_nodes]
        if unknown:
            listed = "、".join(
                f"{esc(name)} 的 {'、'.join(ids)}" for name, ids in unknown
            )
            notes.append(
                "<b>空心虚线框 = 引用了扫描范围之外的票号</b>，本次有这些："
                f"<b>{listed}</b>。它们被当作「已不存在的前置」，不拦路，"
                "但也说明票面里的编号可能写错了。"
            )
        out.append("<p class='note'>" + "<br>".join(notes) + "</p>")
    else:
        out.append("<p class='empty'>没有票声明阻塞关系。</p>")
    out.append("</section>")

    out.append("<section id='specs'><h2>按 spec 明细</h2>")
    for effort in efforts:
        ec = {s: 0 for s in STATUS_LABEL}
        for t in effort.tasks:
            ec[t.status] += 1
        et = len(effort.tasks)
        epct = round(ec[DONE] * 100 / et) if et else 0
        minibar, _ = stacked_bar(et, ec, "") if et else ("", "")
        out += [
            "<div class='spec-head'>",
            f"<h3>{esc(effort.name)}</h3>",
            "<span class='kind'>wayfinder 地图</span>" if effort.is_map else "",
            "<span class='kind'>spec</span>" if effort.has_spec else "",
            f"<span class='cnt'>{et} 张 · {ec[DONE]} 已完成</span></div>",
            f"<div class='minibar'>{minibar}</div>",
            f"<div class='minicap'><span>{STATUS_LABEL[DONE]} {ec[DONE]}</span>"
            f"<span>{epct}%</span></div>" if et else "",
        ]
        if et:
            out += [
                "<table><thead><tr><th style='width:44px'>票</th><th>标题</th>"
                "<th style='width:64px'>状态</th><th style='width:110px'>阻塞于</th>"
                "<th class='num'>解锁</th></tr></thead><tbody>",
            ]
            for t in effort.tasks:
                meta = []
                if t.dangling:
                    meta.append(
                        "<s style='color:#a33'>"
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
                    f"<td class='lbl'>{esc(t.label)}</td>"
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
    out.append("</section>")

    stale = [
        e
        for e in efforts
        if any(t.status != DONE for t in e.tasks)
        and (now - e.mtime) > STALE_DAYS * 86400
    ]
    out += ["<section id='stale'>", "<h2>久未动</h2>",
            f"<p class='sub'>超过 {STALE_DAYS} 天没有任何文件改动、且还有未完成票的 spec。</p>"]
    if stale:
        rows = sorted(stale, key=lambda e: e.mtime)
        out += [
            "<table><thead><tr><th>spec</th><th class='num'>未完成</th>"
            "<th class='num'>最后改动</th></tr></thead><tbody>",
            "".join(
                f"<tr><td class='spec'>{esc(e.name)}</td>"
                f"<td class='num'>{sum(1 for t in e.tasks if t.status != DONE)} 张</td>"
                f"<td class='num'>{int((now - e.mtime) / 86400)} 天前</td></tr>"
                for e in rows
            ),
            "</tbody></table>",
        ]
    else:
        out.append("<p class='empty'>没有搁置超过两周的 spec。</p>")
    out.append("</section>")

    recent = sorted(
        (t for t in all_tasks if t.status == DONE),
        key=lambda t: (not t.from_file, -t.mtime),
    )[:TIMELINE_LIMIT]
    out += [
        "<section id='recent'>",
        f"<h2>最近完成 · {len(recent)} 条</h2>",
        "<p class='sub'>按源文件修改时间倒序，最多 "
        f"{TIMELINE_LIMIT} 条。票面文件排在勾选行前面——勾选行共用同一个文件时间，"
        "彼此之间没有先后。</p>",
    ]
    if recent:
        out += [
            "<table><thead><tr><th style='width:110px'>日期</th><th style='width:130px'>spec</th>"
            "<th>标题</th></tr></thead><tbody>",
            "".join(
                f"<tr class='r-done'><td class='lbl'>"
                f"{time.strftime('%Y-%m-%d', time.localtime(t.mtime))}</td>"
                f"<td class='spec'>{esc(t.effort)}</td>"
                f"<td class='t'>{task_link(t, scratch)}</td></tr>"
                for t in recent
            ),
            "</tbody></table>",
        ]
    else:
        out.append("<p class='empty'>还没有完成的票。</p>")
    out.append("</section>")

    out += [
        "<section id='unknown'>",
        "<h2>未能识别的文件</h2>",
        "<p class='sub'>扫描时读不出任务状态的 markdown 文件。如果里面其实有真任务，"
        "说明这个工具漏了一种写法——那是工具的问题，不是你的。</p>",
    ]
    if unparsed:
        out += [
            "<ul class='filelist'>",
            "".join(
                f"<li><a href='{esc(rel(str(p), scratch))}'>{esc(rel(str(p), scratch))}</a></li>"
                for p in unparsed
            ),
            "</ul>",
        ]
    else:
        out.append("<p class='empty'>没有。全部文件都读出了状态，或本就不含任务。</p>")
    out.append("</section></div>")

    out += [
        "<footer><div class='wrap'><b>关于这份报告</b>",
        "tracking-progress 生成 · 数据来自 .scratch 目录的原始文件，没有数据库、"
        "没有服务端、没有第二份真相。本页不联网：双击打开即完整可用。</div></footer>",
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
    out_path.write_text(render(efforts, unparsed, scratch), encoding="utf-8")
    print(out_path)
    if unparsed:
        print(f"UNPARSED={len(unparsed)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
