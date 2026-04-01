# Adjuster 失败升级策略

## 渐进式升级（Circuit Breaker模式）

| 级别 | 策略 | 触发条件 | 操作 | 下一步 |
|------|------|---------|------|--------|
| 1 | Retry | 首次失败/临时错误 | 调整参数+指数退避(delay=base×2^n, max 60s) | Execution |
| 1.5 | Self-Healing | 匹配17类可预测错误 | 自动修复(详见self-healing.md) | Execution |
| 2 | Debug | Retry×3失败/Self-Heal×2失败 | 收集日志+检查依赖配置+诊断报告 | Execution |
| 2.5 | Micro-Replan | Debug×3无效 | 仅重规划失败任务+直接依赖，保留成功任务 | Planning |
| 3 | Full Replan | Micro-Replan失败/需求变更 | 调用planner重新设计+保留已完成工作 | Planning |
| 4 | Ask User | Replan×2失败/振荡(A→B→A→B)/总失败≥15 | 总结失败历史+结构化提问 | 用户决定 |

## 停滞检测

- **相同错误重复**：最近3次failure_history错误相同 → stalled=true
- **策略无效循环**：同一策略使用≥2次 → 升级到下一级
- **振荡检测**：A→B→A→B模式 → 直接升级到Ask User
- **紧急逃逸**：总失败≥15 → 直接升级到Ask User

## Circuit Breaker 状态

Closed(正常) →[N次失败]→ Open(熔断) →[冷却]→ Half-Open(尝试) →[成功]→ Closed / →[失败]→ Open

## 输出格式

每级策略返回JSON：status(retry/healed/debug/micro_replan/replan/ask_user) + reason + 级别特定详情(adjustments/healing_details/diagnostics/replan_scope/question)
