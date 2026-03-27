# Loop 通信和协作规范

## Agent通信规则

**核心规则**：Agent不得直接与用户交互（禁止AskUserQuestion/直接输出/绕过Team Leader）。

**正确路径**：Agent→SendMessage(@main)→MindFlow→AskUserQuestion(user)→response→SendMessage(Agent)

## 消息类型

| 类型 | 用途 | 关键字段 |
|------|------|---------|
| question | Agent需用户确认/决策 | content/options[]/context |
| response | Team Leader传递用户回答 | content/original_context |
| report | Agent报告进度/结果 | data(task_id/status/duration) |
| alert | Agent检测到异常 | severity(warning/error)/data |
| request | Agent请求执行操作 | action/data |

消息必含：type/agent/content。

## 协作模式

- **顺序**：Planner→Executor→Verifier→[Pass/Fail]→Adjuster/Finalizer
- **并行**：最多2个Agent同时执行无依赖任务
- **反馈循环**：Executor→Verifier→[Failed]→Adjuster→Executor

## 最佳实践

- **消息设计**：明确type、充足上下文、可追踪ID
- **超时**：短任务30s/中等2min/长任务5min，超时发alert
- **错误传播**：结构化错误(code/message/details/logs)→Team Leader决策
- **状态同步**：Agent定期发status_update
- **优先级**：low/medium/high/critical，按优先级处理
- **重试**：指数退避(max 3次，初始1s，×2)
- **批处理**：多条相关消息批量发送(batch_id追踪)

## 安全

- **来源验证**：只允许合法Agent(planner/execute/verifier/adjuster/finalizer)
- **格式验证**：必含type/agent/content
- **循环检测**：跟踪最近10条消息，重复>50%则中断
- **敏感加密**：含密钥/凭证时加密传输
- **访问控制**：权限矩阵限制Agent间通信路径
- **审计日志**：记录timestamp/direction/agent/type/content_hash
