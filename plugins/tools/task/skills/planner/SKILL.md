---
description: "Planner 计划设计 - Loop Planning 阶段调用：分析项目结构和技术栈，将复杂任务分解为子任务，建立依赖关系和并行策略，为每个子任务分配 Agent/Skills。由 Loop 内部调度，不直接面向用户"
model: sonnet
user-invocable: false
agent: task:planner
---


# Skills(task:planner) - 计划设计规范

<scope>
当你需要为复杂任务设计执行计划时使用此 skill。适用于深入分析项目结构和技术栈、将复杂任务分解为可执行的子任务、建立任务依赖关系和并行执行策略、为每个任务分配合适的 Agent 和 Skills，以及 Loop 命令的计划设计（Planning / Plan）阶段。
</scope>

<core_principles>
MECE 分解原则要求子任务之间相互独立（Mutually Exclusive，无文件冲突，可独立执行）且完全穷尽（Collectively Exhaustive，覆盖所有必要工作，无遗漏）。

质量标准包括四个方面：可交付原子化（每个任务必须产生可验证的交付物）、可量化可验证（每个任务必须有明确的、可量化的验收标准）、依赖闭环（任务之间的依赖关系必须形成有向无环图 DAG）、幂等性设计（任务应设计为可安全重复执行，多次执行产生相同结果，支持失败后重试不产生副作用）。

原子任务拆分原则：每个任务是最小、不可再分的工作单元（Atomic Task），遵循以下规则：
- **单文件单任务**：每个任务只修改一个文件，禁止跨文件操作（避免文件冲突和执行依赖）
- **语义完整**：每个任务有明确的单一目标，可独立验证交付
- **粒度平衡**：不过度拆分（避免协调成本超过实际收益），不拆分不足（避免单任务过于复杂）
- **判断标准**：如果一个任务可以描述为"修改文件A的X部分+修改文件B的Y部分"，则必须拆分为两个独立任务
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
| "一个任务修改多个文件更高效" | 违反单文件单任务原则，多文件任务会导致冲突和回滚困难，必须拆分 |
</red_flags>

<execution_workflow>
## Planner 内部执行流程（强制遵守）

**必须按顺序执行以下步骤，禁止跳过任何步骤**：

### ContextLearning：三层上下文学习（前置条件）

**强制要求**：必须完成三层上下文学习才可进入计划设计。未完成则暂停，请求补充信息。

1. **L1 - 项目全局理解**：读取 README.md、CLAUDE.md、AGENTS.md、agent.md，理解项目架构和技术栈
2. **L2 - 规范和记忆**：读取项目记忆，理解项目约束和历史决策
3. **L3 - 目标相关文件**：基于任务目标，读取相关源代码文件（使用 Glob/Grep 定位）

**验证点**：确认已获取足够的项目上下文信息，能够准确理解任务需求和技术约束。

**完成标志**：输出 JSON 中必须包含 `context_learning` 字段，记录每层实际读取的文件列表：
```json
"context_learning": {
  "L1": ["README.md", "CLAUDE.md", "AGENTS.md", "agent.md"],
  "L2": ["项目记忆已加载"],
  "L3": ["src/auth.ts", "src/middleware.ts"]
}
```
每层列表不可为空。若某层无相关信息（如 L2 无记忆），须记录 `["(none)"]` 并说明原因。

### InformationGathering：信息收集（MECE准备）

**强制要求**：收集计划设计所需的所有信息维度。

1. **目标澄清**：用户期望的交付物是什么？
2. **依赖识别**：需要哪些技术栈、库、工具？
3. **现状评估**：相关功能是否已存在？
4. **边界确认**：不在范围内的是什么？

**验证点**：四个维度都有明确答案，无模糊或缺失信息。如有疑问，必须通过 `questions` 字段询问用户。

### PlanDesign：计划设计（自顶向下分解）

**强制要求**：按以下具体步骤分解任务，每一步产出明确的中间结果。

**ScopeMapping：变更范围扫描**

基于 ContextLearning 和 InformationGathering 的结果，列出所有需要修改或新建的文件：
- 使用 Glob/Grep 定位目标文件，不可凭猜测
- 输出：`affected_files[]`（每个元素含文件路径 + 变更类型：create/modify/delete + 变更摘要）

**TaskExtraction：逐文件提取任务**

对 `affected_files` 中的每个文件，生成一个原子任务：
- **一个文件 = 一个任务**（硬性规则）：如果一个文件需要多种不相关的修改，仍归为一个任务（避免对同一文件并发写入）
- **任务描述**必须是单一动作（禁止用"和"/"且"/"并"连接多个不相关目标）
- **交付物**：每个任务必须产出可独立验证的结果（文件存在/测试通过/lint 通过等）

**IndependenceVerification：独立性验证**

逐项检查，任何一项失败必须回到 TaskExtraction 修正：
- [ ] 无文件交叉：每个文件只出现在一个任务的 `files` 中
- [ ] 无隐式耦合：任务 A 的输出不是任务 B 的输入（有依赖的除外，依赖必须显式声明）
- [ ] 可独立执行：移除任务间的依赖后，每个任务仍可独立运行产出交付物

**DependencyModeling：依赖建模**

1. 构建 DAG：任务 B 依赖任务 A 当且仅当 B 的执行需要 A 的交付物
2. 拓扑排序验证：无循环依赖
3. 并行分组：无依赖关系的任务归入同一并行组，每组 ≤ 2 个任务

**ResourceAllocation：资源分配**

为每个任务分配：
- `agent`（单个，必填）：`"name（中文注释）@source"`
- `skills`（数组，≥1个，必填）：`["name（中文注释）@source"]`
- `acceptance_criteria`（数组，必填）：可量化的验收标准，禁止定性描述

**验证点**：所有任务满足原子性 + 独立性 + DAG 合法 + 并行度≤2 + agent/skills/acceptance_criteria 齐全。

### OutputValidation：输出验证（质量门控）

**强制要求**：逐项验证，任何一项失败必须回到 PlanDesign 修正，禁止带着失败项继续。

**FormatCheck：格式验证**
- [ ] JSON 结构正确，必填字段齐全
- [ ] dependencies 引用的任务ID都存在
- [ ] parallel_groups 引用的任务ID都存在，每组≤2个任务
- [ ] 所有 agent/skills 都带中文注释 "（注释）"

**AtomicityCheck：原子性验证**
- [ ] 每个任务的 `files` 数组长度 ≤ 1（单文件单任务）
- [ ] 每个任务描述是单一动作（不含"和"/"且"/"并"连接的多目标）
- [ ] 每个任务的 `acceptance_criteria` 数组非空且每项可量化

**IndependenceCheck：独立性验证**
- [ ] 所有任务的 `files` 无交叉（同一文件不出现在多个任务中）
- [ ] 非依赖任务之间无隐式数据耦合

**CompletenessCheck：完整性验证**
- [ ] ScopeMapping 识别的所有文件都被至少一个任务覆盖
- [ ] 无遗漏的必要工作

**验证点**：所有检查项通过，输出符合规范。

### PlanWrite：格式化并写入计划文件（强制，tasks非空时）

**强制要求**：tasks 非空时，必须将计划格式化为 Markdown 并写入文件，然后再返回 JSON。

1. **生成文件路径**：`.claude/tasks/{task_id}/plan.md`
   - 计划文件与元数据统一存放在任务目录下
   - 若文件已存在则覆盖写入，不存在则直接新建
2. **创建目录**：确保 `.claude/tasks/{task_id}/` 存在（Initialization 阶段已创建）
3. **生成 Markdown**：按计划模板（YAML frontmatter + Mermaid stateDiagram + 任务表格 + 验收标准），参考 [template.md](template.md)
4. **写入文件**：使用 Write 工具写入 plan.md
5. **写入任务清单**：将 tasks 数组写入 `.claude/tasks/{task_id}/tasks.json`
   ```json
   {
     "tasks": [
       { "id": "T1", "description": "...", "agent": "...", "skills": [...], "files": [...], "acceptance_criteria": [...], "dependencies": [...], "status": "pending" }
     ]
   }
   ```
6. **更新输出 JSON**：在返回的 JSON 中设置 `plan_md_path` 字段为 plan.md 的绝对路径

**验证点**：plan_md_path 对应的文件存在且内容完整，tasks.json 已写入且包含与 plan.md 一致的任务列表。

### UserConfirmation：用户确认（根据 auto_approve 参数决定）

**当 `auto_approve=false`（默认）且 tasks 非空时，必须执行此阶段**。

1. **加载 AskUserQuestion schema**：调用 `ToolSearch(query="select:AskUserQuestion")`
2. **请求用户批准**：调用 AskUserQuestion，**参数格式（必须严格遵守）**：

```
AskUserQuestion({
  "questions": [{
    "question": "[MindFlow·${task_id}] 计划已生成（${task_count}个任务），是否批准执行？",
    "header": "计划确认",
    "options": [
      {"label": "批准执行", "description": "开始按计划执行所有任务"},
      {"label": "修改计划", "description": "提供修改意见，重新设计计划"},
      {"label": "取消任务", "description": "放弃当前任务"}
    ],
    "multiSelect": false
  }]
})
```

⚠️ 顶层参数是 `questions`（复数，**数组**），不是 `question`。每个元素必须包含 `question`/`header`/`options`/`multiSelect` 四个字段。`options` 每项必须包含 `label` 和 `description`。**禁止**使用 `type`/`default_value`/`choices` 等不存在的参数。

3. **判定用户响应并设置最终 status**：
   - 选择"批准执行" → `status = "confirmed"`
   - 选择"修改计划"或 Other 文本输入 → `status = "rejected"`，将用户文本存入 `user_feedback`
   - 选择"取消任务" → `status = "cancelled"`

**当 `auto_approve=true` 时**：跳过此阶段，直接设置 `status = "confirmed"`。

**当 tasks 为空时**：跳过此阶段，设置 `status = "no_tasks"`。

### WriteResult：写入结果到 metadata.json（强制，禁止跳过）

**⚠️ 防中止规则（最高优先级）**：

UserConfirmation 完成（用户确认/自动批准/取消）后，**绝对禁止**在此处结束回复。必须**立即**在同一回复中完成以下操作：

1. **更新 metadata.json**：读取 `.claude/tasks/{task_id}/metadata.json`，更新 `result` 字段和 `updated_at`
   ```json
   {
     "result": {
       "status": "confirmed|rejected|no_tasks|cancelled",
       "report": "≤200字计划摘要",
       "task_count": 4,
       "user_feedback": "用户修改意见（rejected 时）"
     }
   }
   ```
2. **禁止**：输出/打印任何 JSON 或计划内容到对话中——所有数据已写入文件（plan.md + tasks.json + metadata.json）
3. **禁止**：输出"计划已确认"等摘要后就停止。**必须**更新 metadata.json 后才能结束

**自检**：在准备结束回复前，检查"我是否已更新了 metadata.json 的 result 字段？"——如果没有，**必须继续**。
</execution_workflow>

<invocation>
调用：`Skill(skill="task:planner", args="设计执行计划：\n任务目标：{desc}\n项目路径：{project_path}\ntask_id：{task_id}\n迭代：{iteration}\nauto_approve：{true/false}\nuser_feedback：{如有}\n要求：1.分析项目结构 2.收集目标/依赖/现状/边界 3.MECE分解 4.DAG依赖 5.分配Agent+Skills(带中文注释) 6.可量化验收标准 7.报告≤200字 8.tasks非空时格式化写入计划文件 9.auto_approve=false时调用AskUserQuestion请求用户确认\n功能已存在则返回空tasks。")`

**结果处理**（planner 返回后，loop 读取 metadata.json 的 `result` 字段）：
- `result.status: "confirmed"` → 进入执行阶段
- `result.status: "rejected"` → 读取 `result.user_feedback`，回到 PromptOptimization
- `result.status: "no_tasks"` → 无需执行
- `result.status: "cancelled"` → 用户取消
</invocation>

<mermaid_generation_rules>

Mermaid stateDiagram 规则：单行文本（禁止`\n`）、标签≤15字符（仅ID+名称）、详情放表格不放图中、节点≤12个。格式：`state "T1: 需求分析" as T1`

</mermaid_generation_rules>

<output_format>

**所有结果通过文件传递，禁止输出 JSON 到对话。**

planner 写入的文件：
- `.claude/tasks/{task_id}/plan.md` — 完整计划文档
- `.claude/tasks/{task_id}/tasks.json` — 任务数组
- `.claude/tasks/{task_id}/metadata.json` — 更新 `result` 字段（status/report/task_count/user_feedback）

tasks.json 中每个 task 必含字段：
- `id`: 任务ID
- `description`: 任务描述
- `agent`（单个，必填）: `"name（中文注释）@source"`
- `skills`（数组，必填，≥1个）: `["name（注释）@source"]`
- `files`（数组，可选）: 关联文件/模块列表
- `acceptance_criteria`（数组，必填）: 验收清单（check list），可量化
- `dependencies`（数组）: 前置任务ID列表

metadata.json `result` 字段：
- `status`: "confirmed"（用户批准/自动批准）| "rejected"（用户要求修改）| "no_tasks"（无需执行）| "cancelled"（用户取消）
- `report`: 计划摘要（≤200字）
- `task_count`: 任务数量（confirmed/rejected 时）
- `user_feedback`: 用户修改意见（rejected 时必填）

**重要**：agent/skills 在规划阶段只是名称引用，实际加载和调用在执行阶段进行（loop 按名称动态查找）
**重要**：tasks 非空时，planner 必须完成 PlanWrite（写文件）和 UserConfirmation（用户确认），然后更新 metadata.json

</output_format>

<field_reference>

结构化验收标准详见 [planner-structured-criteria.md](planner-structured-criteria.md)。

</field_reference>

<references>

- [结构化验收标准](planner-structured-criteria.md) - 精确匹配、量化阈值评估、字段定义
- [上下文学习指南](planner-context-learning.md) - 三层上下文学习、项目理解、记忆系统
- [资源选择指南](planner-resource-guide.md) - Agent/Skills 发现、选择原则、来源标注
- [最佳实践与避坑](planner-best-practices.md) - 常见错误、检查清单、关键要点
- [集成指南](planner-integration.md) - Loop 集成、验证函数、高级用法

</references>

<guidelines>

始终使用 `Skill(skill="task:planner", ...)` 调用，检查 `status` 字段确认执行状态，处理 `questions` 字段中的用户确认请求。验证依赖关系无循环（使用拓扑排序），验证并行度不超过 2，验证 Agent/Skills 带中文注释，处理空 tasks 数组的特殊情况。

不要跳过计划验证步骤，不要忽略 planner 返回的问题，不要修改 planner 返回的 JSON 结构。常见陷阱包括：过度拆分任务（应合并为原子任务）、验收标准模糊（应可量化）、缺少中文注释、循环依赖、并行度超限。

</guidelines>

<agent_skills_rules>

**Agent/Skills 来源**：task插件内置(`task:planner/verifier/adjuster/explorer-*`) | 其他插件(`golang:dev/python:dev`) | 项目自定义(`.claude/agents/`) | 通用(`coder/tester/devops`)

Skills来源：语言插件(`golang:*/python:*`) | 通用(`documentation/code-review`) | 项目(`.claude/skills/`)

**格式**：`name（中文注释）`或`name（中文注释）@source`。Loop内部必须明确来源，任务执行agent来源灵活。

**强制规则**：tasks非空时，每个任务必须有 agent(带中文注释) + skills(≥1项，带中文注释)。仅 tasks 为空时可省略。

</agent_skills_rules>

