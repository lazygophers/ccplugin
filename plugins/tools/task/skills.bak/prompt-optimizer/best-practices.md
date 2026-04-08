# 规格说明设计最佳实践

## 核心理念

提示词优化的本质是**规格说明设计**（Spec Writing），不是"写更长的提示词"。目标是生成一份让后续 Planning/Execution/Verification 都能精确对照的可执行文档。

> "The most durable, high-leverage skill is task deconstruction and boundary definition: explicitly define the deliverable, provide the minimum viable context, and set clear guardrails."
> — Prompt Engineering: Task Deconstruction & Boundary Definition (2025)

## 三要素模型（Deliverable-Context-Guardrails）

| 要素 | 核心问题 | 输出内容 | 缺失后果 |
|------|---------|---------|---------|
| **Deliverable** | 做什么？做到什么程度？ | 目标描述 + 验收标准 | Verification 无判定依据 |
| **Context** | 技术背景、约束、依赖 | 技术上下文 | Planning 选错方案 |
| **Guardrails** | 什么不做？什么不能碰？ | in-scope / out-of-scope | 范围蔓延 |

## 验收标准设计

验收标准直接决定迭代是否继续——是 prompt.md 中最重要的部分。

**SMART-V 原则**（在 SMART 基础上增加 Verifiable）：

| 原则 | 含义 | 好 | 差 |
|------|------|---|---|
| Specific | 具体到单一判定点 | "登录成功后跳转到 /dashboard" | "登录正常" |
| Measurable | 有数值或明确条件 | "响应 P95 < 200ms" | "响应快" |
| Achievable | 当前迭代可完成 | "核心 API 3 个端点" | "完整微服务体系" |
| Relevant | 与交付物直接相关 | "JWT token 含 userId 和 exp" | "代码风格统一" |
| Time-bound | 本次迭代范围内 | 隐含于 in-scope 定义 | 无边界 |
| **Verifiable** | 可通过代码/测试/文件检查验证 | "运行 pytest 全部通过" | "质量好" |

## 澄清对话策略

**优先级排序**（高→低）：What → Where → How → Why → When → Who

| 场景 | 提问 | 不提问 |
|------|------|--------|
| 交付物模糊 | "你期望产出代码还是文档？" | 可从上下文推断时 |
| 多种实现路径 | "偏向 A 方案还是 B 方案？" | 只有一种合理选择时 |
| 边界不清 | "这个变更只涉及后端还是前后端都改？" | 代码探索可确认时 |

**规则**：每次一个问题 + 2-3 建议选项 | 最多 3 轮 | 不累积问题

## 增量修订策略

非首次迭代、用户有新输入时，不重写整个 prompt.md，而是：

1. **读取**已有 prompt.md
2. **识别**用户新输入影响的部分（边界变更？验收标准调整？技术约束变化？）
3. **局部更新**受影响的节，保留其余内容不变
4. **更新** iteration 字段和 revision_delta

## prompt.md 模板

```markdown
---
task_id: ${task_id}
iteration: ${iteration}
created_at: ISO8601
---

## 目标
[具体动词] + [精确对象] + [可观察结果]

## 边界
### In-scope
- [本次要做的事项]

### Out-of-scope
- [明确不做的事项]

## 技术上下文
- [项目类型/技术栈/当前状态/相关依赖]

## 验收标准
- [ ] [可独立验证的条件 1]
- [ ] [可独立验证的条件 2]
- [ ] [可独立验证的条件 3]
```

## 反模式

| 反模式 | 表现 | 修正 |
|--------|------|------|
| 模糊验收 | "代码质量好" | 拆分为可量化指标 |
| 范围蔓延 | 未定义 out-of-scope | 明确列出不做的事 |
| 过度复杂 | 30+ 验收标准 | 拆分为多个子任务 |
| 实现导向 | "用 Redis 缓存" | "查询响应 < 100ms"（结果导向） |
| 假设意图 | 自行决定技术方案 | 提问确认 |

## 参考来源

- [Anthropic Prompting Best Practices (Claude 4.x)](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/claude-4-best-practices)
- [Prompt Engineering: Task Deconstruction & Boundary Definition](https://www.xugj520.cn/en/archives/prompt-engineering-task-deconstruction.html)
- [The Prompt Report: A Systematic Survey (arXiv 2406.06608)](https://arxiv.org/abs/2406.06608)
- [A Systematic Survey of Automatic Prompt Optimization (EMNLP 2025)](https://arxiv.org/abs/2502.16923)
- [Lakera: The Ultimate Guide to Prompt Engineering 2026](https://www.lakera.ai/blog/prompt-engineering-guide)
