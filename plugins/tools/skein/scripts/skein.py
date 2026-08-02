#!/usr/bin/env python3
"""SKEIN — 独立任务管理引擎 (零 trellis 依赖, 纯 stdlib)。**入口薄壳, 业务在 skeinlib/。**

这个路径是对外契约: `.claude-plugin/plugin.json`、`agents/*.md`、`bin/skein` 共 27 处引用它。
所以文件名不动, 只把实现搬进 `skeinlib/` 包 (包名不叫 skein —— 同目录下同名包会遮蔽本模块)。
分层与依赖方向见 `skeinlib/__init__.py`。

工作区布局 (git 根下):
  .skein/.gitignore               init 生成: 忽略 task.md (从 task.json 无损重建); 另补 worktree.root 到根 .gitignore
  .skein/config.yaml              设置 (pools.work/gate / auto_commit / worktree.root / hooks)
  .skein/task.json                {tasks:[{id,status,deps,worktree,parent,kind}]}  顶层状态汇总 — 脚本维护, AI 禁读写
  .skein/task.md                  顶层看板 (task.json 渲染, git 忽略) — 脚本维护, AI 禁读写
  .skein/task/<id>/task.json      单 task 记录 + subtask DAG — 脚本维护, AI 禁读写
  .skein/task/<id>/task.md        单 task 子任务看板 + 调度 DAG (渲染) — 脚本维护, AI 禁读写
  .skein/task/<id>/prd.md         主入口: 需求 + 索引区 (create 落脚手架, skein-plan 填, AI 可读写)
  .skein/task/<id>/design.md      详细设计 (架构/取舍/选型; 不含调度图, 调度归 task.json)
  .skein/task/<id>/findings.md    深度调研收敛结论 (仅真调研时生; skein-researcher 边研边增量写, 非预建)
  .skein/task/<id>/research/       researcher 过程笔记 (多篇, 仅真调研时生; 收敛增量进 findings.md)
  .skein/task/archive/<年>/<月-日>/<id>/  归档 (按完成日期分层)

四个 task.json/task.md (顶层 + per-task) 全由本引擎维护, AI 只经命令 stdout 取态
(current/list/board/subtask list/ready), 禁直接 Read/Edit/Write (skein-hooks guard 硬阻)。
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
_HERE = os.path.dirname(os.path.realpath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from skeinlib.cli import main  # noqa: E402
from skeinlib.commands import Skein  # noqa: E402  对外符号: 测试与 hooks 按名取用
from skeinlib.errors import SkeinError  # noqa: E402

__all__ = ["Skein", "SkeinError", "main"]

if __name__ == "__main__":
    try:
        main()
    except (SkeinError, ValueError) as e:
        # **唯一**转退出码的地方。库侧一律抛 SkeinError (见 skeinlib/errors.py), 配置语法错抛
        # ValueError (见 config._yaml_bad) —— 库里不碰 SystemExit, 测试才能进程内 pytest.raises。
        # 消息原样落 stderr: 套件 71 处 stderr 断言靠它, 禁在此加前缀/包装/翻译。
        raise SystemExit(str(e)) from None
