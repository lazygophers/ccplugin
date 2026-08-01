# 参考手册

## CLI

### skein

| 命令 | 用途 |
| --- | --- |
| `skein init` | 初始化 .skein/ 工作区 |
| `skein doctor` | 健康检查 |
| `skein create <id> [--name] [--desc] [--deps] [--kind] [--parent] [--repos]` | 创建 task |
| `skein confirm <id> [--summary\|--approved]` | 用户确认门 (待处理→就绪)。裸跑非 TTY 会拒。`--summary` 只打印 PRD 审核摘要不改状态; `--approved` = 已在 `AskUserQuestion` 拿到用户批准 |
| `skein start <id>` | 激活 (占 active 槽 + 创建 worktree), 就绪→进行中。通常不必手工跑 — `claim exec` 认领就绪 task 的 subtask 时自动触发 |
| `skein finish <id>` | 收束: commit→merge→销 worktree→标记完成 (归档=保留期后自动, 非 finish 步) |
| `skein archive <id>` | 归档 (丢弃 worktree, 不合并) |
| `skein rename <id> <new-id>` | 重命名 |
| `skein del <id> [<sid>]` `[--dry-run]` | 软删: 整 task 移入 `.skein/trash/`; 给 sid 则只删该 subtask。`--dry-run` 只打印将删什么 |
| `skein current` | 活跃 task |
| `skein list [--status <态>] [--json]` | 列 task。`--status` 取 待处理/就绪/进行中/检查中/已完成 (或 pending/ready/active/check/done), `open`=全部未完成, 逗号多选 |
| `skein board` | 文本看板 |
| `skein view` | 可视化看板 |
| `skein deps <id> [--set <id1,id2>]` | 无 `--set` 只查; 带则设前置 (仅 pending 且无既有 deps 可写, 脚本查自引用/不存在/成环) |
| `skein parent <id> [--set <parent-id>]` | 无 `--set` 只查当前 parent; `--set <id>` 挂到 supertask/task 下 (拒自引用/父不存在/深度超 2 层/自身已有 child); `--set ""` 摘除。任意状态可改, 与 `deps` 正交, 不碰 deps |
| `skein subtask add/claim/ready/start/check/show/done/fail/list <task-id> [sid]` | subtask 管理 (add 登记 / claim 整批认领就绪 / ready 只读预览 / start 单个占槽 / check 勾验收 / show 查全字段 / done 完成 / fail 失败 / list 列态) |
| `skein claim exec\|check` | 全局跨 task 认领批; phase 必填: `exec`=认领 ready subtask → running / `check`=认领 全done 的 进行中 task → 检查中 + 检查通过的 → 已完成 |
| `skein contract list/add <task-id>` | 契约管理 |
| `skein prd read/write/add/check/uncheck <task-id>` | PRD 章节管理 |

### skein-spec

| 命令 | 用途 |
| --- | --- |
| `init` | 初始化 spec 目录 |
| `recall <query>` | 按关键词召回规则 |
| `recall free <text>` | 全文模糊匹配 |
| `sediment --namespace <ns> [--inclusion] [--category]` | 沉淀规则 |
| `prune [--dry-run]` | 清理 stale/重复规则 |
| `maintain` | 全量健康检查 |
| `reconstruct` | 按项目类型重建 |
| `bootstrap [--scan]` | 冷启动播种 |
| `inject-core` | 全文注入 core 规则 |

### skein-hooks

| 命令 | 用途 |
| --- | --- |
| `permission` | 自动批准 .skein/ 操作 |
| `guard` | 阻止直接读写脚本管理文件 |
| `batch` | 阻止并发状态写 |
| `report` | 错误上下文注入 |
| `fmt` | 自动格式化 prd.md |
| `spec-meta` | 检查 spec frontmatter |
| `stop-check` | 扫描 spec → .pending-fix |
| `user-prompt` | 信号路由 |
| `flow-gate` | 跨文件改动无 active task 时提示补建 |
| `agent-start` / `agent-stop` | agent 生命周期钩子入口, 跑 `config.yaml` 的 `hooks.agent.*` (详见 [hooks.md](hooks.md)) |

### Config

| 键 | 默认 | 说明 |
| --- | --- | --- |
| max_active | 2 | 同时活跃 task 数 (subtask 并发复用同一键) |
| retain_days | 7 | 归档保留天数 |
| auto_commit | true | 原地模式 finish 时自动 git commit; worktree 模式恒强制 commit, 本键不参与判定 |
| worktree_root | `.worktrees` | worktree 路径 |
| spec.always_budget | 1000 | always 页常驻注入软预算 (char); 旧键 spec_core_budget 仍作 fallback |
| board_theme/palette/mode | default/blue/light | 看板样式 |

`hooks` (阶段钩子 + agent 钩子) 是可选特性, 不在 `CONFIG_DEFAULTS` 里 (无默认值, `init`/展示均不含),
需手写进 `config.yaml`, 详见 [hooks.md](hooks.md)。

---

## 场景用法

### 请求路由

| 特征 | 路由 | 入口 |
| --- | --- | --- |
| 纯查询/单文件小改 | inline | Claude 直接改 |
| 跨文件/多步/破坏式 | flow | `/skein-flow exec` 或自动 |
| 模糊/边界不清 | grey | AskUserQuestion |

### 场景表

| # | 场景 | 例 | 要点 |
| --- | --- | --- | --- |
| 1 | 单功能开发 | 加手机号登录 | brainstorm 选型, grill, contract |
| 2 | 破坏式重构 | User→UserDTO | 全站 grep 一次改, worktree 可丢弃 |
| 3 | 调研选型 | 选队列方案 | researcher 只读, 结论→sediment |
| 4 | 多 task 并行 | 导出+样式 | `--deps` 声明, max_active=2 |
| 5 | 根因 bug | 金额差 1 分 | 共享函数修, 补回归测试 |
| 6 | 模糊请求 | — | 自动按信号路由 |
| 7 | 中途出问题 | exec/check 卡住 | 自愈→根因复盘|archive |
| 8 | 冷启动空仓 | 空 spec/ | bootstrap 扫 5 维, 默认 recall |
| 9 | 清理残留 | 孤儿 worktree | `/skein-clean` |
| 10 | 大需求冷启动 | 「重构支付」 | 愿景翻译→supertask, grill 3 轴 |

### Super task 模板

普通 `task` 是自成一个闭环的默认类型; `supertask` 是不写代码的顶层聚合层, 仅当需求过大要拆成多个**各自独立跑完 plan→exec→check→finish** 的小需求时才建 — 单 task 能覆盖的中小需求不建 supertask。

```bash
# 建 supertask + child (建时声明)
skein create <id> --kind supertask --name "<名>"
skein create <child1> --parent <id>
skein create <child2> --parent <id>
# child 独立闭环, 末 child → supertask 聚合归档, 深度限 2 层

# 存量 task 改挂 (无需删档重建)
skein parent <child-existing> --set <id>   # 挂
skein parent <child-existing> --set ""     # 摘除
```

`parent` 管归属、`deps` 管执行顺序, 两者正交 — 挂 parent 不隐含也不替代 deps。**supertask finish 前, 全部 child 须已完成**, 否则脚本硬拒并列出未完成 child。

### 错误处理

| 阶段 | 失败 | 重试 | 兜底 |
| --- | --- | --- | --- |
| exec | subtask 报错 | 重派 ≤2 轮 | 停手回传 |
| check | lint/type/test | 修复重跑 | 第 3 轮根因复盘 |
| check | contract | 评估回退 | — |
| finish | 合并冲突 | auto abort→手动 | 禁强解 |
| 任意 | 方案跑歪 | — | `skein archive` |

---

## 术语

### 核心概念

| 术语 | 定义 |
| --- | --- |
| task | SKEIN 管理的闭环工作记录 |
| subtask | task 内最小执行单元, DAG 调度 |
| supertask | 聚合容器, child 各自独立闭环; `kind=supertask` |
| parent | task 的父挂载字段 (`skein parent --set`), 与 deps 正交, 限 2 层 |
| 闭环 | plan→exec→check→finish, 不可跳步 |
| worktree | git worktree, 1 task 1 物理隔离 |
| board | task.md + task.html, 从 task.json 渲染 |
| contract | planning 锁不变量, check 逐条验证 |
| spec | 规则记忆库 (namespace × inclusion) |
| core | 违反即错, 每 session 自动注入 |
| recall | 值得参考, 按关键词召回 |
| sediment | finish 判 learning → namespace×inclusion / drop |
| compaction | SessionStart 对活跃 task 状态压缩重注入 |

### 状态

| 状态 | 含义 | 占 active 槽 |
| --- | --- | --- |
| 待处理 | 规划中 (未过 confirm 用户门) | 否 |
| 就绪 | 规划完成待启动 (已过 confirm, 可 start) | 否 |
| 进行中 | 正在 worktree 中执行 | 是 |
| 检查中 | subtask 全完成, 质量门验证 | 否 |
| 已完成 | 检查通过, 等待归档 | 否 |
| (已归档) | 完成后 _autoclean 目录迁移到 archive/, 非状态值·不在看板; 关联链 (deps + parent/child) 上有未完成 task 时整链不归档 | — |
| 运行中 (subtask) | 正在执行 | — |
| 失败 (subtask) | 执行失败, 可重试 | — |

### Signal Routing

| 术语 | 定义 |
| --- | --- |
| flow | 复杂请求→建 task 闭环 |
| inline | 简单请求→直接改 |
| grey | 模糊→AskUserQuestion |
| /skein-flow exec | 强制 flow 信号 |
