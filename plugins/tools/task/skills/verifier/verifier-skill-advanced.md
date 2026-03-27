# Verifier 高级功能 - 结构化验收标准验证

## 支持格式

| 格式 | 示例 | 验证方式 |
|------|------|---------|
| 字符串(旧) | `"覆盖率≥90%"` | 原有逻辑 |
| 结构化(新) | `{id,type,description,metric,operator,threshold,tolerance,priority}` | 专用验证 |

## 验证类型

### exact_match（精确匹配）

必需字段：verification_method(run_linter/run_tests/check_build) + expected_value(默认0)
验证：actual_value == expected_value → passed/failed

### quantitative_threshold（量化阈值）

必需字段：metric + operator(>=,<=,>,<,==) + threshold
可选：tolerance(相对容差,0-1) + unit

验证逻辑(以>=为例)：actual≥threshold→passed | actual≥threshold×(1-tolerance)→passed_with_tolerance | 否则→failed

## 度量提取

| metric | 提取函数 |
|--------|---------|
| test_coverage | parse_coverage_report |
| response_time | parse_response_time |
| error_count | count_errors |

## 容差指南

适用：测试覆盖率/性能指标/资源使用（允许小幅波动）
不适用：lint错误数(必须0)/构建状态(必须成功)/布尔判断
