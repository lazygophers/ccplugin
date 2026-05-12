"""验证所有 wrapper 含 colorized helper, 5 新 wrapper 走 cortex_stream_runner."""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[2]
GEN = PLUGIN_ROOT / "scripts" / "install_wrappers.sh"


def _run_install(target: Path) -> None:
    r = subprocess.run(
        [
            "bash",
            str(GEN),
            "--install-path",
            str(PLUGIN_ROOT),
            "--target-dir",
            str(target),
        ],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, f"install_wrappers.sh failed: {r.stderr}"


def test_install_wrappers_generates_17(tmp_path: Path) -> None:
    _run_install(tmp_path)
    files = sorted(p.name for p in tmp_path.glob("*.sh"))
    assert len(files) == 17, f"got {len(files)}: {files}"


def test_all_wrappers_have_color_helper(tmp_path: Path) -> None:
    """17 wrapper 全部含 err/ok/banner helper (PRELUDE 注入)."""
    _run_install(tmp_path)
    pat = re.compile(r"_CX_R=|err\(\)\s*\{|ok\(\)\s*\{")
    for f in tmp_path.glob("*.sh"):
        txt = f.read_text(encoding="utf-8")
        assert pat.search(txt), f"{f.name} 缺 colorized helper"


def test_new_wrappers_use_stream_runner(tmp_path: Path) -> None:
    """init/memory/recall/promote/consolidate 必须走 cortex_stream_runner."""
    _run_install(tmp_path)
    for name in ["init", "memory", "recall", "promote", "consolidate"]:
        f = tmp_path / f"{name}.sh"
        assert f.exists(), f"{name}.sh 未生成"
        txt = f.read_text(encoding="utf-8")
        assert "cortex_stream_runner" in txt, f"{name}.sh 未走 cortex_stream_runner"
        assert "stream_progress.sh" in txt, f"{name}.sh 未 source stream_progress.sh"


def test_all_wrappers_syntax_ok(tmp_path: Path) -> None:
    _run_install(tmp_path)
    for f in tmp_path.glob("*.sh"):
        r = subprocess.run(["bash", "-n", str(f)], capture_output=True, text=True)
        assert r.returncode == 0, f"{f.name} syntax fail: {r.stderr}"


def test_non_tty_disables_color(tmp_path: Path) -> None:
    """非 tty (subprocess pipe) 时 ANSI 变量应为空 — CI 友好."""
    _run_install(tmp_path)
    # 跑 memory.sh 不带 config: 触发 err 路径; HOME 指向空目录, stderr captured (非 tty)
    fake_home = tmp_path / "fake-home"
    fake_home.mkdir()
    r = subprocess.run(
        ["bash", str(tmp_path / "memory.sh"), "read", "L0://x"],
        capture_output=True,
        text=True,
        env={"HOME": str(fake_home), "PATH": "/usr/bin:/bin"},
    )
    # 应失败 (config 不存在); stderr 不含 ANSI 转义 (非 tty)
    assert r.returncode != 0
    assert "\033[" not in r.stderr, f"non-tty 不应含 ANSI: {r.stderr!r}"
    assert "✗" in r.stderr  # 但保留 unicode 符号
    assert "config 不存在" in r.stderr


def test_all_stream_wrappers_filter_stdout(tmp_path: Path) -> None:
    """11 stream wrapper 应含 cx_filter_stream 管道, 防止 raw NDJSON 漏到 stdout."""
    _run_install(tmp_path)
    for name in [
        "doctor", "lint", "ingest", "search", "save", "refactor",
        "init", "memory", "recall", "promote", "consolidate",
    ]:
        f = tmp_path / f"{name}.sh"
        assert f.exists(), f"{name}.sh 未生成"
        txt = f.read_text(encoding="utf-8")
        assert "cx_filter_stream" in txt, f"{name}.sh missing cx_filter_stream pipe"


def test_prelude_has_cx_filter_stream_function(tmp_path: Path) -> None:
    """PRELUDE 应注入 cx_filter_stream 函数定义."""
    _run_install(tmp_path)
    txt = (tmp_path / "memory.sh").read_text(encoding="utf-8")
    assert "cx_filter_stream()" in txt, "PRELUDE 缺 cx_filter_stream() 函数"
    assert "python3 -c" in txt, "cx_filter_stream 应基于 python3"
