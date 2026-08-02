"""`bin/` 三个 wrapper 的冒烟 — **生产环境实际走的就是它们**。

`plugin.json` 里 hook 与命令全部指向 `${CLAUDE_PLUGIN_ROOT}/bin/skein-hooks` 之类, 不是
`scripts/*.py`。而 wrapper 用 `runpy.run_path(target)` 加载 —— **`run_path` 不会把目标脚本的
目录塞进 `sys.path`**, 直接 `python3 scripts/hooks.py` 却会 (Python 自动加 sys.path[0])。

这个差别真咬过一次: 拆包时 hooks.py 顶部新增 `from skeinlib...` 而没配套 sys.path 接线,
pytest 全绿 (它是直调脚本), 但七个 hook 子命令在真实插件里全部 `ModuleNotFoundError` 退 1 ——
表现是每次对话的 hook 静默失效。所以这里必须按 wrapper 的方式验, 不能图省事直调 scripts/。
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import conftest  # noqa: F401  模块体把 scripts/ 塞进 sys.path (standalone 直跑时 pytest 不在)
from conftest import SCRIPTS, SKEIN  # noqa: E402

BIN = SCRIPTS.parent / "bin"

def _hook_cmds() -> list[str]:
    """子命令清单取自 hooks.py 的真实 DISPATCH, 不硬编码 —— 新增子命令自动纳入本冒烟,
    删掉的也不会留下一条永远红的断言。argv dispatch 那两个 (agent-start/stop) 单独测。"""
    import hooks
    return [c for c in hooks.DISPATCH if c not in hooks._ARGV_DISPATCH]


def _run(wrapper: str, *args: str, stdin: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(BIN / wrapper), *args],
                          capture_output=True, text=True, input=stdin)


def _json_stdout(r: subprocess.CompletedProcess[str]) -> dict[str, object]:
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError as exc:
        raise AssertionError(f"stdout 不是单个 JSON: {r.stdout!r}") from exc


def test_wrappers_exist() -> None:
    for w in ("skein", "skein-spec", "skein-hooks"):
        assert (BIN / w).exists(), f"bin/{w} 缺失 — plugin.json 指着它"


def test_skein_wrapper_runs() -> None:
    r = _run("skein", "--help")
    assert r.returncode == 0, f"bin/skein --help 挂了:\n{r.stderr}"


def test_skein_spec_wrapper_runs() -> None:
    r = _run("skein-spec", "--help")
    assert r.returncode == 0, f"bin/skein-spec --help 挂了:\n{r.stderr}"


def test_bin_wrappers_stdout_json_only(tmp_path: Path) -> None:
    from conftest import make_ws

    make_ws(tmp_path)
    probes = [
        ("skein", ["status", "nope"]),
        ("skein", ["claim", "--dry-run"]),
    ]
    for wrapper, args in probes:
        r = subprocess.run([sys.executable, str(BIN / wrapper), *args], cwd=tmp_path,
                           capture_output=True, text=True, input="")
        # stdout 要么空 (命令无输出) 要么单个 JSON — 不能是 {"ok","code"} 信封
        if r.stdout.strip():
            data = _json_stdout(r)
            assert "ok" not in data, f"bin/{wrapper} {' '.join(args)} 不该有 ok 信封: {data}"


def test_direct_skein_script_stdout_json_only(tmp_path: Path) -> None:
    from conftest import make_ws

    make_ws(tmp_path)
    r = subprocess.run([sys.executable, str(SKEIN), "claim", "--dry-run"], cwd=tmp_path,
                       capture_output=True, text=True)
    data = _json_stdout(r)
    assert set(data) >= {"phase", "dry_run", "exec", "check"}
    assert data["exec"]["ready"] == []
    assert data["exec"]["empty"]["reason"] in {
        "work_pool_full", "no_pending_subtask", "dependencies_blocked"}
    assert data["check"]["to_check"] == []


def test_direct_skein_serve_uses_config_api(tmp_path: Path) -> None:
    from conftest import make_ws

    make_ws(tmp_path)
    cfg = tmp_path / ".skein" / "config.yaml"
    cfg.write_text(cfg.read_text(encoding="utf-8").replace("serve: true", "serve: false"), encoding="utf-8")
    r = subprocess.run([sys.executable, str(SKEIN), "serve", "--auto"], cwd=tmp_path,
                       capture_output=True, text=True, timeout=20)
    assert r.returncode == 0, r.stderr
    assert "AttributeError" not in r.stderr


def test_every_hook_subcommand_survives_wrapper(tmp_path: Path) -> None:
    """每个 hook 子命令经 wrapper 跑一遍, 全部必须 exit 0。

    hook 退非零会打断用户当次对话, 所以「未初始化工作区 + 空 payload」这种最不利输入也得静默
    放行 —— 这既是冒烟也是那条静默纪律的回归。
    """
    for cmd in _hook_cmds():
        r = subprocess.run([sys.executable, str(BIN / "skein-hooks"), cmd],
                           capture_output=True, text=True, input=json.dumps({}), cwd=tmp_path)
        assert r.returncode == 0, f"bin/skein-hooks {cmd} 退 {r.returncode}:\n{r.stderr}"


def test_agent_hooks_survive_wrapper(tmp_path: Path) -> None:
    """agent-start/stop 走 argv dispatch (不读 stdin) —— 不喂 stdin 也不能挂住。"""
    for cmd in ("agent-start", "agent-stop"):
        r = subprocess.run([sys.executable, str(BIN / "skein-hooks"), cmd,
                            "--agent", "skein-executor", "--cwd", str(tmp_path)],
                           capture_output=True, text=True, input="", cwd=tmp_path, timeout=20)
        assert r.returncode == 0, f"bin/skein-hooks {cmd} 退 {r.returncode}:\n{r.stderr}"


# 每个 prompt 都要付的 import 成本, 越少越好。这几个是实测的大头 (各 2-3ms), 一旦有人在
# hooks.py 或它顶层 import 的模块里顺手加一句 `from pathlib import Path`, 这条会红。
# 真需要时局部 import (函数体内), 别提到模块顶部。
HOT_PATH_BANNED = ("pathlib", "subprocess", "argparse", "datetime", "sqlite3", "shutil")


def test_hook_import_stays_lean() -> None:
    """`import hooks` 不得拉进重模块 —— hooks 在每个 prompt 的热路径上。"""
    # 探针用 `-S` 起 (跳过 site/sitecustomize) —— 本仓 .venv 的 _distutils_hack 会在 site 阶段
    # 就 import pathlib, 混在里面就分不清是谁的账。跳过 site 后 sys.modules 里出现的重模块,
    # 必定是 hooks 自己 (或它顶层 import 的模块) 拉的。
    probe = (
        "import sys, json\n"
        f"sys.path.insert(0, {str(SCRIPTS)!r})\n"
        "import hooks\n"
        f"print(json.dumps([m for m in {list(HOT_PATH_BANNED)!r} if m in sys.modules]))\n"
    )
    r = subprocess.run([sys.executable, "-S", "-c", probe], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    leaked = json.loads(r.stdout.strip())
    assert leaked == [], (
        f"import hooks 拉进了重模块 {leaked} — 每个 prompt 都要付这份钱。"
        f"改成函数内局部 import (见 skeinlib/hooks/__init__.py 的热路径纪律)。")


# skein / spec 的**只读**子命令 (跑一遍不改盘)。写命令另有各自的测试, 这里只验「不挂住」。
NON_BLOCKING_PROBE = [
    ("skein", ["list"]), ("skein", ["current"]), ("skein", ["ready"]), ("skein", ["board"]),
    ("skein", ["doctor"]), ("skein", ["status", "nope"]), ("skein", ["claim", "exec", "--dry-run"]),
    ("spec", ["list"]), ("spec", ["inject-core"]), ("spec", ["maintain"]),
    ("spec", ["recall", "x"]), ("spec", ["session-start"]),
]


def test_no_cli_command_blocks_on_stdin(tmp_path: Path) -> None:
    """🛑 CLI 是被 skill / agent 调用的 —— 任何 stdin 交互都会把调用方永久挂住。

    **stdin 必须是一个开着不关的管道**。两个坑都踩过: 用 `DEVNULL` 的话 `input()` 立刻
    EOFError 返回; 用 `PIPE` 但调 `communicate()` 的话它会把 stdin 关掉, 同样立刻 EOF。
    只有 `Popen(stdin=PIPE)` + `wait()`(不碰 communicate) 才真的把管道留着, 精确复现
    「调用方是 agent, stdin 开着但没人敲」的现场。

    退出码不限 —— 未初始化/参数不全时合法地退非零; 这条只管「有没有返回」。
    """
    from conftest import MEM, SKEIN, make_ws
    make_ws(tmp_path)
    scripts = {"skein": SKEIN, "spec": MEM}
    for tool, args in NON_BLOCKING_PROBE:
        proc = subprocess.Popen(
            [sys.executable, str(scripts[tool]), *args], cwd=tmp_path,
            stdin=subprocess.PIPE,                    # 开着不写不关 = 模拟 agent 调用
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            # 只 wait, **禁用 communicate** —— 后者会把 stdin 关掉, 于是 input() 拿到 EOF
            # 立刻返回, 测试就抓不到了 (踩过一次)。输出丢 DEVNULL 免 PIPE 写满自成死锁。
            proc.wait(timeout=20)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
            raise AssertionError(
                f"`{tool} {' '.join(args)}` 在 stdin 开着时不返回 — 它在等输入。"
                f"CLI 禁交互 (调用方是 agent, 没人能敲那个输入)。") from None


if __name__ == "__main__":
    import tempfile
    test_wrappers_exist()
    test_skein_wrapper_runs()
    test_skein_spec_wrapper_runs()
    with tempfile.TemporaryDirectory() as td:
        test_every_hook_subcommand_survives_wrapper(Path(td))
        test_agent_hooks_survive_wrapper(Path(td))
    test_hook_import_stays_lean()
    with tempfile.TemporaryDirectory() as td:
        test_no_cli_command_blocks_on_stdin(Path(td))
    print("bin wrapper 冒烟过")
