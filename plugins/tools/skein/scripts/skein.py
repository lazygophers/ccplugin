#!/usr/bin/env python3
"""SKEIN — 独立任务管理引擎 (零 trellis 依赖, 纯 stdlib)。**入口薄壳, 业务在 skeinlib/。**

这个路径是对外契约: `.claude-plugin/plugin.json`、`agents/*.md`、`bin/skein` 共 27 处引用它。
所以文件名不动, 只把实现搬进 `skeinlib/` 包 (包名不叫 skein —— 同目录下同名包会遮蔽本模块)。
分层与依赖方向见 `skeinlib/__init__.py`。

工作区布局 (git 根下):
  .skein/.gitignore               init 生成: 忽略 task.md (从 task.json 无损重建); 另补 worktree.root 到根 .gitignore
  .skein/config.yaml              设置 (max_active / auto_commit / worktree.root / hooks)
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

import sys
from pathlib import Path

# hook 环境不走 Bash PATH 也不保证 cwd —— 显式把本目录塞进 sys.path, 才能 import skeinlib。
sys.path.insert(0, str(Path(__file__).resolve().parent))

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
