# 参考手册

## CLI

### skein

| 命令 | 用途 |
| --- | --- |
| `skein init` | 初始化 .skein/ 工作区 |
| `skein doctor` | 健康检查 |
| `skein create <id> [--name] [--desc] [--deps] [--kind] [--parent] [--repos]` | 创建 task |
| `skein start <id>` | 开始 (创建 worktree) |
| `skein finish <id> [--force]` | 完成 (合并 + sediment + archive) |
| `skein archive <id>` | 归档 (丢弃 worktree, 不合并) |
| `skein rename <id> <new-id>` | 重命名 |
| `skein cancel <id>` | 取消 |
| `skein current` | 活跃 task |
| `skein list [--all]` | 列 task |
| `skein board` | 文本看板 |
| `skein view` | 可视化看板 |
| `skein deps <id> [--tree] [--reverse]` | 查看依赖 |
| `skein subtask list/create/start/done/fail/claim <task-id>` | subtask 管理 |
| `skein claim` | 全局跨 task claim |
| `skein contract list/add <task-id>` | 契约管理 |
| `skein prd read/write/add/check/uncheck <task-id>` | PRD 章节管理 |

### skein-spec

| 命令 | 用途 |
| --- | --- |
| `init` | 初始化 spec 目录 |
| `recall <query>` | 按关键词召回规则 |
| `recall free <text>` | 全文模糊匹配 |
| `sediment <task-id> [--layer] [--category]` | 沉淀规则 |
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
| `task-created` | 阻止 TaskCreate |
| `subagent-start` | 注入 core 规则 |
| `session-context` | 注入活跃 task + core |

### Config

| 键 | 默认 | 说明 |
| --- | --- | --- |
| max_active | 2 | 同时活跃 task 数 |
| max_parallel | 2 | 同时运行 subtask 数 |
| retain_days | 7 | 归档保留天数 |
| auto_commit | true | 自动 git commit |
| worktree_root | `.worktrees` | worktree 路径 |
| spec_core_budget | 8000 | core 注入预算 (char) |
| board_theme/palette/mode | default/blue/light | 看板样式 |

---

## 场景用法

### 请求路由

| 特征 | 路由 | 入口 |
| --- | --- | --- |
| 纯查询/单文件小改 | inline | Claude 直接改 |
| 跨文件/多步/破坏式 | flow | `/skein-exec` 或自动 |
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

```bash
skein create <id> --kind supertask --name "<名>"
skein create <child1> --parent <id>
skein create <child2> --parent <id>
# child 独立闭环, 末 child → supertask 聚合归档, 深度限 2 层
```

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
| supertask | 聚合容器, child 各自独立闭环 |
| 闭环 | plan→exec→check→finish, 不可跳步 |
| worktree | git worktree, 1 task 1 物理隔离 |
| board | task.md + task.html, 从 task.json 渲染 |
| contract | planning 锁不变量, check 逐条验证 |
| spec | 两层规则记忆库 |
| core | 违反即错, 每 session 自动注入 |
| recall | 值得参考, 按关键词召回 |
| sediment | finish 判 learning → core/recall/drop |
| compaction | SessionStart 对活跃 task 状态压缩重注入 |

### 状态

| 状态 | 含义 |
| --- | --- |
| 待处理 | 已规划, 未开始 |
| 进行中 | 正在 worktree 中执行 |
| 检查中 | subtask 全完成, 质量门验证 |
| 已完成 | 检查通过, 等待归档 |
| 已归档 | finish 完成, worktree 销毁 |
| 运行中 (subtask) | 正在执行 |
| 失败 (subtask) | 执行失败, 可重试 |

### Signal Routing

| 术语 | 定义 |
| --- | --- |
| flow | 复杂请求→建 task 闭环 |
| inline | 简单请求→直接改 |
| grey | 模糊→AskUserQuestion |
| /skein-exec | 强制 flow 信号 |
