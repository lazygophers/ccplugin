# Loop 监控和可观测性

## 任务状态

`pending` → `ready` → `in_progress` → `completed`/`failed`

## 状态前缀格式

```
[MindFlow·${任务内容}·${当前步骤}/${迭代轮数}·${状态}]
```

## 任务进度表

```
T1: 实现 JWT 工具 ········ ✅ 已完成
T2: 认证中间件 ·········· 🔄 进行中
T3: 编写测试 ············ ⏸️ 等待(T2)
完成：1/3  进行中：1/3  等待中：1/3
```

## 监控指标(KPI)

| 类别 | 指标 |
|------|------|
| 效率 | 平均任务完成时间、并行度利用率 |
| 质量 | 测试覆盖率、验收通过率 |
| 可靠性 | 失败率、停滞率、补偿率 |
| 体验 | 迭代完成时间、用户干预次数 |

## 系统级监控

迭代次数(iteration/total) | 停滞检测(stalled_count/error_signature) | 用户指导(guidance_count) | 整体进度(completed/total)

## 迭代熔断器（Circuit Breaker）

**目标**：防止多轮迭代无限循环，基于迭代次数触发熔断。

### 预警级别

| 级别 | 条件 | 动作 |
|------|------|------|
| 告警（Warning） | iteration >= 4 | 输出 `[MindFlow·${task_id}·预算] 已迭代 {N} 次，建议精简后续操作` |
| 强制确认（Confirm） | iteration >= 5 | AskUserQuestion 询问用户是否继续（"已迭代5次，是否继续？"） |
| 熔断（Circuit Break） | iteration > max_iterations | 强制进入 Cleanup，跳过未完成任务，输出部分结果 |

### 熔断配置

```
circuit_breaker:
  max_iterations: 5          # 单次 loop 最大迭代轮次（用户确认可延长）
  max_tasks_per_iteration: 10 # 单次迭代最大任务数
  reflection_max_rounds: 1    # Reflection 自检最多 1 轮（防止循环）
```

### 集成方式

- 每次 `iteration += 1` 时检查是否触发预警/熔断
- 熔断时保存当前进度到检查点，支持下次恢复
- 用户确认继续后，max_iterations 临时 +2

## 可观测性集成

集成 `task:observability` 技能提供成本/效率/质量/稳定性指标：
- 初始化：`MetricsCollector()` + 预算上限配置
- 迭代监控：`record_iteration_start/end` + `record_task_start/end`
- 预算预警：使用>80%时告警
- 最终报告：`generate_cost_report()` 含总成本/耗时/缓存节省/优化建议

详细文档：[observability/SKILL.md](../observability/SKILL.md)

## 日志

级别：DEBUG/INFO/WARNING/ERROR/CRITICAL

结构化格式：`{timestamp, level, event, ...context}`

关键事件：任务生命周期(创建/开始/完成/失败/重试) | 状态转换(阶段切换/状态变更/决策点) | 错误异常(发生/捕获/补偿)

## 可观测性最佳实践

- **可追踪**：关联ID(迭代→任务)、调用链跟踪
- **可调试**：记录输入参数/中间状态/错误详情、支持重放
- **可理解**：语义化命名、一致性、文档化决策

## Agent 通信规则

**核心规则**：Agent不得直接与用户交互（禁止AskUserQuestion/直接输出）。正确路径：Agent→SendMessage(@main)→MindFlow→AskUserQuestion(user)

**消息类型**：question(需用户确认) | response(传递回答) | report(进度/结果) | alert(异常) | request(请求操作)。消息必含：type/agent/content。

**协作模式**：顺序(Planner→Executor→Verifier→Adjuster/Finalizer) | 并行(最多2个无依赖) | 反馈循环(Executor→Verifier→Adjuster→Executor)

**安全**：来源验证(只允许合法Agent) | 格式验证(必含type/agent/content) | 循环检测(重复>50%中断)
