"""skeinlib — SKEIN 引擎的实现层 (纯 stdlib, 禁第三方依赖)。

## 为什么是 `skeinlib` 而不是 `skein`
同目录下的包 `skein/` 会**遮蔽**模块 `skein.py` (Python 3 的 FileFinder 先看带 `__init__.py`
的目录, 后看同名 .py 文件 — 已实测)。而 `scripts/skein.py` 这个路径是对外契约:
`.claude-plugin/plugin.json`、9 个 `agents/*.md`、`bin/` 下三个 wrapper 共 27 处引用它。
包换个名字, 那 27 处一行都不用改。

## 分层 (依赖只能自上往下, 禁反向 / 禁循环)
```
errors      SkeinError — 无依赖, 谁都能 import
config      CONFIG_DEFAULTS / mini-YAML / hooks schema      → errors
dag         纯函数: 可派发判定 / 关键路径权重 / 进度百分比      → (无)
views       Snapshot + 各视图纯函数 (Snapshot → dict)        → dag
store       TaskStore: load/save/all/sync — 落盘唯一入口     → errors, config
board       markdown 看板渲染                               → store, dag
worktree    git 封装 + worktree 生命周期                     → errors, config
prd         prd.md 章节读写                                 → errors
serve       http 端点 + server 生命周期                      → views, store, config
doctor      体检 + 质量门 + session 上下文注入                → 全部
migrate     trellis 一次性迁移 (与 task 生命周期无关, 单独放)  → store, config
workspace   Workspace: 路径/配置/store/阶段钩子 + 工作区写锁  → config, store, worktree
  ├ admin      init / setup / config / clean / board         → workspace, migrate
  ├ lifecycle  create→confirm→start→check→finish + del/rename → workspace, prd, worktree
  ├ scheduling claim exec / subtask (DAG 调度)                     → workspace, lifecycle, dag
  ├ query      current / ready / status / list (只读)         → workspace, dag, views
  └ artifacts  prd / fmt / contract (task 工件)               → workspace, prd
commands    Skein 门面: 继承 Workspace, 装配上面五个 + 两 mixin → 全部
cli         argparse + dispatch + 工作区锁                   → commands
hooks/      钩子执行器 + 复杂度判定 + harness 子命令           → config
spec/       规则记忆库 (namespace × inclusion)               → errors
```

五个协作对象的依赖**只走构造入参** —— `Scheduler(ws, lifecycle)` 这一行就是完整依赖清单。
门面上刻意没有转发方法, `cli.py` 的 dispatch 直接指到 `sk.lifecycle.create` 这一级。

## 入口
`scripts/skein.py` / `spec.py` / `hooks.py` 三个薄壳, 只做 sys.path 接线 + 调 main。
业务代码禁写在入口文件里。

## 本文件保持零 import
`skeinlib.hooks.judge` 在**每个 prompt** 的热路径上, 而 `import skeinlib.hooks.judge` 必然先
执行本文件。这里 import 一个 `pathlib` 就给每次对话加 2.5ms —— 路径常量因此单独放 `paths.py`。
禁在此处加任何 import。
"""
