"""入口在各种安装形态下都能自举 import — 软链 / 副本 / 异地 cwd / 多副本共存。

## 为什么这条不可省
skein 在一台机器上**同时存在多份**是常态: 开发仓一份、marketplace 一份、plugin cache 按
commit 各一份。调用方的 cwd 是用户仓库根 (不是插件目录), 而 harness 起 hook 时既不走 Bash
PATH 也不保证 cwd。三个入口 (`skein.py` / `spec.py` / `hooks.py`) 全靠顶部那行
`sys.path.insert(0, realpath(__file__) 的目录)` 自举 —— 那行一旦写错:

- **整行没了** → `bin/` wrapper 用 `runpy.run_path()`, 它不设 `sys.path[0]`, 全套 hook
  当场 ModuleNotFoundError。生产环境走的正是 wrapper。(真炸过一次, 见 test_bin_wrappers)
- **不插到 0 位** → 有 `PYTHONPATH` 指向另一副本时, import 到的 skeinlib **不是本入口这一份**,
  于是新版入口配旧版实现, 症状是莫名其妙的 AttributeError
- **用 cwd 推路径** → 换个目录跑就崩

`realpath` vs `abspath`: 实测在 Python 3.11 下这几种形态两者**都能过** (3.11+ 会替直接跑的
脚本解析 sys.path[0] 的软链, 目录软链的遍历也本就透明)。仍统一按 realpath 写是防御性的 —
runpy 那条路径不享受前者的照顾, 且成本为零。下面那条静态检查因此只是**统一写法**, 不宣称
自己拦得住一个当前可复现的故障 —— 说清楚免得后人以为它在守什么强保证。
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import conftest  # noqa: F401  模块体把 scripts/ 塞进 sys.path
from conftest import SCRIPTS  # noqa: E402

PLUGIN = SCRIPTS.parent
ENTRIES = ("skein.py", "spec.py", "hooks.py")


def _ok(*argv: str, cwd: Path | None = None, env: dict[str, str] | None = None) -> bool:
    """跑一条命令, 只关心「没因 import 崩掉」。"""
    r = subprocess.run(argv, cwd=cwd, env=env, capture_output=True, text=True,
                       stdin=subprocess.DEVNULL, timeout=30)
    blew_up = "ModuleNotFoundError" in r.stderr or "ImportError" in r.stderr
    return not blew_up


def test_entries_work_when_plugin_dir_is_symlinked(tmp_path: Path) -> None:
    """整个插件目录被软链 (marketplace 常见装法)。"""
    link = tmp_path / "skein-link"
    link.symlink_to(PLUGIN)
    for e in ENTRIES:
        assert _ok(sys.executable, str(link / "scripts" / e), "--help"), f"软链插件目录下 {e} 起不来"
    assert _ok(sys.executable, str(link / "bin" / "skein"), "--help"), "软链下 bin/skein 起不来"


def test_entry_works_when_only_the_script_is_symlinked(tmp_path: Path) -> None:
    """只有入口脚本被软链, `skeinlib` 在软链**目标**旁边 (最刁钻的一种装法)。

    注: Python 3.11+ 会替直接跑的脚本解析 `sys.path[0]` 的软链, 所以这条在当前版本下
    即便接线写成 abspath 也能过 —— 它守的是「这种装法整体可用」, 不单是 realpath 那一点。
    """
    link = tmp_path / "skein.py"
    link.symlink_to(SCRIPTS / "skein.py")
    assert _ok(sys.executable, str(link), "--help"), "单文件软链下起不来 (abspath 没解析软链?)"


def test_entries_work_from_a_copied_install(tmp_path: Path) -> None:
    """整份复制到无关目录 (plugin cache 就是按 commit 各复制一份)。"""
    dst = tmp_path / "copy"
    shutil.copytree(PLUGIN, dst, ignore=shutil.ignore_patterns(
        "__pycache__", ".ruff_cache", ".mypy_cache", ".worktrees"))
    for e in ENTRIES:
        assert _ok(sys.executable, str(dst / "scripts" / e), "--help"), f"副本里 {e} 起不来"


def test_entries_work_from_unrelated_cwd(ws: Path) -> None:
    """cwd 是用户仓库根, 不是插件目录 —— 这才是真实调用形态。"""
    for e in ENTRIES:
        assert _ok(sys.executable, str(SCRIPTS / e), "--help", cwd=ws), f"异地 cwd 下 {e} 起不来"


def test_pythonpath_pointing_at_another_copy_does_not_cross_contaminate(tmp_path: Path) -> None:
    """有另一副本在 PYTHONPATH 上时, 入口必须 import **自己那一份** skeinlib。

    串副本的症状极难查: 新版入口 + 旧版实现 = 莫名 AttributeError, 而两边文件看着都对。
    (serve 的 reload 子进程就会往 PYTHONPATH 里塞脚本目录, 不是假想场景。)
    """
    other = tmp_path / "other"
    shutil.copytree(PLUGIN, other, ignore=shutil.ignore_patterns(
        "__pycache__", ".ruff_cache", ".mypy_cache", ".worktrees"))
    env = dict(os.environ, PYTHONPATH=str(other / "scripts"))
    probe = (
        "import runpy, sys\n"
        "sys.argv = ['skein.py', '--help']\n"
        "try: runpy.run_path(%r, run_name='__main__')\n"
        "except SystemExit: pass\n"
        "import skeinlib; print(skeinlib.__file__)\n" % str(SCRIPTS / "skein.py"))
    r = subprocess.run([sys.executable, "-c", probe], env=env, cwd=tmp_path,
                       capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=30)
    assert r.returncode == 0, r.stderr
    loaded = r.stdout.strip().splitlines()[-1]
    assert str(SCRIPTS) in loaded, f"串到了另一副本的 skeinlib: {loaded}"
    assert str(other) not in loaded, f"串到了另一副本的 skeinlib: {loaded}"


def test_all_entries_wire_syspath_consistently() -> None:
    """三个入口的接线写法必须一致 (都用 realpath + 插 0 位)。

    ⚠️ 这条守的是**一致性**, 不是某个当前可复现的故障 —— 实测 abspath 在 3.11 下也能过
    (见本文件顶部说明)。留着它是免得三个入口各写一套, 日后换 Python 版本或新增入口时
    有人只改其中一个。真正拦故障的是上面那几条行为测试 + test_bin_wrappers。
    """
    for e in ENTRIES:
        src = (SCRIPTS / e).read_text()
        wire = [ln for ln in src.splitlines()
                if "sys.path.insert" in ln or "_HERE = " in ln]
        assert any("realpath" in ln for ln in wire), f"{e} 的接线没用 realpath: {wire}"
        assert any("sys.path.insert(0," in ln for ln in wire), \
            f"{e} 没把自己插到 sys.path 最前 (多副本共存时会串): {wire}"


if __name__ == "__main__":
    import tempfile

    from conftest import make_ws
    with tempfile.TemporaryDirectory() as td:
        base = Path(td)
        test_entries_work_when_plugin_dir_is_symlinked(base / "a")
        (base / "a").mkdir(exist_ok=True)
    for fn_name in ("test_entry_works_when_only_the_script_is_symlinked",
                    "test_entries_work_from_a_copied_install",
                    "test_pythonpath_pointing_at_another_copy_does_not_cross_contaminate"):
        with tempfile.TemporaryDirectory() as td:
            globals()[fn_name](Path(td))
    with tempfile.TemporaryDirectory() as td:
        d = Path(td) / "w"
        d.mkdir()
        test_entries_work_from_unrelated_cwd(make_ws(d))
    test_all_entries_wire_syspath_consistently()
    print("安装形态自检过")
