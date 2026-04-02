# Verifier 核心功能与检查清单

## 适用场景

Loop Check阶段：系统验证任务完成情况和质量标准，检查验收标准/交付物完整性/回归测试/迭代目标。

## 核心原则

- **可测试**：客观可验证，无主观判断
- **可度量**：数值指标(≥90%, <200ms)
- **独立**：每个标准可独立验证
- **结果导向**：验证用户体验而非技术步骤
- **避免绝对**：不用all/always/never

## 执行流程

1. **调用verifier**：`Skill(skill="task:verifier")` 要求：获取任务状态/系统验证/回归测试/报告≤100字/决定状态
2. **深度校验**：Stage 1/2通过后，执行Stage 3深度校验（用户预期+业务逻辑+交付物完整性），详见 [deep-validation-checklist.md](deep-validation-checklist.md)
3. **处理结果**：passed→退出Loop | suggestions→询问用户 | failed→失败调整
4. **输出报告**：`[MindFlow·{task}·结果验证/{N}·{status}]` + summary统计

## 输出字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| status | string | 必填 | passed/suggestions/failed |
| report | string | 必填 | ≤100字 |
| verified_tasks | array | 必填 | `{task_id, task_name, status, criteria_passed, criteria_total, notes?}` |
| summary | object | 必填 | 统计摘要 |
| suggestions | array | 可选 | 优化建议(suggestions状态) |
| failures | array | 可选 | 失败详情(failed状态) |

## 结构化验收标准验证

| 格式 | 示例 | 验证方式 |
|------|------|---------|
| 字符串(旧) | `"覆盖率≥90%"` | 原有逻辑 |
| 结构化(新) | `{id,type,description,metric,operator,threshold,tolerance,priority}` | 专用验证 |

### exact_match（精确匹配）

必需字段：verification_method(run_linter/run_tests/check_build) + expected_value(默认0)
验证：actual_value == expected_value → passed/failed

### quantitative_threshold（量化阈值）

必需字段：metric + operator(>=,<=,>,<,==) + threshold
可选：tolerance(相对容差,0-1) + unit

验证逻辑(以>=为例)：actual≥threshold→passed | actual≥threshold×(1-tolerance)→passed_with_tolerance | 否则→failed

### 容差指南

适用：测试覆盖率/性能指标/资源使用（允许小幅波动）
不适用：lint错误数(必须0)/构建状态(必须成功)/布尔判断

## 验证检查清单

### 验证前

| 检查项 | 要求 |
|--------|------|
| 任务完成性 | 所有任务 completed、无遗漏、有验收标准、依赖已满足 |
| 验收标准 | 可量化可验证、避免绝对词汇(all/always/never)、符合 SMART |
| 结构化标准 | 必需字段(id/type/description/priority)完整、type特定字段匹配 |
| 环境工具 | 测试环境就绪、工具可用、服务已启动、CI/CD正常 |

### 验证中

| 维度 | 检查项 |
|------|--------|
| 功能 | 核心功能实现、符合需求规格、边界条件正确、异常处理完善 |
| 测试 | 单元覆盖率≥90%、集成测试覆盖关键路径、边界测试+异常测试完整 |
| 代码质量 | Lint 0错误0警告、格式规范、圈复杂度<10 |
| 性能 | 响应时间达标、无内存泄漏、并发性能达标 |
| 安全 | 输入验证、XSS/SQL注入防护、权限检查、敏感数据加密 |

### 验证后

| 检查项 | 要求 |
|--------|------|
| status字段 | passed/suggestions/failed 三选一 |
| report字段 | ≤100字，简洁明了 |
| verified_tasks | 列表完整，覆盖所有任务 |
| 状态处理 | passed→退出, suggestions→询问用户, failed→调整流程 |
| 回归测试 | 完整套件运行，无新增失败 |

## Do's / Don'ts

| 必须 | 禁止 |
|------|------|
| 正确调用：`Skill(skill="task:verifier")` | 接受模糊标准("代码质量好") |
| 处理所有三种状态 | 忽略suggestions直接退出 |
| 验证所有任务不遗漏 | 跳过回归测试 |
| suggestions必须询问用户 | 修改verifier返回的JSON |

## 验收标准最佳实践

| 原则 | 好 | 差 |
|------|---|---|
| 可测试 | "所有单元测试通过" | "功能运行正常" |
| 可度量 | "覆盖率≥90%" | "覆盖率高" |
| 独立 | 每条可独立验证 | "测试通过且质量好" |
| 结果导向 | "用户可成功登录" | "实现了登录函数" |
