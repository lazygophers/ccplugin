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
> **自我验证、自动修复、迭代优化，确保符合项目现有风格**

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

# 获取锁定的项目风格
code_style = align["code_style_follow"]

# 自我迭代循环：生成 → 验证（含风格检查）→ 修复 → 重验
for iteration in range(10):  # 最多10次迭代
    # === 迭代开始 ===
    
    # 阶段1：任务分解（遵循项目风格）
    if iteration == 0:
        subtasks = decompose_task({
            "user_prompt": user_prompt,
            "scope": align["scope"],
            "acceptance": align["acceptance_criteria"],
            "code_style": code_style  # 传入风格约束
        })
    else:
        # 根据上一次验证结果修复
        subtasks = fix_and_redecompose(subtasks, validation_errors, code_style)
    
    # 阶段2：验证任务拆分规范 + 风格符合性
    validation = validate_task_structure(subtasks, code_style)
    
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
    "code_style": code_style,  # 必须遵循的项目风格
    "status": "confirmed",
    "iterations": iteration + 1
}

# 写入任务文件
task_file = f".lazygophers/tasks/{task_id}/task.json"
write_json(task_file, plan)

return {"status": "confirmed"}
```

## 自我修复逻辑

```python
def fix_and_redecompose(subtasks, errors, code_style):
    """根据验证错误和项目风格自动修复任务拆分"""
    
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
                split_large_task(subtasks, task, code_style)
    
    # 修复3：补充验收标准（遵循项目风格）
    for error in errors:
        if "验收标准不能为空" in error:
            task = find_task_by_error(subtasks, error)
            if task:
                generate_acceptance_criteria(
                    task, 
                    align["acceptance_criteria"],
                    code_style  # 遵循项目风格
                )
    
    # 修复4：转换文件路径
    for error in errors:
        if "相对路径" in error:
            task = find_task_by_error(subtasks, error)
            if task:
                convert_to_relative_paths(task, context)
    
    # 修复5：指定默认 agent（项目优先）
    for error in errors:
        if "未指定执行 agent" in error:
            task = find_task_by_error(subtasks, error)
            if task:
                # 优先使用项目自定义 agent
                agent = infer_agent_from_context(task, context, code_style)
                if agent:
                    task["agent"] = agent
    
    # 修复6：解决循环依赖
    if "循环依赖" in str(errors):
        resolve_circular_dependencies(subtasks)
    
    # 修复7：降低并行度
    if "并行任务数超限" in str(errors):
        reduce_parallelism(subtasks, max=2)
    
    # 修复8：确保命名符合项目风格
    for task in subtasks:
        ensure_naming_convention(task, code_style["naming"])
    
    # 修复9：确保文件路径符合项目结构
    for task in subtasks:
        ensure_path_convention(task, code_style["structure"])
    
    return subtasks
```

## 风格符合性验证

```python
def validate_task_structure(subtasks, code_style):
    """验证任务拆分规范 + 项目风格符合性"""
    errors = []
    
    # 原有的规范验证...
    # （必需字段、ID格式、描述长度、验收标准、路径等）
    
    # === 新增：项目风格符合性检查 ===
    
    # 检查1：任务命名是否遵循项目风格
    naming_style = code_style.get("naming", {})
    for task in subtasks:
        task_name = task["id"]
        # 检查描述中的命名是否符合项目风格
        if not follows_naming_convention(task["description"], naming_style):
            errors.append(f"任务 {task_name} 描述命名不符合项目风格")
        
        # 检查文件命名是否符合项目风格
        for file_path in task.get("files", []):
            if not follows_file_naming_convention(file_path, naming_style):
                errors.append(f"任务 {task_name} 文件命名不符合项目风格: {file_path}")
    
    # 检查2：任务粒度是否符合项目习惯
    project_structure = code_style.get("structure", {})
    for task in subtasks:
        # 检查是否应该进一步拆分或合并
        if not follows_project_granularity(task, project_structure):
            errors.append(f"任务 {task['id']} 粒度不符合项目习惯")
    
    # 检查3：agent 选择是否优先使用项目自定义
    for task in subtasks:
        agent = task.get("agent")
        if agent and not is_preferred_project_agent(agent, context):
            errors.append(f"任务 {task['id']} 应优先使用项目自定义 agent: {agent}")
    
    # 检查4：是否遵循项目目录结构
    directory_structure = code_style.get("directories", {})
    for task in subtasks:
        for file_path in task.get("files", []):
            if not follows_project_directory_structure(file_path, directory_structure):
                errors.append(f"任务 {task['id']} 文件路径不符合项目结构: {file_path}")
    
    return {"passed": len(errors) == 0, "errors": errors}
```

## 任务拆分规范

### 子任务结构要求

```json
{
    "id": "T1",
    "description": "简短描述（≤20字，遵循项目命名风格）",
    "goal": "明确的目标（可验证）",
    "acceptance_criteria": ["验收点1", "验收点2"],
    "files": ["相对路径/file1.py"],
    "dependencies": ["T0"],
    "agent": "项目自定义agent或通用agent",
    "estimated_complexity": "low"
}
```

### 拆分原则（加入风格约束）

1. **原子性**：每个子任务应该是原子的、不可再分的
2. **可验证性**：验收标准可测试、具体、可量化
3. **依赖明确**：形成 DAG，无循环，并行≤2
4. **文件范围**：相对路径，不越界
5. **Agent选择**：优先使用项目自定义 agent
6. **复杂度估算**：low/medium/high

### 风格遵守原则（新增）

7. **命名符合项目风格**：任务描述、文件命名都遵循项目现有命名约定
8. **粒度符合项目习惯**：任务大小与项目现有任务粒度一致
9. **结构符合项目布局**：文件组织遵循项目目录结构
10. **Agent优先项目**：优先使用 `.claude/agents/` 中的自定义 agent

## 检查清单

### 上下文检查
- [ ] align.json 已读取
- [ ] context.json 已读取
- [ ] 上下文完整性已验证
- [ ] **code_style_follow 已读取（项目风格）**

### 自我迭代
- [ ] 已实现自我验证机制
- [ ] 已实现自动修复逻辑
- [ ] 最多10次迭代限制
- [ ] 迭代次数已记录

### 风格符合性（新增）
- [ ] 命名遵循项目风格
- [ ] 文件命名遵循项目风格
- [ ] 任务粒度符合项目习惯
- [ ] 优先使用项目自定义 agent
- [ ] 文件路径符合项目结构

### 输出
- [ ] task.json 已写入
- [ ] **包含 code_style 字段（项目风格）**
- [ ] status: "confirmed" | "上下文缺失"
