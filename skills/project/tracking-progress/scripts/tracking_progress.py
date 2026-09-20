#!/usr/bin/env python3
"""Scan a repo's .scratch directory and render a task-progress report.

Writes .scratch/progress.md, then converts it to .scratch/progress.html via
md2html.sh when that script and pandoc are available.

Usage: python3 tracking_progress.py [repo-root]
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

# Directories under .scratch that never hold task state.
SKIP_DIRS = {"memory", "research", ".ask-ui", "node_modules", ".git"}

# Files that are structural, not tasks — never reported as unrecognised.
KNOWN_FILENAMES = {"map.md", "memory.md", "spec.md", "progress.md", "readme.md"}

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
STATUS_RE = re.compile(r"^\s*\**\s*(?:Status|状态)\s*\**\s*[:：]\s*\**\s*(.+?)\s*$", re.I | re.M)
TYPE_RE = re.compile(r"^\s*\**\s*(?:Type|类型)\s*\**\s*[:：]\s*\**\s*(.+?)\s*$", re.I | re.M)
BLOCKED_RE = re.compile(
    r"^\s*\**\s*(?:Blocked by|Blocked-by|阻塞于|依赖于)\s*\**\s*[:：]?\s*(.+?)\s*$",
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

STATUS_LABEL = {
    DONE: "已完成",
    ACTIVE: "进行中",
    OPEN: "可开工",
    BLOCKED: "被阻塞",
}


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
        resolve_blocking(effort)
        if effort.tasks:
            effort.mtime = max(effort.mtime, max(t.mtime for t in effort.tasks))

    ordered = sorted(efforts.values(), key=lambda e: e.name)
    return [e for e in ordered if e.tasks or e.is_map or e.has_spec], unparsed


ROOT = "(根目录)"

PROGRESS = {OPEN: 0, BLOCKED: 0, ACTIVE: 1, DONE: 2}


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


def resolve_blocking(effort: Effort) -> None:
    done_ids = {t.key for t in effort.tasks if t.status == DONE}
    for task in effort.tasks:
        if task.status == OPEN and any(b not in done_ids for b in task.blocked_by):
            task.status = BLOCKED


def counts(tasks: list[Task]) -> dict[str, int]:
    out = {DONE: 0, ACTIVE: 0, OPEN: 0, BLOCKED: 0}
    for task in tasks:
        out[task.status] += 1
    return out


def bar(done: int, total: int, width: int = 24) -> str:
    pct = round(done * 100 / total) if total else 0
    filled = round(pct * width / 100)
    return f"`{'█' * filled}{'░' * (width - filled)}` **{pct}%**"


def link(task: Task, scratch: Path) -> str:
    rel = os.path.relpath(task.source, scratch)
    return f"[{task.title}]({rel})"


def render(efforts: list[Effort], unparsed: list[Path], scratch: Path) -> str:
    all_tasks = [t for e in efforts for t in e.tasks]
    c = counts(all_tasks)
    total = len(all_tasks)
    now = time.time()
    out = [
        "# 任务进度",
        "",
        f"扫描 `{scratch}` · 生成于 {time.strftime('%Y-%m-%d %H:%M')}",
        "",
        "## 总览",
        "",
        f"{len(efforts)} 个 spec · {total} 张票 · "
        f"{c[DONE]} 已完成 · {c[ACTIVE]} 进行中 · {c[OPEN]} 可开工 · {c[BLOCKED]} 被阻塞",
        "",
        bar(c[DONE], total),
        "",
    ]

    actionable = [t for t in all_tasks if t.status == OPEN]
    out += ["## 现在能开工的", ""]
    if actionable:
        out += ["| spec | 票 | 类型 |", "| --- | --- | --- |"]
        out += [
            f"| {t.effort} | {t.label} · {link(t, scratch)} | {t.kind or '—'} |"
            for t in actionable
        ]
    else:
        out.append("没有可直接开工的票——要么全做完了，要么都卡在别的票后面。")
    out.append("")

    out += ["## 按 spec 分组", ""]
    for effort in efforts:
        ec = counts(effort.tasks)
        tag = " · wayfinder 地图" if effort.is_map else ""
        out += [
            f"### {effort.name}{tag}",
            "",
            f"{len(effort.tasks)} 张票 · {bar(ec[DONE], len(effort.tasks))}",
            "",
        ]
        if effort.tasks:
            out += ["| 票 | 标题 | 状态 | 阻塞于 |", "| --- | --- | --- | --- |"]
            out += [
                f"| {t.label} | {link(t, scratch)} | {STATUS_LABEL[t.status]} | "
                f"{', '.join(t.blocked_by) or '—'} |"
                for t in effort.tasks
            ]
        else:
            out.append("_只有 spec / 地图，没扫到票。_")
        out.append("")

    edges = [
        (e.name, t, b)
        for e in efforts
        for t in e.tasks
        for b in t.blocked_by
    ]
    out += ["## 阻塞关系", ""]
    if edges:
        out += ["```mermaid", "flowchart LR"]
        seen = set()
        for effort_name, task, blocker in edges:
            node = f"{slug(effort_name)}_{task.key}"
            dep = f"{slug(effort_name)}_{blocker}"
            if dep not in seen:
                out.append(f'  {dep}["{blocker}"]')
                seen.add(dep)
            if node not in seen:
                out.append(f'  {node}["{task.label} {clip(task.title)}"]')
                seen.add(node)
            out.append(f"  {dep} --> {node}")
        out += ["```", ""]
    else:
        out += ["没有票声明阻塞关系。", ""]

    stale = [
        e
        for e in efforts
        if counts(e.tasks)[DONE] < len(e.tasks)
        and (now - e.mtime) > STALE_DAYS * 86400
    ]
    out += ["## 久未动", ""]
    if stale:
        out += ["| spec | 未完成 | 最后改动 |", "| --- | --- | --- |"]
        out += [
            f"| {e.name} | {len(e.tasks) - counts(e.tasks)[DONE]} 张 | "
            f"{int((now - e.mtime) / 86400)} 天前 |"
            for e in sorted(stale, key=lambda e: e.mtime)
        ]
    else:
        out.append(f"没有超过 {STALE_DAYS} 天没动过的未完成 spec。")
    out.append("")

    # Ticket files first: checklist rows all share one file mtime, so their
    # order among themselves is arbitrary.
    recent = sorted(
        (t for t in all_tasks if t.status == DONE),
        key=lambda t: (not t.from_file, -t.mtime),
    )[:TIMELINE_LIMIT]
    out += ["## 最近完成", ""]
    if recent:
        out += ["| 日期 | spec | 票 |", "| --- | --- | --- |"]
        out += [
            f"| {time.strftime('%Y-%m-%d', time.localtime(t.mtime))} | {t.effort} | "
            f"{t.label} · {link(t, scratch)} |"
            for t in recent
        ]
    else:
        out.append("还没有完成的票。")
    out.append("")

    out += ["## 未能识别的文件", ""]
    if unparsed:
        out += [
            "这些文件扫到了但读不出任务状态。**如果其中有真任务，说明脚本漏了一种写法，"
            "该给 skill 提一张 issue 补上解析规则。**",
            "",
        ]
        out += [f"- `{os.path.relpath(p, scratch)}`" for p in unparsed]
    else:
        out.append("没有。")
    out.append("")
    return "\n".join(out)


def slug(text: str) -> str:
    return re.sub(r"\W", "_", text)


def clip(text: str, limit: int = 20) -> str:
    text = text.replace('"', "'")
    return text if len(text) <= limit else text[:limit] + "…"


def to_html(md_path: Path) -> Path | None:
    script = Path.home() / ".claude" / "scripts" / "md2html.sh"
    if not script.exists():
        return None
    result = subprocess.run(
        [str(script), str(md_path)], capture_output=True, text=True
    )
    if result.returncode != 0:
        print(result.stderr.strip(), file=sys.stderr)
        return None
    return md_path.with_suffix(".html")


def main(argv: list[str]) -> int:
    root = Path(argv[1]).resolve() if len(argv) > 1 else Path.cwd()
    scratch = root / ".scratch"
    if not scratch.is_dir():
        print(f"没有 {scratch}，这个项目还没有 .scratch 目录。", file=sys.stderr)
        return 1

    efforts, unparsed = scan(scratch)
    md_path = scratch / "progress.md"
    md_path.write_text(render(efforts, unparsed, scratch), encoding="utf-8")

    html_path = to_html(md_path)
    print(md_path)
    if html_path:
        print(html_path)
    else:
        print("md2html.sh 不可用，只生成了 markdown。", file=sys.stderr)
    if unparsed:
        print(f"UNPARSED={len(unparsed)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
