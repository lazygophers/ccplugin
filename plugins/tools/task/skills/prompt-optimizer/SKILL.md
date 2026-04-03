---
description: "提示词优化 - 分析任务边界和范围、结构化提问澄清需求、生成明确可执行的提示词并持久化存储"
model: sonnet
context: fork
user-invocable: false
agent: task:prompt-optimizer
---


# Skills(task:prompt-optimizer) - 提示词优化规范

## 范围

分析和优化用户任务描述。适用于：模糊需求("优化代码")、缺乏目标("添加功能")、隐含假设过多、Loop 提示词优化阶段。**每次迭代必须执行**，不可跳过。

## 核心原则（Anthropic 2025）

| 原则 | 好 | 差 |
|------|---|---|
| 明确性 | "实现JWT认证，含token生成和验证" | "处理认证" |
| 上下文 | "在Express.js API v4.18中添加认证中间件" | "添加认证" |
| 范围边界 | "包含：邮箱登录。不包含：社交登录" | "实现登录" |
| 可量化 | "覆盖率≥90%，响应<200ms" | "质量要好" |
| 结构化输出 | "返回JSON {token, user, expiresAt}" | "返回信息" |
| 错误处理 | "密码错误401，锁定403，服务错误500" | "处理错误" |

## 执行流程

### BoundaryAnalysis：任务边界分析

分析用户原始提示词，输出以下四项：
1. **任务边界**：in-scope（本次要做的）/ out-of-scope（明确不做的）
2. **任务范围**：涉及的模块、文件、功能区域
3. **交付物定义**：最终应产出什么
4. **验收标准草案**：可量化的完成标准

### StructuredQuestioning：结构化提问

针对边界/范围中的模糊点，使用 5W1H 框架提问：

| 维度 | 关键问题 |
|------|---------|
| What(目标) | 功能/交付物/成功标准 |
| Why(动机) | 业务问题/价值 |
| Who(受众) | 目标用户/体验要求 |
| When(时间) | 完成时间/优先级/里程碑 |
| Where(范围) | 影响模块/部署环境/交互组件 |
| How(方式) | 技术方案/栈/架构模式 |

不主动执行 WebSearch，仅在用户明确要求搜索时才执行。

### PromptGeneration：生成优化提示词

生成结构化提示词（≤500字），必须包含：
- 明确目标
- 任务边界（in-scope / out-of-scope）
- 技术约束
- 验收标准（可量化）

## 调用

`Skill(skill="task:prompt-optimizer", args="优化用户提示词：\n原始提示：{input}\ntask_id：{task_id}\n项目路径：{project_path}")`

结果处理：status=optimized → 写入 prompt.md，展示给用户确认

## 输出格式

JSON：`{status, quality_score{clarity,completeness,actionability,overall}, original_prompt, optimized_prompt, boundary{in_scope[], out_of_scope[]}, scope[], deliverables[], acceptance_criteria[], improvements[], questions_asked, report}`

- `status`: 固定为 `"optimized"`（每次都执行优化）
- `boundary`: 任务边界（in_scope + out_of_scope 数组）
- `scope`: 涉及的模块/文件/区域
- `deliverables`: 交付物定义
- `acceptance_criteria`: 验收标准

