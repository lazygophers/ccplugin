
# PromptOptimization: Prompt Optimization

每次迭代前评估用户提示词质量，评分 <9 分时触发优化，确保用户输入清晰、完整、可执行。

## 执行流程

1. **质量评估**：`task:prompt-optimizer` 评估清晰度/完整性/可执行性(各10分，总30)
2. **结构化提问**(质量<24)：生成5W1H问题 → AskUserQuestion → 整合答案
3. **WebSearch**(质量<18)：搜索最新最佳实践 → 提取技术建议/陷阱/工具
4. **生成优化提示词**：`task:prompt-optimizer` 生成清晰目标+约束+验收标准(≤500字)
5. **用户交互选择**：展示原始提示词 vs 优化后提示词对比，由用户选择使用哪个版本

## 质量评估维度

| 维度 | 10分 | 4-6分 | 0-3分 |
|------|------|-------|-------|
| 清晰度 | 目标明确无歧义 | 模糊需澄清 | 无法理解 |
| 完整性 | 含所有信息(what/why/how) | 缺关键信息 | 严重不足 |
| 可执行性 | 直接执行无需额外 | 需补充才能执行 | 无法执行 |

## 5W1H提问

| 维度 | 关键问题 |
|------|---------|
| What | 具体功能/期望输出 |
| Why | 目的/解决什么问题 |
| Who | 目标用户/权限要求 |
| When | 截止时间/阶段目标 |
| Where | 涉及模块/部署环境 |
| How | 技术栈限制/性能要求 |

## 用户选择选项

通过 `AskUserQuestion` 向用户展示：
- 原始提示词
- 优化后的提示词
- 优化改进点列表（improvements）

用户可选择：

| 选项 | 描述 | 后续流程 |
|------|------|---------|
| **A: 使用原始提示词** | 保持用户原始输入不变 | 更新 `context.user_task = original_prompt` → DeepResearch/Planning |
| **B: 使用优化后提示词** | 应用 prompt-optimizer 的优化结果 | 更新 `context.user_task = optimized_prompt` → DeepResearch/Planning |
| **C: 重新优化** | 提供反馈后重新评估 | 收集反馈 → 回到质量评估（评分<9才重新优化） |

## 状态转换

- **选项A/B** → 复杂度评估（决定是否触发 DeepResearch，之后进入 Planning）
- **选项C** → 回到质量评估，评分<9才重新触发优化流程

## 提问机制

Agent（prompt-optimizer）不可直接向用户提问。正确路径：Agent 通过 `SendMessage(@main)` 将问题发给 main，由 main 执行 `AskUserQuestion` 向用户提问。

