---
description: 计划设计规范 - 收集项目信息、任务分解、依赖建模、agents/skills 分配的执行规范
model: opus
context: fork
user-invocable: false
---

<!-- STATIC_CONTENT: Cacheable (6000+ tokens) -->

# Skills(task:planner) - 计划设计规范

<scope>

当你需要为复杂任务设计执行计划时使用此 skill。适用于深入分析项目结构和技术栈、将复杂任务分解为可执行的子任务、建立任务依赖关系和并行执行策略、为每个任务分配合适的 Agent 和 Skills，以及 Loop 命令的计划设计（Planning / Plan）阶段。

</scope>

<core_principles>

MECE 分解原则要求子任务之间相互独立（Mutually Exclusive，无文件冲突，可独立执行）且完全穷尽（Collectively Exhaustive，覆盖所有必要工作，无遗漏）。

质量标准包括四个方面：可交付原子化（每个任务必须产生可验证的交付物）、可量化可验证（每个任务必须有明确的、可量化的验收标准）、依赖闭环（任务之间的依赖关系必须形成有向无环图 DAG）、幂等性设计（任务应设计为可安全重复执行，多次执行产生相同结果，支持失败后重试不产生副作用）。

</core_principles>

<red_flags>

| AI Rationalization | Reality Check |
|-------------------|---------------|
| "任务分解已经足够细粒度了" | MECE 原则要求子任务完全独立，操作同一文件即违反，必须检查文件交集 |
| "验收标准是定性的就可以了" | 验收标准必须可量化可验证，"代码改进"不行，"测试覆盖率≥90%"才行 |
| "没有循环依赖就是合理的计划" | 还需验证：并行度≤2、依赖形成DAG、无遗漏任务、agent带中文注释 |
| "这个任务太小，不用拆分了" | 原子性要求每个任务有可交付物和验收标准，"太小"的任务也必须符合 |
| "用户没提出问题就可以跳过确认" | planner 返回的 questions 字段必须处理，不确认等于计划可能被错误执行 |
| "5个并行任务可以分两批执行" | 并行度硬性限制≤2，必须严格遵守，即使有不同的agent也要串行 |
| "已有中文注释，可以省略 depth:1 验证" | 中文注释不等于结构化，必须用 depth:1 检查 agent/skills 是否都带注释 |
| "没有用到 Mermaid 就不用画状态图" | Mermaid 是输出规范的一部分，复杂计划（>5个任务）必须生成 |
| "agent 是可选的，有些任务不需要" | agent 和 skills 在 tasks 不为空时是强制字段，缺失会导致调度失败 |
| "skills 可以留空，让系统自动推断" | skills 必须显式指定，空数组会触发验证错误 |
| "来源必须是 task 插件" | agent/skills 可来自任何插件或项目自定义，来源灵活 |

</red_flags>

<execution_workflow>

## Planner 内部执行流程（强制遵守）

**必须按顺序执行以下 4 个阶段，禁止跳过任何步骤**：

### 阶段1：三层上下文学习（前置条件）

**强制要求**：必须完成三层上下文学习才可进入计划设计。未完成则暂停，请求补充信息。

1. **L1 - 项目全局理解**：读取 README.md、CLAUDE.md、package.json/pyproject.toml，理解项目架构和技术栈
2. **L2 - 规范和记忆**：检查 `.claude/rules/`、项目记忆（如有），理解项目约束和历史决策
3. **L3 - 目标相关文件**：基于任务目标，读取相关源代码文件（使用 Glob/Grep 定位）

**验证点**：确认已获取足够的项目上下文信息，能够准确理解任务需求和技术约束。

### 阶段2：信息收集（MECE准备）

**强制要求**：收集计划设计所需的所有信息维度。

1. **目标澄清**：用户期望的交付物是什么？
2. **依赖识别**：需要哪些技术栈、库、工具？
3. **现状评估**：相关功能是否已存在？
4. **边界确认**：不在范围内的是什么？

**验证点**：四个维度都有明确答案，无模糊或缺失信息。如有疑问，必须通过 `questions` 字段询问用户。

### 阶段3：计划设计（MECE分解 + DAG依赖）

**强制要求**：应用 MECE 原则分解任务，建立 DAG 依赖关系。

1. **MECE 分解**：子任务完全独立（无文件冲突）且穷尽（无遗漏）
2. **原子性检查**：每个任务有可验证的交付物
3. **依赖建模**：构建 DAG，验证无循环依赖
4. **并行度控制**：并行组数量 ≤ 2
5. **Agent/Skills 分配**：为每个任务分配 agent（单个）+ skills（≥1个），带中文注释
6. **验收标准**：为每个任务设计可量化的验收标准

**验证点**：DAG 合法、并行度≤2、所有任务有 agent/skills/acceptance_criteria。

### 阶段4：输出验证（质量门控）

**强制要求**：验证输出JSON符合格式要求，检查字段完整性。

1. **格式验证**：JSON 结构正确，必填字段齐全
2. **依赖验证**：dependencies 引用的任务ID都存在
3. **并行组验证**：parallel_groups 引用的任务ID都存在，每组≤2个任务
4. **中文注释验证**：所有 agent/skills 都带中文注释 "（注释）"
5. **验收标准验证**：每个任务的 acceptance_criteria 数组非空

**验证点**：所有验证通过，输出符合规范，可安全交付给 loop。

</execution_workflow>

<invocation>

调用：`Agent(agent="task:planner", prompt="设计执行计划：\n任务目标：{desc}\n要求：1.分析项目结构 2.收集目标/依赖/现状/边界 3.MECE分解 4.DAG依赖 5.分配Agent+Skills(带中文注释) 6.可量化验收标准 7.报告≤200字\n功能已存在则返回空tasks。")`

**结果处理**：检查 status=completed → 处理 questions(有则询问用户) → tasks为空则直接结束 → validate_plan

**计划验证**：无循环依赖 + 并行组≤2个 + Agent/Skills带中文注释"（" + 每个task有acceptance_criteria

</invocation>

<mermaid_generation_rules>

Mermaid stateDiagram 规则：单行文本（禁止`\n`）、标签≤15字符（仅ID+名称）、详情放表格不放图中、节点≤12个。格式：`state "T1: 需求分析" as T1`

</mermaid_generation_rules>

<output_format>

JSON 输出：`{status, report(≤200字), tasks[], dependencies{}, parallel_groups[[]], iteration_goal, acceptance_criteria[], questions?[]}`

- `status`: "completed" 或 "questions"
- `tasks`: 任务数组（功能已存在时返回空数组`[]`）
- 每个 task 必含字段：
  - `id`: 任务ID
  - `description`: 任务描述
  - `agent`（单个，必填）: `"name（中文注释）@source"`，执行该任务的 agent 名称，执行阶段动态获取
  - `skills`（数组，必填，≥1个）: `["name（注释）@source"]`，该任务使用的 skills，执行阶段动态获取
  - `files`（数组，可选）: 关联文件/模块列表
  - `acceptance_criteria`（数组，必填）: 验收清单（check list），可量化
  - `dependencies`（数组）: 前置任务ID列表
- tasks 为空时 agent/skills 可省略，非空时必填

**重要**：agent/skills 在规划阶段只是名称引用，实际加载和调用在执行阶段进行（loop 按名称动态查找）

</output_format>

<field_reference>

结构化验收标准详见 [planner-structured-criteria.md](planner-structured-criteria.md)。

</field_reference>

<references>

- [结构化验收标准](planner-structured-criteria.md) - 精确匹配、量化阈值评估、字段定义、使用示例
- [上下文学习指南](planner-context-learning.md) - 三层上下文学习、项目理解、记忆系统、规范驱动计划
- [Agent/Skills 选择参考](planner-reference.md) - Agent 和 Skills 的选择指南、使用示例
- [避坑指南](planner-pitfalls.md) - 常见错误、最佳实践、验证检查清单
- [集成示例](planner-integration.md) - Loop 集成、验证函数、高级用法

</references>

<guidelines>

始终使用 `Agent(agent="task:planner", ...)` 调用，检查 `status` 字段确认执行状态，处理 `questions` 字段中的用户确认请求。验证依赖关系无循环（使用拓扑排序），验证并行度不超过 2，验证 Agent/Skills 带中文注释，处理空 tasks 数组的特殊情况。

不要跳过计划验证步骤，不要忽略 planner 返回的问题，不要修改 planner 返回的 JSON 结构。常见陷阱包括：过度拆分任务（应合并为原子任务）、验收标准模糊（应可量化）、缺少中文注释、循环依赖、并行度超限。

</guidelines>

<agent_skills_rules>

**Agent/Skills 来源**：task插件内置(`task:planner/verifier/adjuster/explorer-*`) | 其他插件(`golang:dev/python:dev`) | 项目自定义(`.claude/agents/`) | 通用(`coder/tester/devops`)

Skills来源：语言插件(`golang:*/python:*`) | 通用(`documentation/code-review`) | 项目(`.claude/skills/`)

**格式**：`name（中文注释）`或`name（中文注释）@source`。Loop内部必须明确来源，任务执行agent来源灵活。

**强制规则**：tasks非空时，每个任务必须有 agent(带中文注释) + skills(≥1项，带中文注释)。仅 tasks 为空时可省略。

</agent_skills_rules>

<!-- /STATIC_CONTENT -->
