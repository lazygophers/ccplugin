---
agent: task:verifier
description: 结果验证规范 - 检查任务验收标准、验证完成情况、判断终止条件的执行规范
model: sonnet
context: fork
user-invocable: true
---

# Skills(task:verifier) - 结果验证规范

## 适用场景

- Loop 命令步骤 4：结果验证
- 需要检查任务验收标准是否通过
- 需要验证任务完成情况
- 需要判断是否终止 loop

## 执行流程

### 1. 调用 verifier skill

```
verification_result = Skill(task:verifier, "执行 loop 步骤 4 的结果验证工作：验证所有任务验收标准")
```

### 2. 处理验证结果

- 检查 `verification_result.status`
- `passed` → Loop 完成，跳到"全部迭代完成"
- `suggestions` → `AskUserQuestion` 询问用户
- `failed` → 步骤 5（失败调整）

### 3. 输出验收报告

```
print(f"[MindFlow·{$ARGUMENTS}·步骤4·{verification_result.status}]")
print(verification_result.report)
```

## 输出格式

verifier agent 返回格式：

### 通过（所有验收标准满足）

```json
{
	"status": "passed",
	"report": "所有任务已完成：T1（用户模型）✓、T2（API接口）✓、T3（测试）✓。测试覆盖率 92%，所有 CI 检查通过。"
}
```

### 通过但有建议

```json
{
	"status": "suggestions",
	"report": "任务已完成，但有优化建议：代码复杂度略高，建议后续重构。",
	"suggestions": [
		"建议1：重构用户模型验证逻辑",
		"建议2：添加更多边界测试"
	]
}
```

### 失败（验收标准未满足）

```json
{
	"status": "failed",
	"report": "验收失败：T3 测试未通过（2/10 失败），测试覆盖率仅 75%（要求≥90%）。",
	"failures": [
		{
			"task": "T3",
			"reason": "测试用例 test_login_timeout 失败"
		},
		{
			"task": "T3",
			"reason": "测试覆盖率不足"
		}
	]
}
```

## 终止条件

verifier agent 根据验证结果决定 loop 的终止行为：

| 验证结果 | 终止行为 |
|---------|---------|
| `passed` | Loop 正常退出，进入"全部迭代完成" |
| `suggestions` | `AskUserQuestion` 询问用户是否继续优化 |
| `failed` | 进入步骤 5（失败调整），继续 loop |

## 核心原则

- **全面验证**：检查所有任务，不要遗漏
- **量化标准**：验收标准必须可量化
- **回归检查**：验证不影响已有功能
- **精炼报告**：验收报告简短精炼（≤100字）

## 注意事项

- 使用 Skill(task:verifier) 调用 verifier agent
- 确保返回格式为有效的 JSON
- 记录具体的失败原因
- 提供可操作的建议
