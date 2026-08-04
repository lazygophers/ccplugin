"""skeinlib — SKEIN 引擎的实现层 (纯 stdlib, 禁第三方依赖)。

## 为什么是 `skeinlib` 而不是 `skein`
同目录下的包 `skein/` 会**遮蔽**模块 `skein.py` (Python 3 的 FileFinder 先看带 `__init__.py`
的目录, 后看同名 .py 文件 — 已实测)。而 `scripts/skein.py` 这个路径是对外契约:
`.claude-plugin/plugin.json`、9 个 `agents/*.md`、`bin/` 下三个 wrapper 共 27 处引用它。
包换个名字, 那 27 处一行都不用改。

## 包结构 (9 个子包, 依赖只能自上往下, 禁反向 / 禁循环)
```
utils/        工具底座 — 无业务状态, 无依赖, 谁都能 import
  errors        SkeinError 领域异常
  paths         路径常量 (SCRIPTS_DIR / SKEIN_ENTRY / SPEC_ENTRY)
  debug         Debug 单例 + token 预算守卫
  exec_policy   exec 白名单: 命令 enum → 固定 argv (纯函数)
  token_conversion  char↔token 换算
  derivatives   派生文件白名单 (.gitignore 条目来源)
  fs            git_root / load_stdin / prefix_lines
  timefmt       fmt_ts (epoch → 可读时间)

task/         task 数据模型 + 落盘 + 迁移
  model         TaskStatus / SubtaskStatus / 时间戳常量 (数据底座)       → (无)
  dag           纯函数: 可派发判定 / 关键路径权重 / 进度百分比 / 环检测   → task/model
  timeline      生命周期事件渲染 + fmt_ts                               → task/model
  prd           prd.md 章节读写                                          → utils/errors, task/model
  store         TaskStore: load/save/all/sync — 落盘唯一入口             → utils/errors, task/model, infra/board
  priority      四档优先级校验 + 存量迁移                                → utils/errors, task/model
  readystate    中文 status 一次性迁移                                  → task/model
  migrate       trellis 一次性迁移 (task 文件搬运 + 接线清理)            → task/model

infra/        基础设施 — git 封装 + 渲染
  worktree      git 调用封装 + worktree 生命周期                        → utils/errors, utils/debug
  board         markdown 看板渲染 (纯函数, 被 task/store 调)             → task/dag, task/model

config/       配置层
  manager       Config 类 + pydantic schema + hooks 配置                → utils/errors

core/         业务核心 — 工作区 + 门面 + 协作对象
  workspace     Workspace: 路径/配置/store/阶段钩子 + 工作区写锁         → config, task/store, infra/worktree, hooks
  commands      Skein 门面: 继承 Workspace, 装配协作对象                 → core/*, web/boardsource, core/doctor
  lifecycle     create→confirm→start→check→finish + del/rename          → workspace, task/prd, task/timeline, task/priority, task/dag
  scheduling    claim exec / subtask (DAG 调度)                         → workspace, lifecycle, task/dag, task/timeline
  query         ready / status / list (只读投影)                        → workspace, task/dag, task/model, infra/worktree
  artifacts     prd / fmt / contract (task 工件)                        → workspace, task/prd, task/model
  admin         init / setup / config / clean / board                   → workspace, task/migrate, utils/derivatives, config, infra/worktree
  doctor        DoctorMixin: 体检 + 质量门 + session 上下文注入          → 全部

web/          HTTP/API 层 — 路由 + 数据源 + 视图
  views         Snapshot + DataSource Protocol + 各视图纯函数            → task/dag, task/model, infra/worktree
  serve         build_app 路由 + server 生命周期 + WebSocket 热重载      → web/views, task/store, config, utils/exec_policy
  boardsource   BoardSourceMixin: 生产 adapter + serve 命令编排          → web/serve, task/store, utils/exec_policy

hooks/        钩子执行器 + 复杂度判定 + harness 子命令                   → config (注: 与 spec/ 有运行时双向耦合, 待消解)
spec/         规则记忆库 (namespace × inclusion)                        → utils/errors (注: 与 hooks/ 有运行时双向耦合, 待消解)
cli/          CLI 入口 — Typer 命令树 + dispatch + 工作区锁              → core/commands
  main          主 CLI (skein 命令, ~25 个命令)
```

注: task/store → infra/board 是设计意图 (board 为纯函数, store save 时调它刷 .md; 非循环)。
     hooks/ ↔ spec/ 的双向耦合 (spec/inject→hooks/runner, hooks/{agent,stop}→spec/facade) 待消解 (ADR 0003 S6)。
     core/commands 继承 web/boardsource.BoardSourceMixin + core/doctor.DoctorMixin, 是唯一跨包继承的。

五个协作对象的依赖**只走构造入参** —— `Scheduler(ws, lifecycle)` 这一行就是完整依赖清单。
门面上刻意没有转发方法, `cli/main.py` 的 dispatch 直接指到 `sk.lifecycle.create` 这一级。

## 顶层 shim 文件
顶层 *.py 文件 (errors.py, paths.py, workspace.py, serve.py, views.py 等) 均为一行 re-export shim,
指向对应子包内的实际实现。存在原因: 分批迁移不破坏现有 import 路径 (19+ 处 `from skeinlib.errors import SkeinError`)。
后续可统一改为 `from skeinlib.utils.errors import SkeinError` 后删 shim。

## 入口
`scripts/skein.py` / `spec.py` / `hooks.py` 三个薄壳, 只做 sys.path 接线 + 调 main。
业务代码禁写在入口文件里。

## 本文件保持零 import
`skeinlib.hooks.user_prompt_submit` 在**每个 prompt** 的热路径上, 而 `import skeinlib.hooks.user_prompt_submit` 必然先
执行本文件。这里 import 一个 `pathlib` 就给每次对话加 2.5ms —— 路径常量因此单独放 `utils/paths.py`。
禁在此处加任何 import。
"""
