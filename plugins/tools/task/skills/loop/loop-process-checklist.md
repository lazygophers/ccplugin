# Loop 流程验证检查清单

本文档提供 8 个阶段的完整检查清单，用于验证 loop 执行过程是否符合规范。

## 阶段1：初始化

| 检查点 | 验证方法 | 必须/可选 |
|-------|---------|----------|
| 状态变量已重置 | 确认 iteration=0, context 包含 replan_trigger/start_time/task_id | 必须 |
| 检测到重复任务时已询问用户 | 如果 task_id 重复，检查是否调用了 AskUserQuestion | 必须 |
| 输出初始化状态日志 | 验证输出包含 `[MindFlow·任务·初始化/0·进行中]` | 必须 |

## 阶段2：提示词优化（可选）

| 检查点 | 验证方法 | 必须/可选 |
|-------|---------|----------|
| 复杂度评估正确 | 如果任务复杂度<8，跳过；≥8则触发 | 可选 |
| 调用 prompt-optimizer | 检查是否调用了 `Skill(skill="task:prompt-optimizer")` | 可选 |
| 优化后的提示词已应用 | 验证后续计划设计使用优化后的提示词 | 可选 |

## 阶段3：深度研究（可选）

| 检查点 | 验证方法 | 必须/可选 |
|-------|---------|----------|
| 触发条件检查 | 验证复杂度>8 或 失败2次 的触发逻辑 | 可选 |
| 用户确认机制 | 如果触发，检查是否询问用户 | 可选 |
| 调用 deep-research | 检查是否调用了 `Skill(skill="deepresearch:deep-research")` | 可选 |
| 研究结果已整合 | 验证研究结果是否用于后续计划设计 | 可选 |

## 阶段4：计划设计与确认

| 检查点 | 验证方法 | 必须/可选 |
|-------|---------|----------|
| **Planner 内部流程完整性** | **grep -c "三层上下文学习" <agent输出>** | **必须** |
| L1 - 项目全局理解 | 验证是否读取了 README.md/CLAUDE.md/package.json | 必须 |
| L2 - 规范和记忆 | 验证是否检查了 `.claude/rules/` 和项目记忆 | 必须 |
| L3 - 目标相关文件 | 验证是否使用 Glob/Grep 定位并读取相关文件 | 必须 |
| **原子拆分验证** | **每个任务的files数组长度≤1（单文件单任务）** | **必须** |
| **上下文完整性** | **Skill/Agent调用包含6个必传字段（project_path/task_id/iteration/plan_md_path/working_directory/user_task）** | **必须** |
| **Planner 调用** | **检查是否调用了 `Skill(skill="task:planner")`（planner 内部完成：设计+写文件+用户确认）** | **必须** |
| Planner 返回 status | 验证 status 为 confirmed/rejected/no_tasks/cancelled 之一 | 必须 |
| 计划文件已生成 | 验证 planner 返回的 plan_md_path 文件存在：`ls .claude/plans/*.md` | 必须 |
| 计划文件使用中文文件名 | 验证文件名包含中文关键词 | 必须 |
| 用户确认已在 planner 内完成 | planner 返回 confirmed（已批准）或 rejected（已拒绝并带 user_feedback）| 必须 |
| 后置验证点通过 | 验证 plan_md_path 已设置且文件存在 | 必须 |

## 阶段5：任务执行

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

## 阶段6：结果验证

| 检查点 | 验证方法 | 必须/可选 |
|-------|---------|----------|
| 前置条件检查 | 验证所有任务已执行完成（状态为 ✅ 或 ❌） | 必须 |
| **Verifier 调用** | **检查是否调用了 `Skill(skill="task:verifier")`** | **必须** |
| 跳过检测机制生效 | 如果未调用 verifier，检查是否触发错误 | 必须 |
| 状态日志输出 | 验证输出包含 `[MindFlow·任务·结果验证/N·{status}]` | 必须 |
| 计划文件 frontmatter 更新 | 验证status/completed_count 已更新 | 必须 |
| 后置验证点通过 | 验证 verifier 已被调用并返回结果 | 必须 |

## 阶段7：失败调整（如需）

| 检查点 | 验证方法 | 必须/可选 |
|-------|---------|----------|
| Adjuster 调用 | 检查是否调用了 `Skill(skill="task:adjuster")` | 必须 |
| 策略选择正确 | 验证返回的 strategy 符合失败场景 | 必须 |
| 状态转换正确 | 验证根据 strategy 正确跳转到下一阶段 | 必须 |

## 阶段8：完成清理

| 检查点 | 验证方法 | 必须/可选 |
|-------|---------|----------|
| 前置条件检查 | 验证验证通过或用户确认完成 | 必须 |
| **任务状态文件更新** | **`.claude/task/{task_id}.json` status 为 completed/failed（必须在 finalizer 之前）** | **必须** |
| **Finalizer 调用** | **检查是否调用了 `Skill(skill="task:finalizer")`** | **必须** |
| 即使失败也执行清理 | 验证失败场景下 finalizer 也被调用 | 必须 |
| 计划文件已删除 | 验证文件已删除：`! test -f .claude/plans/*.md` | 必须 |
| 检查点已清理 | 验证检查点文件已删除 | 必须 |
| 执行记忆已保存 | 验证记忆 URI 存在 | 必须 |
| 资源泄漏警告生效 | 如果跳过 finalizer，检查是否显示警告 | 必须 |
| 后置验证点通过 | 验证所有清理操作已完成 | 必须 |

## 阶段8补充：微回顾

| 检查点 | 验证方法 | 必须/可选 |
|-------|---------|----------|
| 微回顾已执行 | 验证输出包含 `[MindFlow·${task_id}·微回顾]` | 必须 |
| 回顾内容完整 | 包含"有效实践"、"需改进"、"下次注意"三个维度 | 必须 |
| 回顾结果已保存 | 情节记忆包含 `retrospective` 字段 | 必须 |

## 全局检查项

| 检查点 | 验证方法 | 必须/可选 |
|-------|---------|----------|
| 所有输出以 [MindFlow] 开头 | 验证所有输出行都符合格式要求 | 必须 |
| 状态追踪日志完整 | 验证每个阶段都有对应的状态日志 | 必须 |
| 铁律严格遵守 | 验证 4 个铁律步骤都已执行 | 必须 |
| 违规日志记录 | 如果存在违规，验证是否记录到短期记忆 | 必须 |
| **Reflection 自检已执行** | **验证每个阶段完成后有 Reflection 检查（无违规时无输出为正常）** | **必须** |
| **成本预算未超限** | **验证未触发熔断（Circuit Break），或触发后正确进入 Phase 8** | **必须** |
| **残留计划文件已清理** | **Phase 1 初始化时检测并清理前次遗留的 .claude/plans/*.md** | **必须** |

## 快速验证命令

```bash
# 检查 planner 是否完成三层上下文学习
grep -i "README\|CLAUDE.md\|package.json" <planner输出>

# 检查是否使用 Skill 工具执行任务
grep "Skill(skill=" <执行日志> | grep -v "planner\|formatter\|verifier\|adjuster\|finalizer"

# 检查 verifier 是否被调用
grep "Skill(skill=\"task:verifier\")" <loop输出>

# 检查 finalizer 是否被调用
grep "Skill(skill=\"task:finalizer\")" <loop输出>

# 检查计划文件是否清理
! test -f .claude/plans/*.md && echo "已清理" || echo "未清理"

# 检查原子拆分（每个任务files≤1个）
grep -A2 '"files"' <计划JSON> | grep -c ',' # 应为0

# 检查上下文字段传递
grep -c 'project_path\|task_id' <Skill调用> # 应≥2（每个调用至少包含这两个字段）

# 检查强制性关键词出现次数
grep -E "必须|MUST|强制|禁止" <文档> | wc -l
```

## 违规场景示例

### 场景1：跳过三层上下文学习

**违规表现**：planner 直接开始任务分解，未读取 README.md 等文件

**检测方法**：`grep -c "Read(" <planner输出> < 3`

**后果**：计划可能不符合项目规范，任务分解不准确

### 场景2：直接使用 Edit 工具

**违规表现**：loop 在任务执行阶段直接调用 `Edit()` 修改文件

**检测方法**：`grep "Edit(" <loop输出> | grep -v "Skill("`

**后果**：bypassed agent logic，验证阶段会报告流程违规

### 场景3：跳过 Verifier

**违规表现**：任务执行完成后直接进入完成清理，未调用 verifier

**检测方法**：`grep "Skill(skill=\"task:verifier\")" <loop输出> || echo "违规"`

**后果**：无法确保任务质量，可能遗漏错误

### 场景4：跳过 Finalizer

**违规表现**：loop 结束但未调用 finalizer

**检测方法**：`test -f .claude/plans/*.md && echo "计划文件未清理"`

**后果**：资源泄漏（计划文件残留、后台任务未终止、检查点未清理）

## 使用指南

1. **执行前检查**：使用本检查清单规划 loop 执行步骤
2. **执行中监控**：对照检查清单验证每个阶段是否符合规范
3. **执行后审计**：使用快速验证命令批量检查流程完整性
4. **违规处理**：发现违规时，参考违规场景示例确定严重程度和处理策略
