#!/usr/bin/env python3
"""依赖自检 + 自动安装 — 纯 stdlib, 入口脚本共享。

入口脚本 (skein.py / spec.py) 在 import 任何 skeinlib 模块**之前**调 ensure_core_deps()。
hooks.py 纯 stdlib 不调 (热路径, 每个 prompt 都跑, 额外 0.1ms 也不值)。

机制:
  1. importlib.util.find_spec 探测 typer / pydantic / yaml 是否可用 (不实际 import)
  2. 任一缺失 → 同步 `pip install -r requirements.txt`
  3. 环境变量 _SKEIN_DEPS_BOOTSTRAPPED 防递归: pip 装完本进程 sys.path 缓存可能未刷新,
     二次进入直接放行, 让原始 ModuleNotFoundError 暴露真正原因

与现有机制的关系:
  - SessionStart hook 的 async pip install 是**预取** (减少首次命中的等待), 本函数是**兜底**
    (预取没跑完 / 没 fire 时仍保证可用)。两者互补不冲突。
  - cli/main.py 的 typer→uv run fallback 仍保留作最后防线 (本函数 pip 装失败时的安全网)。
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


def ensure_core_deps() -> None:
    """核心依赖缺失则自动安装; 已装则秒返回 (find_spec < 0.1ms)。"""
    if os.environ.get(_BOOTSTRAP_ENV) == "1":
        return
    missing = _missing()
    if not missing:
        return
    req = os.path.join(_PLUGIN_ROOT, "requirements.txt")
    cmd = [sys.executable, "-m", "pip", "install", "-q"]
    cmd += ["-r", req] if os.path.isfile(req) else missing
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=120)
    except Exception:
        return  # 装不上不拦 — 让原始 ModuleNotFoundError 暴露真正原因
    os.environ[_BOOTSTRAP_ENV] = "1"
    importlib.invalidate_caches()
