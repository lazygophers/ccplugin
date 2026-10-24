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
    assert ">单文件</a>" in page                            # 徽标
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
