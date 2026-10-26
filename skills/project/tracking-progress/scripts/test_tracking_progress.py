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
        # 否定前缀让子串命中失效:「未完成」不是完成
        ("未完成", tp.OPEN),
        ("无法完成", tp.OPEN),
        ("取消完成", tp.OPEN),
        ("unresolved", tp.OPEN),
        ("undone", tp.OPEN),
        ("not done", tp.OPEN),
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
        # 文档引用带连字符写法要和不带的一致,前缀不能被静默丢掉
        ("ADR-0046", ["ADR46"]),
        ("ADR0046", ["ADR46"]),
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
        # 裸数字后直接接文字不是票号:日期、"404 页面修复"不能铸号
        ("2026 年计划", "", "2026 年计划"),
        ("404 页面修复", "", "404 页面修复"),
        ("3rd-party API", "", "3rd-party API"),
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
    tp.analyse(effort)  # 把 blocked_by 换算成真实依赖
    tp.resolve_blocking(effort)
    assert [t.status for t in effort.tasks] == [tp.DONE, tp.BLOCKED, tp.OPEN]


def build_repo(tmp_path: Path) -> Path:
    scratch = tmp_path / ".scratch"
    write(
        scratch / "memory.md",
        "## checkpoint\n\n- [x] **01** 第一张票\n- [ ] 没编号的收尾动作\n",
    )
    write(scratch / "alpha" / "spec.md", "# Spec\n")
    write(
        scratch / "alpha" / "map.md",
        "# Map\n\n## Destination\n\n出一份 spec。\n\n"
        "- [ ] 04 后续扩展（还没建票）\n",
    )
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
    # 未识别桶取消:feature 内文件进附件(beta/notes.md),顶层文件升格单文件 feature
    assert unparsed == []
    assert any(p.name == "notes.md" for p in names["beta"].assets)


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
    page = tp.render(efforts, unparsed, scratch)
    for anchor in (
        "id='overview'",
        "id='now'",
        "id='specs'",
        "id='memory'",
        "id='research'",
        "data-route='overview'",
        "data-route='specs'",
    ):
        assert anchor in page
    # 链接指向源文件；memory/ 与 research/ 是入口目录的一部分:列文件,不解析状态
    assert "alpha/issues/01-first.md" in page
    assert "notes.md" in page
    assert "2026-09-18.md" in page
    assert "research/deep.md" in page
    # 每个 spec 是侧栏的一个二级菜单项,指向它的独立视图(hash 路由)
    assert "href='#/spec-alpha'" in page
    assert "id='view-spec-alpha'" in page
    assert "class='proj'" in page
    assert "class='mini'" in page
    # 页内预览:md 原文嵌进页面(tp-files),点击链接抽屉渲染
    assert "id='tp-files'" in page
    assert "id='pvWrap'" in page
    assert "renderMd" in page
    assert '"memory/2026-09-18.md":' in page  # 原文确实嵌入
    # 口径必须写明：这是这版设计的核心承诺
    assert "进度 = 已完成 ÷ 总票数" in page
    assert "data-copy-spec='alpha'" in page
    assert "id='waves'" not in page
    assert "关于这份报告" not in page


def test_scan_index_lists_memory_and_research(tmp_path):
    """入口索引:memory/ 与 research/ 的 md 按改动时间倒序;目录缺失返回空。"""
    scratch = tmp_path / ".scratch"
    (scratch / "memory").mkdir(parents=True)
    (scratch / "research").mkdir()
    old = scratch / "memory" / "2026-09-18.md"
    new = scratch / "memory" / "2026-10-22.md"
    old.write_text("a")
    new.write_text("b")
    os.utime(old, (1_700_000_000, 1_700_000_000))
    mem, res = tp.scan_index(scratch)
    assert [p.name for p in mem] == ["2026-10-22.md", "2026-09-18.md"]
    assert res == []
    # 目录不存在:空列表,不抛
    mem2, res2 = tp.scan_index(tmp_path / "nowhere" / ".scratch")
    assert mem2 == [] and res2 == []


def test_render_memory_and_research_hidden_when_absent(tmp_path):
    """memory/research 目录没有文件时整段隐藏(含页签与侧栏项),和 unknown 同一口径。"""
    scratch = tmp_path / ".scratch"
    write(scratch / "alpha" / "spec.md", "# Spec\n")
    efforts, unparsed = tp.scan(scratch)
    page = tp.render(efforts, unparsed, scratch)
    for gone in ("id='memory'", "id='research'", "#memory", "#research"):
        assert gone not in page


def test_mermaid_dependency_graph(tmp_path):
    root = build_repo(tmp_path)
    efforts, _ = tp.scan(root / ".scratch")
    page = tp.render(efforts, [], root / ".scratch")
    # alpha has one real edge (02 blocked by 03); the graph rides it.
    assert "class='mmd'" in page
    assert "graph TD" in page
    # spec name links to its file, ticket id copies as spec#id
    assert "href='alpha/spec.md'" in page or "href='alpha/map.md'" in page
    assert "data-copy-spec='alpha#02'" in page
    # mermaid runtime is inlined so the page stays offline
    assert "mermaid" in page
    assert "cdn.jsdelivr" not in page


def test_view_switch_closes_preview_overlays(tmp_path):
    """切换 spec 详情(hash 路由 show)时必须关掉已打开的预览弹窗。
    用户反馈:在 spec A 展开美人鱼预览后点进 spec B,弹窗残留遮挡。"""
    root = build_repo(tmp_path)
    efforts, _ = tp.scan(root / ".scratch")
    page = tp.render(efforts, [], root / ".scratch")
    # show() 里调用两个弹窗的关闭函数——文件预览(pvWrap)与美人鱼放大(mmdViewer);
    # 关闭函数定义在后面的 IIFE 里,经 window 暴露,show 首跑时用守卫防未定义
    assert "if(window._closePv)window._closePv()" in page
    assert "if(window._closeMmd)window._closeMmd()" in page
    assert "window._closePv=closePv" in page
    assert "window._closeMmd=closeViewer" in page


def test_main_writes_report(tmp_path, monkeypatch, capsys):
    root = build_repo(tmp_path)
    assert tp.main(["tracking_progress.py", str(root)]) == 0
    page = (root / ".scratch" / "progress.html").read_text(encoding="utf-8")
    assert "任务进度" in page
    assert capsys.readouterr().err == ""


def test_main_without_scratch(tmp_path, capsys):
    assert tp.main(["tracking_progress.py", str(tmp_path)]) == 1
    assert ".scratch" in capsys.readouterr().err



def test_clip():
    assert tp.clip("短", 5) == "短"
    assert tp.clip("x" * 30, 20).endswith("…")
    assert '"' not in tp.clip('带"引号"的标题', 20)


def test_normalise_id_without_digits():
    assert tp.normalise_id("Spike") == "spike"


def test_status_from_path_open_directory(tmp_path):
    path = write(tmp_path / "issues" / "open" / "09-x.md", "# 09: 待办\n")
    assert tp.parse_issue_file(path, "spec").status == tp.OPEN


def test_status_from_path_ignores_ancestors_above_scratch(tmp_path):
    # 克隆位置里带 open/done 字样的目录不该翻转判定:只看 .scratch 以下
    path = tmp_path / "done" / ".scratch" / "f" / "issues" / "open" / "09-x.md"
    write(path, "# 09: 待办\n")
    assert tp.parse_issue_file(path, "spec").status == tp.OPEN


def test_absorb_without_root_effort():
    efforts = {"alpha": tp.Effort("alpha", Path("."))}
    tp.absorb_root_checklist(efforts)  # must not raise
    assert list(efforts) == ["alpha"]


def test_render_empty_project(tmp_path):
    scratch = tmp_path / ".scratch"
    write(scratch / "alpha" / "spec.md", "# Spec\n")
    efforts, unparsed = tp.scan(scratch)
    page = tp.render(efforts, unparsed, scratch)
    assert "没有可直接开工的票" in page
    assert "只有 spec / 地图，没扫到票" in page
    # 空区整段隐藏(含导航项);可开工为空时保留,它的空就是结论
    for gone in ("id='stale'", "id='recent'", "id='unknown'", "#stale", "#recent", "#unknown"):
        assert gone not in page


def test_render_flags_stale_spec(tmp_path):
    scratch = tmp_path / ".scratch"
    path = write(scratch / "alpha" / "issues" / "01-x.md", "# 01: 陈年老活\n\nStatus: open\n")
    old = 1_700_000_000
    os.utime(path, (old, old))
    os.utime(path.parent, (old, old))
    os.utime(scratch / "alpha", (old, old))
    efforts, unparsed = tp.scan(scratch)
    page = tp.render(efforts, unparsed, scratch)
    row = page[page.find("id='stale'"):]
    assert "alpha" in row and "1 张" in row


def test_specs_sorted_by_folder_mtime_desc(tmp_path):
    """spec 明细按文件夹最后写入时间倒序,最近动过的 spec 排最前。"""
    scratch = tmp_path / ".scratch"
    write(scratch / "old-spec" / "issues" / "01-a.md", "# 01: 老票\n\nStatus: open\n")
    write(scratch / "new-spec" / "01-b.md", "# 01: 新票\n\nStatus: open\n")
    old = 1_700_000_000
    os.utime(scratch / "old-spec" / "issues" / "01-a.md", (old, old))
    os.utime(scratch / "old-spec" / "issues", (old, old))
    os.utime(scratch / "old-spec", (old, old))
    efforts, _ = tp.scan(scratch)
    assert [e.name for e in efforts] == ["new-spec", "old-spec"]
    page = tp.render(efforts, [], scratch)
    heads = page[page.find("id='specs'"):]
    assert heads.find("new-spec") < heads.find("old-spec")






def test_blocked_by_empty_value_does_not_swallow_next_line(tmp_path):
    """`Blocked by:` with no value must not mint ids from the quote below."""
    path = write(
        tmp_path / "02-tombstone.md",
        "# 02 · 定性\n\nStatus: open\nBlocked by:\n\n"
        "> 已拍板：读法 B。术语表 `CONTEXT.md:108` 是对的。\n",
    )
    task = tp.parse_issue_file(path, "spec")
    assert task.blocked_by == []


def test_status_empty_value_does_not_swallow_next_line(tmp_path):
    path = write(
        tmp_path / "03-x.md",
        "# 03 · 例子\n\nStatus:\n\n后来才写状态 open\n",
    )
    # 空值不再把下一行当状态；没有 Status 也没有别的票面字段，就不算票
    assert tp.parse_issue_file(path, "spec") is None


def test_analyse_depths_and_unlocks():
    effort = tp.Effort("s", Path("."))
    effort.tasks = [
        tp.Task("s", "01", "地基", tp.OPEN),
        tp.Task("s", "02", "等 01", tp.BLOCKED, blocked_by=["1"]),
        tp.Task("s", "03", "等 02", tp.BLOCKED, blocked_by=["2"]),
        tp.Task("s", "04", "也等 01", tp.BLOCKED, blocked_by=["1"]),
    ]
    tp.analyse(effort)
    by = {t.key: t for t in effort.tasks}
    assert [by["1"].depth, by["2"].depth, by["3"].depth, by["4"].depth] == [0, 1, 2, 1]
    assert by["1"].unlocks == 2
    assert effort.edges == [("1", "2"), ("2", "3"), ("1", "4")]


def test_analyse_cycle_detected():
    effort = tp.Effort("s", Path("."))
    effort.tasks = [
        tp.Task("s", "01", "甲", tp.BLOCKED, blocked_by=["13"]),
        tp.Task("s", "13", "乙", tp.BLOCKED, blocked_by=["1"]),
    ]
    tp.resolve_blocking(effort)
    tp.analyse(effort)
    assert len(effort.cycle_edges) >= 1


def test_analyse_dangling_refs_do_not_block():
    effort = tp.Effort("s", Path("."))
    effort.tasks = [
        tp.Task("s", "01", "被文档引用挡住?", tp.OPEN, blocked_by=["46"]),
    ]
    tp.analyse(effort)
    tp.resolve_blocking(effort)  # 46 不存在 → 不算阻塞
    t = effort.tasks[0]
    assert t.status == tp.OPEN
    assert t.dangling == ["46"]
    assert effort.unknown_nodes == ["46"]


def test_headline_variants():
    # 有解锁：点名先做谁
    e = tp.Effort("s", Path("."))
    e.tasks = [
        tp.Task("s", "01", "地基", tp.OPEN),
        tp.Task("s", "02", "等 01", tp.BLOCKED, blocked_by=["1"]),
    ]
    tp.analyse(e)
    h = tp.headline([e])
    assert "2 张现在就能开工" not in h
    assert "先做" in h
    # 全做完
    e2 = tp.Effort("t", Path("."))
    e2.tasks = [tp.Task("t", "01", "唯一", tp.DONE)]
    assert "没有一张现在能开工" in tp.headline([e2])
    # 空项目
    assert tp.headline([]) == "没有扫到任何票。"


def test_links_open_in_new_tab():
    # 票面和 spec/地图标题的链接都开新标签页，不顶掉进度页
    t = tp.Task("s", "01", "demo", tp.DONE, source="/r/.scratch/s/01.md")
    assert 'target="_blank"' in tp.task_link(t, Path("/r/.scratch"))


def test_research_docs_listed(tmp_path):
    # spec 级 research/ 文档要出现在页面里,链接新标签页打开
    import tracking_progress as tp2
    spec = tmp_path / "s1"
    (spec / "research").mkdir(parents=True)
    (spec / "spec.md").write_text("# spec\n")
    (spec / "research" / "01-notes.md").write_text("note\n")
    efforts, _ = tp2.scan(tmp_path)
    e = next(e for e in efforts if e.name == "s1")
    assert len(e.research) == 1


def test_ticket_establishment_marks(tmp_path):
    """未建票(map/清单行、无票面文件)与票已建齐的 spec 在页面上要分得开。"""
    root = build_repo(tmp_path)
    scratch = root / ".scratch"
    efforts, _ = tp.scan(scratch)
    page = tp.render(efforts, [], scratch)
    # alpha: map 上有 04 无票文件 → 未建票徽章 + 票行「未建」标 + 图上虚线
    assert "未建票 1" in page  # map 上的 04;根清单的无编号行算在根 effort 头上
    assert "<i class='tbdmark'>未建</i>" in page
    assert "classDef tbd stroke-dasharray:5 5" in page
    assert "票已建齐" in page  # beta 全部有票面文件
    # 总览表带「未建」列
    assert "<th class='num'>未建</th>" in page


def _bare_task(tid: str) -> tp.Task:
    return tp.Task(effort="d", tid=tid, title="任务", status=tp.OPEN, blocked_by=[],
                   kind="", source="", mtime=0, raw_status="open", from_file=True)


def _bare_effort(n: int, edges: list[tuple[str, str]] | None = None):
    return tp.Effort(name="d", path=Path("/d"), tasks=[_bare_task(f"T{i:02d}") for i in range(1, n + 1)],
                     edges=edges or [], cycle_edges=[])


def test_mermaid_grid_all_isolated():
    """全孤立票:按 ⌈√n⌉ 列切隐形链摊成网格,不再一竖条。"""
    g = tp.mermaid_graph(_bare_effort(12))
    assert g.count("~~~") == 8  # 4 列,每列 3 节点,链 = n - cols


def test_mermaid_grid_edge_cases():
    g1 = tp.mermaid_graph(_bare_effort(1))
    assert "~~~" not in g1  # 单节点无所谓分布
    g3 = tp.mermaid_graph(_bare_effort(3))
    assert g3.count("~~~") == 1  # 2 列:3-2=1 条链


def test_mermaid_no_grid_when_edges_exist():
    g = tp.mermaid_graph(_bare_effort(6, [("T1", "T2")]))  # 边键用归一化后的 key
    assert "~~~" not in g  # 有真依赖时 dagre 正常布局,不加隐形链


def test_now_view_feature_cells_link_to_detail(tmp_path):
    """可开工/停滞/最近表里那列是 feature(.scratch/<feature>/ 单位),不是 spec;
    单元格要能点进该 feature 的独立视图。"""
    root = build_repo(tmp_path)
    efforts, _ = tp.scan(root / ".scratch")
    page = tp.render(efforts, [], root / ".scratch")
    assert "<th style='width:130px'>feature</th>" in page  # 可开工表头
    assert ">spec</th>" not in page
    # 可开工行的 feature 名是指向详情视图的链接
    assert "<a href='#/spec-alpha'>alpha</a>" in page


def test_memory_view_stubs_and_on_demand(tmp_path):
    """决策档案=变更审计流:生成端只写日存根+统计,决策内容不进 HTML;
    实时解析靠 tp-files + ledger 脚本。"""
    root = build_repo(tmp_path)
    scratch = root / ".scratch"
    (scratch / "memory" / "2026-10-22.md").write_text(
        "# 决策\n\n## 主题一\n\n"
        "- 改成: 网格分布 | 原本: 一竖条 | 我说: 要网格 | 为什么: 实测 | 否掉了: 长条\n"
        "- 遗留: 旧渲染器未删\n",
        encoding="utf-8",
    )
    efforts, _ = tp.scan(scratch)
    page = tp.render(efforts, [], scratch)
    assert "class='mstub' data-mem='memory/2026-10-22.md'" in page
    assert "1 条规整 · 3 行原文" in page
    assert "class='mstats'" in page
    # 内容只在 tp-files 嵌入里出现一次,不在视图 HTML 里重复
    assert page.count("网格分布") == 1
    assert "LEDGER" not in page  # 脚本以内联 <script> 注入,不经名字引用
    assert "parseLedger" in page and "mstub" in page


def test_top_level_unknown_md_becomes_single_file_feature(tmp_path):
    """顶层未识别 md(如 平台管理页-重设计.md)是一个 feature,不再进未识别桶。"""
    root = build_repo(tmp_path)
    scratch = root / ".scratch"
    (scratch / "平台管理页-重设计.md").write_text("# 平台管理页重设计\n草稿,还没有 spec/ticket。\n", encoding="utf-8")
    efforts, unparsed = tp.scan(scratch)
    sf = [e for e in efforts if e.name == "平台管理页-重设计"]
    assert sf and sf[0].single is not None
    assert unparsed == []
    page = tp.render(efforts, unparsed, scratch)
    assert "id='view-spec-平台管理页-重设计'" in page       # 独立视图
    assert "href='#/spec-平台管理页-重设计'" in page        # 侧栏/功能台可进
    assert ">单文件</span>" in page                         # 徽标(纯标签不可点)
    assert "id='unknown'" not in page                       # 未识别桶已取消
    assert '"平台管理页-重设计.md":' in page                 # 原文已嵌入预览


def test_feature_assets_and_dirs(tmp_path):
    """feature 目录内的 design.md 进附件,design-demos/ 作为资产目录列出。"""
    root = build_repo(tmp_path)
    scratch = root / ".scratch"
    (scratch / "alpha" / "design.md").write_text("# 设计\n线框描述。\n", encoding="utf-8")
    (scratch / "alpha" / "原型图.png").write_bytes(b"\x89PNG")
    (scratch / "alpha" / "tmp.csv").write_text("a,b\n1,2\n", encoding="utf-8")
    dd = scratch / "alpha" / "design-demos"
    dd.mkdir()
    (dd / "A.html").write_text("<b>a</b>", encoding="utf-8")
    (dd / "B.html").write_text("<b>b</b>", encoding="utf-8")
    (dd / "A-v2.png").write_bytes(b"\x89PNG fake")  # 同名 png 当封面(取 -v2 后缀最新)
    efforts, _ = tp.scan(scratch)
    alpha = next(e for e in efforts if e.name == "alpha")
    assert any(p.name == "design.md" for p in alpha.assets)
    # design-demos 按语义识别为设计样例区,不再进通用资产 chip
    assert alpha.asset_dirs == [] and alpha.design_dir is not None and alpha.design_dir.name == "design-demos"
    page = tp.render(efforts, _, scratch)
    # 附件条:文件 chip;设计样例区:每个样例一张卡
    assert "class='chipf'" in page and "design.md" in page
    assert "design-demos/ · 2 文件" not in page
    assert "设计样例" in page and "class='democard'" in page
    assert ">A<" in page and ">B<" in page  # 卡片名渲染用 stem
    assert "html · " in page
    # html 样例卡面 = 活渲染 iframe;图片文件卡面 = img
    assert "<iframe src='alpha/design-demos/A.html'" in page
    assert "<iframe src='alpha/design-demos/B.html'" in page
    assert "<img src='alpha/design-demos/A-v2.png'" in page
    # 文件清单:未归类的非 md 文件一个不漏
    assert any(p.name == "原型图.png" for p in alpha.extra_files)
    assert any(p.name == "tmp.csv" for p in alpha.extra_files)
    assert "原型图.png" in page and "tmp.csv" in page
    assert '"alpha/design.md":' in page                     # 附件原文进预览嵌入


def test_md_title_extraction():
    # 前 10 行内的 h1 → 「h1（文件名）」
    assert tp.md_title("# 进度页重设计\n正文\n", "spec.md") == "进度页重设计（spec.md）"
    # YAML frontmatter 跳过,取正文里的 h1
    assert tp.md_title("---\ntitle: x\n---\n# 真标题\n", "spec.md") == "真标题（spec.md）"
    # ``` 围栏内的 # 行不是标题
    assert tp.md_title("```bash\n# 注释\n```\n", "a.md") == "a.md"
    # 无 h1 → 回退文件名
    assert tp.md_title("只有正文,没有标题\n", "notes.md") == "notes.md"


def test_render_badges_are_plain_labels(tmp_path):
    """徽章去链接化:kind 全是 span 不带 href/target,展示入口移到 docbar。"""
    root = build_repo(tmp_path)
    scratch = root / ".scratch"
    efforts, _ = tp.scan(scratch)
    page = tp.render(efforts, [], scratch)
    assert "<span class='kind'>spec</span>" in page
    assert "<span class='kind'>wayfinder 地图</span>" in page
    assert "class='kind' href" not in page


def test_render_docbar_and_tp_titles(tmp_path):
    """docbar 是新展示入口,标题用生成期 h1;tp-titles JSON 通道存在。"""
    root = build_repo(tmp_path)
    scratch = root / ".scratch"
    (scratch / "alpha" / "spec.md").write_text("# Alpha 规格\n正文\n", encoding="utf-8")
    efforts, _ = tp.scan(scratch)
    page = tp.render(efforts, [], scratch)
    assert "class='docbar'" in page
    assert "href='alpha/spec.md'" in page
    assert "id='tp-titles'" in page
    assert "Alpha 规格（spec.md）" in page  # 生成期提取,不是文件名
    assert "TITLES[k]||k" in page


def test_render_data_attachments_embedded_and_beautify_fns(tmp_path):
    """非 md 数据附件保持可点,内容进 tp-files 弹窗美化;其余文件回退新标签。"""
    root = build_repo(tmp_path)
    scratch = root / ".scratch"
    (scratch / "alpha" / "data.json").write_text('{"k": 1}\n', encoding="utf-8")
    (scratch / "alpha" / "table.csv").write_text("a,b\n1,2\n", encoding="utf-8")
    (scratch / "alpha" / "conf.yaml").write_text("k: v\n", encoding="utf-8")
    (scratch / "alpha" / "diagram.png").write_bytes(b"\x89PNG")
    efforts, _ = tp.scan(scratch)
    page = tp.render(efforts, [], scratch)
    # 数据附件进预览通道
    for key in ('"alpha/data.json":', '"alpha/table.csv":', '"alpha/conf.yaml":'):
        assert key in page
    # 弹窗内美化函数存在,openPv 按后缀分发
    for fn in ("renderCsv", "parseCsv", "renderJson", "hlYaml", "extOf"):
        assert fn in page
    # 附件在底部独立区块,顶部 assetbar 不复存在
    assert "class='filebox'" in page
    assert "class='assetbar'" not in page
    # png 进 tp-imgs base64 data URI 通道,弹窗直显;条目不再带 ↗
    assert "id='tp-imgs'" in page
    assert '"alpha/diagram.png": "data:image/png;base64,' in page
    assert "href='alpha/diagram.png' target='_blank'" in page
    assert ">diagram.png ↗</a>" not in page


def test_render_asset_dir_expandable(tmp_path):
    """asset_dirs 目录条目可展开:details/summary 列出目录内每个文件。"""
    root = build_repo(tmp_path)
    scratch = root / ".scratch"
    dd = scratch / "alpha" / "mockups"
    dd.mkdir()
    (dd / "A.png").write_bytes(b"\x89PNG")
    (dd / "B.png").write_bytes(b"\x89PNG")
    efforts, _ = tp.scan(scratch)
    alpha = next(e for e in efforts if e.name == "alpha")
    assert alpha.asset_dirs and alpha.asset_dirs[0][0] == "mockups"
    page = tp.render(efforts, [], scratch)
    assert "<details class='fdir' open><summary>mockups/ · 2 文件</summary>" in page
    assert "href='alpha/mockups/A.png'" in page
    assert "href='alpha/mockups/B.png'" in page


def test_render_asset_dir_nested_tree(tmp_path):
    """asset_dirs 按相对路径建树:子目录递归嵌套 details/summary,文件为叶子。"""
    root = build_repo(tmp_path)
    scratch = root / ".scratch"
    dd = scratch / "alpha" / "mockups"
    (dd / "v1" / "deep").mkdir(parents=True)
    (dd / "v1" / "deep" / "x.png").write_bytes(b"\x89PNG")
    (dd / "v1" / "a.txt").write_text("a\n", encoding="utf-8")
    (dd / "top.md").write_text("# 顶\n", encoding="utf-8")
    efforts, _ = tp.scan(scratch)
    alpha = next(e for e in efforts if e.name == "alpha")
    assert alpha.asset_dirs and alpha.asset_dirs[0][0] == "mockups"
    page = tp.render(efforts, [], scratch)
    # 顶层 summary 用递归文件数
    assert "<details class='fdir' open><summary>mockups/ · 3 文件</summary>" in page
    # 两层子目录各自一层 details,嵌套出现
    assert "<details class='fdir' open><summary>v1/ · 2 文件</summary>" in page
    assert "<details class='fdir' open><summary>deep/ · 1 文件</summary>" in page
    # 嵌套结构:deep 的 details 出现在 v1 的 details 之后、顶层闭合之前
    top = page.index("<summary>mockups/")
    v1 = page.index("<summary>v1/")
    deep = page.index("<summary>deep/")
    assert top < v1 < deep
    # 叶子文件条目规则不变
    assert "href='alpha/mockups/v1/deep/x.png'" in page
    assert "href='alpha/mockups/top.md'" in page


def test_render_html_design_embedded_with_iframe_srcdoc(tmp_path):
    """html 设计稿原文进 tp-files,openPv 有 iframe srcdoc + sandbox 分支。"""
    root = build_repo(tmp_path)
    scratch = root / ".scratch"
    dd = scratch / "alpha" / "design-demos"
    dd.mkdir()
    (dd / "A.html").write_text(
        "<!DOCTYPE html><html><body><script>alert(1)</script><b>稿</b></body></html>",
        encoding="utf-8",
    )
    efforts, _ = tp.scan(scratch)
    page = tp.render(efforts, [], scratch)
    assert '"alpha/design-demos/A.html":' in page
    assert 'sandbox=\\"allow-scripts allow-same-origin\\"' in page
    assert "srcdoc=" in page
    # 卡片条目不再带 ↗
    assert ">A ↗</a>" not in page


def test_render_image_data_uri_per_type(tmp_path):
    """png/jpg/gif/svg 按各自 MIME 转 base64 data URI 进 tp-imgs。"""
    root = build_repo(tmp_path)
    scratch = root / ".scratch"
    (scratch / "alpha" / "a.png").write_bytes(b"\x89PNG")
    (scratch / "alpha" / "b.jpg").write_bytes(b"\xff\xd8\xff")
    (scratch / "alpha" / "c.gif").write_bytes(b"GIF8")
    (scratch / "alpha" / "d.svg").write_text("<svg/>", encoding="utf-8")
    efforts, _ = tp.scan(scratch)
    page = tp.render(efforts, [], scratch)
    assert '"alpha/a.png": "data:image/png;base64,' in page
    assert '"alpha/b.jpg": "data:image/jpeg;base64,' in page
    assert '"alpha/c.gif": "data:image/gif;base64,' in page
    assert '"alpha/d.svg": "data:image/svg+xml;base64,' in page


def test_render_rich_budget_fallback_and_fair_share(tmp_path, monkeypatch):
    """超预算条目回退 ↗ 新标签;预算按文件大小升序分配,小文件不被饿死。"""
    root = build_repo(tmp_path)
    scratch = root / ".scratch"
    (scratch / "alpha" / "big.html").write_text("B" * 500, encoding="utf-8")
    (scratch / "alpha" / "small.html").write_text("S" * 100, encoding="utf-8")
    (scratch / "alpha" / "big.png").write_bytes(b"P" * 500)
    monkeypatch.setattr(tp, "PV_HTML_BUDGET", 200)
    monkeypatch.setattr(tp, "PV_IMG_BUDGET", 100)
    efforts, _ = tp.scan(scratch)
    page = tp.render(efforts, [], scratch)
    # small.html 在预算内进 tp-files;big.html 超预算回退 ↗ 新标签
    assert '"alpha/small.html":' in page
    assert '"alpha/big.html":' not in page
    assert ">big.html ↗</a>" in page
    # big.png 超图片预算,回退 ↗
    assert '"alpha/big.png":' not in page
    assert ">big.png ↗</a>" in page


def test_render_unknown_text_extension_embedded(tmp_path):
    """未知扩展文本(utf-8 可解码、前 8KB 无 NUL)原文进 tp-files 弹窗通道。"""
    root = build_repo(tmp_path)
    scratch = root / ".scratch"
    (scratch / "alpha" / "util.py").write_text("print('hi')\n", encoding="utf-8")
    (scratch / "alpha" / "run.log").write_text("line1\nline2\n", encoding="utf-8")
    efforts, _ = tp.scan(scratch)
    page = tp.render(efforts, [], scratch)
    assert '"alpha/util.py":' in page
    assert '"alpha/run.log":' in page
    assert ">util.py ↗</a>" not in page


def test_render_binary_non_image_falls_back_new_tab(tmp_path):
    """解码失败的二进制非图片不进弹窗通道,回退 ↗ 新标签。"""
    root = build_repo(tmp_path)
    scratch = root / ".scratch"
    (scratch / "alpha" / "blob.bin").write_bytes(b"\x00\x01\x02\xff\xfe")
    efforts, _ = tp.scan(scratch)
    page = tp.render(efforts, [], scratch)
    assert '"alpha/blob.bin":' not in page
    assert ">blob.bin ↗</a>" in page


def test_render_video_pdf_not_embedded_no_arrow(tmp_path):
    """mp4/pdf 不进 tp-files/tp-imgs 通道、条目不带 ↗(拦截器接住进弹窗)。"""
    root = build_repo(tmp_path)
    scratch = root / ".scratch"
    (scratch / "alpha" / "demo.mp4").write_bytes(b"\x00\x00\x00\x18ftypmp42")
    (scratch / "alpha" / "doc.pdf").write_bytes(b"%PDF-1.4\n")
    efforts, _ = tp.scan(scratch)
    page = tp.render(efforts, [], scratch)
    assert '"alpha/demo.mp4":' not in page
    assert '"alpha/doc.pdf":' not in page
    assert ">demo.mp4 ↗</a>" not in page
    assert ">doc.pdf ↗</a>" not in page


def test_render_docx_keeps_new_tab_arrow(tmp_path):
    """office 与其余二进制维持 ↗ 新标签,不接进弹窗。"""
    root = build_repo(tmp_path)
    scratch = root / ".scratch"
    (scratch / "alpha" / "r.docx").write_bytes(b"PK\x00\x00")
    efforts, _ = tp.scan(scratch)
    page = tp.render(efforts, [], scratch)
    assert '"alpha/r.docx":' not in page
    assert ">r.docx ↗</a>" in page


def test_openpv_video_pdf_interceptor_source(tmp_path):
    """openPv 有 video(相对 src + error 降级 ↗)与 pdf iframe 分支;拦截器
    按 media 扩展名接住 _blank 条目,metaKey/ctrlKey 逃生口保留。"""
    root = build_repo(tmp_path)
    scratch = root / ".scratch"
    efforts, _ = tp.scan(scratch)
    page = tp.render(efforts, [], scratch)
    assert "v.controls=true;v.preload='metadata'" in page
    assert "v.src=k" in page
    assert "该格式无法在浏览器播放" in page
    assert 'iframe class=\\"pv-frame\\" src=' in page
    assert "/^(mp4|m4v|mov|webm|pdf)$/.test(extOf(href))" in page
    assert "!e.metaKey&&!e.ctrlKey" in page


def test_render_webp_bmp_data_uri(tmp_path):
    """webp/bmp 按各自 MIME 转 base64 data URI 进 tp-imgs。"""
    root = build_repo(tmp_path)
    scratch = root / ".scratch"
    (scratch / "alpha" / "p.webp").write_bytes(b"RIFF\x00\x00WEBP")
    (scratch / "alpha" / "q.bmp").write_bytes(b"BM\x00\x00")
    efforts, _ = tp.scan(scratch)
    page = tp.render(efforts, [], scratch)
    assert '"alpha/p.webp": "data:image/webp;base64,' in page
    assert '"alpha/q.bmp": "data:image/bmp;base64,' in page


def test_dir_files_not_duplicated_in_extra_files(tmp_path):
    """目录树内的文件不再在外层 extra_files 平铺区重复;顶层散文件保留。"""
    root = build_repo(tmp_path)
    scratch = root / ".scratch"
    dd = scratch / "alpha" / "mockups"
    dd.mkdir()
    (dd / "x.txt").write_text("x\n", encoding="utf-8")
    (dd / "note.md").write_text("普通文档,无任务清单\n", encoding="utf-8")
    (scratch / "alpha" / "loose.txt").write_text("l\n", encoding="utf-8")
    efforts, _ = tp.scan(scratch)
    alpha = next(e for e in efforts if e.name == "alpha")
    assert all("mockups" not in p.parts for p in alpha.extra_files)
    assert all(p.name != "note.md" for p in alpha.assets)  # 目录内 md 也不进外层附件区
    assert any(p.name == "loose.txt" for p in alpha.extra_files)
    page = tp.render(efforts, [], scratch)
    assert page.count("href='alpha/mockups/x.txt'") == 1


def test_fdir_default_open(tmp_path):
    """目录树 details 生成期带 open 属性(无脚本依赖,默认展开)。"""
    root = build_repo(tmp_path)
    scratch = root / ".scratch"
    dd = scratch / "alpha" / "mockups"
    (dd / "v1").mkdir(parents=True)
    (dd / "v1" / "x.txt").write_text("x\n", encoding="utf-8")
    efforts, _ = tp.scan(scratch)
    page = tp.render(efforts, [], scratch)
    assert "<details class='fdir' open><summary>mockups/" in page
    assert "<details class='fdir' open><summary>v1/" in page
    assert "<details class='fdir'><summary>" not in page  # 无一漏网
