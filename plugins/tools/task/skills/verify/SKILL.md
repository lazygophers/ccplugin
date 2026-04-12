---
description: 结果校验，验证执行结果是否符合预期
memory: project
color: cyan
model: haiku
permissionMode: plan
background: false
context: fork
agent: task:verify
---

# Verify Skill

## 执行流程

> 对照验收标准逐一检查，验收失败返回 False 由 adjust 处理后续迭代
> **所有验证必须基于实际执行证据，不接受假设或主观判断**

```python
# 读取验收标准和执行结果
align_file = f".lazygophers/tasks/{task_id}/align.json"
align = read_json(align_file)
criteria = align["acceptance_criteria"]

# 读取执行结果
task_file = f".lazygophers/tasks/{task_id}/task.json"
exec_result = read_json(task_file)

all_passed = True
failed_criteria = []

# 阶段1：功能验收
functional_criteria = [c for c in criteria if c.get("verifiable", True)]
for item in functional_criteria:
	check_result = verify_functional_item(item, exec_result)
	if not check_result["passed"]:
		all_passed = False
		failed_criteria.append({
			"name": item.get("name"),
			"description": item.get("description"),
			"category": "功能",
			"reason": check_result["reason"],
			"evidence": check_result.get("evidence", "")
		})

# 阶段2：质量标准
quality_check = verify_quality_standards(exec_result)
if not quality_check["passed"]:
	all_passed = False
	for failure in quality_check["failures"]:
		failed_criteria.append({
			"category": "质量",
			"reason": failure["reason"],
			"evidence": failure.get("evidence", "")
		})

# 阶段3：边界条件
boundary_check = verify_boundary_conditions(criteria, exec_result)
if not boundary_check["passed"]:
	all_passed = False
	for failure in boundary_check["failures"]:
		failed_criteria.append({
			"category": "边界",
			"reason": failure["reason"],
			"evidence": failure.get("evidence", "")
		})

# 输出格式：所有输出必须包含前缀 [flow·{task_id}·{state}]
if all_passed:
	quality_score = calculate_quality_score(exec_result, criteria)
	print(f"[flow·{task_id}·verify] 验收通过，质量分：{quality_score}")
	return {
		"status": True,
		"quality_score": quality_score
	}
else:
	print(f"[flow·{task_id}·verify] 验收失败，{len(failed_criteria)} 个标准未通过")
	return {
		"status": False,
		"failed_criteria": failed_criteria,
		"summary": format_failure_summary(failed_criteria)
	}
```

## 验证方法

### verify_functional_item
```python
def verify_functional_item(item, exec_result):
	"""验证单个功能点是否符合标准"""
	# 基于实际执行证据验证
	# 返回 {"passed": bool, "reason": str, "evidence": str}
	pass
```

### verify_quality_standards
```python
def verify_quality_standards(exec_result):
	"""验证代码质量标准"""
	# 检查：
	# - 代码风格一致性
	# - 错误处理完整性
	# - 测试覆盖率（如有）
	# 返回 {"passed": bool, "failures": [...]}
	pass
```

### verify_boundary_conditions
```python
def verify_boundary_conditions(criteria, exec_result):
	"""验证边界条件和约束"""
	# 检查：
	# - 性能要求
	# - 资源使用
	# - 兼容性要求
	# 返回 {"passed": bool, "failures": [...]}
	pass
```

## 检查清单

### 验收检查
- [ ] 功能验收已对照
- [ ] 质量标准已检查
- [ ] 边界条件已验证

### 证据要求
- [ ] 每个验收点都有实际证据
- [ ] 失败原因具体可操作
- [ ] 质量分数基于客观指标

### 输出
- [ ] status: True (验收通过) / False (验收失败)
- [ ] quality_score: 0-100 (仅通过时)
- [ ] failed_criteria: [...] (仅失败时)

## 输出格式

所有输出必须包含前缀：`[flow·{task_id}·{state}]`

- task_id：当前任务ID
- state：当前状态（verify）

## 与 adjust 的协作

验收失败时返回 `status: False`，flow 会自动调用 adjust agent，由 adjust 分析失败原因并决定后续策略：
- 上下文缺失 → 返回 explore
- 需求偏差 → 返回 align
- 重新计划 → 返回 plan
- 进一步迭代优化 → 优化后重新执行
