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
