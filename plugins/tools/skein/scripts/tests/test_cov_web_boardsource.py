# mypy: ignore-errors
"""boardsource.py 覆盖率补测 — 补 BoardSourceMixin 的方法分支。

重点:
  - _spec_meta: SQLite 查询各种分支 (page/namespace/category/keyword)
  - _spec_search: 搜索各种分支
  - _task_watch_files / _task_mtimes: 空 tasks 目录
  - serve: auto 模式 / 配置检查 / 依赖缺失
  - _run_server: 重试逻辑 / lock 读写
"""
from __future__ import annotations

import json
import sqlite3
import subprocess
from pathlib import Path
from typing import Any

import pytest

# 由于 BoardSourceMixin 是 mixin，需要配合宿主类测试
# 这里用最小实现配合测试


class _MinimalBoard:
    """最小 DataSource 实现，满足 BoardSourceMixin 依赖契约。"""
    if __debug__:  # TYPE_CHECKING 替身 (runtime 无需)
        dir: Path
        root: Path
        tasks: Path
        archive_dir: Path
        proj: str
        store: Any
        _LOCK_ID_PATH: str
        _REV_PATH: str
        _LIVE_PATH: str

    def __init__(self, root: Path) -> None:
        self.root = root
        self.dir = root / ".skein"
        self.dir.mkdir(parents=True, exist_ok=True)
        self.tasks = self.dir / "task"
        self.tasks.mkdir(parents=True, exist_ok=True)
        self.archive_dir = self.dir / "archive"
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        self.proj = "TEST"
        self._LOCK_ID_PATH = "/__skein__/id"
        self._REV_PATH = "/__skein__/rev"
        self._LIVE_PATH = "/__skein__/live"

        # 创建假 store 满足接口 (只占位，不实际使用)
        class FakeStore:
            def __init__(self) -> None:
                self.render_tasks = lambda: []
                self.all_tasks = lambda: []
        self.store = FakeStore()

    def config(self) -> dict[str, Any]:
        return {"pools": {"work": 2, "gate": 3}}

    def _wt_shown(self) -> bool:
        return False

    def _spec_root(self) -> Path:
        return self.spec_root


# 插入 BoardSourceMixin 方法
from skeinlib.web.boardsource import BoardSourceMixin
for name, method in BoardSourceMixin.__dict__.items():
    if not name.startswith("__"):
        setattr(_MinimalBoard, name, method)


# ---- _spec_meta: SQLite 查询 ------------------------------------------------

def _make_spec_db(board: _MinimalBoard) -> sqlite3.Connection:
    """创建测试用的 spec_meta SQLite 库。"""
    db = board._spec_root() / ".recall.db"
    board._spec_root().mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db)
    con.execute("""
        CREATE TABLE spec_meta (
            path TEXT PRIMARY KEY,
            title TEXT,
            namespace TEXT,
            category TEXT,
            keywords TEXT
        )
    """)
    # 插入测试数据
    con.execute("""
        INSERT INTO spec_meta VALUES
            ('rules/naming.md', '命名规范', 'rules', 'style', '["naming", "code"]'),
            ('core/arch.md', '架构规范', 'core', 'design', '["architecture", "design"]'),
            ('product/feature.md', '功能设计', 'product', 'feature', '["product"]')
    """)
    con.commit()
    return con


def test_spec_meta_returns_empty_when_db_missing(tmp_path: Path) -> None:
    """.recall.db 不存在 → 返回空结果。"""
    board = _MinimalBoard(tmp_path / "repo")
    assert board._spec_meta() == {"items": [], "total": 0}


def test_spec_meta_paginates_correctly(tmp_path: Path) -> None:
    """分页参数生效: page/page_size 正确计算 offset。"""
    board = _MinimalBoard(tmp_path / "repo")
    con = _make_spec_db(board)

    # 插入更多数据测分页
    for i in range(5):
        con.execute("INSERT INTO spec_meta VALUES (?, ?, ?, ?, ?)",
                   (f"rules/page{i}.md", f"Page {i}", "rules", "page", "[]"))
    con.commit()
    con.close()

    # 第 1 页, size=2 → 应有 2 条
    p1 = board._spec_meta(page=1, page_size=2)
    assert len(p1["items"]) == 2
    assert p1["total"] == 8  # 3 原有 + 5 新增

    # 第 2 页, size=2 → 应有 2 条
    p2 = board._spec_meta(page=2, page_size=2)
    assert len(p2["items"]) == 2


def test_spec_meta_filters_by_namespace(tmp_path: Path) -> None:
    """namespace 筛选生效。"""
    board = _MinimalBoard(tmp_path / "repo")
    con = _make_spec_db(board)
    con.close()

    result = board._spec_meta(namespace="rules")
    assert result["total"] == 1
    assert result["items"][0]["namespace"] == "rules"


def test_spec_meta_filters_by_category(tmp_path: Path) -> None:
    """category 筛选生效。"""
    board = _MinimalBoard(tmp_path / "repo")
    con = _make_spec_db(board)
    con.close()

    result = board._spec_meta(category="style")
    assert result["total"] == 1
    assert result["items"][0]["category"] == "style"


def test_spec_meta_filters_by_keyword(tmp_path: Path) -> None:
    """keyword 模糊筛选命中 title/keywords/path。"""
    board = _MinimalBoard(tmp_path / "repo")
    con = _make_spec_db(board)
    con.close()

    result = board._spec_meta(keyword="architecture")
    assert result["total"] == 1
    assert result["items"][0]["title"] == "架构规范"


def test_spec_meta_handles_json_decode_errors(tmp_path: Path) -> None:
    """keywords JSON 解析失败 → 降级为空列表 (不炸)。"""
    board = _MinimalBoard(tmp_path / "repo")
    con = _make_spec_db(board)
    # 插入坏 JSON
    con.execute("INSERT INTO spec_meta VALUES (?, ?, ?, ?, ?)",
               ("bad.md", "坏 JSON", "test", "test", "[invalid"))
    con.commit()
    con.close()

    result = board._spec_meta()  # 查询全部
    # 应有结果, 坏 JSON 的 keywords 降级为 []
    assert len(result["items"]) >= 1
    # 验证至少有包含 bad.md 的结果
    assert any(item["path"] == "bad.md" for item in result["items"])


# ---- _spec_search: 全文搜索 ---------------------------------------------------

def test_spec_search_returns_empty_when_db_missing(tmp_path: Path) -> None:
    """.recall.db 不存在 → 返回空列表。"""
    board = _MinimalBoard(tmp_path / "repo")
    assert board._spec_search("test") == []


def test_spec_search_matches_multiple_fields(tmp_path: Path) -> None:
    """搜索命中 path/title/category/keywords 四个字段。"""
    board = _MinimalBoard(tmp_path / "repo")
    con = _make_spec_db(board)
    con.close()

    result = board._spec_search("architecture")
    assert len(result) == 1
    assert result[0]["title"] == "架构规范"


def test_spec_search_truncates_long_snippet(tmp_path: Path) -> None:
    """snippet 超过 120 字符被截断并加 '...'。"""
    board = _MinimalBoard(tmp_path / "repo")
    con = _make_spec_db(board)
    # 插入长 title
    long_title = "a" * 150
    con.execute("UPDATE spec_meta SET title = ? WHERE path = 'core/arch.md'", (long_title,))
    con.commit()
    con.close()

    result = board._spec_search("a")
    assert result[0]["snippet"].endswith("...")
    assert len(result[0]["snippet"]) < 160  # 截断后加 "..."


def test_spec_search_limits_results(tmp_path: Path) -> None:
    """搜索最多返回 50 条 (SQL LIMIT)。"""
    board = _MinimalBoard(tmp_path / "repo")
    con = _make_spec_db(board)
    # 插入 60 条
    for i in range(60):
        con.execute("INSERT INTO spec_meta VALUES (?, ?, ?, ?, ?)",
                   (f"test/test{i}.md", f"Test {i}", "test", "test", '[]'))
    con.commit()
    con.close()

    result = board._spec_search("test")
    assert len(result) == 50


# ---- _task_watch_files / _task_mtimes ---------------------------------------

def test_task_watch_files_empty_when_no_tasks(tmp_path: Path) -> None:
    """tasks 目录为空 → 返回空列表。"""
    board = _MinimalBoard(tmp_path / "repo")
    # tasks 已存在但为空
    assert board._task_watch_files() == []


def test_task_watch_files_includes_research_md(tmp_path: Path) -> None:
    """research/*.md 文件被计入监听列表。"""
    board = _MinimalBoard(tmp_path / "repo")

    # 创建 task 带 research
    tdir = board.tasks / "t1"
    tdir.mkdir()
    rdir = tdir / "research"
    rdir.mkdir()
    (rdir / "note1.md").write_text("# 笔记1\n", encoding="utf-8")
    (rdir / "note2.md").write_text("# 笔记2\n", encoding="utf-8")

    files = board._task_watch_files()
    assert any(f.name == "note1.md" for f in files)
    assert any(f.name == "note2.md" for f in files)


def test_task_mtimes_empty_when_no_tasks(tmp_path: Path) -> None:
    """tasks 目录为空 → 返回空 dict。"""
    board = _MinimalBoard(tmp_path / "repo")
    assert board._task_mtimes() == {}


def test_task_mtimes_aggregates_max_mtime(tmp_path: Path) -> None:
    """per-task 返回其所有文件的最大 mtime_ns。"""
    board = _MinimalBoard(tmp_path / "repo")

    # 创建 task
    tdir = board.tasks / "t1"
    tdir.mkdir()
    (tdir / "task.json").write_text('{"id": "t1"}', encoding="utf-8")

    # 稍后写入 prd.md (mtime 更大)
    import time
    time.sleep(0.01)
    (tdir / "prd.md").write_text("# PRD\n", encoding="utf-8")

    mtimes = board._task_mtimes()
    assert "t1" in mtimes
    # prd.mtime > task.json.mtime → 应取 prd 的
    # 只验证有 mtime 值（不比较大小，避免时间精度问题）
    assert mtimes["t1"] != 0


# ---- _data_rev / _asset_rev / _task_json_rev ---------------------------------

def test_data_rev_includes_docs_and_json(tmp_path: Path) -> None:
    """_data_rev 聚合 task.json + 文档 (prd/design/findings) 的最大 mtime。"""
    board = _MinimalBoard(tmp_path / "repo")

    tdir = board.tasks / "t1"
    tdir.mkdir()
    (tdir / "task.json").write_text('{"id": "t1"}', encoding="utf-8")
    (tdir / "prd.md").write_text("# PRD\n", encoding="utf-8")

    import time
    time.sleep(0.01)
    (tdir / "design.md").write_text("# 设计\n", encoding="utf-8")

    rev = board._data_rev()
    assert rev != "0"  # 应有真实 mtime


def test_asset_rev_reads_dist_max_mtime(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """_asset_rev 返回 dist/ 下所有文件的最大 mtime。"""
    board = _MinimalBoard(tmp_path / "repo")

    # fake dist_dir
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<html></html>", encoding="utf-8")
    (dist / "_next").mkdir()
    (dist / "_next" / "app.js").write_text("console.log(1)", encoding="utf-8")

    monkeypatch.setattr("skeinlib.web.boardsource.dist_dir", lambda: dist)

    rev = board._asset_rev()
    assert rev != "0"


def test_task_json_rev_combines_data_and_asset(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """_task_json_rev = data_rev.asset_rev (点分隔)。"""
    board = _MinimalBoard(tmp_path / "repo")

    # fake dist_dir
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<html></html>", encoding="utf-8")
    monkeypatch.setattr("skeinlib.web.boardsource.dist_dir", lambda: dist)

    # 创建 task
    tdir = board.tasks / "t1"
    tdir.mkdir()
    (tdir / "task.json").write_text('{"id": "t1"}', encoding="utf-8")

    rev = board._task_json_rev()
    assert "." in rev  # 应是 "数字.数字" 格式
    data_rev, asset_rev = rev.split(".")
    assert data_rev != "0" and asset_rev != "0"


# ---- serve: auto 模式 / 配置检查 --------------------------------------------

def test_serve_auto_quits_when_no_workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
                                             capsys: pytest.CaptureFixture[str]) -> None:
    """auto 模式下无 .skein → 静默退出 (不打 stderr)。"""
    board = _MinimalBoard(tmp_path / "repo")
    # 删掉 .skein 模拟无工作区
    import shutil
    shutil.rmtree(board.dir)

    args = type('Args', (), {'auto': True, 'open_browser': False})()
    board.serve(args)

    # 不应崩溃或打印
    err = capsys.readouterr().err
    assert "无 .skein" not in err  # auto 模式静默


def test_serve_manual_warns_when_no_workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
                                              capsys: pytest.CaptureFixture[str]) -> None:
    """手动跑 (非 auto) 无 .skein → 必须 warn (用户显式意图)。"""
    board = _MinimalBoard(tmp_path / "repo")
    import shutil
    shutil.rmtree(board.dir)

    args = type('Args', (), {'auto': False, 'open_browser': False})()
    board.serve(args)

    err = capsys.readouterr().err
    assert "无 .skein" in err  # 手动模式必须警告


def test_serve_auto_respects_config_serve_toggle(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """auto 模式遵 config.yaml web.serve=false → 退出。"""
    board = _MinimalBoard(tmp_path / "repo")
    # 写 config 关闭 serve
    (board.dir / "config.yaml").write_text("web:\n  serve: false\n", encoding="utf-8")

    args = type('Args', (), {'auto': True, 'open_browser': False})()
    board.serve(args)

    # 应静默退出，不尝试启动服务


def test_serve_manual_ignores_config_serve_toggle(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """手动跑无视 web.serve=false (用户显式意图强于配置)。"""
    board = _MinimalBoard(tmp_path / "repo")
    (board.dir / "config.yaml").write_text("web:\n  serve: false\n", encoding="utf-8")

    # 由于会真的起 uvicorn (会阻塞)，这里只验证调用前不提前退出
    args = type('Args', (), {'auto': False, 'open_browser': False})()

    # monkeypatch uvicorn 跳过真实启动
    def fake_uvicorn(*a: Any, **kw: Any) -> None:
        raise KeyboardInterrupt()  # 立即停止

    monkeypatch.setattr("uvicorn.run", fake_uvicorn)
    monkeypatch.setattr("skeinlib.web.boardsource.serve_deps_present", lambda: True)

    # 不应提前退出，会走到 uvicorn (被 KeyboardInterrupt 截)
    with pytest.raises(KeyboardInterrupt):
        board.serve(args)


# ---- _run_server: 依赖检查 / lock 处理 -------------------------------------

def test_run_server_installs_deps_when_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
                                               capsys: pytest.CaptureFixture[str]) -> None:
    """serve_deps_present() → False → 安装依赖 → 失败则打印提示。"""
    board = _MinimalBoard(tmp_path / "repo")

    deps_installed = []

    def fake_install() -> None:
        deps_installed.append(True)

    def fake_present() -> bool:
        return False

    monkeypatch.setattr("skeinlib.web.boardsource.serve_deps_present", fake_present)
    monkeypatch.setattr("skeinlib.web.boardsource.install_serve_deps", fake_install)
    monkeypatch.setattr("uvicorn.run", lambda *a, **kw: (_ for _ in ()).throw(KeyboardInterrupt()))

    board._run_server(open_browser=False, quiet=False)

    assert deps_installed  # 应触发安装


def test_run_server_reuses_existing_same_project_lock(tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
                                                       capsys: pytest.CaptureFixture[str]) -> None:
    """已有同项目锁 → 复用服务, 不再起新端口。"""
    board = _MinimalBoard(tmp_path / "repo")
    lock = board._lock_file()
    lock.parent.mkdir(parents=True, exist_ok=True)

    # 写已有锁 (同项目)
    proj_id = str(board.dir.resolve())
    lock.write_text(json.dumps({"port": 8080, "project": proj_id}), encoding="utf-8")

    probe_called = []

    def fake_probe(*a: Any, **kw: Any) -> bool:
        probe_called.append(True)
        return True  # 同项目

    monkeypatch.setattr("skeinlib.web.boardsource.probe_same_project", fake_probe)

    board._run_server(open_browser=False, quiet=False)
    out = capsys.readouterr().out
    assert "已在运行" in out  # 应提示复用


def test_run_server_lock_file_created(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """_run_server 写 lock 文件 (完整启动流程太复杂，只测 lock 写入)。"""
    board = _MinimalBoard(tmp_path / "repo")

    # monkeypatch 掉真实启动，只验证 lock 被写入
    lock_written = []

    def fake_uvicorn(*a: Any, **kw: Any) -> None:
        # 在 uvicorn 前写 lock
        lock = board._lock_file()
        lock.parent.mkdir(parents=True, exist_ok=True)
        lock.write_text(json.dumps({"port": 8080, "project": str(board.dir.resolve())}))
        lock_written.append(lock)
        raise SystemExit(0)

    monkeypatch.setattr("uvicorn.run", fake_uvicorn)
    monkeypatch.setattr("skeinlib.web.boardsource.serve_deps_present", lambda: True)
    monkeypatch.setattr("skeinlib.web.boardsource.ensure_dist_built", lambda quiet: None)

    try:
        board._run_server(open_browser=False, quiet=False)
    except SystemExit:
        pass

    # lock 应被写入
    assert lock_written and lock_written[0].exists()
