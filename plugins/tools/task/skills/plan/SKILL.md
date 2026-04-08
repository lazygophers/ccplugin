---
description: 任务规划，分解任务并制定执行方案
memory: project
color: purple
model: opus
permissionMode: plan
background: false
disable-model-invocation: true
user-invocable: false
context: fork
agent: task:plan
---

# Plan Skill

## 执行流程

> 基于对齐结果，将任务分解为可执行的子任务
> **自我验证、自动修复、迭代优化，直到符合规范**

```python
# 读取对齐结果和上下文
align_file = f".lazygophers/tasks/{task_id}/align.json"
context_file = f".lazygophers/tasks/{task_id}/context.json"
align = read_json(align_file)
context = read_json(context_file)

# 检查上下文完整性
required_context = ["scope", "acceptance_criteria", "code_style_follow"]
if any(key not in align for key in required_context):
    return {"status": "上下文缺失"}

# 自我迭代循环：生成 → 验证 → 修复 → 重验
for iteration in range(10):  # 最多10次迭代
    # === 迭代开始 ===
    
    # 阶段1：任务分解
    if iteration == 0:
        subtasks = decompose_task({
            "user_prompt": user_prompt,
            "scope": align["scope"],
            "acceptance": align["acceptance_criteria"]
        })
    else:
        # 根据上一次验证结果修复
        subtasks = fix_and_re decompose(subtasks, validation_errors)
    
    # 阶段2：验证任务拆分规范
    validation = validate_task_structure(subtasks)
    
    if validation["passed"]:
        # 验证通过，退出迭代
        break
    else:
        # 验证失败，记录错误，继续下一轮迭代
        validation_errors = validation["errors"]
        continue  # ← 下一轮迭代

# 如果10次迭代后仍不通过，返回失败
if not validation["passed"]:
    return {
        "status": "上下文缺失",
        "reason": "任务拆分无法满足规范要求"
    }

# 阶段3：确定执行顺序
ordered = sequence_tasks({
    "subtasks": subtasks,
    "dependencies": find_dependencies(subtasks),
    "parallel": identify_parallel(subtasks, max=2)
})

# 阶段4：风险识别
risks = analyze_risks({
    "tasks": ordered,
    "context": context
})

# 阶段5：资源估算
resources = estimate_resources({
    "tasks": ordered,
    "complexity": calculate_complexity(ordered)
})

# 构建执行计划
plan = {
    "subtasks": ordered,
    "execution_order": build_dag(ordered),
    "risks": risks,
    "resources": resources,
    "code_style": align["code_style_follow"],
    "status": "confirmed",
    "iterations": iteration + 1  # 记录迭代次数
}

# 写入任务文件
task_file = f".lazygophers/tasks/{task_id}/task.json"
write_json(task_file, plan)

return {"status": "confirmed"}
```

## 自我修复逻辑

```python
# 验证失败后自动修复的常见模式

def fix_and_redecompose(subtasks, errors):
    """根据验证错误自动修复任务拆分"""
    
    # 修复1：补充缺失字段
    for error in errors:
        if "缺少字段" in error:
            task = find_task_by_error(subtasks, error)
            if task:
                add_missing_field(task, extract_field_from_error(error))
    
    # 修复2：拆分过大任务
    for error in errors:
        if "描述过长" in error:
            task = find_task_by_error(subtasks, error)
            if task:
                split_large_task(subtasks, task)
    
    # 修复3：补充验收标准
    for error in errors:
        if "验收标准不能为空" in error:
            task = find_task_by_error(subtasks, error)
            if task:
                generate_acceptance_criteria(task, align["acceptance_criteria"])
    
    # 修复4：转换文件路径
    for error in errors:
        if "相对路径" in error:
            task = find_task_by_error(subtasks, error)
            if task:
                convert_to_relative_paths(task, context)
    
    # 修复5：指定默认 agent
    for error in errors:
        if "未指定执行 agent" in error:
            task = find_task_by_error(subtasks, error)
            if task:
                infer_agent_from_context(task, context)
    
    # 修复6：解决循环依赖
    if "循环依赖" in str(errors):
        resolve_circular_dependencies(subtasks)
    
    # 修复7：降低并行度
    if "并行任务数超限" in str(errors):
        reduce_parallelism(subtasks, max=2)
    
    return subtasks
```

## 任务拆分规范

### 子任务结构要求

```json
{
    "id": "T1",
    "description": "简短描述（≤20字）",
    "goal": "明确的目标（可验证）",
    "acceptance_criteria": ["验收点1", "验收点2"],
    "files": ["相对路径/file1.py"],
    "dependencies": ["T0"],
    "agent": "coder",
    "estimated_complexity": "low"
}
```

### 拆分原则

1. **原子性**：每个子任务应该是原子的、不可再分的
   - 一个子任务只做一件事
   - 完成后产生可验证的结果

2. **可验证性**：每个子任务必须有明确的验收标准
   - 验收标准必须是可测试的
   - 验收标准必须是具体的（不模糊）
   - 验收标准必须可量化（有明确指标）

3. **依赖明确**：子任务之间的依赖关系必须清晰
   - 依赖必须形成 DAG（无循环）
   - 并行任务数 ≤ 2
   - 关键路径已识别

4. **文件范围**：每个子任务涉及的文件必须列出
   - 必须使用相对路径
   - 路径必须在 align 界定的范围内

5. **Agent选择**：必须指定执行 agent
   - 项目自定义 agent（`.claude/agents/`）
   - 通用 agent（`coder`, `tester` 等）

6. **复杂度估算**：标注任务复杂度
   - `low`：简单任务（<30分钟）
   - `medium`：中等任务（30-120分钟）
   - `high`：复杂任务（>120分钟）

### 验证规则

```python
def validate_task_structure(subtasks):
    errors = []
    
    for task in subtasks:
        # 必需字段
        required_fields = ["id", "description", "goal", "acceptance_criteria", "files", "agent"]
        for field in required_fields:
            if field not in task:
                errors.append(f"任务 {task.get('id', '?')} 缺少字段: {field}")
        
        # ID 格式：T1, T2, T3...
        if "id" in task and not re.match(r'^T\d+$', task["id"]):
            errors.append(f"任务 ID 格式错误: {task['id']}")
        
        # 描述≤20字
        if "description" in task and len(task["description"]) > 20:
            errors.append(f"任务 {task['id']} 描述过长")
        
        # 验收标准非空
        if "acceptance_criteria" in task:
            if not isinstance(task["acceptance_criteria"], list) or len(task["acceptance_criteria"]) == 0:
                errors.append(f"任务 {task['id']} 验收标准不能为空")
        
        # 相对路径
        if "files" in task:
            for file_path in task["files"]:
                if not file_path.startswith("./") and not file_path.startswith("../"):
                    errors.append(f"任务 {task['id']} 文件路径应为相对路径")
        
        # agent 已指定
        if "agent" not in task or not task["agent"]:
            errors.append(f"任务 {task['id']} 未指定执行 agent")
    
    # 依赖无循环
    if not is_dag(subtasks):
        errors.append("任务依赖存在循环")
    
    # 并行度≤2
    parallel_count = max_parallel_tasks(subtasks)
    if parallel_count > 2:
        errors.append(f"并行任务数超限: {parallel_count}")
    
    return {"passed": len(errors) == 0, "errors": errors}
```

## 检查清单

### 上下文检查
- [ ] align.json 已读取
- [ ] context.json 已读取
- [ ] 上下文完整性已验证

### 自我迭代
- [ ] 已实现自我验证机制
- [ ] 已实现自动修复逻辑
- [ ] 最多10次迭代限制
- [ ] 迭代次数已记录

### 任务拆分
- [ ] 任务已分解为可执行单元
- [ ] 所有必需字段已存在
- [ ] 任务 ID 格式正确
- [ ] 描述≤20字
- [ ] 验收标准非空
- [ ] 文件路径为相对路径
- [ ] Agent 已指定
- [ ] 依赖无循环
- [ ] 并行度≤2

### 输出
- [ ] task.json 已写入
- [ ] status: "confirmed" | "上下文缺失"
