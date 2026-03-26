---
name: hooks
description: Task插件Hook系统 - 8个生命周期钩子，用于事件驱动的自动化和指标收集
---

# Hooks - 生命周期钩子系统

<overview>

Task插件提供8个生命周期hooks，支持事件驱动的自动化、指标收集和自定义扩展。

**可用Hooks**：
- TaskStart - 任务启动
- IterationStart - 迭代开始
- IterationEnd - 迭代结束
- TaskComplete - 任务完成
- TaskFailed - 任务失败
- CheckpointSave - 检查点保存
- SessionEnd - 会话结束

**用途**：
- 指标收集（自动化）
- 日志记录（调试）
- 通知发送（Slack、Email）
- 自定义集成（CI/CD）

</overview>

## 可用Hooks

### TaskStart

**触发时机**：Loop初始化完成，进入计划设计前

**环境变量**：
- `TASK_ID` - 任务ID
- `SESSION_ID` - 会话ID
- `USER_TASK` - 用户任务描述

**用途**：
- 初始化跟踪
- 发送任务启动通知
- 设置环境变量

**示例**：
```javascript
// task-start.js
const taskId = process.env.TASK_ID;
console.log(`任务启动: ${taskId}`);
// 发送Slack通知
// sendSlackNotification(`任务 ${taskId} 启动`);
```

---

### IterationStart

**触发时机**：每次迭代开始（计划设计阶段）

**环境变量**：
- `TASK_ID` - 任务ID
- `SESSION_ID` - 会话ID
- `ITERATION` - 当前迭代次数
- `PHASE` - 当前阶段（planning/execution/etc.）

**用途**：
- 迭代计数
- 阶段追踪
- 性能基准（开始时间戳）

---

### IterationEnd

**触发时机**：验证完成后，进入调整/完成前

**环境变量**：
- `TASK_ID` - 任务ID
- `SESSION_ID` - 会话ID
- `ITERATION` - 迭代次数
- `PHASE` - 阶段
- `STATUS` - 状态（passed/failed/suggestions）

**用途**：
- 收集指标（Token消耗、耗时）
- 保存检查点
- 生成中间报告

**示例**：
```javascript
// iteration-end.js
const metrics = {
  task_id: process.env.TASK_ID,
  iteration: process.env.ITERATION,
  status: process.env.STATUS,
  timestamp: new Date().toISOString()
};
// 保存到metrics.jsonl
fs.appendFileSync('metrics.jsonl', JSON.stringify(metrics) + '\n');
```

---

### TaskComplete

**触发时机**：Finalizer运行前（任务成功完成）

**环境变量**：
- `TASK_ID` - 任务ID
- `SESSION_ID` - 会话ID
- `TOTAL_ITERATIONS` - 总迭代次数
- `SUCCESS` - 是否成功（true/false）

**用途**：
- 模式提取（调用pattern-extraction）
- 归档记忆
- 清理资源
- 发送完成通知

**注意**：此hook为**同步执行**（async: false），确保完成逻辑在清理前执行

---

### TaskFailed

**触发时机**：任务最终失败（无法恢复）

**环境变量**：
- `TASK_ID` - 任务ID
- `SESSION_ID` - 会话ID
- `ITERATION` - 失败时的迭代次数
- `ERROR_MESSAGE` - 错误消息

**用途**：
- 失败记录
- 报警通知
- 生成失败报告

---

### CheckpointSave

**触发时机**：保存检查点时

**环境变量**：
- `TASK_ID` - 任务ID
- `SESSION_ID` - 会话ID
- `CHECKPOINT_PATH` - 检查点文件路径

**用途**：
- 备份检查点到远程存储
- 记录保存事件
- 压缩历史检查点

---

### SessionEnd

**触发时机**：会话结束

**环境变量**：
- `SESSION_ID` - 会话ID

**用途**：
- 清理临时文件
- 归档日志
- 生成会话报告

---

## Hook配置

### 自定义Hook

在 `.claude/task.local.md` 中自定义hooks：

```yaml
---
custom_hooks:
  TaskComplete:
    - command: "python my-notification.py"
      async: true
      timeout: 10
  IterationEnd:
    - command: "bash collect-metrics.sh"
      async: true
      timeout: 5
---

# Custom Hooks 配置

## TaskComplete Hook

任务完成时发送Slack通知：

\`\`\`python
# my-notification.py
import os
import requests

task_id = os.getenv('TASK_ID')
success = os.getenv('SUCCESS') == 'true'

webhook_url = os.getenv('SLACK_WEBHOOK_URL')
requests.post(webhook_url, json={
    'text': f'任务 {task_id} {"成功" if success else "失败"}'
})
\`\`\`
```

### 禁用Hook

禁用特定hook：

```yaml
---
hooks_config:
  enabled_hooks:
    - TaskStart
    - TaskComplete
  disabled_hooks:
    - IterationStart
    - IterationEnd
---
```

## Hook开发指南

### 输入

**环境变量**：`TASK_*`, `SESSION_*`, `ITERATION`, etc.

**标准输入**：JSON格式的上下文数据（可选）

### 输出

**标准输出**：日志消息（显示给用户）

**标准错误**：错误消息（调试用）

**Exit code**：
- `0` = 成功
- 非`0` = 失败（不阻塞主流程，仅记录）

### 最佳实践

1. **保持轻量**：执行时间<1秒，避免阻塞
2. **使用async**：默认async: true，避免阻塞主流程
3. **错误处理**：健壮的错误处理，不依赖外部服务
4. **日志清晰**：输出清晰的日志，便于调试
5. **幂等性**：Hook可能重复触发，确保幂等

### 超时保护

每个hook都有超时设置：

- `TaskStart`: 5秒
- `IterationStart`: 3秒
- `IterationEnd`: 5秒
- `TaskComplete`: 10秒（同步，允许更长）
- `TaskFailed`: 5秒
- `CheckpointSave`: 5秒
- `SessionEnd`: 5秒

超时后hook会被终止，不影响主流程。

## 指标收集

### 自动指标

IterationEnd hook自动收集以下指标：

- 任务ID
- 迭代次数
- 阶段
- 状态
- 时间戳

保存到：`.claude/metrics/task-metrics.jsonl`

### 查看指标

```bash
# 查看所有指标
cat ~/.claude/metrics/task-metrics.jsonl | jq '.'

# 查看特定任务
cat ~/.claude/metrics/task-metrics.jsonl | jq 'select(.task_id == "t_abc123")'

# 统计迭代次数
cat ~/.claude/metrics/task-metrics.jsonl | jq -s 'group_by(.task_id) | map({task: .[0].task_id, iterations: length})'
```

## Hook日志

所有hook执行记录保存到：

`.claude/logs/task-hooks-{session_id}.jsonl`

**格式**：每行一个JSON对象

```json
{"hook": "TaskStart", "task_id": "t_abc123", "timestamp": "2026-03-25T10:00:00Z"}
{"hook": "IterationEnd", "iteration": 1, "status": "passed", "timestamp": "2026-03-25T10:05:00Z"}
{"hook": "TaskComplete", "total_iterations": 3, "success": true, "timestamp": "2026-03-25T10:15:00Z"}
```

## 故障排查

### Hook未触发

1. 检查plugin.json配置是否正确
2. 检查脚本是否可执行（`chmod +x`）
3. 检查脚本路径是否正确
4. 查看hook日志：`.claude/logs/task-hooks-*.jsonl`

### Hook执行失败

1. 检查脚本语法错误
2. 检查环境变量是否正确传递
3. 查看stderr输出
4. 检查超时设置是否合理

### Hook性能问题

1. 检查执行时间（使用`time`命令）
2. 优化脚本逻辑
3. 考虑使用async: true
4. 减少外部依赖

## 示例：集成Observability

使用IterationEnd hook自动生成成本报告：

```javascript
// iteration-end-observability.js
const fs = require('fs');
const path = require('path');

const taskId = process.env.TASK_ID;
const iteration = process.env.ITERATION;

// 读取token使用情况（假设从某处获取）
const tokenUsage = getTokenUsage(taskId, iteration);

// 生成成本报告
const report = {
  task_id: taskId,
  iteration: iteration,
  tokens: tokenUsage,
  cost: calculateCost(tokenUsage),
  timestamp: new Date().toISOString()
};

// 保存报告
const reportPath = path.join(process.env.HOME, `.claude/reports/cost-${taskId}.json`);
fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));

console.log(`成本报告已生成: ${reportPath}`);
```

配置：
```yaml
---
custom_hooks:
  IterationEnd:
    - command: "node iteration-end-observability.js"
      async: true
      timeout: 5
---
```
