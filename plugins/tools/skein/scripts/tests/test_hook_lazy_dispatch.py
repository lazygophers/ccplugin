"""hook 子命令**只加载自己那条链** —— DISPATCH 存字符串而非函数对象的全部理由。

## 为什么要守
`DISPATCH = {"fmt": cmd_fmt, ...}` 这种写法要求 11 个子命令的模块全部先 import 一遍才拿得到
函数对象。于是每次跑 `permission` (用户每次授权都跑) 都顺带加载 `subprocess`、`pathlib`、整个
`skeinlib.spec` 门面 —— 全是 fmt / stop-check 才用得上的。

改回去不会让任何测试变红, 也不会有任何肉眼可见的症状, 只是每次对话默默多付几十毫秒。这种
「退化无症状」的性质正是需要静态守卫的那类。

## 局限
只测「模块有没有被 import」, 不测耗时 —— 实测子进程启动噪声 (20~40ms 波动) 远大于这里省下的
量, 拿墙钟做断言必然出 flake。模块加载与否是确定性的, 所以断这个。
"""
from __future__ import annotations

import json
import subprocess
import sys

import conftest  # noqa: F401  模块体把 scripts/ 塞进 sys.path
from conftest import SCRIPTS  # noqa: E402

# 每个子命令**允许**加载的 skeinlib.hooks 子模块 (cli/util 是分发骨架, 人人都要)
BASE = {"skeinlib.hooks", "skeinlib.hooks.cli", "skeinlib.hooks.util"}
EXPECTED: dict[str, set[str]] = {
    "permission": BASE | {"skeinlib.hooks.permission"},
    "guard": BASE | {"skeinlib.hooks.guard"},
    "batch": BASE | {"skeinlib.hooks.batch"},
    "report": BASE | {"skeinlib.hooks.report"},
    "fmt": BASE | {"skeinlib.hooks.postwrite"},
    "spec-meta": BASE | {"skeinlib.hooks.postwrite"},
    "flow-gate": BASE | {"skeinlib.hooks.postwrite"},
    "stop-check": BASE | {"skeinlib.hooks.stopcheck"},
    "user-prompt": BASE | {"skeinlib.hooks.prompt", "skeinlib.hooks.judge"},
    "agent-start": BASE | {"skeinlib.hooks.agent"},
    "agent-stop": BASE | {"skeinlib.hooks.agent"},
}


def _loaded(sub: str) -> set[str]:
    """解析该子命令后, sys.modules 里出现了哪些 skeinlib.hooks.* 模块。"""
    probe = (
        "import sys, json\n"
        f"sys.path.insert(0, {str(SCRIPTS)!r})\n"
        "from skeinlib.hooks.cli import _resolve\n"
        f"_resolve({sub!r})\n"
        "print(json.dumps([m for m in sys.modules if m.startswith('skeinlib.hooks')]))\n"
    )
    r = subprocess.run([sys.executable, "-c", probe],
                       capture_output=True, text=True, timeout=30)
    assert r.returncode == 0, r.stderr
    return set(json.loads(r.stdout.strip()))


def test_each_subcommand_loads_only_its_own_module() -> None:
    extra: list[str] = []
    for sub, allowed in EXPECTED.items():
        loaded = _loaded(sub)
        surplus = loaded - allowed
        if surplus:
            extra.append(f"{sub} 多加载了 {sorted(surplus)}")
    assert not extra, (
        "hook 子命令加载了用不上的模块 (DISPATCH 是不是被改回存函数对象了?):\n  "
        + "\n  ".join(extra))


def test_dispatch_stores_strings_not_callables() -> None:
    """DISPATCH 的值必须是 `"模块:函数"` 字符串 —— 存函数对象就等于放弃懒加载。"""
    sys.path.insert(0, str(SCRIPTS))
    from skeinlib.hooks.cli import DISPATCH
    bad = {k: v for k, v in DISPATCH.items() if not isinstance(v, str) or ":" not in v}
    assert not bad, f"DISPATCH 里这些值不是 '模块:函数' 字符串: {bad}"


def test_every_dispatch_target_resolves() -> None:
    """字符串 dispatch 的代价: 打错模块/函数名, 要跑到那个子命令才炸。这条把它提前到单测。"""
    sys.path.insert(0, str(SCRIPTS))
    from skeinlib.hooks.cli import DISPATCH, _resolve
    for name in DISPATCH:
        fn = _resolve(name)
        assert callable(fn), f"{name} → {DISPATCH[name]} 解析出来不可调用: {fn!r}"


if __name__ == "__main__":
    for fn_name, fn in sorted(globals().items()):
        if fn_name.startswith("test_") and callable(fn):
            fn()
    print("hook 懒 dispatch 自检过")
