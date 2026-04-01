---
description: Loop 验证流程 - 质量门控、持续改进决策
model: sonnet
context: fork
user-invocable: false
---

# Loop 验证流程

Loop Check阶段：调用verifier skill验证验收标准 → 质量门控评分 → 状态转换决策

## 验证流程

1. **调用verifier**：传入6个必传上下文字段，每次调用独立
   ```
   Skill(skill="task:verifier", args="执行结果验证：\n项目路径：{project_path}\n任务ID：{task_id}\n任务目标：{user_task}\n迭代：{iteration}\n计划文件：{plan_md_path}\n工作目录：{working_directory}")
   ```
   验证所有任务验收标准 + 回归测试
2. **深度校验**：Stage 1/2 通过后，执行 Stage 3 深度校验（用户预期验证+业务逻辑验证+交付物完整性验证），确保交付物从用户视角完全对齐
3. **更新计划状态**：`update_plan_frontmatter(status, completed_count)`
4. **同步任务状态文件**：更新 `.claude/tasks/{task_id}/status.json`
   - `status` → `"verifying"`
   - `phase` → `"verification"`
   - `updated_at` → 当前时间戳
   - `tasks[]` → 同步各子任务验证结果（passed/failed/suggestions + 证据摘要）
   - `quality_score` → 本轮验证评分
5. **质量评分**：加权计算综合分数

## 质量评分

| 维度 | 权重 |
|------|------|
| 功能完整性 | 25% |
| 测试覆盖率 | 20% |
| 用户预期符合度 | 15% |
| 性能指标 | 15% |
| 可维护性 | 10% |
| 安全性 | 10% |
| 最佳实践 | 5% |

质量阈值：迭代1→60分 | 迭代2→75分 | 迭代3→85分 | 迭代4+→90分

## 状态转换

| 条件 | 行为 |
|------|------|
| passed + 质量达标 | 全部完成 |
| suggestions | 自动继续优化 |
| failed | 失败调整(Adjustment) |
| 质量不达标 | 失败调整(Adjustment) |
| 深度校验失败 | 失败调整(Adjustment) |
| 深度校验suggestions | 自动继续优化 |

## 最佳实践

**必须**：全面验证所有验收标准 | 回归测试确认无破坏 | 立即报告具体失败原因 | 5 Why根因分析 | 渐进升级(retry→debug→replan→ask_user) | 深度校验不可跳过，即使Stage 1/2全部通过

**禁止**：接受模糊标准("代码质量好") | 忽略suggestions建议 | 跳过回归测试 | 失败时盲目重试所有任务 | 修改verifier返回的JSON结构 | 仅凭技术指标通过就跳过用户预期验证

## 验收标准要求

- **SMART原则**：具体/可度量/可达成/相关/有时限
- **可测试**：好="测试覆盖率≥90%"，差="覆盖率高"
- **独立**：每个标准可独立验证，不混合多个条件
- **结果导向**：好="用户可成功登录"，差="实现了登录函数"

## 常见陷阱

| 陷阱 | 表现 | 解决 |
|------|------|------|
| 忽略反馈 | 重复相同错误 | 分析根因+调整策略+记录教训 |
| 资源泄漏 | 临时文件未删 | try-finally确保清理 |
| 停滞检测失败 | 死循环重试 | 跟踪错误历史，3次相同→请求指导 |
| 忽略用户预期 | 技术正确但不符合用户意图 | Stage 3深度校验溯源用户原始需求 |
| 跳过深度校验 | 仅Stage 1/2通过就完成 | 强制执行三阶段完整验证链路 |
