#!/usr/bin/env python3
"""boardsource / views / infra.board 三模块的行覆盖补齐 — 纯进程内单测。

分三段:
  1. `skeinlib.infra.board` — markdown 渲染纯函数 (状态标签回落 / 空表)。
  2. `skeinlib.web.views` — Snapshot 边界 + 各 `_view_*` 的少见分支 (归档/坏 JSON/搜索命中)。
  3. `skeinlib.web.boardsource` — BoardSourceMixin 各成员, 用最小假宿主 (`_Host`) 满足依赖契约,
     `serve` / `_run_server` 的外部副作用 (uvicorn/浏览器/依赖安装) 全部 monkeypatch 掉。

不联网、不碰真实 `~/.claude`、不写仓库根: 一切落 `tmp_path`。
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from types import SimpleNamespace
from pathlib import Path
from typing import Any, Callable, Optional, cast

import pytest

from skeinlib.infra.board import (_subtask_status_label, _task_status_label, render_board,
                                  render_task_board)
from skeinlib.task.model import SubtaskStatus, TaskStatus
from skeinlib.utils.paths import SCRIPTS_DIR
from skeinlib.web.boardsource import BoardSourceMixin
from skeinlib.web.views import (Snapshot, _prd_parse, _spec_frontmatter, _view_archive,
                                _view_archive_list, _view_board_data, _view_search,
                                _view_task_detail)
from skeinlib.web.views import (Snapshot, _prd_parse, _spec_frontmatter, _view_archive,
                                _view_archive_list, _view_board_data, _view_search,
                                _view_task_detail)

# ══════════════════════════════════════════════════════════════════════════════
# 1. skeinlib/infra/board.py — 纯渲染函数
# ══════════════════════════════════════════════════════════════════════════════


def _t(tid: str, status: str = TaskStatus.PENDING, **kw: Any) -> dict[str, Any]:
    base: dict[str, Any] = {"id": tid, "name": f"名-{tid}", "status": status, "deps": []}
    base.update(kw)
    return base


def test_status_label_falls_back_to_raw_string() -> None:
    # 合法枚举 → 中文展示名; 非法值 (老盘/脏数据) → 原样字符串, 不抛 ValueError
    assert _task_status_label(TaskStatus.DONE) == "已完成"
    assert _task_status_label("外星状态") == "外星状态"
    assert _subtask_status_label(SubtaskStatus.RUNNING) == "运行中"
    assert _subtask_status_label("外星状态") == "外星状态"


def test_render_board_empty_and_worktree_column() -> None:
    # 无 task → 占位空行; wt_shown 决定表头/空行是 4 列还是 5 列
    assert "| - | - | - | - |\n" in render_board([], wt_shown=False)
    assert "| - | - | - | - | - |\n" in render_board([], wt_shown=True)
    assert "worktree" not in render_board([], wt_shown=False)
    # 有 task 且开 worktree 列: 无 worktree 字段回落 "-"
    out = render_board([_t("t1", TaskStatus.ACTIVE, deps=["t0"], worktree="/wt/t1"),
                        _t("t2")], wt_shown=True)
    assert "| t1 | 名-t1 | 进行中 | t0 | /wt/t1 |" in out
    assert "| t2 | 名-t2 | 待处理 | - | - |" in out


def test_render_task_board_rows_and_empty() -> None:
    # 无 subtask → 7 列占位行; 有 subtask → 依赖/技能/验收标准逐列渲染, 空列表回落 "-"
    empty = render_task_board(_t("t1"), work_active=2, gate_active=3)
    assert "| - | - | - | - | - | - | - |" in empty
    assert "work 池上限: 2" in empty and "gate 池上限: 3" in empty
    t = _t("t1", subtasks=[
        {"sid": "s1", "name": "子一", "status": SubtaskStatus.DONE,
         "depends_on": ["s0"], "acceptance": ["能跑", "有测"], "skills": ["py"]},
        {"sid": "s2", "name": "子二", "status": SubtaskStatus.PENDING},
    ])
    out = render_task_board(t, work_active=1, gate_active=1)
    assert "| s1 | 子一 | 已完成 | 100% | py | s0 | 能跑; 有测 |" in out
    assert "| s2 | 子二 | 待处理 | 2% | - | - | - |" in out


# ══════════════════════════════════════════════════════════════════════════════
# 2. skeinlib/web/views.py — Snapshot + _view_* 少见分支
# ══════════════════════════════════════════════════════════════════════════════


def _mk_snap(root: Path, tasks: Optional[list[dict[str, Any]]] = None,
             all_tasks: Optional[list[dict[str, Any]]] = None) -> Snapshot:
    """最小 Snapshot: 目录落 tmp, tasks/all_tasks 直接喂内存列表 (不走 store 扫盘)。"""
    tdir = root / "task"
    tdir.mkdir(parents=True, exist_ok=True)
    ts = tasks if tasks is not None else []
    return Snapshot(proj="p", wt_shown=False,
                    tasks_fn=lambda: ts,
                    all_tasks_fn=lambda: (all_tasks if all_tasks is not None else ts),
                    tasks_dir=tdir, archive_dir=root / "archive",
                    spec_root=root / "spec")


def test_dep_unfinished_archived_unknown_and_pending(tmp_path: Path) -> None:
    # 三条判据: 已归档 dep → 不阻塞; 未知 dep (无 per-task 目录) → 不阻塞; 已知未完成 → 阻塞
    (tmp_path / "archive" / "2026" / "08-10" / "arch1").mkdir(parents=True)
    snap = _mk_snap(tmp_path, all_tasks=[_t("open1", TaskStatus.ACTIVE),
                                         _t("done1", TaskStatus.DONE)])
    assert snap.dep_unfinished("arch1") is False
    assert snap.dep_unfinished("查无此 task") is False
    assert snap.dep_unfinished("open1") is True
    assert snap.dep_unfinished("done1") is False
    # _dep_index 只建一次 (第二轮走缓存分支)
    assert snap.dep_unfinished("open1") is True
    # archived_path: 命中归档目录; 未归档返回 None
    ap = snap.archived_path("arch1")
    assert ap is not None and ap.name == "arch1"
    assert snap.archived_path("open1") is None


def test_dep_unfinished_without_archive_dir(tmp_path: Path) -> None:
    # archive/ 目录根本不存在 → archived_ids 空集, 不因缺目录抛错
    snap = _mk_snap(tmp_path, all_tasks=[_t("a", TaskStatus.ACTIVE)])
    assert not (tmp_path / "archive").exists()
    assert snap.dep_unfinished("a") is True
    assert snap.archived_path("a") is None


def test_prd_parse_sections_and_todo_skip() -> None:
    # 只有「目标」一节 → 输出只含该节 (「验收标准」缺失时跳过, 不产空壳)
    out = _prd_parse("# 目标\n- [x] 已做\n- [ ] 未做\n散文行\n- TODO 占位\n")
    assert [s["name"] for s in out] == ["目标"]
    assert out[0]["badge"] == [1, 2]
    kinds = [(i["kind"], i["done"], i["text"]) for i in out[0]["items"]]
    assert kinds == [("check", True, "已做"), ("check", False, "未做"), ("prose", False, "散文行")]
    # 空文本 / None → 空列表
    assert _prd_parse("") == [] and _prd_parse(None) == []
    # 只有 prose 行 → badge 为 None (无 checkbox 不显示进度徽标)
    prose_only = _prd_parse("## 验收标准\n全部人工验收\n")
    assert prose_only[0]["badge"] is None


def test_board_data_survives_git_failure_and_missing_timestamps(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # git config 调用抛异常 → assignee 回落 None, 不让整个看板 500
    def _boom(*a: Any, **kw: Any) -> Any:
        raise OSError("git 不在 PATH")
    monkeypatch.setattr("subprocess.run", _boom)
    # 进行中但既无 started 也无 created → elapsed 归 0 (不拿 now() 当起点算出天文数字)
    snap = _mk_snap(tmp_path, [_t("t1", TaskStatus.ACTIVE, subtasks=[])])
    data = _view_board_data(snap)
    card = data["cards"][0]
    assert card["assignee"] is None
    assert card["elapsed"] == 0
    assert data["overview"]["estMeta"] == ""  # 总耗时 0 → 不渲染「已耗 …」


def test_task_detail_returns_none_on_broken_json(tmp_path: Path) -> None:
    # task.json 存在但不是合法 JSON → 返回 None (而非抛栈到 http 层)
    snap = _mk_snap(tmp_path)
    d = tmp_path / "task" / "t1"
    d.mkdir(parents=True)
    (d / "task.json").write_text("{ 不是 json", encoding="utf-8")
    assert _view_task_detail(snap, "t1") is None
    # 连目录都没有 → 也是 None
    assert _view_task_detail(snap, "查无此 task") is None


def test_task_detail_research_docs_and_dependents(tmp_path: Path) -> None:
    # research/*.md 全文内联 + 被依赖方 (dependents) 反查
    d = tmp_path / "task" / "t1"
    (d / "research").mkdir(parents=True)
    (d / "task.json").write_text(json.dumps({"id": "t1", "status": TaskStatus.ACTIVE,
                                             "deps": ["t0"]}), encoding="utf-8")
    (d / "prd.md").write_text("# 目标\n- [ ] 甲\n", encoding="utf-8")
    (d / "research" / "b.md").write_text("笔记B", encoding="utf-8")
    (d / "research" / "a.md").write_text("笔记A", encoding="utf-8")
    snap = _mk_snap(tmp_path, all_tasks=[
        _t("t0", TaskStatus.DONE),                    # t1 的前置
        _t("t2", TaskStatus.PENDING, deps=["t1"]),    # 依赖 t1 → 落 dependents
    ])
    det = _view_task_detail(snap, "t1")
    assert det is not None
    assert list(det["research"]) == ["a.md", "b.md"]  # 按文件名排序
    assert det["research"]["a.md"] == "笔记A"
    assert [x["id"] for x in det["depTasks"]] == ["t0"]
    assert [x["id"] for x in det["dependents"]] == ["t2"]
    assert det["docs"]["design"] is None and det["docs"]["prd"].startswith("# 目标")
    assert det["archived"] is False
    assert det["prd"][0]["name"] == "目标"


def test_archive_views_skip_incomplete_dirs(tmp_path: Path) -> None:
    # 归档目录里: 缺 task.json 的目录跳过, 坏 JSON 跳过, 合法的才进列表
    arch = tmp_path / "archive" / "2026" / "08-10"
    (arch / "empty").mkdir(parents=True)
    (arch / "broken").mkdir()
    (arch / "broken" / "task.json").write_text("{坏", encoding="utf-8")
    (arch / "good").mkdir()
    (arch / "good" / "task.json").write_text(
        json.dumps({"id": "good", "name": "已归档", "status": TaskStatus.DONE,
                    "finished": 100, "subtasks": [{"sid": "s1"}]}), encoding="utf-8")
    # task/ 里还有一个已完成但未到保留期的 task → 归档页也要列
    snap = _mk_snap(tmp_path, [_t("fresh", TaskStatus.DONE), _t("run", TaskStatus.ACTIVE)])
    lst = _view_archive_list(snap)
    assert [x["id"] for x in lst] == ["good"]
    assert lst[0]["archivedAt"] == "08-10" and lst[0]["subs"] == 1
    assert [x["id"] for x in _view_archive(snap)["tasks"]] == ["good", "fresh"]


def test_archive_views_without_archive_dir(tmp_path: Path) -> None:
    # 无 archive/ 目录 → 空列表, 不抛
    snap = _mk_snap(tmp_path, [])
    assert _view_archive_list(snap) == []
    assert _view_archive(snap) == {"tasks": []}


def test_view_search_hits_subtask_prd_and_spec(tmp_path: Path) -> None:
    # 命中四类: task / subtask / prd 正文 / spec 文件; index.md 是衍生索引, 不进结果
    spec = tmp_path / "spec" / "rules"
    spec.mkdir(parents=True)
    (spec / "index.md").write_text("关键词", encoding="utf-8")   # 衍生索引 → 跳过
    (spec / "r1.md").write_text("含关键词的规则", encoding="utf-8")
    d = tmp_path / "task" / "t1"
    d.mkdir(parents=True)
    (d / "prd.md").write_text("prd 里也有关键词", encoding="utf-8")
    snap = _mk_snap(tmp_path, [_t("t1", TaskStatus.ACTIVE, desc="关键词描述", subtasks=[
        {"sid": "s1", "name": "子", "desc": "带关键词的子任务", "status": SubtaskStatus.PENDING},
        {"sid": "s2", "name": "子二", "desc": "无关", "status": SubtaskStatus.PENDING},
    ])])
    hits = _view_search(snap, "关键词")["hits"]
    assert [(h["kind"], h["id"]) for h in hits] == [
        ("task", "t1"), ("subtask", "t1/s1"), ("prd", "t1"), ("spec", "rules/r1.md")]
    # 空查询 → 直接短路, 不扫盘
    assert _view_search(snap, "  ") == {"query": "", "hits": []}
    assert _view_search(snap, None) == {"query": "", "hits": []}


def test_spec_frontmatter_parses_scalars_arrays_and_missing() -> None:
    # `---` 包裹的 YAML 子集: 标量剥引号, `[a,b]` 转数组, 非 kv 行忽略; 无 frontmatter → ({}, 原文)
    meta, body = _spec_frontmatter(
        '---\ntitle: "标题"\nkeywords: [a, "b", \'c\']\ninclusion: auto\n# 注释行\n---\n正文\n')
    assert meta == {"title": "标题", "keywords": ["a", "b", "c"], "inclusion": "auto"}
    assert body == "正文\n"
    assert _spec_frontmatter("没有头部\n") == ({}, "没有头部\n")
    # 空数组
    assert _spec_frontmatter("---\nk: []\n---\nx")[0] == {"k": []}


# ══════════════════════════════════════════════════════════════════════════════
# 3. skeinlib/web/boardsource.py — BoardSourceMixin
# ══════════════════════════════════════════════════════════════════════════════


class _FakeStore:
    """TaskStore 的最小替身: 只提供 _snapshot 用到的两个读方法。"""

    def __init__(self, tasks: list[dict[str, Any]]) -> None:
        self._tasks = tasks

    def render_tasks(self) -> list[dict[str, Any]]:
        return self._tasks

    def all_tasks(self) -> list[dict[str, Any]]:
        return self._tasks


class _Host(BoardSourceMixin):
    """满足 mixin 依赖契约 (dir/root/tasks/archive_dir/proj/store/config/_wt_shown) 的最小宿主。"""

    _LOCK_ID_PATH = "/__skein__/id"
    _REV_PATH = "/__skein__/rev"
    _LIVE_PATH = "/__skein__/live"

    def __init__(self, root: Path, tasks: Optional[list[dict[str, Any]]] = None) -> None:
        self.root = root
        self.dir = root / ".skein"
        self.tasks = self.dir / "task"
        self.tasks.mkdir(parents=True, exist_ok=True)
        self.archive_dir = self.dir / "archive"
        self.proj = "测试项目"
        self.store = cast(Any, _FakeStore(tasks or []))

    def config(self) -> dict[str, Any]:
        return {"pools": {"work": 4, "gate": 5}}

    def _wt_shown(self) -> bool:
        return True

    def _exec_argv(self, body: dict[str, Any]) -> Optional[list[str]]:
        return None


def test_snapshot_wires_config_pools_and_store(tmp_path: Path) -> None:
    # _snapshot 把 config().pools 与 store 的两个读方法接到 Snapshot 上 (每请求构造一次)
    h = _Host(tmp_path, [_t("t1", TaskStatus.ACTIVE)])
    snap = h._snapshot()
    assert (snap.proj, snap.wt_shown) == ("测试项目", True)
    assert (snap.pool_work, snap.gate_active) == (4, 5)
    assert [t["id"] for t in snap.tasks] == ["t1"]
    assert [t["id"] for t in snap.all_tasks] == ["t1"]
    assert snap.spec_root == (h.dir / "spec").resolve()


def test_webapp_html_prefers_board_page_then_root(tmp_path: Path,
                                                  monkeypatch: pytest.MonkeyPatch) -> None:
    # Next.js static export: 优先 dist/board/index.html (SPA entry); 缺失才回落 dist/index.html
    dist = tmp_path / "dist"
    (dist / "board").mkdir(parents=True)
    (dist / "index.html").write_text("根页", encoding="utf-8")
    monkeypatch.setattr("skeinlib.web.boardsource.dist_dir", lambda: dist)
    h = _Host(tmp_path)
    assert h._webapp_html() == "根页"
    (dist / "board" / "index.html").write_text("看板页", encoding="utf-8")
    assert h._webapp_html() == "看板页"


def test_spec_rev_zero_without_dir_and_tracks_md_mtime(tmp_path: Path) -> None:
    # 无 .skein/spec/ → "0"; 有 .md → 取最大 mtime_ns, 改文件后 rev 变
    h = _Host(tmp_path)
    assert h._spec_rev() == "0"
    d = h.dir / "spec" / "rules"
    d.mkdir(parents=True)
    f = d / "a.md"
    f.write_text("v1", encoding="utf-8")
    rev1 = h._spec_rev()
    assert rev1 != "0"
    import os as _os
    st = f.stat()
    _os.utime(f, ns=(st.st_atime_ns, st.st_mtime_ns + 10_000_000))
    assert h._spec_rev() != rev1


def test_spec_tree_scans_namespaces_by_directory(tmp_path: Path) -> None:
    # namespace 靠目录扫描得 (禁硬编码白名单): 任意新目录都要出现在树里
    h = _Host(tmp_path)
    assert h._spec_tree() == {}  # 无 spec/ 目录 → 空
    spec = h.dir / "spec"
    (spec / "rules" / "cat1").mkdir(parents=True)
    (spec / "rules" / "cat1" / "a.md").write_text("x", encoding="utf-8")
    (spec / "rules" / "cat1" / "index.md").write_text("x", encoding="utf-8")      # 衍生索引 → 排除
    (spec / "rules" / "cat1" / "backlinks.md").write_text("x", encoding="utf-8")  # 同上
    (spec / "rules" / "空类目").mkdir()                                            # 无 .md → 不出现
    (spec / "自定义ns" / "c").mkdir(parents=True)
    (spec / "自定义ns" / "c" / "b.md").write_text("x", encoding="utf-8")
    (spec / ".archive").mkdir()                                                   # 点开头 → 排除
    (spec / "顶层游离.md").write_text("x", encoding="utf-8")                        # 非目录 → 忽略
    assert h._spec_tree() == {"rules": {"cat1": ["a.md"]}, "自定义ns": {"c": ["b.md"]}}


def _mk_spec_db(spec_root: Path,
                rows: list[tuple[str, str, str, str, Optional[str]]]) -> None:
    """造 .recall.db 的 spec_meta 表 (path, title, namespace, category, keywords)。"""
    spec_root.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(spec_root / ".recall.db")
    con.execute("CREATE TABLE spec_meta (path TEXT, title TEXT, namespace TEXT, "
                "category TEXT, keywords TEXT)")
    con.executemany("INSERT INTO spec_meta VALUES (?,?,?,?,?)", rows)
    con.commit()
    con.close()


def test_spec_meta_without_db_returns_empty(tmp_path: Path) -> None:
    # .recall.db 未建 (未跑过 reindex) → 空结果而非抛错
    assert _Host(tmp_path)._spec_meta() == {"items": [], "total": 0}


def test_spec_meta_filters_and_paginates(tmp_path: Path) -> None:
    h = _Host(tmp_path)
    _mk_spec_db(h.dir / "spec", [
        ("rules/a.md", "规则A", "rules", "cat1", '["kw1","kw2"]'),
        ("rules/b.md", "规则B", "rules", "cat2", '["kw3"]'),
        ("product/c.md", "产品C", "product", "cat1", "不是 JSON"),
        ("map/d.md", "地图D", "map", "", None),  # keywords 为 NULL
    ])
    # 无筛选 → 全量, 按 path 排序
    allm = h._spec_meta(page=1, page_size=10)
    assert allm["total"] == 4
    assert [i["path"] for i in allm["items"]] == ["map/d.md", "product/c.md",
                                                  "rules/a.md", "rules/b.md"]
    # keywords 坏 JSON / NULL 都回落空列表 (不让一条脏数据打爆整个列表页)
    by_path = {i["path"]: i for i in allm["items"]}
    assert by_path["product/c.md"]["keywords"] == []
    assert by_path["map/d.md"]["keywords"] == []
    assert by_path["map/d.md"]["category"] == ""
    assert by_path["rules/a.md"]["keywords"] == ["kw1", "kw2"]
    # namespace / category / keyword 三个筛选条件与分页
    assert h._spec_meta(namespace="rules")["total"] == 2
    assert h._spec_meta(category="cat1")["total"] == 2
    assert h._spec_meta(keyword="kw3")["total"] == 1
    assert h._spec_meta(namespace="rules", category="cat2")["total"] == 1
    page2 = h._spec_meta(page=2, page_size=2)
    assert [i["path"] for i in page2["items"]] == ["rules/a.md", "rules/b.md"]
    assert page2["total"] == 4  # total 是筛选后全量, 不受分页影响


def test_spec_search_without_db_returns_empty(tmp_path: Path) -> None:
    assert _Host(tmp_path)._spec_search("任意") == []


def test_spec_search_matches_and_builds_snippet(tmp_path: Path) -> None:
    h = _Host(tmp_path)
    long_title = "很长的标题" * 40  # >120 字符 → snippet 截断加省略号
    _mk_spec_db(h.dir / "spec", [
        ("rules/a.md", "规则A", "rules", "cat1", '["kw1"]'),
        ("rules/no-title.md", "", "rules", "", '["关键词甲"]'),  # 无 title → snippet 取 keywords
        ("rules/only-cat.md", "", "rules", "分类名", "坏 JSON"),  # 再回落 category
        ("rules/bare.md", "", "rules", "", None),                # 全空 → 回落 path
        ("rules/long.md", long_title, "rules", "", None),
    ])
    # 大小写不敏感 (SQL 侧 LOWER + Python 侧 lower)
    hits = h._spec_search("RULES/")
    assert len(hits) == 5
    snip = {x["path"]: x["snippet"] for x in hits}
    assert snip["rules/a.md"] == "规则A"
    assert snip["rules/no-title.md"] == "关键词甲"
    assert snip["rules/only-cat.md"] == "分类名"
    assert snip["rules/bare.md"] == "rules/bare.md"
    assert snip["rules/long.md"] == long_title[:120] + "..."
    # keywords 坏 JSON → 空列表
    assert {x["path"]: x["keywords"] for x in hits}["rules/only-cat.md"] == []
    # 命中 keywords 字段
    assert [x["path"] for x in h._spec_search("关键词甲")] == ["rules/no-title.md"]
    assert h._spec_search("查无此物") == []


def test_spec_resolve_blocks_traversal(tmp_path: Path) -> None:
    # realpath 校验: 解析后必须落在 .skein/spec/ 内, 越界一律 None
    h = _Host(tmp_path)
    root = h._spec_root()
    root.mkdir(parents=True)
    assert h._spec_resolve("rules/a.md") == root / "rules" / "a.md"
    assert h._spec_resolve(".") == root          # 解析到 root 自身也放行
    assert h._spec_resolve("../../etc/passwd") is None
    assert h._spec_resolve("..") is None
    assert h._spec_resolve("") is None
    assert h._spec_resolve("   ") is None
    assert h._spec_resolve(None) is None         # 非字符串 (前端传坏参数)
    assert h._spec_resolve(123) is None
    # resolve() 自身抛错 (内嵌 NUL 的路径) 也吞成 None, 不把 ValueError 漏到 http 层
    assert h._spec_resolve("a\0b") is None
    # resolve() 自身抛错 (内嵌 NUL 的路径) 也吞成 None, 不把 ValueError 漏到 http 层
    assert h._spec_resolve("a\0b") is None


def test_data_rev_and_task_mtimes_cover_docs(tmp_path: Path) -> None:
    # rev / per-task mtime 都要把 prd/design/findings + research/*.md 算进来,
    # 否则改文档后详情页不刷新 (「前端不刷新」bug 的典型成因)
    h = _Host(tmp_path)
    (h.dir / "task.json").write_text("{}", encoding="utf-8")
    d = h.tasks / "t1"
    (d / "research").mkdir(parents=True)
    (d / "task.json").write_text("{}", encoding="utf-8")
    watched = {p.name for p in h._task_watch_files()}
    assert {"task.json", "prd.md", "design.md", "findings.md"} <= watched
    rev1 = h._data_rev()
    mt1 = h._task_mtimes()
    assert set(mt1) == {"t1"}
    (d / "research" / "r.md").write_text("笔记", encoding="utf-8")
    assert (d / "research" / "r.md") in h._task_watch_files()
    assert h._data_rev() != rev1
    assert h._task_mtimes()["t1"] != mt1["t1"]
    # 合并 rev = data.asset, 任一变即变
    assert h._task_json_rev() == f"{h._data_rev()}.{h._asset_rev()}"


def test_build_serve_app_delegates_to_build_app(tmp_path: Path,
                                                monkeypatch: pytest.MonkeyPatch) -> None:
    # _build_serve_app 只是 build_app(DataSource seam) 的转发, 四个参数原样透传
    seen: list[Any] = []

    def _fake_build_app(*a: Any) -> str:
        seen.append(a)
        return "APP"
    monkeypatch.setattr("skeinlib.web.boardsource.build_app", _fake_build_app)
    h = _Host(tmp_path)
    assert h._build_serve_app("proj-id", True) == "APP"
    assert seen[0] == (h, "proj-id", True, None)


# ---- serve() 命令入口: 无工作区 / config 开关 / 参数折算 ----------------------


def _stub_run_server(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, Any]]:
    """把 _run_server 换成记录器 — serve() 的职责到「是否起 + 用什么参数起」为止。"""
    calls: list[dict[str, Any]] = []

    def _rec(self: Any, open_browser: bool = True, quiet: bool = False) -> None:
        calls.append({"open_browser": open_browser, "quiet": quiet})
    monkeypatch.setattr("skeinlib.web.boardsource.BoardSourceMixin._run_server", _rec)
    return calls


def test_serve_noop_without_workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # 无 .skein/config.yaml → 空跑退出 (auto 与手动都退, 只是提示级别不同)
    calls = _stub_run_server(monkeypatch)
    h = _Host(tmp_path)
    h.serve(argparse.Namespace(auto=True))
    h.serve(argparse.Namespace(auto=False))
    assert calls == []


def test_serve_respects_web_serve_switch_only_for_auto(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # config web.serve=false: monitor 自动起被拦; 手动跑是用户显式意图, 无视开关强起
    calls = _stub_run_server(monkeypatch)
    h = _Host(tmp_path)
    (h.dir / "config.yaml").write_text("web:\n  serve: false\n  board_open: true\n",
                                       encoding="utf-8")
    h.serve(argparse.Namespace(auto=True))
    assert calls == []
    h.serve(argparse.Namespace(auto=False))
    assert len(calls) == 1
    # 非 tty (pytest 捕获 stdout) → 不自动开浏览器且静默; --open 仍可强开
    assert calls[0] == {"open_browser": False, "quiet": True}
    h.serve(argparse.Namespace(auto=False, open_browser=True))
    assert calls[1]["open_browser"] is True


def test_serve_auto_starts_when_switch_on_and_debug_unmutes(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # web.serve=true → auto 也起; --debug 时即便非 tty 也不静默 (否则误判「无法启动」)
    calls = _stub_run_server(monkeypatch)
    h = _Host(tmp_path)
    (h.dir / "config.yaml").write_text("web:\n  serve: true\n", encoding="utf-8")
    h.serve(argparse.Namespace(auto=True))
    assert calls[0]["quiet"] is True
    monkeypatch.setattr("skeinlib.utils.debug.DBG.enabled", True)
    h.serve(argparse.Namespace(auto=True))
    assert calls[1]["quiet"] is False


# ---- _run_server(): lock 去重 / 依赖兜底 / uvicorn 重试 -----------------------


class _FakeTimer:
    """threading.Timer 替身 — 只记录, 不真起线程 (免测试结束后延迟弹真浏览器)。"""

    fired: list[float] = []

    def __init__(self, interval: float, fn: Callable[[], Any]) -> None:
        self.interval, self.fn = interval, fn

    def start(self) -> None:
        _FakeTimer.fired.append(self.interval)


def _stub_serve_env(monkeypatch: pytest.MonkeyPatch, run: Callable[..., Any]) -> list[Any]:
    """把 _run_server 的外部副作用全部换掉: 依赖检测 / dist 构建 / uvicorn / 浏览器 / sleep。"""
    seen: list[Any] = []

    def _run(*a: Any, **kw: Any) -> Any:
        seen.append((a, kw))
        return run(*a, **kw)
    monkeypatch.setattr("skeinlib.web.boardsource.serve_deps_present", lambda: True)
    monkeypatch.setattr("skeinlib.web.boardsource.ensure_dist_built", lambda quiet=False: None)
    monkeypatch.setitem(sys.modules, "uvicorn", cast(Any, SimpleNamespace(run=_run)))
    monkeypatch.setattr("threading.Timer", _FakeTimer)
    monkeypatch.setattr("webbrowser.open", lambda url: None)
    monkeypatch.setattr("time.sleep", lambda s: None)
    # 这三个环境变量会被 _run_server 直接写 os.environ; 先经 monkeypatch 登记, 测试结束自动还原
    monkeypatch.setenv("PYTHONPATH", "/占位")
    monkeypatch.setenv("SKEIN_SERVE_QUIET", "")
    monkeypatch.setenv("SKEIN_DEBUG", "")
    return seen


def test_run_server_reuses_existing_same_project_service(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    # lock 里的端口探测确认是同项目服务 → 直接复用并开浏览器, 绝不起第二个
    h = _Host(tmp_path)
    h._lock_file().write_text(json.dumps({"port": 54321, "project": str(h.dir.resolve())}))
    monkeypatch.setattr("skeinlib.web.boardsource.probe_same_project",
                        lambda port, proj, path: True)

    def _never() -> bool:
        raise AssertionError("已复用现有服务, 不该再走依赖检测/启动流程")
    monkeypatch.setattr("skeinlib.web.boardsource.serve_deps_present", _never)
    opened: list[str] = []
    monkeypatch.setattr("webbrowser.open", lambda url: opened.append(url))
    h._run_server(open_browser=True, quiet=False)
    assert opened == ["http://127.0.0.1:54321/"]
    assert "已在运行: http://127.0.0.1:54321/" in capsys.readouterr().out
    assert h._lock_file().exists()  # 复用路径不得删别人的 lock


def test_run_server_aborts_when_deps_install_fails(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    # lock 内容损坏 → 当作无锁继续; fastapi/uvicorn 装不上 → 报错退出, 不硬闯 uvicorn.run
    h = _Host(tmp_path)
    h._lock_file().write_text("不是 JSON")
    installed: list[bool] = []
    monkeypatch.setattr("skeinlib.web.boardsource.serve_deps_present", lambda: False)
    monkeypatch.setattr("skeinlib.web.boardsource.install_serve_deps",
                        lambda: installed.append(True))
    monkeypatch.setitem(sys.modules, "uvicorn", cast(Any, SimpleNamespace(
        run=lambda *a, **kw: (_ for _ in ()).throw(AssertionError("依赖缺失时不该启动"))) ))
    h._run_server(open_browser=False, quiet=False)
    assert installed == [True]
    err = capsys.readouterr()
    assert "看板依赖缺失" in err.out and "依赖安装失败" in err.err


def test_run_server_starts_uvicorn_and_cleans_lock(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    # 正常路径: 写 lock (随机 port) → 排浏览器定时器 → uvicorn.run 阻塞 → 退出时删自己的 lock
    h = _Host(tmp_path)
    _FakeTimer.fired = []
    lock = h._lock_file()
    seen = _stub_serve_env(monkeypatch, lambda *a, **kw: None)

    port_seen: list[int] = []

    def _run(*a: Any, **kw: Any) -> None:
        # uvicorn 阻塞期间 lock 必须在盘上 (供其它 session 探测复用)
        assert json.loads(lock.read_text())["project"] == str(h.dir.resolve())
        port_seen.append(json.loads(lock.read_text())["port"])
    monkeypatch.setitem(sys.modules, "uvicorn", cast(Any, SimpleNamespace(run=_run)))
    h._run_server(open_browser=True, quiet=False)

    assert len(port_seen) == 1 and port_seen[0] > 0
    assert not lock.exists()  # atexit 之外, 正常收尾也删 lock
    assert _FakeTimer.fired == [0.3]
    out = capsys.readouterr().out
    assert "看板服务已启动" in out and "看板服务已停止" in out.replace("\n", "")
    assert str(SCRIPTS_DIR) in os.environ["PYTHONPATH"]
    assert os.environ["SKEIN_SERVE_QUIET"] == "0"
    assert seen == []  # 本用例自带 uvicorn 替身, 上面那份未被调用


def test_run_server_quiet_mode_prints_nothing(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    # monitor 模式 (quiet=True): 启动/停止行全静默, 且 SKEIN_SERVE_QUIET 透传给 reload 子进程
    h = _Host(tmp_path)
    _stub_serve_env(monkeypatch, lambda *a, **kw: None)
    monkeypatch.setattr("skeinlib.utils.debug.DBG.enabled", True)
    h._run_server(open_browser=False, quiet=True)
    assert capsys.readouterr().out == ""
    assert os.environ["SKEIN_SERVE_QUIET"] == "1"
    assert os.environ["SKEIN_DEBUG"] == "1"  # --debug 传进 reload 子进程 (argv 不继承)


def test_run_server_retries_on_nonzero_systemexit(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # uvicorn 非零 SystemExit → 递增退避重试, 达上限 (3) 后收手并留日志
    h = _Host(tmp_path)

    def _boom(*a: Any, **kw: Any) -> None:
        raise SystemExit(2)
    seen = _stub_serve_env(monkeypatch, _boom)
    slept: list[float] = []
    monkeypatch.setattr("time.sleep", lambda s: slept.append(s))
    h._run_server(open_browser=False, quiet=True)
    assert len(seen) == 4          # 首次 + 3 次重试
    assert slept == [1, 2, 3]      # 退避 = 基数 1s × (attempt+1)
    log = (h.dir / ".skein" / "serve.log").read_text(encoding="utf-8")
    assert "exit code=2, attempt=3/3" in log
    # 启动参数锁死: app 字符串必须与 _serve_app_factory 实际所在模块一致
    assert seen[0][0][0] == "skeinlib.web.serve:_serve_app_factory"
    assert seen[0][1]["factory"] is True and seen[0][1]["reload"] is True


def test_run_server_stops_on_clean_systemexit(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # SystemExit(0) = 优雅停机 → 立即收手, 不重试
    h = _Host(tmp_path)

    def _bye(*a: Any, **kw: Any) -> None:
        raise SystemExit(0)
    seen = _stub_serve_env(monkeypatch, _bye)
    h._run_server(open_browser=False, quiet=True)
    assert len(seen) == 1
    assert "exit code=0, attempt=0/3" in (h.dir / ".skein" / "serve.log").read_text(encoding="utf-8")


def test_run_server_cleanup_tolerates_corrupt_lock(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # 收尾清理只删「本进程写的」lock: 内容读不出来时静默放过, 绝不误删别实例的锁
    h = _Host(tmp_path)
    lock = h._lock_file()

    def _corrupt(*a: Any, **kw: Any) -> None:
        lock.write_text("被别的进程改花了")
    _stub_serve_env(monkeypatch, _corrupt)
    h._run_server(open_browser=False, quiet=True)
    assert lock.read_text() == "被别的进程改花了"


def test_run_server_reraises_crash_after_max_retries(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # 非 SystemExit 崩溃: 同样重试, 达上限后原样抛出 (不吞异常), 日志记类型与消息
    h = _Host(tmp_path)

    def _crash(*a: Any, **kw: Any) -> None:
        raise RuntimeError("端口被占")
    seen = _stub_serve_env(monkeypatch, _crash)
    with pytest.raises(RuntimeError, match="端口被占"):
        h._run_server(open_browser=False, quiet=True)
    assert len(seen) == 4
    log = (h.dir / ".skein" / "serve.log").read_text(encoding="utf-8")
    assert "serve crashed: RuntimeError: 端口被占, attempt=3/3" in log
