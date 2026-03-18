# Loop 最佳实践和注意事项

本文档包含 MindFlow Loop 的最佳实践、常见陷阱和注意事项。

## 最佳实践

### 规划阶段

#### 充分规划

**目标明确**：
- 明确定义任务目标
- 识别关键交付物
- 设定可量化的成功标准

**任务分解**：
- 使用 MECE 原则（互斥且完全穷尽）
- 每个任务都是原子性的
- 避免过度拆分或拆分不足

**依赖建模**：
- 识别任务间的依赖关系
- 确保依赖关系形成 DAG（有向无环图）
- 标注关键路径

**资源分配**：
- 为每个任务分配合适的 Agent
- 指定必要的 Skills
- 考虑资源约束（最多 2 个并行）

#### 可扩展性

**选择可扩展的方案**：
- 优先使用灵活的架构
- 避免硬编码
- 支持配置驱动

**支持灵活调整**：
```python
# ❌ 不灵活（硬编码）
max_parallel = 2

# ✓ 灵活（可配置）
max_parallel = config.get("max_parallel_tasks", 2)
```

**避免过度耦合**：
- 任务之间松耦合
- 使用接口而非具体实现
- 支持任务替换和扩展

### 执行阶段

#### 持续监控

**实时跟踪任务进度**：
- 监控任务状态变化
- 记录执行时间
- 追踪资源使用

**识别低效或失败**：
```python
def monitor_task_execution(task):
    """监控任务执行"""
    start_time = time.time()

    while task.is_running():
        # 检查是否超时
        if time.time() - start_time > task.timeout:
            alert("任务执行超时", task.id)

        # 检查资源使用
        if get_resource_usage(task) > threshold:
            alert("资源使用过高", task.id)

        time.sleep(5)
```

**及时调整策略**：
- 发现问题立即处理
- 动态调整并行度
- 必要时重新规划

#### 并行优化

**最大化并行度**：
- 识别可并行的任务
- 优先调度 Ready 任务
- 最多 2 个任务同时执行

**最小化等待时间**：
```python
def schedule_tasks(tasks, max_parallel=2):
    """智能调度任务"""
    running = []
    pending = tasks.copy()

    while pending or running:
        # 补充槽位
        while len(running) < max_parallel and pending:
            # 查找就绪的任务
            ready_task = find_ready_task(pending)
            if ready_task:
                running.append(ready_task)
                pending.remove(ready_task)
                start_task(ready_task)
            else:
                break  # 没有就绪任务

        # 检查完成
        for task in running.copy():
            if task.is_completed():
                running.remove(task)
```

**优化资源利用**：
- CPU 密集型和 I/O 密集型任务搭配
- 避免资源竞争
- 平衡负载

### 验证阶段

#### 全面验证

**检查所有验收标准**：
- 功能完整性
- 测试覆盖率
- 代码质量
- 性能指标

**验证回归测试**：
```python
def run_regression_tests():
    """运行回归测试"""
    # 运行完整的测试套件
    result = run_tests(suite="all")

    # 检查是否有新的失败
    new_failures = result.failures - baseline.failures

    if new_failures:
        alert("检测到回归", new_failures)
        return False

    return True
```

**确保质量达标**：
- Lint 检查通过
- 安全扫描通过
- 文档完整

#### 快速反馈

**立即报告验证结果**：
```python
# ✓ 好的反馈
print("[验证/2·failed]")
print("验收失败：T3 测试未通过（2/10 失败）")
print("失败测试：test_login_timeout, test_invalid_token")

# ❌ 不好的反馈
print("验证完成")  # 缺少细节
```

**提供具体的失败原因**：
- 哪个任务失败
- 哪个标准未满足
- 失败的具体原因
- 失败的日志或错误信息

**给出可操作的建议**：
```python
failure_report = {
    "task_id": "T3",
    "criterion": "测试覆盖率 ≥ 90%",
    "actual": "75%",
    "suggestion": "补充以下模块的测试：jwt.py (错误处理分支), middleware.py (边界情况)"
}
```

### 改进阶段

#### 根因分析

**深入分析失败原因**：
- 不要只看表面症状
- 找到根本原因
- 使用 5 Why 分析法

**识别系统性问题**：
```python
def analyze_root_cause(failures):
    """分析失败的根本原因"""
    patterns = {}

    for failure in failures:
        # 提取错误模式
        pattern = extract_pattern(failure)
        patterns[pattern] = patterns.get(pattern, 0) + 1

    # 识别最常见的模式
    most_common = max(patterns, key=patterns.get)

    return {
        "root_cause": most_common,
        "frequency": patterns[most_common],
        "affected_tasks": [f for f in failures if extract_pattern(f) == most_common]
    }
```

**防止重复错误**：
- 记录已解决的问题
- 创建检查清单
- 自动化验证

#### 渐进式升级

**从简单重试开始**：
1. Level 1: Retry（简单重试）
2. Level 2: Debug（深度诊断）
3. Level 3: Replan（重新规划）
4. Level 4: Ask User（请求指导）

**逐步升级策略**：
```python
def apply_graduated_escalation(failure_count):
    """应用分级升级策略"""
    if failure_count == 1:
        return "retry"
    elif failure_count == 2:
        return "debug"
    elif failure_count >= 3:
        return "replan"
    else:
        return "ask_user"
```

**避免过早放弃**：
- 给予足够的重试机会
- 尝试多种解决方案
- 只在真正停滞时请求用户

## 注意事项

### Do's ✓

1. **✓ 使用 PDCA 循环持续改进**
   - 每次迭代都经过计划、执行、检查、改进
   - 从失败中学习
   - 持续优化流程

2. **✓ 小步迭代，快速反馈**
   - 最小迭代次数根据任务复杂度动态确定（1-3 轮）
   - 无最大轮数限制，持续迭代直到质量完美
   - 每次迭代产生可验证的增量
   - 快速发现和修正问题

3. **✓ 充分监控和日志记录**
   - 记录所有关键事件
   - 监控任务状态和进度
   - 保存执行日志供分析

4. **✓ 及时清理临时资源**
   - 删除临时文件
   - 清理 Team 资源
   - 释放占用的资源

5. **✓ 声明式定义状态转换**
   - 使用状态机模式
   - 明确定义状态和转换条件
   - 易于理解和维护

6. **✓ 应用指数退避策略**
   - 避免重试风暴
   - 给系统恢复时间
   - 0s → 2s → 4s

7. **✓ 实施补偿操作保证一致性**
   - 失败时回滚已完成的任务
   - 确保系统状态一致
   - 防止数据不一致

### Don'ts ✗

1. **✗ 不要一次性完成所有工作**
   - 违背迭代式改进原则
   - 风险高，难以调试
   - 缺少中间反馈

2. **✗ 不要忽略验证和测试**
   - 可能引入缺陷
   - 无法保证质量
   - 增加后期成本

3. **✗ 不要在停滞时继续重试**
   - 浪费资源
   - 不会解决问题
   - 应该升级策略或请求指导

4. **✗ 不要让 Agent 直接与用户交互**
   - 造成通信混乱
   - 难以追踪对话
   - 违背 Team Leader 模式

5. **✗ 不要遗漏资源清理**
   - 造成资源泄漏
   - 影响系统性能
   - 可能导致错误

6. **✗ 不要忽略错误信号**
   - 小问题会演变成大问题
   - 及时处理才能避免恶化
   - 监控和警报很重要

7. **✗ 不要跳过迭代强行完成**
   - 质量无法保证
   - 缺少验证环节
   - 违背设计原则

## 常见陷阱

### 1. 过度规划

**表现**：
- 花费大量时间完善计划
- 规划的时间超过执行时间
- 分析瘫痪（analysis paralysis）

**解决方案**：
- 设定规划时间上限
- 采用敏捷方法：刚刚好的规划
- 快速开始，在执行中调整

```python
# ❌ 过度规划
planning_time = 2_hours
execution_time = 30_minutes

# ✓ 合理规划
planning_time = 20_minutes
execution_time = 2_hours
```

### 2. 过早优化

**表现**：
- 在验证可行性前就优化性能
- 过度设计架构
- 引入不必要的复杂性

**解决方案**：
- 先实现，再优化
- 基于实际数据优化
- 遵循 YAGNI 原则（You Aren't Gonna Need It）

```python
# ❌ 过早优化
def process_data(data):
    # 引入复杂的缓存、并发处理等
    # 但数据量实际很小

# ✓ 先简单实现
def process_data(data):
    # 简单直接的实现
    # 发现性能问题后再优化
```

### 3. 忽略反馈

**表现**：
- 不根据验证结果调整
- 重复相同的错误
- 不听取用户意见

**解决方案**：
- 认真对待每次验证结果
- 记录失败原因并改进
- 积极响应用户反馈

```python
# ✓ 响应反馈
def handle_verification_result(result):
    if result.status == "failed":
        # 分析失败原因
        root_cause = analyze_failure(result)
        # 调整策略
        adjust_strategy(root_cause)
        # 记录教训
        record_lesson_learned(root_cause)
```

### 4. 资源泄漏

**表现**：
- 临时文件未删除
- Team 未清理
- 进程未终止

**解决方案**：
- 使用 try-finally 确保清理
- 维护资源清单
- 定期检查资源使用

```python
# ✓ 正确的资源管理
def execute_with_cleanup():
    team = None
    temp_files = []

    try:
        team = TeamCreate(...)
        temp_files = create_temp_files()
        # 执行任务
    finally:
        # 确保清理
        if team:
            TeamDelete(team)
        for file in temp_files:
            os.remove(file)
```

### 5. 停滞检测失败

**表现**：
- 未识别重复错误
- 在死循环中反复尝试
- 浪费资源

**解决方案**：
- 实现停滞检测算法
- 设置最大重试次数
- 及时请求用户指导

```python
# ✓ 停滞检测
error_history = []

def detect_stall(error):
    error_history.append(error)

    # 检查最近 3 次错误
    if len(error_history) >= 3:
        recent = error_history[-3:]
        if all(e.signature == recent[0].signature for e in recent):
            # 检测到停滞
            request_user_guidance()
            return True

    return False
```

## 检查清单

### 规划阶段检查清单

- [ ] 任务目标明确
- [ ] 任务分解遵循 MECE 原则
- [ ] 依赖关系形成 DAG（无循环）
- [ ] 每个任务都有明确的验收标准
- [ ] Agent 和 Skills 分配合理
- [ ] 并行度不超过 2

### 执行阶段检查清单

- [ ] 任务按依赖顺序执行
- [ ] 实时监控任务进度
- [ ] 记录执行日志
- [ ] 及时发现和处理异常
- [ ] 资源使用在合理范围内

### 验证阶段检查清单

- [ ] 所有验收标准已验证
- [ ] 测试覆盖率达标
- [ ] 回归测试通过
- [ ] Lint 检查通过
- [ ] 文档完整

### 完成阶段检查清单

- [ ] 所有任务完成
- [ ] 临时文件已清理
- [ ] Team 已删除
- [ ] 生成最终报告
- [ ] 记录经验教训
