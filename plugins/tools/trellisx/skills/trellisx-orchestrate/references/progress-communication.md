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

## 禁止

- **批量执行后才汇总进度** — 用户失去中途干预机会
- **coordinator 派 subtask 后转去做其他事** — 失去调度视角
- **teammate 完成不发 SendMessage 直接退出** — leader 不知任务结束
- **摘要写 "完成" / "OK" / "没问题"** — 必须含产出路径
- **失败时只回 "失败" 不说原因** — 必须含错误信息或文件:行
- **延迟通讯 "等全部跑完再回报"** — 必须每个 subtask 完成立即回

## 异步并行调度 (提效)

subtask 派发**尽可能并行**, 提升整体效率:
- 无依赖的 subtask → 一次性同时派发 (同一消息多个 Agent 调用), 不串行干等
- 有依赖的 subtask → 按调度图顺序, 上游 done 才派下游
- 资源冲突的 subtask (改同文件/共享配置) → 必须串行 (见 `shared-resources.md`)
- 并行执行者各自 worktree (sub-agent isolation / agent-team 成员路径), 互不干扰
- coordinator (main) 单线程协调: 不自己并跑多 subtask, 但派出去的 agent 并行推进; 收每个 agent 返回立即回传用户进度
