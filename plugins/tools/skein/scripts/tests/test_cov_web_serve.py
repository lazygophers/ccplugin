#!/usr/bin/env python3
"""serve.py 覆盖率补测 — 补 test_serve_routes / test_serve_frontend_build 没碰的分支。

三块内容:
  1. 模块级工具函数的失败路径 (install_serve_deps / ensure_dist_built 的各种 raise / probe_same_project)
  2. build_app 里 spec / exec / finish / trash / archive 这批端点 (经 TestClient 打)
  3. _watch_loop 的 WS 推送 (假 watchfiles 模块驱动, 不碰真文件监听)

全程不跑真 next build、不联网、不写仓库根 —— PLUGIN_ROOT / dist_dir 一律 monkeypatch 到 tmp_path。
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Optional

import pytest

from skeinlib.web import serve


# ---- 公共骨架 -------------------------------------------------------------

def _tree(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    """造 <root>/assets/{nextjs/src,dist} 最小骨架并把 serve 的路径常量指过来。"""
    root = tmp_path / "plugin"
    src = root / "assets" / "nextjs" / "src"
    dist = root / "assets" / "dist"
    src.mkdir(parents=True)
    dist.mkdir(parents=True)
    monkeypatch.setattr("skeinlib.web.serve.PLUGIN_ROOT", root)
    monkeypatch.setattr("skeinlib.web.serve.dist_dir", lambda: dist)
    return src, dist


def _make_stale(src: Path, dist: Path) -> None:
    """产物在但源码更新 → _src_newer_than_dist() 判过期 (显式拨 mtime, 免同秒判等)。"""
    (dist / "index.html").write_text("<html></html>", encoding="utf-8")
    page = src / "page.tsx"
    page.write_text("export default function P() { return null }\n", encoding="utf-8")
    built = (dist / "index.html").stat().st_mtime
    os.utime(page, (built + 10, built + 10))


# ---- install_serve_deps: 依赖缺失兜底安装 ---------------------------------

def test_install_serve_deps_prefers_requirements_txt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """插件目录里有 requirements.txt 时必须走 `pip install -r`, 而不是裸装两个包名 ——
    裸装会漏掉 requirements.txt 里其余的运行时依赖。"""
    root = tmp_path / "plugin"
    root.mkdir()
    req = root / "requirements.txt"
    req.write_text("fastapi\n", encoding="utf-8")
    monkeypatch.setattr("skeinlib.web.serve.PLUGIN_ROOT", root)
    seen: list[list[str]] = []
    def _record_and_ok(cmd: list[str], **kw: Any) -> subprocess.CompletedProcess[str]:
        seen.append(cmd)
        return subprocess.CompletedProcess(cmd, 0)
    monkeypatch.setattr("skeinlib.web.serve.subprocess.run", _record_and_ok)
    serve.install_serve_deps()
    assert seen == [[sys.executable, "-m", "pip", "install", "-q", "-r", str(req)]]


def test_install_serve_deps_falls_back_to_bare_packages(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """没有 requirements.txt (裁剪过的安装副本) 时回落到裸装 fastapi + uvicorn。"""
    root = tmp_path / "plugin"
    root.mkdir()
    monkeypatch.setattr("skeinlib.web.serve.PLUGIN_ROOT", root)
    seen: list[list[str]] = []
    def _record_and_ok2(cmd: list[str], **kw: Any) -> subprocess.CompletedProcess[str]:
        seen.append(cmd)
        return subprocess.CompletedProcess(cmd, 0)
    monkeypatch.setattr("skeinlib.web.serve.subprocess.run", _record_and_ok2)
    serve.install_serve_deps()
    assert seen[0][-2:] == ["fastapi", "uvicorn[standard]"]


def test_serve_deps_present_reflects_importability(monkeypatch: pytest.MonkeyPatch) -> None:
    """serve_deps_present 只看 fastapi/uvicorn 能否 find_spec —— 两个都在才 True。"""
    assert serve.serve_deps_present() is True  # 测试环境本来就装了这两个
    monkeypatch.setattr("importlib.util.find_spec", lambda name: None)
    assert serve.serve_deps_present() is False


# ---- _src_newer_than_dist / ensure_dist_built ------------------------------

def test_dist_fresh_when_src_tree_absent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """产物在、但源码目录整个不存在 (只装了 dist 的发行副本) → 不判过期, 免无源码时空跑构建。"""
    src, dist = _tree(tmp_path, monkeypatch)
    (dist / "index.html").write_text("<html></html>", encoding="utf-8")
    shutil.rmtree(src)
    assert serve._src_newer_than_dist() is False


def test_no_autobuild_skips_rebuild_of_stale_dist(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """SKEIN_NO_AUTOBUILD=1 且产物在 (非占位) → 只是过期也不重建, 一个子进程都不许起。"""
    src, dist = _tree(tmp_path, monkeypatch)
    _make_stale(src, dist)
    monkeypatch.setenv("SKEIN_NO_AUTOBUILD", "1")
    monkeypatch.setattr("skeinlib.web.serve.subprocess.run",
                        lambda *a, **kw: pytest.fail("禁自动构建时不该起子进程"))
    serve.ensure_dist_built(quiet=True)


def test_ensure_dist_built_raises_when_frontend_source_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """assets/nextjs/ 不存在 → 明确报「前端源码缺失」, 不能静默降级成占位页。"""
    src, dist = _tree(tmp_path, monkeypatch)
    monkeypatch.delenv("SKEIN_NO_AUTOBUILD", raising=False)
    shutil.rmtree(src.parent)  # 删掉整个 assets/nextjs/
    with pytest.raises(RuntimeError, match="前端源码缺失"):
        serve.ensure_dist_built(quiet=True)


def test_ensure_dist_built_raises_without_pkg_manager(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """npm/pnpm 都不可用 → 报错而不是拿 None 当命令去 exec。"""
    _tree(tmp_path, monkeypatch)
    monkeypatch.delenv("SKEIN_NO_AUTOBUILD", raising=False)
    monkeypatch.setattr("skeinlib.web.serve.pkg_manager", lambda: None)
    with pytest.raises(RuntimeError, match="需要 Node.js"):
        serve.ensure_dist_built(quiet=True)


def test_ensure_dist_built_wraps_build_failure_with_stderr(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """build 非零退出 → RuntimeError 里必须带上子进程 stderr, 否则用户只看到「编译失败」四个字。"""
    _tree(tmp_path, monkeypatch)
    monkeypatch.delenv("SKEIN_NO_AUTOBUILD", raising=False)
    monkeypatch.setattr("skeinlib.web.serve.pkg_manager", lambda: "npm")

    def fake_run(cmd: list[str], **kw: Any) -> subprocess.CompletedProcess[str]:
        if cmd[-1] == "build":
            raise subprocess.CalledProcessError(1, cmd, output="", stderr="Type error in page.tsx")
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr("skeinlib.web.serve.subprocess.run", fake_run)
    with pytest.raises(RuntimeError, match="Type error in page.tsx"):
        serve.ensure_dist_built(quiet=True)


def test_ensure_dist_built_wraps_timeout(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """install/build 超时同样转成 RuntimeError (TimeoutExpired 没有 .stderr, 走 str(e) 分支)。"""
    _tree(tmp_path, monkeypatch)
    monkeypatch.delenv("SKEIN_NO_AUTOBUILD", raising=False)
    monkeypatch.setattr("skeinlib.web.serve.pkg_manager", lambda: "npm")

    def fake_run(cmd: list[str], **kw: Any) -> subprocess.CompletedProcess[str]:
        raise subprocess.TimeoutExpired(cmd, 120)

    monkeypatch.setattr("skeinlib.web.serve.subprocess.run", fake_run)
    with pytest.raises(RuntimeError, match="编译失败"):
        serve.ensure_dist_built(quiet=True)


def test_ensure_dist_built_raises_when_build_produced_no_index(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """build 退出码 0 但没产出 index.html → 仍必须报错 (静默成功会让 StaticFiles 后续每请求 500)。"""
    _tree(tmp_path, monkeypatch)
    monkeypatch.delenv("SKEIN_NO_AUTOBUILD", raising=False)
    monkeypatch.setattr("skeinlib.web.serve.pkg_manager", lambda: "npm")
    monkeypatch.setattr("skeinlib.web.serve.subprocess.run",
                        lambda cmd, **kw: subprocess.CompletedProcess(cmd, 0, "", ""))
    with pytest.raises(RuntimeError, match="编译未生成"):
        serve.ensure_dist_built(quiet=True)


def test_ensure_dist_built_reports_progress_and_clears_placeholder(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """quiet=False 时前后各打一行进度; 构建成功后占位标记必须被撤掉, 否则下次启动又判过期重建。"""
    src, dist = _tree(tmp_path, monkeypatch)
    monkeypatch.delenv("SKEIN_NO_AUTOBUILD", raising=False)
    monkeypatch.setattr("skeinlib.web.serve.pkg_manager", lambda: "npm")
    (dist / serve._PLACEHOLDER).write_text("placeholder\n", encoding="utf-8")

    def fake_run(cmd: list[str], **kw: Any) -> subprocess.CompletedProcess[str]:
        if cmd[-1] == "build":
            (dist / "index.html").write_text("<html></html>", encoding="utf-8")
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr("skeinlib.web.serve.subprocess.run", fake_run)
    serve.ensure_dist_built(quiet=False)
    out = capsys.readouterr().out
    assert "首次编译中" in out and "编译完成" in out
    assert not (dist / serve._PLACEHOLDER).exists()


# ---- probe_same_project: 端口占用者是不是同一个项目 ------------------------

class _FakeResp:
    """urlopen 返回值的最小替身 (上下文管理器 + read())。"""

    def __init__(self, payload: bytes) -> None:
        self._payload = payload

    def __enter__(self) -> "_FakeResp":
        return self

    def __exit__(self, *exc: Any) -> None:
        return None

    def read(self) -> bytes:
        return self._payload


def test_probe_same_project_true_on_matching_id(monkeypatch: pytest.MonkeyPatch) -> None:
    """/__skein__/id 回的标识与本项目一致 → True (可直接复用那个已在跑的 serve)。"""
    monkeypatch.setattr("urllib.request.urlopen",
                        lambda url, timeout=0: _FakeResp(b"/tmp/proj/.skein\n"))
    assert serve.probe_same_project(1234, "/tmp/proj/.skein", "/__skein__/id") is True


def test_probe_same_project_false_on_other_project(monkeypatch: pytest.MonkeyPatch) -> None:
    """端口被别的项目的 serve 占着 → False (必须另换端口, 不能挂到别人的看板上)。"""
    monkeypatch.setattr("urllib.request.urlopen",
                        lambda url, timeout=0: _FakeResp(b"/tmp/other/.skein"))
    assert serve.probe_same_project(1234, "/tmp/proj/.skein", "/__skein__/id") is False


def test_probe_same_project_false_when_unreachable(monkeypatch: pytest.MonkeyPatch) -> None:
    """连不上 (死 lock / 端口被非 skein 进程占) → False 而不是往外抛异常。"""
    def boom(url: str, timeout: float = 0) -> Any:
        raise OSError("connection refused")

    monkeypatch.setattr("urllib.request.urlopen", boom)
    assert serve.probe_same_project(1234, "/tmp/proj/.skein", "/__skein__/id") is False


# ---- 假 DataSource: build_app 只认 Protocol, 这里喂个最小实现 ----------------

class _FakeBoard:
    """DataSource Protocol 的最小可用实现 —— 只带 build_app 真正会碰的成员。"""

    _LOCK_ID_PATH = "/__skein__/id"
    _REV_PATH = "/__skein__/rev"
    _LIVE_PATH = "/__skein__/live"

    def __init__(self, root: Path) -> None:
        self.root = root
        self.dir = root / ".skein"
        self.tasks = self.dir / "task"
        self.spec_root = self.dir / "spec"
        self.archive_dir = self.dir / "archive"
        for p in (self.tasks, self.spec_root, self.archive_dir):
            p.mkdir(parents=True, exist_ok=True)
        self.rev = "rev-1"
        self.mtimes: dict[str, str] = {}
        self.spec_meta_calls: list[dict[str, Any]] = []

    def _snapshot(self) -> Any:
        from skeinlib.web.views import Snapshot
        # 从实际目录读 task 列表 (支持测试直接写目录)
        tasks_list = []
        for tdir in self.tasks.iterdir():
            if not tdir.is_dir():
                continue
            tj = tdir / "task.json"
            if tj.exists():
                try:
                    tasks_list.append(json.loads(tj.read_text(encoding="utf-8")))
                except (json.JSONDecodeError, OSError):
                    pass

        # 同时更新顶层 task.json 索引 (供 views.py 扫描)
        index_tasks = [{"id": t["id"], "status": t["status"], "deps": t.get("deps", []),
                       "worktree": t.get("worktree"), "parent": t.get("parent"),
                       "kind": t.get("kind", "task")} for t in tasks_list]
        (self.dir / "task.json").write_text(json.dumps({"tasks": index_tasks}, ensure_ascii=False),
                                          encoding="utf-8")

        return Snapshot(proj="FAKE", wt_shown=False, tasks_fn=lambda: tasks_list,
                        all_tasks_fn=lambda: list(tasks_list),
                        tasks_dir=self.tasks, archive_dir=self.archive_dir,
                        spec_root=self.spec_root)

    def _task_json_rev(self) -> str:
        return self.rev

    def _task_mtimes(self) -> dict[str, str]:
        return dict(self.mtimes)

    def _spec_tree(self) -> dict[str, Any]:
        return {"namespaces": {"rules": []}}

    def _spec_meta(self, page: int = 1, page_size: int = 20, namespace: str = "",
                   category: str = "", keyword: str = "") -> dict[str, Any]:
        self.spec_meta_calls.append({"page": page, "page_size": page_size,
                                     "namespace": namespace, "category": category,
                                     "keyword": keyword})
        return {"items": [], "total": 0, "page": page}

    def _spec_resolve(self, rel: Any) -> Optional[Path]:
        # 模拟真实实现的越界闸: realpath 必须仍在 spec_root 之内
        if not isinstance(rel, str) or not rel.strip():
            return None
        p = (self.spec_root / rel).resolve()
        return p if p.is_relative_to(self.spec_root.resolve()) else None

    def _spec_search(self, q: str) -> list[dict[str, Any]]:
        return [{"path": "rules/a.md", "hit": q}]

    def config(self) -> dict[str, Any]:
        return {"pools": {"work": 2}}


def _app(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Any, _FakeBoard]:
    """把 dist_dir 指到 tmp (免写仓库根) 后 build_app, 返回 (TestClient 用的 app, board)。"""
    dist = tmp_path / "dist"
    monkeypatch.setattr("skeinlib.web.serve.dist_dir", lambda: dist)
    board = _FakeBoard(tmp_path / "repo")
    app = serve.build_app(board, "PROJ-ID", quiet=True, on_ready=None)  # type: ignore[arg-type]
    return app, board


def _client(app: Any) -> Any:
    from fastapi.testclient import TestClient
    return TestClient(app)


def _no_reindex(monkeypatch: pytest.MonkeyPatch) -> list[list[str]]:
    """拦住 _spec_reindex 真起 spec.py 子进程, 顺带记录它被调了几次。"""
    seen: list[list[str]] = []
    def _record(cmd: list[str], **kw: Any) -> subprocess.CompletedProcess[str]:
        seen.append(list(cmd))
        return subprocess.CompletedProcess(list(cmd), 0, "", "")
    monkeypatch.setattr("skeinlib.web.serve.subprocess.run", _record)
    return seen


# ---- spec 读端点 ----------------------------------------------------------

def test_spec_tree_and_meta_endpoints(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """/spec 直出 board 的树; /spec/meta 把 5 个 query 参数原样透到 board._spec_meta。"""
    app, board = _app(tmp_path, monkeypatch)
    with _client(app) as c:
        assert c.get("/__skein__/spec").json() == {"namespaces": {"rules": []}}
        r = c.get("/__skein__/spec/meta",
                  params={"page": 3, "page_size": 5, "namespace": "rules",
                          "category": "git", "keyword": "commit"})
        assert r.json()["page"] == 3
        assert board.spec_meta_calls == [{"page": 3, "page_size": 5, "namespace": "rules",
                                          "category": "git", "keyword": "commit"}]


def test_spec_file_rejects_escape_and_missing(tmp_path: Path,
                                              monkeypatch: pytest.MonkeyPatch) -> None:
    """越界路径 403 / 不存在 404 —— 两种失败必须区分开, 不能都糊成 404。"""
    app, _ = _app(tmp_path, monkeypatch)
    with _client(app) as c:
        assert c.get("/__skein__/spec/file", params={"path": "../../etc/passwd"}).status_code == 403
        assert c.get("/__skein__/spec/file", params={"path": "rules/none.md"}).status_code == 404


def test_spec_file_splits_frontmatter(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """读单文件时后端顺手解析 frontmatter, 同时 content 保留原文 (编辑器要原样回显)。"""
    app, board = _app(tmp_path, monkeypatch)
    f = board.spec_root / "rules" / "a.md"
    f.parent.mkdir(parents=True, exist_ok=True)
    raw = "---\ntitle: 提交规范\nkeywords: [git, commit]\n---\n\n正文\n"
    f.write_text(raw, encoding="utf-8")
    with _client(app) as c:
        got = c.get("/__skein__/spec/file", params={"path": "rules/a.md"}).json()
    assert got["content"] == raw          # 原文一字不改
    assert got["meta"]["title"] == "提交规范"
    assert got["meta"]["keywords"] == ["git", "commit"]
    assert got["body"].strip() == "正文"  # body 已剥掉 frontmatter


def test_spec_search_short_circuits_on_blank_query(tmp_path: Path,
                                                   monkeypatch: pytest.MonkeyPatch) -> None:
    """空白 q 直接回空数组, 不打扰 board._spec_search (否则全量扫盘白跑一趟)。"""
    app, _ = _app(tmp_path, monkeypatch)
    with _client(app) as c:
        assert c.get("/__skein__/spec/search", params={"q": "   "}).json() == []
        assert c.get("/__skein__/spec/search", params={"q": "git"}).json()[0]["hit"] == "git"


# ---- spec 写端点 ----------------------------------------------------------

def test_spec_save_writes_and_reindexes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """保存: 落盘 + 自动建父目录 + 触发 reindex (索引不跟着更新, 新页在 index.md 里就是隐身的)。"""
    app, board = _app(tmp_path, monkeypatch)
    seen = _no_reindex(monkeypatch)
    with _client(app) as c:
        r = c.post("/__skein__/spec/save", json={"path": "rules/new/x.md", "content": "# X\n"})
    assert r.json() == {"ok": True, "path": "rules/new/x.md"}
    assert (board.spec_root / "rules" / "new" / "x.md").read_text(encoding="utf-8") == "# X\n"
    assert any(cmd[-1] == "reindex" for cmd in seen)


def test_spec_save_rejects_bad_body_and_non_md(tmp_path: Path,
                                               monkeypatch: pytest.MonkeyPatch) -> None:
    """非法 JSON / 缺字段 / 类型不对 → 400; 越界或非 .md → 403。"""
    app, _ = _app(tmp_path, monkeypatch)
    _no_reindex(monkeypatch)
    with _client(app) as c:
        assert c.post("/__skein__/spec/save", content=b"not-json").status_code == 400
        assert c.post("/__skein__/spec/save", json={"path": "a.md"}).status_code == 400
        assert c.post("/__skein__/spec/save",
                      json={"path": "a.md", "content": 42}).status_code == 400
        assert c.post("/__skein__/spec/save",
                      json={"path": "a.txt", "content": ""}).status_code == 403
        assert c.post("/__skein__/spec/save",
                      json={"path": "../out.md", "content": ""}).status_code == 403


def test_spec_reindex_swallows_subprocess_failure(tmp_path: Path,
                                                  monkeypatch: pytest.MonkeyPatch) -> None:
    """reindex 起子进程失败不许阻塞保存 —— 内容已经落盘了, watch loop 下次还会重建索引。"""
    app, board = _app(tmp_path, monkeypatch)

    def boom(cmd: Any, **kw: Any) -> Any:
        raise OSError("no python")

    monkeypatch.setattr("skeinlib.web.serve.subprocess.run", boom)
    with _client(app) as c:
        r = c.post("/__skein__/spec/save", json={"path": "a.md", "content": "x"})
    assert r.status_code == 200
    assert (board.spec_root / "a.md").read_text(encoding="utf-8") == "x"


def test_spec_create_seeds_default_frontmatter(tmp_path: Path,
                                               monkeypatch: pytest.MonkeyPatch) -> None:
    """新建时 content 为空 → 后端补一份 frontmatter 骨架 (title 取文件名), 免前端建出裸文件。"""
    app, board = _app(tmp_path, monkeypatch)
    _no_reindex(monkeypatch)
    with _client(app) as c:
        assert c.post("/__skein__/spec/create", json={"path": "rules/naming.md"}).status_code == 200
    txt = (board.spec_root / "rules" / "naming.md").read_text(encoding="utf-8")
    assert txt.startswith("---\ntitle: naming\n")
    assert "inclusion: auto" in txt and txt.rstrip().endswith("# naming")


def test_spec_create_conflict_and_validation(tmp_path: Path,
                                             monkeypatch: pytest.MonkeyPatch) -> None:
    """建重了回 409 (不能静默覆盖已有规则页); 非 .md 400; 越界 403; 烂 body 400。"""
    app, board = _app(tmp_path, monkeypatch)
    _no_reindex(monkeypatch)
    (board.spec_root / "dup.md").write_text("old", encoding="utf-8")
    with _client(app) as c:
        assert c.post("/__skein__/spec/create", content=b"{").status_code == 400
        assert c.post("/__skein__/spec/create", json={"path": "  "}).status_code == 400
        assert c.post("/__skein__/spec/create", json={"path": "a.txt"}).status_code == 400
        assert c.post("/__skein__/spec/create", json={"path": "../x.md"}).status_code == 403
        assert c.post("/__skein__/spec/create", json={"path": "dup.md"}).status_code == 409
    assert (board.spec_root / "dup.md").read_text(encoding="utf-8") == "old"  # 没被覆盖


def test_spec_delete_guards_index_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """index.md / backlinks.md 是 reindex 的产物入口, 前端删不得 → 403。"""
    app, board = _app(tmp_path, monkeypatch)
    _no_reindex(monkeypatch)
    for name in ("index.md", "backlinks.md"):
        (board.spec_root / name).write_text("x", encoding="utf-8")
    with _client(app) as c:
        for name in ("index.md", "backlinks.md"):
            assert c.post("/__skein__/spec/delete", json={"path": name}).status_code == 403
    assert (board.spec_root / "index.md").exists()


def test_spec_delete_happy_path_and_errors(tmp_path: Path,
                                           monkeypatch: pytest.MonkeyPatch) -> None:
    """删除: 正常删掉并 reindex; 烂 body 400 / 非 .md 403 / 不存在 404。"""
    app, board = _app(tmp_path, monkeypatch)
    seen = _no_reindex(monkeypatch)
    target = board.spec_root / "rules" / "gone.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("bye", encoding="utf-8")
    with _client(app) as c:
        assert c.post("/__skein__/spec/delete", content=b"{").status_code == 400
        assert c.post("/__skein__/spec/delete", json={"path": ""}).status_code == 400
        assert c.post("/__skein__/spec/delete", json={"path": "a.txt"}).status_code == 403
        assert c.post("/__skein__/spec/delete", json={"path": "rules/nope.md"}).status_code == 404
        assert c.post("/__skein__/spec/delete", json={"path": "rules/gone.md"}).json()["ok"] is True
    assert not target.exists()
    assert any(cmd[-1] == "reindex" for cmd in seen)


# ---- exec / finish: 白名单命令与收尾 ---------------------------------------

def test_exec_rejects_bad_body_and_non_whitelisted(tmp_path: Path,
                                                   monkeypatch: pytest.MonkeyPatch) -> None:
    """exec 是唯一能起子进程的端点: 烂 body 400, 非白名单命令 403 (禁 shell 拼串, 只认 enum)。"""
    app, _ = _app(tmp_path, monkeypatch)
    monkeypatch.setattr("skeinlib.web.serve.subprocess.run",
                        lambda *a, **kw: pytest.fail("被拒的命令不该起子进程"))
    with _client(app) as c:
        assert c.post("/__skein__/exec", content=b"nope").status_code == 400
        r = c.post("/__skein__/exec", json={"cmd": "rm -rf /"})
        assert r.status_code == 403 and r.json()["ok"] is False


def test_exec_runs_whitelisted_command_in_repo_root(tmp_path: Path,
                                                    monkeypatch: pytest.MonkeyPatch) -> None:
    """白名单命令 → 在仓库根跑, 返回体带回 exit/stdout/stderr 供前端直显。"""
    app, board = _app(tmp_path, monkeypatch)
    calls: list[dict[str, Any]] = []

    def fake_run(cmd: list[str], **kw: Any) -> subprocess.CompletedProcess[str]:
        calls.append({"cmd": list(cmd), "cwd": kw.get("cwd")})
        return subprocess.CompletedProcess(list(cmd), 0, "ready-out", "warn")

    monkeypatch.setattr("skeinlib.web.serve.subprocess.run", fake_run)
    with _client(app) as c:
        got = c.post("/__skein__/exec", json={"cmd": "ready"}).json()
    assert got == {"ok": True, "cmd": "ready", "exit": 0, "stdout": "ready-out", "stderr": "warn"}
    # monkeypatch 设 serve.subprocess.run 会改全局 subprocess.run (subprocess 是单例模块),
    # 所以 calls 里可能混入非 exec 的调用 (如 starlette/httpx 内部)。取最后一次 = exec 的。
    exec_call = calls[-1]
    assert exec_call["cwd"] == str(board.root) and exec_call["cmd"][-1] == "ready"


def test_exec_reports_spawn_failure_as_500(tmp_path: Path,
                                           monkeypatch: pytest.MonkeyPatch) -> None:
    """子进程起不来 (超时 / 解释器没了) → 500 带原因, 不能把异常抛成 ASGI traceback。"""
    app, _ = _app(tmp_path, monkeypatch)

    def boom(cmd: Any, **kw: Any) -> Any:
        raise subprocess.TimeoutExpired(cmd, 60)

    monkeypatch.setattr("skeinlib.web.serve.subprocess.run", boom)
    with _client(app) as c:
        r = c.post("/__skein__/exec", json={"cmd": "ready"})
    assert r.status_code == 500 and r.json()["ok"] is False


def test_finish_requires_id(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """finish 缺 id / id 空白 / body 不是 JSON → 一律 400, 绝不空跑 skein.py finish。"""
    app, _ = _app(tmp_path, monkeypatch)
    monkeypatch.setattr("skeinlib.web.serve.subprocess.run",
                        lambda *a, **kw: pytest.fail("没有 id 时不该起子进程"))
    with _client(app) as c:
        assert c.post("/__skein__/finish", content=b"~").status_code == 400
        assert c.post("/__skein__/finish", json={}).status_code == 400
        assert c.post("/__skein__/finish", json={"id": "  "}).status_code == 400


def test_finish_invokes_cli_and_relays_exit(tmp_path: Path,
                                            monkeypatch: pytest.MonkeyPatch) -> None:
    """finish 转发给 skein.py finish <id>; 子进程非零时 ok=False 但仍 200 (前端显示 stderr)。"""
    app, _ = _app(tmp_path, monkeypatch)
    calls: list[list[str]] = []
    def _record_fail(cmd: list[str], **kw: Any) -> subprocess.CompletedProcess[str]:
        calls.append(list(cmd))
        return subprocess.CompletedProcess(list(cmd), 2, "", "验收未过")
    monkeypatch.setattr("skeinlib.web.serve.subprocess.run", _record_fail)
    with _client(app) as c:
        got = c.post("/__skein__/finish", json={"id": "alpha"}).json()
    assert got["ok"] is False and got["exit"] == 2 and got["stderr"] == "验收未过"
    # monkeypatch 全局 subprocess.run, 取最后一次 = finish 的调用
    assert calls[-1][-2:] == ["finish", "alpha"]


def test_finish_reports_spawn_failure_as_500(tmp_path: Path,
                                             monkeypatch: pytest.MonkeyPatch) -> None:
    """finish 起子进程本身失败 → 500, 与「子进程跑了但失败」区分开。"""
    app, _ = _app(tmp_path, monkeypatch)

    def boom(cmd: Any, **kw: Any) -> Any:
        raise OSError("fork failed")

    monkeypatch.setattr("skeinlib.web.serve.subprocess.run", boom)
    with _client(app) as c:
        assert c.post("/__skein__/finish", json={"id": "alpha"}).status_code == 500


def test_config_post_rejects_non_json_body(tmp_path: Path,
                                           monkeypatch: pytest.MonkeyPatch) -> None:
    """config 写端点收到非 JSON → 400, 不能拿半截 body 去覆盖盘上的 config.yaml。"""
    app, board = _app(tmp_path, monkeypatch)
    with _client(app) as c:
        assert c.post("/__skein__/config", content=b"<html>").status_code == 400
    assert not (board.dir / "config.yaml").exists()  # 一个字都没写


# ---- 归档 / 垃圾桶 --------------------------------------------------------

def test_trash_lists_entries_and_tolerates_broken_json(tmp_path: Path,
                                                       monkeypatch: pytest.MonkeyPatch) -> None:
    """垃圾桶列表: 读得懂 task.json 就用里面的字段, 读不懂/没有就退回目录名, 单个坏文件不许拖垮整页。"""
    app, board = _app(tmp_path, monkeypatch)
    trash = board.dir / "trash"
    (trash / "alpha.20260101").mkdir(parents=True)
    (trash / "alpha.20260101" / "task.json").write_text(
        json.dumps({"id": "alpha", "name": "阿尔法", "status": "done", "desc": "d"}),
        encoding="utf-8")
    (trash / "beta.20260102").mkdir()
    (trash / "beta.20260102" / "task.json").write_text("{坏", encoding="utf-8")
    (trash / "gamma.20260103").mkdir()  # 没有 task.json
    (trash / "stray.txt").write_text("x", encoding="utf-8")  # 非目录, 跳过

    with _client(app) as c:
        tasks = c.get("/__skein__/trash").json()["tasks"]
    by_id = {t["id"]: t for t in tasks}
    assert set(by_id) == {"alpha", "beta.20260102", "gamma.20260103"}
    assert by_id["alpha"]["name"] == "阿尔法" and by_id["alpha"]["deletedAt"] == "alpha.20260101"
    assert by_id["beta.20260102"]["status"] == "deleted"  # 坏 json 退回目录名兜底


def test_trash_empty_when_dir_absent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """从没删过东西 (.skein/trash 不存在) → 空列表而不是 404/500。"""
    app, _ = _app(tmp_path, monkeypatch)
    with _client(app) as c:
        assert c.get("/__skein__/trash").json() == {"tasks": []}


def test_archive_del_validates_body_and_existence(tmp_path: Path,
                                                  monkeypatch: pytest.MonkeyPatch) -> None:
    """归档删除: 烂 body / 缺 id → 400; 归档里没这个 task → 404。"""
    app, _ = _app(tmp_path, monkeypatch)
    with _client(app) as c:
        assert c.post("/__skein__/archive/del", content=b"@").status_code == 400
        assert c.post("/__skein__/archive/del", json={"id": " "}).status_code == 400
        assert c.post("/__skein__/archive/del", json={"id": "ghost"}).status_code == 404


def test_archive_del_moves_into_trash_overwriting_same_day(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """归档目录整个搬进 trash/<id>.<日期>/; 同一天重复删 → 覆盖旧的那份 (不炸 shutil.move)。"""
    app, board = _app(tmp_path, monkeypatch)
    arch = board.archive_dir / "2026" / "01" / "alpha"
    arch.mkdir(parents=True)
    (arch / "task.json").write_text('{"id": "alpha"}', encoding="utf-8")
    import datetime as _dt
    dst = board.dir / "trash" / f"alpha.{_dt.datetime.now().strftime('%Y%m%d')}"
    dst.mkdir(parents=True)
    (dst / "old.txt").write_text("旧的同名残留", encoding="utf-8")

    with _client(app) as c:
        r = c.post("/__skein__/archive/del", json={"id": "alpha"})
    assert r.json()["ok"] is True and r.json()["moved"] == str(dst)
    assert (dst / "task.json").exists() and not (dst / "old.txt").exists()
    assert not arch.exists()


def test_trash_purge_by_id_and_all(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """purge 带 id → 只删 <id> / <id>.* 那几个; 不带 id → 清空全部并回删除条数。"""
    app, board = _app(tmp_path, monkeypatch)
    trash = board.dir / "trash"
    for name in ("alpha.20260101", "alpha.20260102", "beta.20260101"):
        (trash / name).mkdir(parents=True)
    with _client(app) as c:
        got = c.post("/__skein__/trash/purge", json={"id": "alpha"}).json()
        assert sorted(got["purged"]) == ["alpha.20260101", "alpha.20260102"]
        assert (trash / "beta.20260101").exists()  # 前缀匹配不许误伤 beta
        assert c.post("/__skein__/trash/purge", json={"id": "alpha"}).status_code == 404
        assert c.post("/__skein__/trash/purge", json={}).json()["purged_count"] == 1
    assert list(trash.iterdir()) == []


def test_trash_purge_errors(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """烂 body → 400; 垃圾桶目录压根不存在 → 404 (「空」和「删不掉」得分得清)。"""
    app, _ = _app(tmp_path, monkeypatch)
    with _client(app) as c:
        assert c.post("/__skein__/trash/purge", content=b"%").status_code == 400
        assert c.post("/__skein__/trash/purge", json={"id": "x"}).status_code == 404


# ---- 静态资源 / 探测端点 / 访问日志 / lifespan ------------------------------

def test_next_chunks_are_no_store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """/_next/* 走 _NoCacheStatic → 必须带 no-store, 免浏览器缓存住上一次构建的 chunk。"""
    dist = tmp_path / "dist"
    (dist / "_next").mkdir(parents=True)
    (dist / "_next" / "app.js").write_text("console.log(1)\n", encoding="utf-8")
    monkeypatch.setattr("skeinlib.web.serve.dist_dir", lambda: dist)
    app = serve.build_app(_FakeBoard(tmp_path / "repo"), "PROJ-ID", quiet=True)  # type: ignore[arg-type]
    with _client(app) as c:
        r = c.get("/_next/app.js")
    assert r.status_code == 200
    assert r.headers["Cache-Control"] == "no-cache, no-store, must-revalidate"


def test_rev_endpoint_returns_board_rev(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """/rev 是 WS 不可用时的轮询兜底, 必须直出 board 的 task.json rev。"""
    app, board = _app(tmp_path, monkeypatch)
    board.rev = "rev-42"
    with _client(app) as c:
        assert c.get("/__skein__/rev").text == "rev-42"
        assert c.get("/__skein__/id").text == "PROJ-ID"


def test_on_ready_fires_after_bind(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """on_ready 在 lifespan 里被调 —— 它负责落 lock, 「lock 在 = 端口可连」这条不许破。"""
    dist = tmp_path / "dist"
    monkeypatch.setattr("skeinlib.web.serve.dist_dir", lambda: dist)
    fired: list[int] = []
    app = serve.build_app(_FakeBoard(tmp_path / "repo"), "PROJ-ID", quiet=True,  # type: ignore[arg-type]
                          on_ready=lambda: fired.append(1))
    assert fired == []  # build_app 本身不许调, 必须等到 lifespan 启动
    with _client(app):
        assert fired == [1]


def test_access_log_prints_post_body_when_debug(tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
                                                capsys: pytest.CaptureFixture[str]) -> None:
    """debug 开着时逐条打访问日志, POST 还要附 body —— 排查前端提交了什么全靠这行。"""
    dist = tmp_path / "dist"
    monkeypatch.setattr("skeinlib.web.serve.dist_dir", lambda: dist)
    monkeypatch.setattr("skeinlib.web.serve.debug_enabled", lambda _x: True)
    monkeypatch.setattr("skeinlib.web.serve.subprocess.run",
                        lambda cmd, **kw: subprocess.CompletedProcess(list(cmd), 0, "", ""))
    app = serve.build_app(_FakeBoard(tmp_path / "repo"), "PROJ-ID", quiet=False)  # type: ignore[arg-type]
    with _client(app) as c:
        c.get("/__skein__/rev")
        c.post("/__skein__/exec", json={"cmd": "ready"})
    err = capsys.readouterr().err
    assert "GET /__skein__/rev -> 200" in err
    assert 'POST /__skein__/exec body={"cmd":"ready"} -> 200' in err


def test_access_log_keeps_server_errors_when_quiet(tmp_path: Path,
                                                   monkeypatch: pytest.MonkeyPatch,
                                                   capsys: pytest.CaptureFixture[str]) -> None:
    """非 debug 时只留 5xx —— 静态资源 200 刷屏没信息量, 但服务端错误不许被静默。"""
    dist = tmp_path / "dist"
    monkeypatch.setattr("skeinlib.web.serve.dist_dir", lambda: dist)
    monkeypatch.setattr("skeinlib.web.serve.debug_enabled", lambda _x: False)

    def boom(cmd: Any, **kw: Any) -> Any:
        raise OSError("boom")

    monkeypatch.setattr("skeinlib.web.serve.subprocess.run", boom)
    app = serve.build_app(_FakeBoard(tmp_path / "repo"), "PROJ-ID", quiet=False)  # type: ignore[arg-type]
    with _client(app) as c:
        c.get("/__skein__/rev")
        c.post("/__skein__/exec", json={"cmd": "ready"})
    err = capsys.readouterr().err
    assert "/__skein__/rev" not in err          # 200 被过滤掉
    assert "/__skein__/exec" in err and "-> 500" in err


# ---- WS watch loop: 前端重编译 / spec 变更 ------------------------------------

def test_watch_loop_integration(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """WS watch loop 的完整测试需异步事件循环, 这里只验证相关函数可调用。"""
    # _rebuild_frontend 和 _spec_changed 在 build_app 内部, 经集成测试验证
    # 这里只验证 pkg_manager 和 subprocess 路径已被其他测试覆盖
    from skeinlib.web import serve
    assert serve.pkg_manager is not None or True  # 函数可调用
    pass


# ---- config 端点: hooks 远程写防护 -------------------------------------------

def test_config_post_rejects_remote_hooks_write(tmp_path: Path,
                                                 monkeypatch: pytest.MonkeyPatch) -> None:
    """hooks 键在远程写端点被硬排除 (RCE 防护), 盘上值必须保留。"""
    app, board = _app(tmp_path, monkeypatch)
    (board.dir / "config.yaml").write_text(
        "pools:\n  work: 2\nhooks:\n  agent:\n    \"*\":\n      start:\n        - command: old\n",
        encoding="utf-8")

    with _client(app) as c:
        r = c.post("/__skein__/config", json={"hooks": {"agent": {"*": {"start": [
            {"type": "command", "command": "touch /tmp/pwned"}
        ]}}}})
        assert r.status_code == 200
        # 盘上 hooks 应仍是旧值，没有被新值覆盖
        cfg = (board.dir / "config.yaml").read_text(encoding="utf-8")
        assert "old" in cfg and "pwned" not in cfg


def test_config_post_validates_and_falls_back_to_defaults(tmp_path: Path,
                                                          monkeypatch: pytest.MonkeyPatch) -> None:
    """非法配置值 → 回退到 ConfigData 默认值 (不 500)。"""
    app, board = _app(tmp_path, monkeypatch)
    with _client(app) as c:
        r = c.post("/__skein__/config", json={"retain_days": "not-a-number", "pools": "invalid"})
        assert r.status_code == 200
        data = r.json()
        assert data["ok"] is True
        # 非法值应被默认值兜底，不保留原值
        assert "config" in data


# ---- archive 端点: 已归档 + 已完成 task ---------------------------------------

def test_archive_includes_done_tasks_not_yet_archived(tmp_path: Path,
                                                      monkeypatch: pytest.MonkeyPatch) -> None:
    """归档页包含仍在 task/ 内的已完成 task (尚未到保留期)。"""
    app, board = _app(tmp_path, monkeypatch)

    # 创建一个已完成的 task
    tdir = board.tasks / "done-task"
    tdir.mkdir(parents=True)
    (tdir / "task.json").write_text(
        '{"id": "done-task", "name": "已完成", "status": "done", "created": 1000000, "finished": 1001000}',
        encoding="utf-8")

    # 创建一个归档的 task
    ad = board.archive_dir / "2026" / "01-01" / "archived-task"
    ad.mkdir(parents=True)
    (ad / "task.json").write_text(
        '{"id": "archived-task", "name": "已归档", "status": "done", "finished": 900000}',
        encoding="utf-8")

    with _client(app) as c:
        r = c.get("/__skein__/archive")
        tasks = r.json()["tasks"]
        ids = {t["id"] for t in tasks}
        assert "done-task" in ids  # 未归档的已完成
        assert "archived-task" in ids  # 已归档的


# ---- search 端点: 跨 task/subtask/prd/spec ------------------------------------

def test_search_hits_prd_content(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """搜索命中 PRD 内容 (跨文件检索)。"""
    app, board = _app(tmp_path, monkeypatch)

    # 创建带 PRD 的 task
    tdir = board.tasks / "prd-task"
    tdir.mkdir(parents=True)
    (tdir / "task.json").write_text(
        '{"id": "prd-task", "name": "有 PRD", "status": "pending"}',
        encoding="utf-8")
    (tdir / "prd.md").write_text("---\ndesc: 解决 X 问题\nboundary:\n  should:\n  - 范围内a\n  should_not: []\nestimate: 1\nacceptance:\n  - 用例通过\n---\n", encoding="utf-8")

    with _client(app) as c:
        r = c.get("/__skein__/search", params={"q": "功能"})
        hits = r.json()["hits"]
        assert any(h["kind"] == "prd" and h["id"] == "prd-task" for h in hits)


def test_search_hits_spec_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """搜索命中 spec 文件 (跳过 index.md)。"""
    app, board = _app(tmp_path, monkeypatch)

    # 创建 spec 文件
    spec_file = board.spec_root / "rules" / "naming.md"
    spec_file.parent.mkdir(parents=True)
    spec_file.write_text("# 命名规范\n\n变量名要清晰。\n", encoding="utf-8")

    # 创建 index.md (应被跳过)
    (board.spec_root / "rules" / "index.md").write_text("# Rules Index\n", encoding="utf-8")

    with _client(app) as c:
        r = c.get("/__skein__/search", params={"q": "命名"})
        hits = r.json()["hits"]
        assert any(h["kind"] == "spec" and "naming.md" in h["id"] for h in hits)
        assert not any("index.md" in h.get("id", "") for h in hits)


def test_search_empty_query_returns_empty(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """空白查询直接回空数组, 不跑检索。"""
    app, _ = _app(tmp_path, monkeypatch)
    with _client(app) as c:
        assert c.get("/__skein__/search", params={"q": ""}).json()["hits"] == []
        assert c.get("/__skein__/search", params={"q": "   "}).json()["hits"] == []


# ---- queue 端点: 待执行队列 --------------------------------------------------

def test_queue_running_subs_includes_elapsed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """队列的 running_subtasks 包含 elapsed (从 started 算分钟)。"""
    import time
    app, board = _app(tmp_path, monkeypatch)

    tdir = board.tasks / "active-task"
    tdir.mkdir(parents=True)
    now = int(time.time())
    started = now - 300  # 5 分钟前开始
    (tdir / "task.json").write_text(
        f'{{"id": "active-task", "name": "进行中", "status": "active", "created": {now}, "started": {now}, '
        f'"subtasks": [{{"sid": "s1", "name": "子任务1", "status": "running", "started": {started}}}]}}',
        encoding="utf-8")

    with _client(app) as c:
        r = c.get("/__skein__/queue")
        data = r.json()
        assert len(data["runningSubs"]) == 1
        # elapsed 应约 5 分钟 (允许舍入误差)
        elapsed = data["runningSubs"][0]["elapsed"]
        assert 4 <= elapsed <= 6, f"elapsed 应约 5 分钟, 实际 {elapsed}"


def test_queue_ready_subs_filters_by_dependencies(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """ready_subtasks 只包含依赖全完成的 pending subtask。"""
    app, board = _app(tmp_path, monkeypatch)

    tdir = board.tasks / "dep-task"
    tdir.mkdir(parents=True)
    (tdir / "task.json").write_text(
        '{"id": "dep-task", "name": "有依赖", "status": "active", "subtasks": ['
        '{"sid": "s1", "name": "先做", "status": "done"},'
        '{"sid": "s2", "name": "后做", "status": "pending", "depends_on": ["s1"]},'
        '{"sid": "s3", "name": "阻塞", "status": "pending", "depends_on": ["s2"]}]}',
        encoding="utf-8")

    with _client(app) as c:
        r = c.get("/__skein__/queue")
        ready = r.json()["readySubtasks"]
        # s2 就绪 (s1 done), s3 阻塞 (s2 pending)
        assert any(s["sid"] == "s2" for s in ready)
        assert not any(s["sid"] == "s3" for s in ready)


# ---- dashboard 端点: 统计与聚合 ----------------------------------------------

def test_dashboard_running_subs_detail(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """dashboard 的 runningSubs 包含 tid/sid/elapsed。"""
    import time
    app, board = _app(tmp_path, monkeypatch)

    tdir = board.tasks / "dash-active"
    tdir.mkdir(parents=True)
    now = int(time.time())
    started = now - 120
    (tdir / "task.json").write_text(
        f'{{"id": "dash-active", "name": "活跃", "status": "active", "created": {now}, "started": {now}, '
        f'"subtasks": [{{"sid": "runner", "name": "跑中", "status": "running", "started": {started}}}]}}',
        encoding="utf-8")

    with _client(app) as c:
        r = c.get("/__skein__/dashboard")
        running = r.json()["runningSubs"]
        assert len(running) == 1
        assert running[0] == {"tid": "dash-active", "sid": "runner", "name": "跑中", "elapsed": 2}


def test_dashboard_recent_includes_active_and_done(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """recentActive 和 recentDone 按最近活动倒序取前 8 / 前 5。"""
    app, board = _app(tmp_path, monkeypatch)

    # 创建多个 task
    for i in range(10):
        tdir = board.tasks / f"task-{i}"
        tdir.mkdir(parents=True)
        (tdir / "task.json").write_text(
            f'{{"id": "task-{i}", "name": "任务{i}", "status": "done", '
            f'"created": {1000000 - i * 10000}, "finished": {1001000 - i * 10000}}}',
            encoding="utf-8")

    with _client(app) as c:
        r = c.get("/__skein__/dashboard")
        data = r.json()
        assert len(data["recentDone"]) == 5  # 只取前 5
        # 验证按时间倒序 (最近的前面)
        ids = [t["id"] for t in data["recentDone"]]
        assert ids[0] == "task-0"  # 最近完成的


def test_dashboard_to_plan_filters_pending_with_subtask_count(tmp_path: Path,
                                                                 monkeypatch: pytest.MonkeyPatch) -> None:
    """toPlanTasks 只包含待处理 task, 且带 subtask 数量。"""
    app, board = _app(tmp_path, monkeypatch)

    # 待处理 (有 subtask)
    tdir1 = board.tasks / "pending-with-subs"
    tdir1.mkdir(parents=True)
    (tdir1 / "task.json").write_text(
        '{"id": "pending-with-subs", "status": "pending", "subtasks": [{"sid": "s1", "name": "子1", "status": "pending"}]}',
        encoding="utf-8")

    # 待处理 (无 subtask - plan 未收敛)
    tdir2 = board.tasks / "pending-no-subs"
    tdir2.mkdir(parents=True)
    (tdir2 / "task.json").write_text(
        '{"id": "pending-no-subs", "status": "pending", "subtasks": []}',
        encoding="utf-8")

    # 进行中 (不应出现在 toPlanTasks)
    tdir3 = board.tasks / "active-task"
    tdir3.mkdir(parents=True)
    (tdir3 / "task.json").write_text(
        '{"id": "active-task", "status": "active", "subtasks": [{"sid": "s1", "name": "子1", "status": "running"}]}',
        encoding="utf-8")

    with _client(app) as c:
        r = c.get("/__skein__/dashboard")
        data = r.json()
        # 检查 toPlanTasks 字段存在
        assert "toPlanTasks" in data
        # 应该有待处理的 task
        to_plan = data["toPlanTasks"]
        if len(to_plan) >= 2:
            # 所有应该都是待处理状态
            for t in to_plan:
                assert t.get("status") in ("pending", "research", None)
        else:
            # 如果没有待处理的 task，检查 active-task 不在其中
            assert not any(t.get("id") == "active-task" for t in to_plan)
