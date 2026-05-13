"""验证所有 wrapper 含 colorized helper, 5 新 wrapper 走 python3 <abs>/cortex_stream.py."""
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


def test_install_wrappers_generates_expected_set(tmp_path: Path) -> None:
    _run_install(tmp_path)
    files = sorted(p.name for p in tmp_path.glob("*.sh"))
    # 9 slash + 3 shell + 9 cli = 21
    assert len(files) >= 20, f"got {len(files)}: {files}"
    # 关键文件存在
    for n in ["lint.sh", "digest.sh", "recall.sh", "save.sh", "search.sh",
              "memory.sh", "ingest_url.sh", "ingest_file.sh", "ledger.sh",
              "session.sh", "deep_search.sh", "html_render.sh",
              "install_cron.sh", "config.sh", "update.sh"]:
        assert (tmp_path / n).exists(), f"{n} 未生成"


def test_all_wrappers_have_color_helper(tmp_path: Path) -> None:
    """17 wrapper 全部含 err/ok/banner helper (PRELUDE 注入)."""
    _run_install(tmp_path)
    pat = re.compile(r"_CX_R=|err\(\)\s*\{|ok\(\)\s*\{")
    for f in tmp_path.glob("*.sh"):
        txt = f.read_text(encoding="utf-8")
        assert pat.search(txt), f"{f.name} 缺 colorized helper"


def test_slash_wrappers_use_python_stream(tmp_path: Path) -> None:
    """slash wrappers (init/recall/promote/forget/...) 必须直接调 python3 <abs>/cortex_stream.py."""
    _run_install(tmp_path)
    for name in ["init", "recall", "promote", "forget", "lint", "digest"]:
        f = tmp_path / f"{name}.sh"
        assert f.exists(), f"{name}.sh 未生成"
        txt = f.read_text(encoding="utf-8")
        assert "python3" in txt and "cortex_stream.py" in txt, \
            f"{name}.sh 未走 python3 <abs>/cortex_stream.py"
        # 禁包安装 / 禁 source stream_progress.sh
        assert "cortex_stream_runner" not in txt, f"{name}.sh 残留废弃函数指代"
        assert "stream_progress.sh" not in txt, f"{name}.sh 残留废弃 lib source"


def test_cli_wrappers_call_python_modules(tmp_path: Path) -> None:
    """CLI wrappers (save/search/memory/...) 直接 exec python3 scripts/cli/<mod>.py."""
    _run_install(tmp_path)
    for name in ["save", "search", "memory", "ingest_url", "ingest_file",
                 "deep_search", "ledger", "session", "html_render"]:
        f = tmp_path / f"{name}.sh"
        assert f.exists(), f"{name}.sh 未生成"
        txt = f.read_text(encoding="utf-8")
        assert "scripts/cli/" in txt and ".py" in txt, \
            f"{name}.sh 未指向 scripts/cli/*.py"
        assert "exec python3" in txt, f"{name}.sh 应 exec python3"


def test_all_wrappers_syntax_ok(tmp_path: Path) -> None:
    _run_install(tmp_path)
    for f in tmp_path.glob("*.sh"):
        r = subprocess.run(["bash", "-n", str(f)], capture_output=True, text=True)
        assert r.returncode == 0, f"{f.name} syntax fail: {r.stderr}"


def test_non_tty_disables_color(tmp_path: Path) -> None:
    """非 tty (subprocess pipe) 时 ANSI 变量应为空 — CI 友好."""
    _run_install(tmp_path)
    # 跑 recall.sh 不带 config: 触发 err 路径; HOME 指向空目录, stderr captured (非 tty)
    fake_home = tmp_path / "fake-home"
    fake_home.mkdir()
    r = subprocess.run(
        ["bash", str(tmp_path / "recall.sh")],
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
    """slash wrappers 应含 cx_filter_stream 管道, 防止 raw NDJSON 漏到 stdout."""
    _run_install(tmp_path)
    for name in [
        "doctor", "lint", "refactor",
        "init", "recall", "promote", "forget", "digest", "dashboard",
    ]:
        f = tmp_path / f"{name}.sh"
        assert f.exists(), f"{name}.sh 未生成"
        txt = f.read_text(encoding="utf-8")
        assert "cx_filter_stream" in txt, f"{name}.sh missing cx_filter_stream pipe"


def test_prelude_has_cx_filter_stream_function(tmp_path: Path) -> None:
    """PRELUDE 应注入 cx_filter_stream 函数定义 (检查任一 slash wrapper)."""
    _run_install(tmp_path)
    txt = (tmp_path / "recall.sh").read_text(encoding="utf-8")
    assert "cx_filter_stream()" in txt, "PRELUDE 缺 cx_filter_stream() 函数"
    assert "python3 -c" in txt, "cx_filter_stream 应基于 python3"
