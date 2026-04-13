# Plan 验证逻辑

## 自我验证

```python
def validate_plan(subtasks, code_style):
    errors = []
    
    # === 规范验证（per-task）===
    for task in subtasks:
        if not is_atomic(task):
            errors.append(f"{task['id']}: 非原子任务")
        if not task.get("acceptance_criteria"):
            errors.append(f"{task['id']}: 缺少验收标准")
        if not task.get("files"):
            errors.append(f"{task['id']}: 缺少 files 字段（无法确定修改范围）")
        if not task.get("goal"):
            errors.append(f"{task['id']}: 缺少 goal 字段")
    
    # === 单文件单任务验证 ===
    file_owners = {}  # file → task_id
    for task in subtasks:
        for file in task.get("files", []):
            if file in file_owners:
                errors.append(f"文件冲突：'{file}' 被 {file_owners[file]} 和 {task['id']} 同时修改")
            else:
                file_owners[file] = task["id"]
    
    # === 全局验证 ===
    if has_circular_dependency(subtasks):
        errors.append("存在循环依赖")
    if count_parallel(subtasks) > 2:
        errors.append("并行任务超过2个")
    
    # === 幂等性验证 ===
    for task in subtasks:
        if has_side_effects(task):
            errors.append(f"{task['id']}: 包含不可重试的副作用操作（如发送通知、删除数据）")
    
    # === 风格验证 ===
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
        elif "缺少 files" in error:
            fixed = infer_files(fixed, extract_task_id(error), context)
        elif "缺少 goal" in error:
            fixed = generate_goal(fixed, extract_task_id(error))
        elif "文件冲突" in error:
            fixed = merge_conflicting_tasks(fixed, extract_file(error))
        elif "命名不符合" in error:
            fixed = rename_task(fixed, extract_task_id(error), code_style)
        elif "路径不符合" in error:
            fixed = restructure_files(fixed, extract_task_id(error), code_style)
        elif "循环依赖" in error:
            fixed = resolve_circular(fixed)
        elif "并行超过" in error:
            fixed = reduce_parallel(fixed)
        elif "副作用操作" in error:
            fixed = isolate_side_effects(fixed, extract_task_id(error))
    
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
