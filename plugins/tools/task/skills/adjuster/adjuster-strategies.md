# Adjuster 失败升级策略指南

## 弹性模式最佳实践

### 基于 Circuit Breaker 模式

**渐进式升级（Progressive Escalation）**：
- 不是第一次失败就放弃，而是逐步升级策略
- Level 1: Retry（快速重试）
- Level 2: Debug（深度诊断）
- Level 3: Replan（重新规划）
- Level 4: Ask User（请求指导）

**停滞检测（Stall Detection）**：
- 识别无进展的重复失败模式
- 防止无限重试循环
- 及时切换到更高级别策略

**智能恢复（Intelligent Recovery）**：
- 根据错误类型选择最合适的恢复策略
- 临时网络错误 → Retry
- 配置错误 → Debug
- 需求变更 → Replan
- 不确定情况 → Ask User

## 失败升级策略表

| 级别 | 策略 | 适用场景 | 停滞阈值 | 预期效果 |
|------|------|---------|---------|---------|
| **Level 1** | **Retry** | 临时性错误、偶发性故障 | 连续 3 次相同错误 | 快速恢复，无需人工介入 |
| **Level 2** | **Debug** | 持续性错误、配置问题 | 连续 2 次 Debug 无效 | 收集详细信息，定位根本原因 |
| **Level 3** | **Replan** | 需求变更、架构调整 | 连续 2 次 Replan 无效 | 重新设计，调整执行路径 |
| **Level 4** | **Ask User** | 所有自动策略失败 | - | 人工介入，明确方向 |

## 四级升级策略详解

### Level 1: Retry（调整后重试）

**触发条件**：
- 首次失败
- 临时性错误（网络超时、依赖暂时不可用）
- 环境错误（文件未找到、权限问题）

**执行操作**：
- 调整任务参数（扩大超时时间、修正文件路径）
- 修复环境问题（创建缺失目录、调整权限）
- 使用指数退避策略（delay = base_delay * 2^n）
- 保持原计划不变

**输出示例**：
```json
{
  "status": "retry",
  "reason": "临时性网络错误",
  "adjustments": {
    "timeout": "扩大超时时间从 30s 到 60s",
    "retry_delay": "3 秒后重试（指数退避）"
  }
}
```

### Level 2: Debug（深度诊断）

**触发条件**：
- Retry 3 次失败后
- 检测到停滞（相同错误重复）
- 配置问题、依赖缺失

**执行操作**：
- 收集详细错误日志和堆栈跟踪
- 检查依赖版本和配置文件
- 分析环境变量和系统状态
- 生成诊断报告

**输出示例**：
```json
{
  "status": "debug",
  "reason": "连续 3 次 Retry 失败，触发深度诊断",
  "diagnostics": {
    "error_log": "/tmp/error.log",
    "dependencies": "缺少 numpy==1.21.0",
    "config_issues": ["DATABASE_URL 未设置"]
  }
}
```

### Level 3: Replan（重新规划）

**触发条件**：
- Debug 2 次失败后
- 需求变更或理解偏差
- 架构不匹配

**执行操作**：
- 调用 planner 重新设计任务
- 调整任务分解和依赖关系
- 重新分配 agent/skills
- 保留已完成的工作

**输出示例**：
```json
{
  "status": "replan",
  "reason": "Debug 2 次失败，需要重新规划",
  "replan_scope": {
    "affected_tasks": ["T2", "T3"],
    "keep_completed": ["T1"],
    "new_approach": "改用异步方式实现"
  }
}
```

### Level 4: Ask User（请求用户指导）

**触发条件**：
- Replan 2 次失败后
- 所有自动策略失败
- 不确定如何处理的情况

**执行操作**：
- 总结失败历史和已尝试策略
- 生成结构化问题
- 使用 `SendMessage` 向用户请求指导
- 等待用户响应

**输出示例**：
```json
{
  "status": "ask_user",
  "reason": "所有自动策略失败，需要用户指导",
  "question": {
    "summary": "任务 T2 连续失败 8 次",
    "tried_strategies": ["Retry×3", "Debug×2", "Replan×2"],
    "ask": "是否需要：1) 调整技术栈？2) 跳过该任务？3) 其他方案？"
  }
}
```

## 停滞检测

### 停滞模式识别

**相同错误重复**：
```python
# 检测是否是相同的错误重复
if len(failure_history) >= 3:
    recent_errors = [f["error"] for f in failure_history[-3:]]
    if len(set(recent_errors)) == 1:
        stalled = True  # 相同错误重复 3 次
```

**策略无效循环**：
```python
# 检测同一策略是否重复无效
same_strategy_count = sum(1 for f in failure_history if f["strategy"] == current_strategy)
if same_strategy_count >= 2:
    escalate_to_next_level = True
```

### Circuit Breaker 状态机

```
Closed (正常) -[失败]-> Open (熔断)
    ↑                        ↓
    └─── Half-Open (尝试) ←──┘
```

**状态转换规则**：
- **Closed → Open**：连续 N 次失败
- **Open → Half-Open**：等待冷却时间后尝试
- **Half-Open → Closed**：尝试成功
- **Half-Open → Open**：尝试失败

## 指数退避可视化

```
Retry 次数  →  延迟时间
    0              1s
    1              2s (1 * 2^1)
    2              4s (1 * 2^2)
    3              8s (1 * 2^3)
    4             16s (1 * 2^4)
    5             32s (1 * 2^5)
```

最大延迟上限：60 秒（防止无限等待）

## 执行检查清单

### 失败信息收集检查
- [ ] 获取失败任务列表
- [ ] 构建失败历史（包含所有失败记录）
- [ ] 记录失败时间、错误类型、尝试策略

### 失败原因分析检查
- [ ] 错误分类（环境/依赖/逻辑/网络）
- [ ] 根本原因识别
- [ ] 是否是重复失败

### 停滞检测检查
- [ ] 检查相同错误重复模式
- [ ] 检查策略无效循环
- [ ] 计算停滞次数

### 升级策略检查
- [ ] 根据失败历史选择正确策略
- [ ] 遵循渐进式升级路径
- [ ] 避免跳级（除非紧急情况）

### 报告生成检查
- [ ] 包含失败原因
- [ ] 包含调整措施
- [ ] 包含下一步操作
- [ ] 报告简洁（≤200字）
