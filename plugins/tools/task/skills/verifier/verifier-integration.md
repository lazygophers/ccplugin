# Verifier 集成指南

## 基础集成（Loop内）

1. **调用verifier**：`Skill(skill="task:verifier")` 传入任务目标、迭代轮次
2. **输出报告**：`[MindFlow·{task}·结果验证/{N}·{status}]`
3. **状态路由**：passed→exit | suggestions→自动继续优化 | failed→adjustment

### 结果处理

- 验证status有效性(passed/suggestions/failed)
- 输出summary统计(total/completed/failed/coverage/regression)
- passed：所有标准通过
- suggestions：显示建议(priority图标❗⚠️💡)
- failed：列出每个failure的criterion/actual/reason

### 自定义场景

- **单任务验证**：传入task_id + acceptance_criteria
- **批量验证**：传入tasks JSON列表
- **增量验证**：传入new_tasks + previous_verification

## 高级集成（结构化验收标准）

### validate_structured_criterion

字符串格式直接通过(向后兼容)。结构化格式验证：

| 检查 | 规则 |
|------|------|
| 必需字段 | id + type + description + priority |
| priority | required/recommended |
| exact_match | 需verification_method(run_linter/run_tests/check_build) |
| quantitative_threshold | 需metric + operator(>=,<=,>,<,==) + threshold；tolerance可选(0-1) |

### validate_all_criteria

遍历所有tasks的acceptance_criteria，收集验证错误。返回 `{valid: bool, errors: [{task_id, criterion_index, error}]}`

### 容差处理

对于 quantitative_threshold + tolerance：
- actual ≥ threshold → `passed`
- actual ≥ threshold×(1-tolerance) → `passed_with_tolerance`
- actual < threshold×(1-tolerance) → `failed`

## 调试与错误处理

- **自定义规则**：`Skill(skill="task:verifier")` 传入custom_rules JSON
- **条件验证**：根据环境/配置调整验证标准
- **分阶段验证**：foundation(基本通过) → enhancement(覆盖≥90%) → refinement(质量+文档+性能)
- **调试模式**：开启debug时输出详细日志（Status/任务数/criteria通过数/Failures数量）
- **重试机制**：`verify_with_retry(tasks, max_retries=3)`，指数退避(`2^attempt`秒)
