#!/usr/bin/env python3
"""依赖自检 + 自动重跑 — 纯 stdlib, 入口脚本共享。

入口脚本 (skein.py / spec.py) 在 import 任何 skeinlib 模块**之前**调 ensure_core_deps()。
hooks.py 纯 stdlib 不调 (热路径, 每个 prompt 都跑, 额外 0.1ms 也不值)。

机制:
  1. importlib.util.find_spec 探测 typer / pydantic / yaml 是否可用 (不实际 import)
  2. 任一缺失 → 用 uv 的临时环境把**本进程原样重跑一遍**, 退出码透传
  3. 环境变量 _SKEIN_DEPS_BOOTSTRAPPED 防递归: 重跑那一次仍缺就放行, 让原始
     ModuleNotFoundError 暴露真正原因, 不无限重启

为什么不再用 `pip install`: Homebrew / 发行版自带的 python3 是 PEP 668 externally-managed,
pip 直接拒装 (`error: externally-managed-environment`), 而这恰恰是用户裸调本脚本时最常用的
解释器 —— 兜底在最需要它的场景下 100% 失效。uv 的 `--with-requirements` 装进临时环境, 不碰
系统 site-packages, 绕开该限制。`--no-project` 必带: 否则 uv 会去解析**调用方仓库**的
pyproject.toml (用户仓库跟本插件毫无关系), 装出一堆无关依赖甚至直接失败。

与现有机制的关系:
  - SessionStart hook 的 async pip install 是**预取** (减少首次命中的等待), 本函数是**兜底**
    (预取没跑完 / 没 fire 时仍保证可用)。两者互补不冲突。
  - cli/main.py 的 typer→uv 重跑 fallback 仍保留作最后防线, 共用下面的 uv_rerun_cmd()。
"""
from __future__ import annotations

import importlib.util
import os
import subprocess
import sys

_HERE = os.path.dirname(os.path.realpath(__file__))
_PLUGIN_ROOT = os.path.dirname(_HERE)  # scripts/ 上一级 = 插件根

# 核心运行依赖: import 名 → pip 包名 (fastapi/uvicorn 仅 serve 需要, 由 serve.py 自行兜底)
_CORE_DEPS: dict[str, str] = {"typer": "typer", "pydantic": "pydantic", "yaml": "pyyaml"}

_BOOTSTRAP_ENV = "_SKEIN_DEPS_BOOTSTRAPPED"


def _missing() -> list[str]:
    """返回缺失的 pip 包名列表 (find_spec 探测, 不实际 import)。"""
    return [pkg for mod, pkg in _CORE_DEPS.items()
            if importlib.util.find_spec(mod) is None]


def uv_rerun_cmd(argv: list[str]) -> list[str]:
    """构造「带齐依赖重跑 argv」的命令行 (不执行)。

    requirements.txt 缺失时退化成逐个 `--with` 核心包 —— 装少点也比整条兜底哑掉强。
    """
    req = os.path.join(_PLUGIN_ROOT, "requirements.txt")
    deps = (["--with-requirements", req] if os.path.isfile(req)
            else [arg for pkg in _CORE_DEPS.values() for arg in ("--with", pkg)])
    return ["uv", "run", *deps, "--no-project", "python3", *argv]


def ensure_core_deps() -> None:
    """核心依赖缺失则用 uv 带依赖重跑本进程; 已装则秒返回 (find_spec < 0.1ms)。"""
    if os.environ.get(_BOOTSTRAP_ENV) == "1":
        return
    if not _missing():
        return
    try:
        proc = subprocess.run(uv_rerun_cmd(sys.argv),
                              env=dict(os.environ, **{_BOOTSTRAP_ENV: "1"}))
    except OSError:
        return  # 连 uv 都没有 — 不拦, 让原始 ModuleNotFoundError 暴露真正原因
    raise SystemExit(proc.returncode)
