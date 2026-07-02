# 进度通讯硬规

coordinator (main / agent-team leader) 必须实时回传用户 subtask 进度, **禁批量延迟汇总**。用户失去中途干预机会 = 调度失败。

## 通讯场景表

| 场景 | 必须动作 |
| --- | --- |
| sub-agent 完成 / 阻塞 | main 立即输出 `进度: <subtask-id> <状态> <≤30 字摘要>` 回传用户 |
| teammate 完成 / 阻塞 | SendMessage → leader; leader 综合后向用户输出 `团队进度: <subtask> <成员> <摘要>` |
| workflow 阶段完成 | main 读 `/workflows` 进度视图, 输出 `阶段 <N>/<M> <摘要>` |
| coordinator 收到失败 | 立即决策 (重试 / 换执行者 / 重规划) + 向用户说明决策理由 |
| ≥ 30 分钟无产出 | coordinator 主动 ping 执行者; 无响应按 `failure-recovery.md` 失败回退 |
| 用户审批等待中 | 允许执行无人工依赖的 subtask, 但禁同时跑 ≥ 2 个会触发审批的 |
| 异步等待 (派任务后结束回合前) | main MUST 输出 in_flight + pending task 清单表格 (格式见 §异步等待清单格式) |

## 通讯模式 (按执行层)

### sub-agent 模式

```
sub-agent 执行 → 输出摘要 → main 收到 → main 立即"进度:"行回用户 → 决策下一步
```

- sub-agent 之间互不通信; main 是唯一汇聚点
- 摘要必须含: subtask id / 状态 (done/blocked/partial) / 关键产出路径 / 阻塞原因 (若有)
- main 禁攒多条再汇总 — 每条 sub-agent 返回 = 一次回传

### agent-team 模式

```
teammate 完成 → SendMessage(leader, "S<id> done <摘要>")
            ↓
leader 收 → 综合当前团队全部 in_flight subtask 状态
            ↓
leader 向用户输出 "团队进度: <汇总>"
            ↓
leader 决策: 唤醒下游 / 重派 / 上报阻塞
```

- teammate 完成不发 SendMessage 直接退出 = leader 不知任务结束 (禁)
- leader 必须维持团队状态视图; 收到 SendMessage 立即综合, 不延迟
- TeammateIdle hook 可用于阻止空闲并发反馈 (按需)

### workflow 模式

```
workflow 脚本 → 各 agent 完成 → 脚本变量收集
            ↓
main 监听 /workflows 视图变化
            ↓
每阶段完成 main 输出 "阶段 N/M <摘要>"
            ↓
全部完成 main 综合输出最终结果
```

- workflow 之间无 SendMessage; 各 agent 独立完成
- 阶段失败 → workflow 脚本 try/catch 转 null, 下游 `.filter(Boolean)` 跳过
- 主会话不直接干预正在跑的 workflow agent; 中途停止用 `/workflows` 选中按 `x`

## 摘要格式 (≤ 30 字)

| 字段 | 示例 |
| --- | --- |
| subtask id + 标题 | `S3 · auth-jwt-rotation` |
| 状态 | `done` / `blocked` / `partial` |
| 关键产出 | `src/auth/jwt.ts:42-87 + 3 tests` |
| 阻塞原因 (若有) | `blocked: missing JWT_SECRET in env` |

组合示例:
```
进度: S3 · auth-jwt-rotation done; src/auth/jwt.ts + tests/auth/jwt.test.ts; 12 passing
```

## 异步等待清单格式

main 派出异步任务后**结束本回合前** (workflow 异步跑等 notification / 后台 sub-agent 在跑 / 用户审批等待), MUST 输出当前任务全景表格, 让用户在异步间隙保持中途干预视角。同步前台阻塞等待 (main 自己在等, 无独立清单) / 无在跑任务 → 不触发。

### 触发场景 (任一即触发)

| 场景 | 说明 |
| --- | --- |
| workflow 异步跑 | `run_in_background` workflow 派出, main 结束回合等 notification |
| 后台 sub-agent | 派出 background sub-agent, main 等返回 |
| 用户审批等待 | 有在跑的无人工依赖 subtask, 同时等用户审批 |

### 表格模板

```
当前任务清单
| subtask | 状态 | 摘要 | 阻塞 |
|---|---|---|---|
| <id> | in_flight/pending/blocked | ≤30 字 | blocked 填原因, 否则 - |
```

- `subtask` = subtask id + 标题 (如 `S1 · jwt-utils`)
- `状态` 取值: `in_flight` (在跑) / `pending` (待派, 含等上游依赖) / `blocked` (阻塞)
- `摘要` ≤ 30 字, 含交付物路径或关键产出
- `阻塞` = blocked 时填阻塞原因 (如 `缺 JWT_SECRET` / `等 S1`), 非 blocked 填 `-`
- 内容复用 main 已维护的 DAG 调度态 (见 `scheduling.md`) + workflow `/workflows` 视图, 不新算

### 范例

```
当前任务清单
| subtask | 状态 | 摘要 | 阻塞 |
|---|---|---|---|
| S1 · jwt-utils | in_flight | src/auth/jwt.ts 实现 + 单测 | - |
| S2 · jwt-middleware | pending | middleware 接入 Express | 等 S1 |
| S3 · e2e 测试 | blocked | tests/e2e/auth.test.ts | blocked: 缺测试环境 |
```

### 与进度回传的区别

- **进度回传** (`进度: <id> done <摘要>`): 单 subtask 完成时一行通知
- **异步等待清单**: 派出异步任务结束回合前, **全景表格** (含所有 in_flight/pending/blocked)

两者不互斥: 任一 subagent 完成 → 先回传进度行; 若该完成触发 main 进入异步等待 → 再输出清单表格。

## 禁止

- **批量执行后才汇总进度** — 用户失去中途干预机会
- **coordinator 派 subtask 后转去做其他事** — 失去调度视角
- **teammate 完成不发 SendMessage 直接退出** — leader 不知任务结束
- **摘要写 "完成" / "OK" / "没问题"** — 必须含产出路径
- **失败时只回 "失败" 不说原因** — 必须含错误信息或文件:行
- **延迟通讯 "等全部跑完再回报"** — 必须每个 subtask 完成立即回
- **异步等待结束回合不输出清单** — 用户面对空白, 失去任务全景视角, 必须输出 §异步等待清单格式 的表格

## 中途修正路由 (in-flight correction)

执行中 (agent/member 已派发在跑) 收到用户新指令时, coordinator 的标准动作。核心: **新指令不是直接动手的信号, 是先判归属再决定路由的信号**。

### 判归属 (三分支)

| 判定 | 含义 | 路由 |
| --- | --- | --- |
| **属当前任务** | 对已派交付的修正 / 补充 / 细化 (同一 deliverable 范围内) | → 改文档 + 通知在跑 agent (下方流程) |
| **独立新任务** | 与当前 in_flight 交付无关 | → no_task 强推 task 新建 / 排队, **不打断**当前 agent |
| **判不准** | 边界模糊, 既像修正又像新需求 | → 🔴 AskUserQuestion 让用户裁定, 禁擅自二选一 |

判断原则: 改动是否落在某个**已派 subtask 的验收边界**内? 在 → 属当前任务; 跨出或新增 deliverable → 新任务。

### 属当前任务: 文档先于通知 (按序, 禁颠倒)

```
① 先改真值文档  ── prd.md / design.md / implement.md 受影响条款 (标锚点, 记 rewrite 点)
        ↓        (PRD 是 agent 复读的真值; 文档没改就通知 = agent 拿到口头指令与文档冲突)
② 再通知执行者  ── SendMessage(目标 agent/member, "PRD §<锚点> 已更新: <修正要点>, 就地纠偏")
        ↓
③ 执行者复读 PRD 锚点 → 调整当前执行, 不等跑完返工
```

⛔ 禁 main 自己直接改源码绕过在跑 agent (产生两份分叉改动); ⛔ 禁跳过①直接 SendMessage 口头指令 (文档与执行脱节)。

### 按执行层的可达性 (能否中途 SendMessage)

| 执行层 | 在跑 agent 可达? | 修正手法 |
| --- | --- | --- |
| **agent-team 成员** | ✅ 可 SendMessage(成员名) | 改文档 → SendMessage 成员 → 成员就地纠偏 |
| **background sub-agent** | ✅ 可 SendMessage(agent id/name) | 同上; 用启动时的 agent 标识寻址 |
| **前台 sub-agent (阻塞等待)** | ⚠️ 返回前不可达 | 等本次返回 → 用修正后的 PRD 重派 / 在 check 阶段纠正 |
| **workflow agent** | ❌ 不可中途注入 (见本文 workflow 模式) | 停掉相关 agent (`/workflows` 选中按 `x`) → 按新 PRD 重跑该阶段 |
| **inline 单交付 (main 自己在 worktree 改)** | — (无 running agent) | main 改 PRD → 自己就地调整执行, 无需 SendMessage |

### 兜底

| 触发 | 一线修复 | 仍失败兜底 |
| --- | --- | --- |
| 目标 agent 已完成 / 已退出 | 不能 SendMessage → 在其产出上按新 PRD 做 check 阶段修正 | 修正量大 → 用更新后的 subtask 文件重派一个修正 agent |
| workflow 模式无法中途干预 | 停掉相关 stage agent, 按新 PRD 重跑该 stage | 影响面跨多 stage → 停整条 workflow, 重 plan 后重启 |
| 改了文档但忘了通知 → agent 按旧 PRD 跑完 | check 阶段对照新 PRD 抓偏差并修 | 偏差过大 → 该 subtask 作废重派 |

## 异步并行调度 (提效)

subtask 派发**尽可能并行**, 提升整体效率:
- 无依赖的 subtask → 一次性同时派发 (同一消息多个 Agent 调用), 不串行干等
- 有依赖的 subtask → 按调度图顺序, 上游 done 才派下游
- 资源冲突的 subtask (改同文件/共享配置) → 必须串行 (见 `shared-resources.md`)
- 并行执行者各自 worktree (sub-agent isolation / agent-team 成员路径), 互不干扰
- coordinator (main) 单线程协调: 不自己并跑多 subtask, 但派出去的 agent 并行推进; 收每个 agent 返回立即回传用户进度
- 🔴 **回传 ≠ 问序**: 进度回传是"已做完 X, 正在派 Y"的单向通知, **禁变成"X 做完了, 下一个做哪个?"的提问**。下一个由 DAG 决定 (scheduling.md §4), 自动派; 顺序缺失 → 退回 planning 补, 不在 exec 回传里问用户。
