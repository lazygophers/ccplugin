# Loop 错误处理和重试

本文档包含 MindFlow Loop 的错误处理、重试策略和补偿模式。

## 声明式错误处理

### Retry 配置

**首次失败（failure_count=1）**：
- 退避时间：0 秒
- 策略：立即重试
- 操作：应用简单调整后重新执行

**重复失败（failure_count=2）**：
- 退避时间：2 秒
- 策略：深度诊断
- 操作：调用 debug agent 分析根因

**持续失败（failure_count=3）**：
- 退避时间：4 秒
- 策略：重新规划
- 操作：返回计划设计阶段

### Catch 配置

**停滞检测（stalled_count=3）**：
- 触发条件：连续 3 次相同错误
- 操作：请求用户指导
- 行为：不退出循环，等待用户输入

**超过最大停滞次数**：
- 触发条件：stalled_count >= max_stalled_attempts
- 操作：强制结束循环
- 行为：输出停滞报告，建议人工介入

### 指数退避策略

```python
def calculate_backoff(failure_count):
    """计算退避时间"""
    if failure_count == 1:
        return 0  # 立即重试
    elif failure_count == 2:
        return 2  # 2 秒
    elif failure_count >= 3:
        return 4  # 4 秒
    return 0
```

## Saga Pattern（补偿模式）

### 补偿场景

当任务执行失败且无法恢复时，需要执行补偿操作以确保系统一致性。

### 补偿策略

1. **识别已完成的任务**：
   - 查询任务状态
   - 标记已完成的任务
   - 确定需要回滚的操作

2. **生成补偿操作**：
   - 为每个已完成任务生成逆操作
   - 考虑任务间的依赖关系
   - 按反向顺序执行

3. **执行补偿**：
   - 从最后一个任务开始
   - 逐个撤销已完成的更改
   - 记录补偿执行日志

### 补偿实现

```python
def compensate_on_failure(completed_tasks):
    """在失败时执行补偿操作

    Args:
        completed_tasks: 已完成的任务列表
    """
    # 反向遍历已完成的任务
    for task in reversed(completed_tasks):
        if task.has_compensation:
            try:
                print(f"执行补偿操作：{task.id} - {task.description}")
                execute_compensation(task)
                print(f"✓ 补偿成功：{task.id}")
            except Exception as e:
                print(f"✗ 补偿失败：{task.id} - {str(e)}")
                # 记录失败但继续执行其他补偿
```

### 补偿操作示例

```python
# 任务定义包含补偿操作
task = {
    "id": "T1",
    "description": "创建数据库表",
    "compensation": {
        "type": "sql",
        "operation": "DROP TABLE users;"
    }
}

# 执行补偿
def execute_compensation(task):
    """执行具体的补偿操作"""
    comp = task.compensation

    if comp["type"] == "sql":
        execute_sql(comp["operation"])
    elif comp["type"] == "file":
        delete_file(comp["path"])
    elif comp["type"] == "api":
        call_api(comp["endpoint"], comp["params"])
```

## 错误分类和处理

### 可恢复错误

- **网络超时**：自动重试
- **资源临时不可用**：应用退避后重试
- **测试失败**：分析原因后重新执行

### 不可恢复错误

- **配置错误**：请求用户修正
- **权限不足**：请求用户授权
- **依赖缺失**：请求用户安装

### 停滞模式检测

```python
def detect_stall(error_history):
    """检测停滞模式

    Returns:
        bool: True 表示检测到停滞
    """
    if len(error_history) < 3:
        return False

    # 检查最近 3 次错误是否相同
    recent_errors = error_history[-3:]
    error_signatures = [get_error_signature(e) for e in recent_errors]

    return len(set(error_signatures)) == 1  # 所有错误签名相同
```

## 分级升级策略

### Level 1: Retry（重试）
- **适用场景**：首次失败
- **操作**：应用简单调整后重试
- **示例**：增加超时时间、清理缓存

### Level 2: Debug（调试）
- **适用场景**：重复失败
- **操作**：深度诊断和修复
- **示例**：分析日志、检查环境

### Level 3: Replan（重新规划）
- **适用场景**：持续失败
- **操作**：返回计划设计阶段
- **示例**：调整任务分解、修改依赖

### Level 4: Ask User（请求指导）
- **适用场景**：检测到停滞
- **操作**：请求用户提供指导
- **示例**：询问是否调整目标、是否需要人工介入
