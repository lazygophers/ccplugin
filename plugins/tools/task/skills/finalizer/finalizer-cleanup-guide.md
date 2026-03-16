# Finalizer 资源清理指南

## 资源清理最佳实践

### 明确所有权（Clear Ownership）

- 识别每个资源的"所有者"（哪个组件负责创建）
- 所有者模块负责正确释放资源
- 最小化共享所有权，减少混乱和潜在泄漏

### 错误处理（Error Handling）

- 即使操作失败，也要释放部分资源
- 维护健壮的错误处理路径
- 关闭打开的句柄或中止未完成的任务
- 防止一个错误阻止整个清理流程

### 清理顺序（Cleanup Order）

- 按依赖关系逆序清理（先创建的后清理）
- 先停止运行的任务，再清理文件
- 确保清理过程的原子性
- 遵循正确的依赖关系

### 防御性清理（Defensive Cleanup）

- 使用 try-except 包裹清理逻辑
- 记录清理过程中的所有异常
- 即使部分清理失败，也继续剩余清理
- 确保资源不泄漏，降低成本，保持系统稳定

### 语言特定模式

- **Python**：使用 `with` 语句进行作用域资源管理
- **Java/C#**：使用 `try-with-resources` 或 `using` 语句自动释放对象
- **C++**：使用 RAII（资源获取即初始化）模式

## 执行流程详解

### 阶段 1：资源盘点

**目标**：识别需要清理的所有资源类型和实例

#### 1.1 任务资源

```python
# 获取所有任务
tasks = TaskList()

task_resources = {
    "total_tasks": len(tasks),
    "running_tasks": [t for t in tasks if t.status == "in_progress"],
    "pending_tasks": [t for t in tasks if t.status == "pending"],
    "completed_tasks": [t for t in tasks if t.status == "completed"],
    "failed_tasks": [t for t in tasks if t.status == "failed"]
}
```

#### 1.2 文件资源

```python
# 识别计划文件
plan_dir = os.path.expanduser("~/.claude/plans/")
plan_files = glob.glob(os.path.join(plan_dir, "*.md"))

# 识别临时文件
temp_files = glob.glob("/tmp/claude_task_*")

file_resources = {
    "plan_files": plan_files,
    "temp_files": temp_files,
    "total_files": len(plan_files) + len(temp_files)
}
```

#### 1.3 其他资源

```python
# 检查其他可能的资源
other_resources = {
    "lock_files": find_lock_files(),
    "cache_files": find_cache_files(),
    "log_files": find_log_files()
}
```

### 阶段 2：任务终止

**目标**：系统性地停止所有正在运行和待执行的任务

#### 2.1 停止运行中的任务

```python
stopped_tasks = []
failed_to_stop = []

for task in task_resources["running_tasks"]:
    try:
        TaskStop(task.id)
        stopped_tasks.append({
            "id": task.id,
            "name": task.description,
            "status": "stopped"
        })
    except Exception as e:
        failed_to_stop.append({
            "id": task.id,
            "name": task.description,
            "error": str(e)
        })
        # 记录错误但继续清理其他任务
        log_error(f"Failed to stop task {task.id}: {e}")
```

#### 2.2 取消待执行的任务

```python
for task in task_resources["pending_tasks"]:
    try:
        TaskStop(task.id)  # 取消待执行任务
        stopped_tasks.append({
            "id": task.id,
            "name": task.description,
            "status": "cancelled"
        })
    except Exception as e:
        failed_to_stop.append({
            "id": task.id,
            "error": str(e)
        })
```

### 阶段 3：文件清理

**目标**：删除所有计划文件、临时文件和缓存文件

#### 3.1 清理计划文件

```python
deleted_plans = []
failed_to_delete = []

for plan_file in file_resources["plan_files"]:
    try:
        os.remove(plan_file)
        deleted_plans.append(plan_file)
    except Exception as e:
        failed_to_delete.append({
            "file": plan_file,
            "error": str(e)
        })
        log_error(f"Failed to delete plan file {plan_file}: {e}")
```

#### 3.2 清理临时文件

```python
for temp_file in file_resources["temp_files"]:
    try:
        os.remove(temp_file)
        deleted_plans.append(temp_file)
    except Exception as e:
        failed_to_delete.append({
            "file": temp_file,
            "error": str(e)
        })
```

#### 3.3 清理空目录

```python
# 清理空的计划目录
try:
    if os.path.exists(plan_dir) and not os.listdir(plan_dir):
        os.rmdir(plan_dir)
except Exception as e:
    log_error(f"Failed to remove empty plan directory: {e}")
```

### 阶段 4：最终报告生成

**目标**：生成清理摘要报告，记录清理结果和任何错误

#### 4.1 收集清理统计

```python
cleanup_summary = {
    "tasks_stopped": len(stopped_tasks),
    "tasks_failed_to_stop": len(failed_to_stop),
    "files_deleted": len(deleted_plans),
    "files_failed_to_delete": len(failed_to_delete),
    "total_duration_seconds": calculate_duration()
}
```

#### 4.2 生成报告

基于清理结果生成简洁报告（≤100字）。

## 清理检查清单

### 任务清理检查
- [ ] 所有运行中的任务已停止
- [ ] 所有待执行的任务已取消
- [ ] 任务清理失败已记录

### 文件清理检查
- [ ] 所有计划文件已删除
- [ ] 所有临时文件已删除
- [ ] 空目录已清理
- [ ] 文件删除失败已记录

### 错误处理检查
- [ ] 所有清理操作都有错误处理
- [ ] 错误不会阻止剩余清理
- [ ] 所有错误都已记录

### 报告生成检查
- [ ] 清理统计准确
- [ ] 报告简洁（≤100字）
- [ ] 包含所有必要信息
