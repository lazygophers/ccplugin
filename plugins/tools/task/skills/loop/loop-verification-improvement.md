# Loop 验证和改进最佳实践

本文档包含 MindFlow Loop 验证和改进阶段的最佳实践、注意事项和常见陷阱。

## 验证阶段最佳实践

### 全面验证

检查所有验收标准：功能完整性、测试覆盖率、代码质量、性能指标。

验证回归测试：
```python
def run_regression_tests():
    """运行回归测试"""
    result = run_tests(suite="all")
    new_failures = result.failures - baseline.failures
    if new_failures:
        alert("检测到回归", new_failures)
        return False
    return True
```

### 快速反馈

立即报告验证结果：
```python
# ✓ 好的反馈
print("[验证/2·failed]")
print("验收失败：T3 测试未通过（2/10 失败）")
print("失败测试：test_login_timeout, test_invalid_token")
```

提供具体的失败原因和可操作的建议：
```python
failure_report = {
    "task_id": "T3",
    "criterion": "测试覆盖率 ≥ 90%",
    "actual": "75%",
    "suggestion": "补充以下模块的测试：jwt.py (错误处理分支), middleware.py (边界情况)"
}
```

---

## 改进阶段最佳实践

### 根因分析

深入分析失败原因，找到根本原因，使用 5 Why 分析法。

识别系统性问题：
```python
def analyze_root_cause(failures):
    """分析失败的根本原因"""
    patterns = {}
    for failure in failures:
        pattern = extract_pattern(failure)
        patterns[pattern] = patterns.get(pattern, 0) + 1

    most_common = max(patterns, key=patterns.get)
    return {
        "root_cause": most_common,
        "frequency": patterns[most_common],
        "affected_tasks": [f for f in failures if extract_pattern(f) == most_common]
    }
```

### 渐进式升级

从简单重试开始：
1. Level 1: Retry（简单重试）
2. Level 2: Debug（深度诊断）
3. Level 3: Replan（重新规划）
4. Level 4: Ask User（请求指导）

逐步升级策略：
```python
def apply_graduated_escalation(failure_count):
    if failure_count == 1:
        return "retry"
    elif failure_count == 2:
        return "debug"
    elif failure_count >= 3:
        return "replan"
    else:
        return "ask_user"
```

---

## 注意事项

### Do's ✓

1. **使用 PDCA 循环持续改进** - 每次迭代都经过计划、执行、检查、改进
2. **小步迭代，快速反馈** - 最小迭代次数1-3轮，无最大轮数限制
3. **充分监控和日志记录** - 记录所有关键事件
4. **及时清理临时资源** - 删除临时文件、清理 Team 资源
5. **声明式定义状态转换** - 使用状态机模式
6. **应用指数退避策略** - 0s → 2s → 4s
7. **实施补偿操作保证一致性** - 失败时回滚已完成的任务

### Don'ts ✗

1. **不要一次性完成所有工作** - 违背迭代式改进原则
2. **不要忽略验证和测试** - 可能引入缺陷
3. **不要在停滞时继续重试** - 应该升级策略或请求指导
4. **不要让 Agent 直接与用户交互** - 违背 Team Leader 模式
5. **不要遗漏资源清理** - 造成资源泄漏
6. **不要忽略错误信号** - 及时处理才能避免恶化
7. **不要跳过迭代强行完成** - 质量无法保证

---

## 常见陷阱

### 1. 忽略反馈

**表现**：不根据验证结果调整、重复相同的错误

**解决方案**：
```python
def handle_verification_result(result):
    if result.status == "failed":
        root_cause = analyze_failure(result)
        adjust_strategy(root_cause)
        record_lesson_learned(root_cause)
```

### 2. 资源泄漏

**表现**：临时文件未删除、Team 未清理、进程未终止

**解决方案**：
```python
def execute_with_cleanup():
    team = None
    temp_files = []
    try:
        team = TeamCreate(...)
        temp_files = create_temp_files()
        # 执行任务
    finally:
        if team:
            TeamDelete(team)
        for file in temp_files:
            os.remove(file)
```

### 3. 停滞检测失败

**表现**：未识别重复错误、在死循环中反复尝试

**解决方案**：
```python
error_history = []

def detect_stall(error):
    error_history.append(error)
    if len(error_history) >= 3:
        recent = error_history[-3:]
        if all(e.signature == recent[0].signature for e in recent):
            request_user_guidance()
            return True
    return False
```

---

## 检查清单

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
