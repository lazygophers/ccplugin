"""serve 的前端构建链回归 —— 「改了前端不生效」那条 bug 的两个成因各钉一条。

不跑真的 `next build` (太慢, 且 CI 未必有 node): 只测**决策**部分 —— 选哪个包管理器、
判不判得出 dist 过期。真构建由 `ensure_dist_built` 在这两个判断之后调用。

成因一: `_do_build` 原先用裸 `shutil.which("pnpm")` 挑包管理器。实测一台机器上 `which pnpm`
命中, 但 wrapper 指向已删掉的 `@pnpm/exe/pnpm`, 一跑 exit 127 —— 于是每次自动重编译都选中
坏的那个、每次都失败, 失败信息只进了 serve 的 stderr, 用户看到的就是「改了没反应」。
成因二: `ensure_dist_built` 原先只判 `index.html` 存不存在, dist 一旦生成就永远沿用,
改了源码重启 serve 也看不到 (dist/ 还被 .gitignore 忽略, 拉新代码同样不更新它)。
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import pytest

from skeinlib.web import serve


def test_pkg_manager_skips_installed_but_broken(monkeypatch: pytest.MonkeyPatch) -> None:
    """pnpm 在 PATH 里但一跑就非零 → 必须跳过它选 npm, 而不是硬用坏的那个。"""
    monkeypatch.setattr("skeinlib.web.serve.shutil.which", lambda name: f"/fake/bin/{name}")

    def fake_run(cmd: list[str], **kw: Any) -> Any:
        if cmd[0] == "pnpm":
            raise subprocess.CalledProcessError(127, cmd)
        return subprocess.CompletedProcess(cmd, 0, "11.0.0", "")

    monkeypatch.setattr("skeinlib.web.serve.subprocess.run", fake_run)
    assert serve.pkg_manager() == "npm"


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


def test_dist_stale_when_index_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """没产物 = 过期 (原行为, 不能回退)。"""
    _fake_tree(tmp_path, monkeypatch)
    assert serve._src_newer_than_dist() is True


def test_dist_stale_when_placeholder_exists(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """占位 index 不是构建产物, 即使比源码新也必须重建。"""
    _, dist = _fake_tree(tmp_path, monkeypatch)
    (dist / "index.html").write_text("placeholder", encoding="utf-8")
    (dist / serve._PLACEHOLDER).write_text("placeholder\n", encoding="utf-8")
    assert serve._src_newer_than_dist() is True


def test_dist_stale_when_src_newer(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """产物在, 但源码后改过 → 判过期 (这条是本次修的核心)。"""
    src, dist = _fake_tree(tmp_path, monkeypatch)
    (dist / "index.html").write_text("<html></html>", encoding="utf-8")
    page = src / "page.tsx"
    page.write_text("export default function P() { return null }\n", encoding="utf-8")
    import os
    built = (dist / "index.html").stat().st_mtime
    os.utime(page, (built + 10, built + 10))  # 显式拨时间: 同秒写入在低精度 fs 上会判等
    assert serve._src_newer_than_dist() is True


def test_dist_fresh_when_build_newer(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """产物比源码新 → 不重建 (否则每次启动都白跑一次 build)。"""
    src, dist = _fake_tree(tmp_path, monkeypatch)
    page = src / "page.tsx"
    page.write_text("export default function P() { return null }\n", encoding="utf-8")
    (dist / "index.html").write_text("<html></html>", encoding="utf-8")
    import os
    changed = page.stat().st_mtime
    os.utime(dist / "index.html", (changed + 10, changed + 10))
    assert serve._src_newer_than_dist() is False


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


def test_placeholder_still_counts_as_stale(tmp_path: Path,
                                           monkeypatch: pytest.MonkeyPatch) -> None:
    """占位页不许冒充产物 —— 否则它的 mtime 让 dist 永远「不过期」, 前端再也不会被编译。"""
    src, dist = _fake_tree(tmp_path, monkeypatch)
    serve.ensure_dist_serveable()
    assert (dist / "index.html").is_file()
    assert serve._src_newer_than_dist() is True


def test_stamp_written_after_build_and_beats_mtime_lie(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """编译成功后写入源码 hash 戳; 之后即使 dist mtime 被刷新变新, 戳不匹配仍判过期。

    覆盖: 戳文件生成、内容随源码变化、戳比 mtime 权威。
    """
    src, dist = _fake_tree(tmp_path, monkeypatch)
    page = src / "page.tsx"
    page.write_text("v1", encoding="utf-8")
    monkeypatch.setattr(serve, "pkg_manager", lambda: "npm")

    def fake_run(cmd: list[str], **kw: Any) -> subprocess.CompletedProcess[str]:
        if cmd[-1] == "build":
            (dist / "index.html").write_text("<html></html>", encoding="utf-8")
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr("skeinlib.web.serve.subprocess.run", fake_run)
    serve.ensure_dist_built(quiet=True)

    stamp = dist / serve._STAMP_FILE
    assert stamp.is_file()
    hash_v1 = stamp.read_text(encoding="utf-8")
    assert hash_v1 == serve._src_hash()

    # 戳新鲜: 即使把 index.html mtime 拨到远早于源码, 戳匹配就仍判「不过期」。
    import os
    old = page.stat().st_mtime - 1000
    os.utime(dist / "index.html", (old, old))
    assert serve._src_newer_than_dist() is False

    # 改源码内容 → 戳变化, 且即便手动把 dist mtime 拨得比源码新, 戳不匹配仍判过期。
    page.write_text("v2", encoding="utf-8")
    assert serve._src_hash() != hash_v1
    new_built = page.stat().st_mtime + 1000
    os.utime(dist / "index.html", (new_built, new_built))
    assert serve._src_newer_than_dist() is True

    # 戳缺失时行为与改动前一致: 回落 mtime 逻辑。
    stamp.unlink()
    assert serve._src_newer_than_dist() is False  # dist mtime 已比源码新
