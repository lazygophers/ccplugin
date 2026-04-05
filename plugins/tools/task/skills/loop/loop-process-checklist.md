# Loop 流程验证检查清单

本文档提供 8 个阶段的完整检查清单，用于验证 loop 执行过程是否符合规范。

## Initialization：初始化

| 检查点 | 验证方法 | 必须/可选 |
|-------|---------|----------|
| 状态变量已重置 | 确认 iteration=0, context 包含 replan_trigger/started_at/task_id | 必须 |
| 检测到重复任务时已询问用户 | 如果 task_id 重复，检查是否调用了 AskUserQuestion | 必须 |
| 输出初始化状态日志 | 验证输出包含 `[MindFlow·${task_id}·Initialization/0·进行中]` | 必须 |

## PromptOptimization：提示词优化（条件触发）

| 检查点 | 验证方法 | 必须/可选 |
|-------|---------|----------|
| 触发条件判定 | 首次迭代→必须执行；用户新输入→增量修订；无新输入→跳过 | 必须 |
| prompt.md 存在 | 验证 `.lazygophers/tasks/{task_id}/prompt.md` 文件存在（首次生成或已有） | 必须 |
| 验收标准可验证 | prompt.md 中每条验收标准可独立验证、可量化 | 必须 |
| 用户确认已执行 | 首次/增量修订时验证用户选择 A/B/C/D，header 包含 `[MindFlow·${task_id}·提示词确认]` | 条件必须 |
| 增量修订保留未变更内容 | 非首次修订时验证未变更部分保持不变 | 条件必须 |

## DeepResearch：深度研究（可选）

| 检查点 | 验证方法 | 必须/可选 |
|-------|---------|----------|
| 触发条件检查 | 验证复杂度>8 或 失败2次 的触发逻辑 | 可选 |
| 用户确认机制 | 如果触发，检查是否询问用户 | 可选 |
| 调用 deep-research | 检查是否调用了 `Skill(skill="deepresearch:deep-research")` | 可选 |
| 研究结果已整合 | 验证研究结果是否用于后续计划设计 | 可选 |

## Planning：计划设计与确认

| 检查点 | 验证方法                                                                                              | 必须/可选 |
|-------|---------------------------------------------------------------------------------------------------|----------|
| **Planner 内部流程完整性** | **grep -c "三层上下文学习" <agent输出>**                                                                   | **必须** |
| L1 - 项目全局理解 | 验证是否读取了 README.md、CLAUDE.md                                                           | 必须 |
| L2 - 规范和记忆 | 验证是否读取了项目记忆                                                                                       | 必须 |
| L3 - 目标相关文件 | 验证是否使用 Glob/Grep 定位并读取相关文件                                                                        | 必须 |
| **原子拆分验证** | **每个任务的files数组长度≤1（单文件单任务）**                                                                      | **必须** |
| **上下文完整性** | **Skill/Agent调用包含6个必传字段（project_path/task_id/iteration/plan_md_path/working_directory/user_task）** | **必须** |
| **Planner 调用** | **检查是否调用了 `Skill(skill="task:planner")`（planner 内部完成：设计+写文件+用户确认）**                               | **必须** |
| Planner 返回 status | 验证 status 为 confirmed/rejected/no_tasks/cancelled 之一                                              | 必须 |
| 计划文件已生成 | 验证 planner 返回的 plan_md_path 文件存在：`ls .lazygophers/tasks/{task_id}/plan.md`                        | 必须 |
| 计划文件使用中文文件名 | 验证文件名包含中文关键词                                                                                      | 必须 |
| 用户确认已在 planner 内完成 | planner 返回 confirmed（已批准）或 rejected（已拒绝并带 user_feedback）                                          | 必须 |
| 后置验证点通过 | 验证 plan_md_path 已设置且文件存在                                                                          | 必须 |

## Execution：任务执行

| 检查点 | 验证方法 | 必须/可选 |
|-------|---------|----------|
| 前置条件检查 | 验证计划文件存在且已获得批准 | 必须 |
| 读取计划文件 | 检查是否从 plan_md_path 读取任务列表 | 必须 |
| **上下文字段传递** | **Skill/Agent调用args/prompt包含project_path和task_id** | **必须** |
| **使用 Skill 工具执行** | **grep "Skill(" <执行日志> \| grep -v "Edit\|Write\|Bash"** | **必须** |
| 禁止直接使用工具 | 验证没有直接调用 Edit/Write/Bash（除 Skill 内部） | 必须 |
| 任务状态更新 | 验证计划文件中任务状态从 📋 → ✅/❌ | 必须 |
| **执行完整性检查** | **每个任务执行后验证文件已创建/修改、验收标准有证据** | **必须** |
| 未完成自动继续 | 检查 incomplete 任务是否触发重试（最多2次） | 必须 |
| 后置验证点通过 | 验证所有任务已执行完成 | 必须 |

## Verification：结果验证

| 检查点 | 验证方法 | 必须/可选 |
|-------|---------|----------|
| 前置条件检查 | 验证所有任务已执行完成（状态为 ✅ 或 ❌） | 必须 |
| **Verifier 调用** | **检查是否调用了 `Skill(skill="task:verifier")`** | **必须** |
| 跳过检测机制生效 | 如果未调用 verifier，检查是否触发错误 | 必须 |
| 状态日志输出 | 验证输出包含 `[MindFlow·${task_id}·Verification/N·{passed或failed}]` | 必须 |
| 计划文件 frontmatter 更新 | 验证status/completed_count 已更新 | 必须 |
| 后置验证点通过 | 验证 verifier 已被调用并返回结果 | 必须 |

## Adjustment：失败调整（如需）

| 检查点 | 验证方法 | 必须/可选 |
|-------|---------|----------|
| Adjuster 调用 | 检查是否调用了 `Skill(skill="task:adjuster")` | 必须 |
| 策略选择正确 | 验证返回的 strategy 符合失败场景 | 必须 |
| 状态转换正确 | 验证根据 strategy 正确跳转到下一阶段 | 必须 |

## Cleanup：完成清理（loop 自身执行）

| 检查点 | 验证方法 | 必须/可选 |
|-------|---------|----------|
| 前置条件检查 | 验证验证通过或用户确认完成 | 必须 |
| **metadata.json 更新** | **phase 为 completed/failed** | **必须** |
| **index.json 更新** | **Bash+jq 命令更新为终态** | **必须** |
| 即使失败也执行 | 验证失败场景下 Cleanup 也执行 | 必须 |
| 检查点已清理 | 验证 `cleanup_checkpoint()` 已调用 | 必须 |
| 执行记忆已保存 | 验证记忆 URI 存在 | 必须 |
| 最终报告已输出 | 验证最终报告包含状态/迭代/时长 | 必须 |

## Cleanup 补充：微回顾

| 检查点 | 验证方法 | 必须/可选 |
|-------|---------|----------|
| 微回顾已执行 | 验证输出包含 `[MindFlow·${task_id}·微回顾]` | 必须 |
| 回顾内容完整 | 包含"有效实践"、"需改进"、"下次注意"三个维度 | 必须 |
| 回顾结果已保存 | 情节记忆包含 `retrospective` 字段 | 必须 |

## 快速验证命令

```bash
# 检查 planner 是否完成三层上下文学习
grep -i "README\|CLAUDE.md\|package.json" <planner输出>

# 检查是否使用 Agent 工具执行任务
grep "Agent(subagent_type=" <执行日志>

# 检查 verifier 是否被调用
grep "Agent(subagent_type=\"task:verifier\")" <loop输出>

# 检查 metadata.json 是否更新为终态
jq '.phase' .lazygophers/tasks/*/metadata.json

# 检查原子拆分（每个任务files≤1个）
grep -A2 '"files"' <计划JSON> | grep -c ',' # 应为0

# 检查上下文字段传递
grep -c 'project_path\|task_id' <Skill调用> # 应≥2（每个调用至少包含这两个字段）

# 检查强制性关键词出现次数
grep -E "必须|MUST|强制|禁止" <文档> | wc -l
```

**注**：违规检测与处理详见 SKILL.md §流程违规检测与处理。
