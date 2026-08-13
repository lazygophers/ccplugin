# 共享资源 (互斥 / 串行规则)

资源 = 任意"同一时刻只能由一方安全使用"的对象。subtask 之间资源相交 → 必须串行。design / implement 阶段就标注, 不要丢给 dispatch 时临时判定。

## 资源类型

| 资源 | 示例 | 互斥粒度 |
| --- | --- | --- |
| 目录 / 文件 | 同一文件夹、同一文件 | 文件级 / 目录级 |
| 运行环境 | 进程、端口、数据库实例 | 端口号 / 实例 |
| 配置 / 设置 | `settings.json`、共享配置项 | 文件 + 字段 |
| 环境变量 | `.env`、shell export | 变量名 |
| 网络 / 外部 API | 限流配额、API 密钥、第三方服务额度 | 密钥 / quota |
| token 预算 | 模型上下文窗口、月度配额 | 全局共享 |
| 人工审批 | 用户确认槽位 | 同一时刻只能问一个 |
| 顺序敏感步骤 | 发布、合并、状态切换 | 步骤序列 |
| Trellis 状态 | `task.json` / journal / spec 写入 | 文件 |

## Trellis 特定互斥

| 操作 | 互斥范围 | 后果 |
| --- | --- | --- |
| `task.py start` / `complete` | 同一 task | 状态机冲突, 必串行 |
| `.trellis/tasks/<dir>/` 写 | 同一 task 目录 | 文件覆盖, 必串行或 worktree |
| `.trellis/workspace/<dev>/journal-*.md` 写 | 同一 developer | journal 损坏, 必串行 |
| spec 写入 (走 trellisx-spec) | 整个 spec 目录 | 双源漂移, 必走审批门 |
| `implement.jsonl` / `check.jsonl` curate | 同一 task | 必串行 |

## 标注示例

design.md 模块表加资源列:

| 模块 | 执行层 | 独占资源 |
| --- | --- | --- |
| M1 | sub-agent | `packages/api/src/auth/**`, port 5432 (test DB), `.env.test` |
| M2 | sub-agent | `packages/web/src/auth/**` |

M1 与 M2 资源不交 → 可并行。

implement.md subtask 一行:

```
资源: packages/api/src/auth/**, .env.test, port 5432
```

## 并行判定算法

```
for each pair (Si, Sj) where i < j:
    if Si.resources ∩ Sj.resources == ∅ and Sj 不依赖 Si:
        可并行
    else:
        必串行 → 在 Sj.依赖 加 Si
```

## 冲突解决策略

| 冲突 | 解决 |
| --- | --- |
| 两 subtask 改同文件不同区段 | 仍串行 (合并冲突难自动) |
| 两 subtask 改不同文件但共享配置 | 串行或拆配置 |
| 全局 token 预算 | coordinator 追踪各 subtask 累计消耗, 超预算收窄并行 |
| 用户审批槽位 | 等待用户期间允许执行无人工依赖 subtask |
| 同一 task 目录写入 | 串行或并行 worktree |

## 等待用户期间

trellis 任务编排允许:
- 等待用户审批某 deliverable 时, 其他 deliverable 无人工依赖的 subtask 可继续推进
- 等待用户回答某调研问题时, 其他主题调研可并行
- 等待用户决定某接口契约时, 不依赖该契约的实现不可启动 (但相关 mock 可写)

> 硬停 — 等待用户期间禁 spawn ≥ 2 个会问用户的 sub-agent。审批槽位同一时刻只能问一个, 并发提问会让用户上下文错乱、答非所问。
