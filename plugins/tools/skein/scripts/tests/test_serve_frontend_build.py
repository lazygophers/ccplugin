"""serve 的前端构建链回归 —— 「改了前端不生效」那条 bug 钉下的测试。

不跑真的 `next build` (太慢, 且 CI 未必有 node): 只测**决策**部分 —— 选哪个包管理器、
占位产物是否触发重建。真构建由 `ensure_dist_built` 在这些判断之后调用。

背景: `_do_build` 曾用裸 `shutil.which("pnpm")` 挑包管理器。实测一台机器上 `which pnpm`
命中, 但 wrapper 指向已删掉的 `@pnpm/exe/pnpm`, 一跑 exit 127 —— 于是每次自动重编译都选中
坏的那个、每次都失败, 失败信息只进了 serve 的 stderr, 用户看到的就是「改了没反应」。
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import pytest

from skeinlib.web import serve


def test_pkg_manager_skips_installed_but_broken(monkeypatch: pytest.MonkeyPatch) -> None:
    """pnpm 在 PATH 里但一跑就非零 → 必须跳过它, 沿链条回落到下一个健康的 (yarn)。"""
    monkeypatch.setattr("skeinlib.web.serve.shutil.which", lambda name: f"/fake/bin/{name}")

    def fake_run(cmd: list[str], **kw: Any) -> Any:
        if cmd[0] == "pnpm":
            raise subprocess.CalledProcessError(127, cmd)
        return subprocess.CompletedProcess(cmd, 0, "11.0.0", "")

    monkeypatch.setattr("skeinlib.web.serve.subprocess.run", fake_run)
    assert serve.pkg_manager() == "yarn"


def test_pkg_manager_none_when_nothing_usable(monkeypatch: pytest.MonkeyPatch) -> None:
    """两个都不可用时返回 None —— 调用方据此报「没有可用的 npm/pnpm」而不是拿 None 去 exec。"""
    monkeypatch.setattr("skeinlib.web.serve.shutil.which", lambda name: None)
    assert serve.pkg_manager() is None


def test_pkg_manager_prefers_pnpm_when_healthy(monkeypatch: pytest.MonkeyPatch) -> None:
    """pnpm 健康时仍优先 pnpm (本仓前端用 pnpm lockfile)。"""
    monkeypatch.setattr("skeinlib.web.serve.shutil.which", lambda name: f"/fake/bin/{name}")
    monkeypatch.setattr("skeinlib.web.serve.subprocess.run",
                        lambda cmd, **kw: subprocess.CompletedProcess(cmd, 0, "9.0.0", ""))
    assert serve.pkg_manager() == "pnpm"


def _fake_tree(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    """造一份 <root>/assets/{nextjs/src,dist} 的最小骨架, 并把 serve 的路径指过来。"""
    root = tmp_path / "plugin"
    src = root / "assets" / "nextjs" / "src"
    dist = root / "assets" / "dist"
    src.mkdir(parents=True)
    dist.mkdir(parents=True)
    monkeypatch.setattr(serve, "PLUGIN_ROOT", root)
    monkeypatch.setattr(serve, "dist_dir", lambda: dist)
    return src, dist


def test_no_autobuild_still_builds_when_index_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """测试禁自动构建只允许复用旧产物；产物缺失时仍必须构建。"""
    _, dist = _fake_tree(tmp_path, monkeypatch)
    monkeypatch.setenv("SKEIN_NO_AUTOBUILD", "1")
    monkeypatch.setattr(serve, "pkg_manager", lambda: "npm")
    commands: list[list[str]] = []

    def fake_run(cmd: list[str], **kw: Any) -> subprocess.CompletedProcess[str]:
        commands.append(cmd)
        if cmd[-1] == "build":
            (dist / "index.html").write_text("<html></html>", encoding="utf-8")
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr("skeinlib.web.serve.subprocess.run", fake_run)
    serve.ensure_dist_built(quiet=True)

    assert commands == [["npm", "install"], ["npm", "run", "build"]]


def test_read_dist_page_falls_back_for_missing_nested_page(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """嵌套路由产物缺失时返回说明页，不把 FileNotFoundError 变成 HTTP 500。"""
    _, dist = _fake_tree(tmp_path, monkeypatch)
    (dist / "index.html").write_text("root", encoding="utf-8")

    assert serve._read_dist_page() == "root"
    fallback = serve._read_dist_page("task", "detail")
    assert "SKEIN 前端未构建" in fallback
    assert "assets/dist/task/detail/index.html" in fallback


def test_serveable_creates_dirs_and_placeholder(tmp_path: Path,
                                                monkeypatch: pytest.MonkeyPatch) -> None:
    """dist/ 整个不存在时: 建出 dist/ 与 dist/_next/ 并放说明页。

    StaticFiles 的 check_dir=False 只免 mount 时校验, Starlette 每个请求仍 os.stat(directory),
    目录不在就抛 `RuntimeError: StaticFiles directory ... does not exist` —— 用户实测收到的是
    一屏一屏的 ASGI traceback。
    """
    src, dist = _fake_tree(tmp_path, monkeypatch)
    import shutil
    shutil.rmtree(dist)
    serve.ensure_dist_serveable()
    assert dist.is_dir() and (dist / "_next").is_dir()
    assert "未构建" in (dist / "index.html").read_text(encoding="utf-8")


def test_placeholder_triggers_rebuild(tmp_path: Path,
                                      monkeypatch: pytest.MonkeyPatch) -> None:
    """占位页不许冒充产物 —— ensure_dist_built 检测到占位标记必须触发编译并撤掉它。"""
    src, dist = _fake_tree(tmp_path, monkeypatch)
    serve.ensure_dist_serveable()
    assert (dist / "index.html").is_file()
    monkeypatch.setattr(serve, "pkg_manager", lambda: "npm")

    def fake_run(cmd: list[str], **kw: Any) -> subprocess.CompletedProcess[str]:
        if cmd[-1] == "build":
            (dist / "index.html").write_text("<html></html>", encoding="utf-8")
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr("skeinlib.web.serve.subprocess.run", fake_run)
    serve.ensure_dist_built(quiet=True)
    assert not (dist / serve._PLACEHOLDER).exists()
    assert (dist / "index.html").read_text(encoding="utf-8") == "<html></html>"
