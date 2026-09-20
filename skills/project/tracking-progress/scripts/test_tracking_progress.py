"""Tests for tracking_progress.py. Run: python3 -m pytest -q"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import tracking_progress as tp


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("resolved", tp.DONE),
        ("done（2026-09-18，见 report.md）", tp.DONE),
        ("**已抵达目的地**（2026-09-18）", tp.DONE),
        ("resolved · 见 research/13.md", tp.DONE),
        ("closed（out of scope）", tp.DONE),
        ("定稿", tp.DONE),
        ("claimed", tp.ACTIVE),
        ("in-progress (phases 1-3 on branch feat/x)", tp.ACTIVE),
        ("open · **可延后**", tp.OPEN),
        ("ready-for-agent", tp.OPEN),
        ("needs-triage", tp.OPEN),
        ("", tp.OPEN),
    ],
)
def test_classify(raw, expected):
    assert tp.classify(raw) == expected


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("02, 13", ["2", "13"]),
        ("—", []),
        ("None (can start immediately)", []),
        ("无", []),
        ("I02 I04", ["I2", "I4"]),
        ("", []),
    ],
)
def test_parse_ids(raw, expected):
    assert tp.parse_ids(raw) == expected


def test_normalise_id_keeps_prefix():
    # Two numbering schemes can coexist in one effort; they must not collide.
    assert tp.normalise_id("I01") == tp.normalise_id("i1") == "I1"
    assert tp.normalise_id("01") == "1"
    assert tp.normalise_id("T01") != tp.normalise_id("01")


@pytest.mark.parametrize(
    "title,tid,rest",
    [
        ("01 — 协议层", "01", "协议层"),
        ("**I01** 骨架 + RPC", "I01", "骨架 + RPC"),
        ("23: 地图", "23", "地图"),
        ("01 · 选路器收成深模块", "01", "选路器收成深模块"),
        ("没有编号的标题", "", "没有编号的标题"),
    ],
)
def test_split_title(title, tid, rest):
    assert tp.split_title(title) == (tid, rest)


def test_split_title_keeps_underscores():
    assert tp.split_title("A `open_session` 改真") == ("", "A open_session 改真")


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_parse_issue_file_bold_fields(tmp_path):
    path = write(
        tmp_path / "issues" / "01-kinds.md",
        "# 01: 检测种类扩容\n\n**Blocked by:** None (can start immediately)\n\n"
        "**Status:** ready-for-agent\n\n- [ ] 子项不该被当成独立任务\n",
    )
    task = tp.parse_issue_file(path, "spec")
    assert (task.tid, task.status, task.blocked_by) == ("01", tp.OPEN, [])


def test_parse_issue_file_reads_blocking(tmp_path):
    path = write(
        tmp_path / "issues" / "01-x.md",
        "# 01 · 选路器\n\nStatus: ready-for-agent\nBlocked by: 02, 13\n",
    )
    assert tp.parse_issue_file(path, "spec").blocked_by == ["2", "13"]


def test_parse_issue_file_without_status_uses_directory(tmp_path):
    path = write(tmp_path / "issues" / "done" / "07-x.md", "# 07: 干完了\n")
    assert tp.parse_issue_file(path, "spec").status == tp.DONE


def test_parse_issue_file_without_status_falls_back_to_fields(tmp_path):
    path = write(tmp_path / "impl" / "01-protocol.md", "# T01 — 协议层\n\nBlocked by: —\n")
    task = tp.parse_issue_file(path, "spec")
    assert (task.tid, task.status) == ("T01", tp.OPEN)


def test_parse_issue_file_rejects_prose(tmp_path):
    path = write(tmp_path / "prior-art.md", "# 调研：先例\n\n正文。\n")
    assert tp.parse_issue_file(path, "spec") is None


def test_parse_checklist_marks(tmp_path):
    path = write(
        tmp_path / "memory.md",
        "## checkpoint\n\n"
        "- [x] **I01** 骨架 — 合并 8a155c39\n"
        "- [ ] I07 页面 B（阻塞于 I02 I04）\n"
        "- [ ] **I06** 页面 A — agent 在跑\n"
        "- [~] I08 手动标进行中\n",
    )
    tasks = tp.parse_checklist_file(path, "spec")
    assert [t.status for t in tasks] == [tp.DONE, tp.OPEN, tp.ACTIVE, tp.ACTIVE]
    assert tasks[1].blocked_by == ["I2", "I4"]


def test_dedupe_takes_furthest_status_and_keeps_file(tmp_path):
    row = tp.Task("s", "I01", "骨架", tp.DONE, source="memory.md")
    ticket = tp.Task("s", "I01", "骨架", tp.OPEN, source="impl/I01.md", from_file=True)
    merged = tp.dedupe([row, ticket])
    assert len(merged) == 1
    assert merged[0].status == tp.DONE
    assert merged[0].from_file is True


def test_dedupe_keeps_untitled_rows_apart():
    rows = [
        tp.Task("s", "", "读 CONTEXT.md", tp.DONE, source="m.md"),
        tp.Task("s", "", "跑测试", tp.DONE, source="m.md"),
    ]
    assert len(tp.dedupe(rows)) == 2


def test_resolve_blocking():
    effort = tp.Effort("s", Path("."))
    effort.tasks = [
        tp.Task("s", "01", "先做", tp.DONE),
        tp.Task("s", "02", "等 01 和 03", tp.OPEN, blocked_by=["1", "3"]),
        tp.Task("s", "03", "也要做", tp.OPEN),
    ]
    tp.resolve_blocking(effort)
    assert [t.status for t in effort.tasks] == [tp.DONE, tp.BLOCKED, tp.OPEN]


def build_repo(tmp_path: Path) -> Path:
    scratch = tmp_path / ".scratch"
    write(
        scratch / "memory.md",
        "## checkpoint\n\n- [x] **01** 第一张票\n- [ ] 没编号的收尾动作\n",
    )
    write(scratch / "alpha" / "spec.md", "# Spec\n")
    write(scratch / "alpha" / "map.md", "# Map\n\n## Destination\n\n出一份 spec。\n")
    write(
        scratch / "alpha" / "issues" / "01-first.md",
        "# 01 — 第一张票\n\nType: research\nStatus: resolved\nBlocked by: —\n",
    )
    write(
        scratch / "alpha" / "issues" / "02-second.md",
        "# 02 — 第二张票\n\nType: grilling\nStatus: open\nBlocked by: 03\n",
    )
    write(
        scratch / "alpha" / "issues" / "03-third.md",
        "# 03 — 第三张票\n\nStatus: open\nBlocked by: —\n",
    )
    write(scratch / "beta" / "issues" / "done" / "05-old.md", "# 05: 旧活\n")
    write(scratch / "beta" / "notes.md", "# 随手记\n\n没有任务。\n")
    write(scratch / "memory" / "2026-09-18.md", "- [ ] 历史账本不该被扫到\n")
    write(scratch / "research" / "deep.md", "- [ ] 调研产物不该被扫到\n")
    return tmp_path


def test_scan_end_to_end(tmp_path):
    root = build_repo(tmp_path)
    efforts, unparsed = tp.scan(root / ".scratch")
    names = {e.name: e for e in efforts}
    assert set(names) == {"alpha", "beta", tp.ROOT}
    assert names["alpha"].is_map and names["alpha"].has_spec

    alpha = {t.key: t for t in names["alpha"].tasks}
    assert alpha["1"].status == tp.DONE  # root checklist row absorbed into alpha
    assert alpha["2"].status == tp.BLOCKED
    assert alpha["3"].status == tp.OPEN
    assert alpha["1"].kind == "research"
    assert names["beta"].tasks[0].status == tp.DONE

    # The unnumbered root row has nowhere to go, so it stays at the root.
    assert len(names[tp.ROOT].tasks) == 1
    assert [p.name for p in unparsed] == ["notes.md"]


def test_absorb_skips_ambiguous_ids(tmp_path):
    """Two specs numbering from 01 must not swallow the same checklist row."""
    root = build_repo(tmp_path)
    write(
        root / ".scratch" / "beta" / "issues" / "01-dup.md",
        "# 01 — beta 也有一张 01\n\nStatus: open\n",
    )
    efforts, _ = tp.scan(root / ".scratch")
    names = {e.name: e for e in efforts}
    assert len(names[tp.ROOT].tasks) == 2


def test_render_contains_every_section(tmp_path):
    root = build_repo(tmp_path)
    scratch = root / ".scratch"
    efforts, unparsed = tp.scan(scratch)
    md = tp.render(efforts, unparsed, scratch)
    for heading in (
        "## 总览",
        "## 现在能开工的",
        "## 按 spec 分组",
        "## 阻塞关系",
        "## 久未动",
        "## 最近完成",
        "## 未能识别的文件",
    ):
        assert heading in md
    assert "```mermaid" in md
    assert "notes.md" in md
    assert "2026-09-18.md" not in md


def test_main_writes_report(tmp_path, monkeypatch, capsys):
    root = build_repo(tmp_path)
    monkeypatch.setattr(tp, "to_html", lambda path: None)
    assert tp.main(["tracking_progress.py", str(root)]) == 0
    out = (root / ".scratch" / "progress.md").read_text(encoding="utf-8")
    assert "# 任务进度" in out
    assert "UNPARSED=1" in capsys.readouterr().err


def test_main_without_scratch(tmp_path, capsys):
    assert tp.main(["tracking_progress.py", str(tmp_path)]) == 1
    assert ".scratch" in capsys.readouterr().err


def test_bar_endpoints():
    assert "0%" in tp.bar(0, 0)
    assert "100%" in tp.bar(4, 4)


def test_clip():
    assert tp.clip("短") == "短"
    assert tp.clip("x" * 30).endswith("…")
    assert '"' not in tp.clip('带"引号"的标题')


def test_normalise_id_without_digits():
    assert tp.normalise_id("Spike") == "spike"


def test_status_from_path_open_directory(tmp_path):
    path = write(tmp_path / "issues" / "open" / "09-x.md", "# 09: 待办\n")
    assert tp.parse_issue_file(path, "spec").status == tp.OPEN


def test_absorb_without_root_effort():
    efforts = {"alpha": tp.Effort("alpha", Path("."))}
    tp.absorb_root_checklist(efforts)  # must not raise
    assert list(efforts) == ["alpha"]


def test_render_empty_project(tmp_path):
    scratch = tmp_path / ".scratch"
    write(scratch / "alpha" / "spec.md", "# Spec\n")
    efforts, unparsed = tp.scan(scratch)
    md = tp.render(efforts, unparsed, scratch)
    assert "没有可直接开工的票" in md
    assert "只有 spec / 地图，没扫到票" in md
    assert "没有票声明阻塞关系" in md
    assert "还没有完成的票" in md
    assert md.rstrip().endswith("没有。")


def test_render_flags_stale_spec(tmp_path):
    scratch = tmp_path / ".scratch"
    path = write(scratch / "alpha" / "issues" / "01-x.md", "# 01: 陈年老活\n\nStatus: open\n")
    old = 1_700_000_000
    os.utime(path, (old, old))
    os.utime(path.parent, (old, old))
    os.utime(scratch / "alpha", (old, old))
    efforts, unparsed = tp.scan(scratch)
    md = tp.render(efforts, unparsed, scratch)
    assert "| alpha | 1 张 |" in md


def test_to_html_missing_script(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))
    assert tp.to_html(tmp_path / "progress.md") is None


def test_to_html_runs_converter(tmp_path, monkeypatch, capsys):
    script = tmp_path / ".claude" / "scripts" / "md2html.sh"
    write(script, "#!/bin/sh\nexit 0\n")
    monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))
    md = write(tmp_path / "progress.md", "# x\n")

    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(tp.subprocess, "run", fake_run)
    assert tp.to_html(md) == tmp_path / "progress.html"
    assert calls == [[str(script), str(md)]]


def test_to_html_reports_converter_failure(tmp_path, monkeypatch, capsys):
    script = tmp_path / ".claude" / "scripts" / "md2html.sh"
    write(script, "#!/bin/sh\nexit 1\n")
    monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))
    monkeypatch.setattr(
        tp.subprocess,
        "run",
        lambda cmd, **kw: subprocess.CompletedProcess(cmd, 1, "", "pandoc 没装"),
    )
    assert tp.to_html(write(tmp_path / "progress.md", "# x\n")) is None
    assert "pandoc 没装" in capsys.readouterr().err


def test_main_prints_html_path(tmp_path, monkeypatch, capsys):
    root = build_repo(tmp_path)
    html = root / ".scratch" / "progress.html"
    monkeypatch.setattr(tp, "to_html", lambda path: html)
    assert tp.main(["tracking_progress.py", str(root)]) == 0
    assert str(html) in capsys.readouterr().out
