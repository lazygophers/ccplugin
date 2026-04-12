# Plan 验证逻辑

## 自我验证

```python
def validate_plan(subtasks, code_style):
    errors = []
    
    # 规范验证（per-task）
    for task in subtasks:
        if not is_atomic(task):
            errors.append(f"{task['id']}: 非原子任务")
        if not task.get("acceptance_criteria"):
            errors.append(f"{task['id']}: 缺少验收标准")
    
    # 全局验证
    if has_circular_dependency(subtasks):
        errors.append("存在循环依赖")
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

## 自动修复

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

## 自我评估

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

## DAG 验证

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
