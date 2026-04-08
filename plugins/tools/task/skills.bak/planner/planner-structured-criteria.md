# Planner 结构化验收标准

## 三种格式（向后兼容）

| 格式 | 示例 |
|------|------|
| 字符串(旧) | `["覆盖率≥90%", "Lint 0错误"]` |
| 结构化(新) | `[{id, type, description, metric, operator, threshold, tolerance, priority}]` |
| 混合 | 同一数组中字符串和对象共存 |

## 评估方法

### exact_match（精确匹配）

必需：id + type="exact_match" + description + verification_method(run_linter/run_tests/check_build) + priority(required/recommended)
可选：expected_value(默认0)
适用：测试通过/lint 0错误/构建成功等二元判定

### quantitative_threshold（量化阈值）

必需：id + type="quantitative_threshold" + description + metric + operator(>=,<=,>,<,==) + threshold + priority
可选：unit(percentage/ms/MB) + tolerance(相对值,如0.02=±2%)
适用：覆盖率/响应时间/内存使用/圈复杂度

容差说明：threshold=0.9, tolerance=0.02 → [0.882, 0.918]范围内视为通过

## 验证规则

字符串格式：必须含量化词(contains_quantifier)
结构化格式：必需字段(id/type/description/priority) + priority∈{required,recommended} + 类型特定字段验证 + operator有效性
