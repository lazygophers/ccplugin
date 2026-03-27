# Planner 基础集成

## Loop集成

在Loop计划设计阶段调用：`Skill(skill="task:planner", args="设计执行计划：\n任务目标：{desc}\n当前迭代：{n}\n要求：1-7项标准要求")`

处理流程：questions→AskUserQuestion→validate_plan→tasks为空则完成→输出报告

## validate_plan 验证规则

| 检查项 | 规则 | 条件 |
|--------|------|------|
| 循环依赖 | DFS检测dependencies有向图回边 | 始终 |
| 并行度 | parallel_groups每组≤2个 | 始终 |
| agent字段 | 非空+含"（"中文注释 | tasks非空时 |
| skills字段 | 非空数组+每项含"（" | tasks非空时 |
| acceptance_criteria | 非空 | tasks非空时 |
| 结构化标准 | validate_structured_criterion | criterion为dict时 |

### validate_structured_criterion

必需字段：id + type + description + priority(required/recommended)

| type | 额外必需字段 | 验证 |
|------|------------|------|
| exact_match | verification_method(run_linter/run_tests/check_build) | 方法值有效性 |
| quantitative_threshold | metric + operator(>=,<=,>,<,==) + threshold | 运算符有效性+tolerance∈[0,1] |

## 结果处理

status≠completed→异常 → questions→询问用户 → tasks为空→完成 → validate_plan → 输出摘要(任务数/并行组/迭代目标)
