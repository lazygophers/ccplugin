---
description: 任务规划，分解任务并制定执行方案
memory: project
color: purple
model: opus
permissionMode: plan
background: false
context: fork
agent: task:plan
---

# Plan Skill

## 执行流程

> 基于对齐结果，将任务分解为可执行的子任务
> **自我验证、自动修复、迭代优化，无需用户确认**

```python
# 读取输入
align = read_json(f".lazygophers/tasks/{task_id}/align.json")
context = read_json(f".lazygophers/tasks/{task_id}/context.json")
code_style = align["code_style_follow"]  # 锁定的项目风格

# 自我迭代循环
for i in range(10):
    # 阶段1：任务分解
    subtasks = decompose_task(align, code_style)
    
    # 阶段2：验证规范
    validation = validate_plan(subtasks, code_style)
    
    if validation["passed"]:
        break  # 通过则退出
    
    # 阶段3：自动修复
    subtasks = fix_issues(subtasks, validation["errors"], code_style)

# 验证失败处理
if not validation["passed"]:
    return {"status": "上下文缺失"}

# 阶段4：构建执行计划
plan = {
    "subtasks": list(subtasks.values()),
    "code_style": code_style,
    "metadata": {
        "total_tasks": len(subtasks),
        "generated_at": datetime.now().isoformat()
    }
}

# 阶段5：自我评估
assessment = self_assess(plan, code_style)

# 阶段6：验证 DAG 可用性
dag_valid = validate_dag(plan["subtasks"])
if not dag_valid["passed"]:
    return {"status": "上下文缺失", "reason": f"DAG 验证失败: {dag_valid['errors']}"}

# 写入结果
write_json(f".lazygophers/tasks/{task_id}/task.json", plan)

# 输出格式：所有输出必须包含前缀 [flow·{task_id}·{state}]
print(f"[flow·{task_id}·plan] 任务规划已完成，共 {len(plan['subtasks'])} 个子任务")

return {"status": "confirmed", "iterations": i + 1, "assessment": assessment}
```

## 任务拆分规范

### 子任务结构

```json
{
    "id": "AuthMiddleware",
    "description": "实现认证中间件",
    "goal": "验证请求头中的JWT令牌",
    "acceptance_criteria": [
        "无效令牌返回401",
        "有效令牌解析用户信息"
    ],
    "files": ["src/middleware/auth.py"],
    "dependencies": ["JWTUtils"],
    "agent": "general-purpose",
    "estimated_complexity": "medium"
}
```

### 拆分原则

**原子性**：每个子任务独立完成、不可再分
**可验证性**：验收标准具体、可测试、可量化
**依赖明确**：形成 DAG，无循环依赖
**并行限制**：并行任务数量 ≤ 2
**文件范围**：使用相对路径，不得越界
**复杂度估算**：low / medium / high
**单文件单任务**：每个任务只修改一个文件，禁止跨文件操作（避免冲突）
**幂等性设计**：任务可安全重复执行，多次执行产生相同结果（支持失败重试）

### 风格遵守

**命名约定**：任务ID、描述遵循项目命名风格
**文件组织**：文件路径符合项目目录结构
**粒度一致**：任务大小与项目现有任务粒度匹配
**Agent优先**：优先使用项目自定义 agent（`.claude/agents/`）

## 自我验证逻辑

```python
def validate_plan(subtasks, code_style):
    errors = []
    
    # 规范验证
    for task in subtasks:
        # 原子性检查
        if not is_atomic(task):
            errors.append(f"{task['id']}: 非原子任务")
        
        # 可验证性检查
        if not task.get("acceptance_criteria"):
            errors.append(f"{task['id']}: 缺少验收标准")
        
        # 依赖检查
        if has_circular_dependency(subtasks):
            errors.append("存在循环依赖")
        
        # 并行检查
        if count_parallel(subtasks) > 2:
            errors.append("并行任务超过2个")
    
    # 风格验证
    style_errors = validate_style(subtasks, code_style)
    errors.extend(style_errors)
    
    return {"passed": len(errors) == 0, "errors": errors}
```

## 风格符合性验证

```python
def validate_style(subtasks, code_style):
    errors = []
    
    # 命名风格检查
    naming = code_style.get("naming", {})
    for task in subtasks:
        if not matches_naming_convention(task["id"], naming):
            errors.append(f"{task['id']}: 命名不符合项目风格")
    
    # 文件结构检查
    structure = code_style.get("structure", {})
    for task in subtasks:
        for file in task.get("files", []):
            if not matches_project_structure(file, structure):
                errors.append(f"{file}: 路径不符合项目结构")
    
    # Agent 使用检查
    custom_agents = code_style.get("custom_agents", [])
    for task in subtasks:
        if task["agent"] == "general-purpose" and custom_agents:
            errors.append(f"{task['id']}: 未优先使用项目自定义 agent")
    
    return errors
```

## 自动修复逻辑

```python
def fix_issues(subtasks, errors, code_style):
    fixed = subtasks
    
    for error in errors:
        if "非原子任务" in error:
            fixed = split_task(fixed, extract_task_id(error))
        elif "缺少验收标准" in error:
            fixed = add_criteria(fixed, extract_task_id(error), code_style)
        elif "命名不符合" in error:
            fixed = rename_task(fixed, extract_task_id(error), code_style)
        elif "路径不符合" in error:
            fixed = restructure_files(fixed, extract_task_id(error), code_style)
        elif "循环依赖" in error:
            fixed = resolve_circular(fixed)
        elif "并行超过" in error:
            fixed = reduce_parallel(fixed)
    
    return fixed
```

## 自我评估逻辑

```python
def self_assess(plan, code_style):
    return {
        "task_count": len(plan["subtasks"]),
        "complexity_distribution": count_complexity(plan),
        "max_parallel_depth": calculate_max_parallel_depth(plan),
        "style_compliance": check_compliance(plan, code_style),
        "estimated_duration": estimate_duration(plan)
    }
```

## DAG 验证逻辑

```python
def validate_dag(subtasks):
    """验证 DAG 可用性：无循环依赖、依赖存在性"""
    errors = []
    
    # 构建 task_id 映射
    task_ids = {t["id"] for t in subtasks}
    
    # 检查依赖存在性
    for task in subtasks:
        for dep in task.get("dependencies", []):
            if dep not in task_ids:
                errors.append(f"{task['id']}: 依赖的任务 '{dep}' 不存在")
    
    # 检查循环依赖
    graph = {t["id"]: set(t.get("dependencies", [])) for t in subtasks}
    if has_cycle(graph):
        errors.append("存在循环依赖")
    
    return {"passed": len(errors) == 0, "errors": errors}
```

## 检查清单

### 上下文读取
- [ ] align.json 已读取
- [ ] context.json 已读取
- [ ] code_style_follow 已获取

### 自我迭代
- [ ] 最多10次迭代
- [ ] 验证 → 修复 → 重验循环已实现
- [ ] 迭代次数已记录

### 任务拆分
- [ ] 原子性已验证
- [ ] 可验证性已验证
- [ ] 依赖关系已验证
- [ ] 并行数量 ≤ 2
- [ ] 文件路径使用相对路径

### 风格遵守
- [ ] 命名符合项目风格
- [ ] 文件组织符合项目结构
- [ ] 粒度符合项目习惯
- [ ] 优先使用项目自定义 agent

### DAG 验证
- [ ] 依赖任务存在性已验证
- [ ] 无循环依赖已验证
- [ ] DAG 可用性已确认

### 输出
- [ ] task.json 已写入
- [ ] 包含 subtasks 数组
- [ ] 包含 code_style 字段
- [ ] 包含自我评估结果（assessment）
- [ ] status: "confirmed" | "上下文缺失"

## 输出格式

所有输出必须包含前缀：`[flow·{task_id}·{state}]`

- task_id：当前任务ID
- state：当前状态（plan）
