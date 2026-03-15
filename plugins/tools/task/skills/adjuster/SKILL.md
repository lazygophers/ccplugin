---
agent: task:adjuster
description: 失败调整规范 - 分析失败原因、检测停滞、应用升级策略的执行规范
model: sonnet
context: fork
user-invocable: false
---

# Skills(task:adjuster) - 失败调整规范

## 适用场景

- Loop 命令步骤 5：失败调整
- 需要分析失败原因
- 需要检测停滞（相同错误重复）
- 需要应用失败升级策略

## 执行流程

### 1. 调用 adjuster skill

```
adjustment_result = Skill(task:adjuster, "执行 loop 步骤 5 的失败调整工作：分析失败并决定下一步策略")
```

### 2. 处理调整结果

根据 `adjustment_result.strategy` 执行对应操作：
- `retry` → 回到步骤 1
- `debug` → 调用 debug agent 后回到步骤 1
- `replan` → 回到步骤 1 重新规划
- `ask_user` → `AskUserQuestion` 请求用户指导后回到步骤 1

### 3. 输出调整报告

```
print(f"[MindFlow·{$ARGUMENTS}·步骤5·{adjustment_result.strategy}]")
print(adjustment_result.report)
```

## 输出格式

adjuster agent 返回格式：

### 调整后重试（第 1 次失败）

```json
{
	"strategy": "retry",
	"report": "T3 测试失败：断言错误。修复方案：调整断言条件，重新运行测试。",
	"adjustments": [
		{
			"task": "T3",
			"action": "修复测试断言",
			"details": "将 assertEqual(x, 0) 改为 assertEqual(x, 1)"
		}
	]
}
```

### 调试诊断（第 2 次失败）

```json
{
	"strategy": "debug",
	"report": "T3 测试再次失败，需要诊断。将调用 debug agent 深入分析。",
	"adjustments": [
		{
			"task": "T3",
			"action": "调用调试 agent",
			"details": "使用 debug agent 分析测试失败原因"
		}
	]
}
```

### 重新规划（第 3 次失败）

```json
{
	"strategy": "replan",
	"report": "T3 连续 3 次失败，需要重新规划。建议拆分任务或调整技术方案。",
	"adjustments": [
		{
			"task": "T3",
			"action": "重新规划",
			"details": "将 T3 拆分为两个子任务：T3a（基础功能）和 T3b（边界测试）"
		}
	]
}
```

### 请求用户指导（停滞 3 次）

```json
{
	"strategy": "ask_user",
	"report": "检测到停滞：T3 测试失败已重复 3 次。需要用户指导。",
	"stalled_info": {
		"error": "AssertionError: Expected 0 but got 1",
		"occurrences": 3,
		"tasks": ["T3"]
	},
	"question": "T3 测试连续失败，是否需要调整验收标准或修改实现方案？"
}
```

## 失败升级策略

| 失败次数 | 策略 | 说明 |
|---------|------|------|
| 第 1 次 | `retry` | 调整后重试 |
| 第 2 次 | `debug` | 调用 debug agent 诊断 |
| 第 3 次 | `replan` | 重新规划任务 |
| 停滞 3 次 | `ask_user` | 请求用户指导 |

## 核心原则

- **错误分类**：编译/测试/依赖/其他
- **停滞检测**：识别相同错误重复
- **渐进升级**：从简单重试到重新规划
- **精炼报告**：调整报告简短精炼（≤100字）

## 注意事项

- 使用 Skill(task:adjuster) 调用 adjuster agent
- 确保返回格式为有效的 JSON
- 正确识别失败类型
- 检测停滞模式
- 提供可操作的调整建议