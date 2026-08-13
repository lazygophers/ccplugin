"""依赖自举兜底 — 断言构造出的 uv 命令行形状。

不真装包、不依赖系统上存在哪个 python: 历史缺陷正是「命令行少了依赖声明, 子进程照样缺 typer」,
形状对了缺陷就不会复现。
"""
from __future__ import annotations

import os
import subprocess
import sys

import _bootstrap


def test_uv_rerun_cmd_carries_requirements() -> None:
    cmd = _bootstrap.uv_rerun_cmd(["/x/skein.py", "init"])
    assert cmd[:2] == ["uv", "run"]
    # 缺了依赖声明 = 子进程照样没 typer, 兜底等于没跑
    assert "--with-requirements" in cmd
    req = cmd[cmd.index("--with-requirements") + 1]
    assert os.path.isfile(req) and os.path.basename(req) == "requirements.txt"
    # 少了它 uv 会去解析调用方仓库的 pyproject
    assert "--no-project" in cmd
    assert cmd[-3:] == ["python3", "/x/skein.py", "init"]


def test_uv_rerun_cmd_falls_back_without_requirements(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(os.path, "isfile", lambda _p: False)
    cmd = _bootstrap.uv_rerun_cmd(["/x/skein.py"])
    assert "--with-requirements" not in cmd
    for pkg in _bootstrap._CORE_DEPS.values():
        assert ["--with", pkg] == cmd[cmd.index(pkg) - 1:cmd.index(pkg) + 1]


def test_ensure_core_deps_noop_when_bootstrapped(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """防递归: 重跑那一次不再重跑, 否则无限重启。"""
    monkeypatch.setenv("_SKEIN_DEPS_BOOTSTRAPPED", "1")
    monkeypatch.setattr(_bootstrap, "_missing", lambda: ["typer"])
    monkeypatch.setattr(subprocess, "run", _boom)
    _bootstrap.ensure_core_deps()


def test_ensure_core_deps_survives_missing_uv(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """机器上没有 uv 时静默返回, 让原始 ModuleNotFoundError 暴露真正原因。"""
    monkeypatch.delenv("_SKEIN_DEPS_BOOTSTRAPPED", raising=False)
    monkeypatch.setattr(_bootstrap, "_missing", lambda: ["typer"])
    monkeypatch.setattr(subprocess, "run",
                        lambda *a, **kw: (_ for _ in ()).throw(FileNotFoundError("uv")))
    _bootstrap.ensure_core_deps()


def test_ensure_core_deps_reruns_and_exits(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    seen: dict[str, object] = {}

    def fake_run(cmd, env=None, **kw):  # type: ignore[no-untyped-def]
        seen["cmd"], seen["env"] = cmd, env
        return type("P", (), {"returncode": 3})()

    monkeypatch.delenv("_SKEIN_DEPS_BOOTSTRAPPED", raising=False)
    monkeypatch.setattr(_bootstrap, "_missing", lambda: ["typer"])
    monkeypatch.setattr(subprocess, "run", fake_run)
    try:
        _bootstrap.ensure_core_deps()
    except SystemExit as e:
        assert e.code == 3
    else:
        raise AssertionError("应透传子进程退出码")
    assert seen["cmd"] == _bootstrap.uv_rerun_cmd(sys.argv)
    assert seen["env"]["_SKEIN_DEPS_BOOTSTRAPPED"] == "1"  # type: ignore[index]


def _boom(*a: object, **kw: object) -> None:
    raise AssertionError("不该重跑")
