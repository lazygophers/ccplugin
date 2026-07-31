#!/usr/bin/env python3
"""SKEIN hook 统一入口 — **入口薄壳, 业务在 skeinlib/hooks/。**

这个路径是对外契约 (`bin/skein-hooks`、`.claude-plugin/plugin.json` 的 11 条 hook 配置都指着
它), 故文件名不动, 只把实现搬进包。分层与模块划分见 `skeinlib/hooks/__init__.py`。

子命令:
  permission  PermissionRequest/PermissionDenied: .skein/ 自有内容操作默认同意, 免逐次授权。
  guard       PreToolUse: 硬阻 AI 直接读写 .skein/ 脚本管理文件 + trellis 未初始化迁移门。
  batch       PostToolBatch: 拦并行的 ≥2 个 .skein 状态写命令 (竞态防护)。
  report      PostToolUseFailure: 本插件脚本报错时注入上下文 + 引导手动报 issue。
  fmt         PostToolUse: 写 .skein/task/<id>/prd.md 后自动 skein fmt <id> 规范化。
  spec-meta   PostToolUse: 写 .skein/spec/**/*.md 后检查 frontmatter 必填字段 + layer 合法 (非阻塞 warning)。
  flow-gate   PostToolUse: 写源码后若无 active task 且已跨 ≥2 文件 → 提示补 create (非阻塞, 一次)。
  stop-check  Stop: 扫 spec 问题写 .pending-fix 标记 (只读不修, 供 main 下回合派 specer bg 修复)。
  user-prompt UserPromptSubmit: 已初始化按 prompt 信号注入判据 + 证据; 未初始化注入 setup 提示。
  agent-start / agent-stop  agent 生命周期钩子 (参数走 --flag argv, 不读 stdin)。

各子命令读 stdin JSON, 无命中一律静默 exit 0。
"""
from __future__ import annotations

import os
import sys

# 入口接线: 把**本文件真实所在目录**放到 sys.path 最前, 才能 import skeinlib。
#
# 为什么必须显式写这行 (Python 不会替你做):
# ① `bin/` wrapper 走 `runpy.run_path()`, 它**根本不设 sys.path[0]** —— 直接 `python3 x.py`
#    才会自动加脚本目录。生产环境 (plugin.json) 走的正是 wrapper, 漏了这行整套 hook 全崩。
# ② 插到**最前**: 一台机器上 skein 常同时存在多份 (开发仓 / marketplace / plugin cache 按
#    commit 各一份), serve 的 reload 子进程还会往 PYTHONPATH 塞脚本目录。插 0 位保证 import
#    到的是**跟本入口同一份**的 skeinlib —— 串副本的症状是新版入口配旧版实现, 极难查。
# ③ 靠 `__file__` 而非 cwd: 调用方的工作目录是用户仓库根, 不是插件目录; harness 起 hook 时
#    既不走 Bash PATH 也不保证 cwd。
#
# 用 `realpath` 而非 `abspath` 是防御性的: Python 3.11+ 对直接跑的脚本已会解析 sys.path[0]
# 的软链, 目录软链的遍历也本就透明 —— 实测两者当前无差别。但 runpy 那条路径不享受前者,
# 且成本为零, 所以按更严的写。
#
# 刻意用 os.path 而非 pathlib: pathlib 要 2.5ms, 而这是每个 prompt 都跑的路径, os 本就已导入。
_HERE = os.path.dirname(os.path.realpath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from skeinlib.hooks.cli import DISPATCH, _ARGV_DISPATCH, main, self_check  # noqa: E402

__all__ = ["DISPATCH", "_ARGV_DISPATCH", "main", "self_check"]

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--self-check":
        sys.exit(self_check())
    sys.exit(main())
