# Loop 验证和改进最佳实践

本文档包含 MindFlow Loop 验证和改进阶段的最佳实践、注意事项和常见陷阱。

<verification_best_practices>

## 验证阶段

全面验证要求检查所有验收标准：功能完整性、测试覆盖率、代码质量、性能指标。验证不仅是对单个任务的检查，还包括回归测试——确保新变更没有破坏已有功能。回归测试之所以重要，是因为局部修改可能产生意想不到的全局影响。

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

快速反馈要求立即报告验证结果，并提供具体的失败原因和可操作的建议。模糊的失败报告会延长调试时间，而精确的失败信息让修复工作可以立即开始。

```python
# 好的反馈
print("[验证/2·failed]")
print("验收失败：T3 测试未通过（2/10 失败）")
print("失败测试：test_login_timeout, test_invalid_token")
```

```python
failure_report = {
    "task_id": "T3",
    "criterion": "测试覆盖率 >= 90%",
    "actual": "75%",
    "suggestion": "补充以下模块的测试：jwt.py (错误处理分支), middleware.py (边界情况)"
}
```

</verification_best_practices>

<improvement_best_practices>

## 改进阶段

根因分析要求深入分析失败原因，找到根本原因而非表面现象。使用 5 Why 分析法逐层追问，直到找到可以直接解决的根本原因。如果只修复表面症状，同样的问题会反复出现。

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

渐进式升级从简单重试开始逐步升级：Level 1 Retry（简单重试）、Level 2 Debug（深度诊断）、Level 3 Replan（重新规划）、Level 4 Ask User（请求指导）。渐进式策略的理由是大多数失败是瞬态的，轻量重试即可解决，没有必要每次都触发代价高昂的重规划。

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

</improvement_best_practices>

<guidelines>

## 注意事项

应当做的：使用 PDCA 循环持续改进，每次迭代都经过计划、执行、检查、改进。小步迭代快速反馈（最小迭代 1-3 轮，无最大轮数限制）。充分监控和日志记录，记录所有关键事件。及时清理临时资源（删除临时文件、清理 Team 资源）。声明式定义状态转换，使用状态机模式。应用指数退避策略（0s、2s、4s）。实施补偿操作保证一致性，失败时回滚已完成的任务。

不应做的：不要一次性完成所有工作（违背迭代式改进原则）。不要忽略验证和测试（可能引入缺陷）。不要在停滞时继续重试（应该升级策略或请求指导）。不要让 Agent 直接与用户交互（违背 Team Leader 模式）。不要遗漏资源清理（造成资源泄漏）。不要忽略错误信号（及时处理才能避免恶化）。不要跳过迭代强行完成（质量无法保证）。

</guidelines>

<common_pitfalls>

## 常见陷阱

忽略反馈表现为不根据验证结果调整、重复相同的错误。解决方案是分析失败根因、调整策略并记录经验教训。

```python
def handle_verification_result(result):
    if result.status == "failed":
        root_cause = analyze_failure(result)
        adjust_strategy(root_cause)
        record_lesson_learned(root_cause)
```

资源泄漏表现为临时文件未删除、Team 未清理、进程未终止。解决方案是使用 try-finally 确保清理逻辑总是执行。

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

停滞检测失败表现为未识别重复错误、在死循环中反复尝试。解决方案是跟踪错误历史，当连续 3 次出现相同错误时请求用户指导。

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

</common_pitfalls>

<checklist>

## 检查清单

验证阶段：所有验收标准已验证、测试覆盖率达标、回归测试通过、Lint 检查通过、文档完整。

完成阶段：所有任务完成、临时文件已清理、Team 已删除、生成最终报告、记录经验教训。

</checklist>
