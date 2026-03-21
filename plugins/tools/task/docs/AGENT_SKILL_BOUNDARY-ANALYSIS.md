# Agent 与 Skill 功能边界 - 模块分析

本文档包含各模块的详细分析和优化方案。

---

## 二、现有模块分析

### 2.1 Planner 模块

#### Agent: `task:planner`
- **文件**: `/plugins/tools/task/agents/planner.md`
- **职责**: 执行计划设计流程
- **核心工作流**:
  1. 阶段 1：信息收集与项目理解（ACE 三层上下文学习）
  2. 阶段 2：计划设计（生成规范、任务分解、依赖建模、资源分配）
- **状态维护**: 项目理解报告、上下文文件验证状态
- **输出**: JSON 格式的执行计划（tasks、dependencies、parallel_groups）
- **调用示例**:
  ```python
  planner_result = Agent(agent="task:planner", prompt="设计执行计划...")
  ```

#### Skill: `task:planner`
- **文件**: `/plugins/tools/task/skills/planner/SKILL.md`
- **职责**: 定义计划设计规范和标准
- **内容**:
  - MECE 分解原则说明
  - 输出格式定义（JSON schema）
  - 字段参考表（status、report、tasks、dependencies 等）
  - Mermaid 图生成规范
  - 调用方式说明
  - 最佳实践指南
- **无执行逻辑**: 纯文档，不包含工作流步骤
- **支持文档**: `planner-context-learning.md`、`planner-reference.md`、`planner-pitfalls.md` 等

#### 边界评估
✅ **边界清晰**：Agent 负责执行多步骤流程，Skill 提供规范和知识支持。无功能重叠。

---

### 2.2 Verifier 模块

#### Agent: `task:verifier`
- **文件**: `/plugins/tools/task/agents/verifier.md`
- **职责**: 执行任务验收流程
- **核心工作流**:
  1. 阶段 1：任务状态收集
  2. 阶段 2：验收标准验证（运行测试、检查覆盖率、验证指标）
  3. 阶段 3：影响分析（回归测试、依赖检查）
  4. 阶段 4：生成验收报告
- **状态维护**: 任务验证历史、测试结果、回归测试状态
- **输出**: JSON 格式的验收报告（status: passed/suggestions/failed）
- **工具调用**: `TaskList()`、`Bash`（运行测试）

#### Skill: `task:verifier`
- **文件**: `/plugins/tools/task/skills/verifier/SKILL.md`
- **职责**: 定义验收验证规范
- **内容**:
  - 验收测试最佳实践（客观性、可度量性、独立性、AAA 模式）
  - 输出格式定义（passed/suggestions/failed）
  - 验证策略表（exact_match、quantitative_threshold 等）
  - 字段说明
  - 导航到子文档（verifier-skill-core.md、verifier-skill-advanced.md 等）
- **无执行逻辑**: 导航型文档，将详细规范拆分到子文件

#### 边界评估
✅ **边界清晰**：Agent 执行验证流程，Skill 定义验证标准和规范。无功能重叠。

---

### 2.3 Adjuster 模块

#### Agent: `task:adjuster`
- **文件**: `/plugins/tools/task/agents/adjuster.md`
- **职责**: 执行失败调整流程
- **核心工作流**:
  1. 阶段 1：失败信息收集
  2. 阶段 1.5：自愈尝试（依赖缺失/端口占用等 6 类错误）
  3. 阶段 2：失败原因分析
  4. 阶段 3：停滞检测
  5. 阶段 4：失败升级策略（retry/self_healing/debug/replan/ask_user）
  6. 阶段 5：生成调整报告
- **状态维护**: 失败历史、重试计数、停滞模式识别
- **输出**: JSON 格式的调整策略（strategy、retry_config、adjustments）
- **工具调用**: `TaskList()`、`SendMessage`

#### Skill: `task:adjuster`
- **文件**: `/plugins/tools/task/skills/adjuster/SKILL.md`
- **职责**: 定义失败调整规范
- **内容**:
  - Circuit Breaker 模式说明
  - 四级升级策略表（retry/debug/replan/ask_user）
  - 指数退避公式
  - 输出格式定义
  - 调用方式示例
  - 处理流程伪代码
- **无执行逻辑**: 纯规范文档
- **支持文档**: `adjuster-strategies.md`、`self-healing.md`、`adjuster-output-formats.md`

#### 边界评估
✅ **边界清晰**：Agent 执行失败处理流程，Skill 定义策略和规范。无功能重叠。

---

### 2.4 Finalizer 模块

#### Agent: `task:finalizer`
- **文件**: `/plugins/tools/task/agents/finalizer.md`
- **职责**: 执行资源清理流程
- **核心工作流**:
  1. 阶段 1：资源盘点
  2. 阶段 2：任务终止
  3. 阶段 3：文件清理
  4. 阶段 4：最终报告生成
- **状态维护**: 清理进度、错误列表
- **输出**: JSON 格式的清理报告（status、cleanup_summary、errors）
- **工具调用**: `TaskStop`、文件删除操作

#### Skill: `task:finalizer`
- **文件**: `/plugins/tools/task/skills/finalizer/SKILL.md`
- **职责**: 定义资源清理规范
- **内容**:
  - 防御性清理原则
  - 清理顺序规则（逆序执行）
  - 输出格式定义
  - 常见错误类型表
  - 调用方式示例
- **无执行逻辑**: 纯规范文档
- **支持文档**: `finalizer-cleanup-guide.md`

#### 边界评估
✅ **边界清晰**：Agent 执行清理流程，Skill 定义清理规范。无功能重叠。

---

### 2.5 Prompt Optimizer 模块

#### Agent: `task:prompt-optimizer`
- **文件**: `/plugins/tools/task/agents/prompt-optimizer.md`
- **职责**: 执行提示词优化流程
- **核心工作流**:
  1. 阶段 1：质量分析（三维度评分、识别模糊点）
  2. 阶段 2：搜索最佳实践（WebSearch，触发条件：得分 < 6）
  3. 阶段 3：结构化提问（5W1H 框架，每次一个问题）
  4. 阶段 4：生成优化提示（Markdown 模板）
- **状态维护**: 质量评分、提问历史、用户回答
- **输出**: JSON 格式的优化结果（status、quality_score、optimized_prompt）
- **工具调用**: `SendMessage`（提问）、`WebSearch`（搜索最佳实践）

#### Skill: `task:prompt-optimizer`
- **文件**: `/plugins/tools/task/skills/prompt-optimizer/SKILL.md`
- **职责**: 定义提示词优化规范
- **内容**:
  - 提示词工程最佳实践（明确性、上下文、范围边界等 6 项原则）
  - 5W1H 评估框架（What/Why/Who/When/Where/How）
  - 质量评分标准（清晰度/完整性/可执行性，0-10 分）
  - 执行流程详细说明（4 个阶段的步骤）
  - 提问模板和示例
  - 输出格式定义
- **包含详细执行逻辑**: ⚠️ 与其他 Skill 不同，此 Skill 包含大量执行流程描述

#### 边界评估
⚠️ **边界模糊**：Skill 文件包含过多执行逻辑（步骤 1.1、1.2、1.3、2.1、2.2 等），这些应该在 Agent 中。

**建议优化**：
1. **Skill 保留内容**：
   - 提示词工程最佳实践（6 项原则）
   - 5W1H 框架定义
   - 质量评分标准
   - 输出格式定义
   - 调用方式示例
2. **Skill 移除内容**（应在 Agent 中）：
   - 阶段 1-4 的详细执行步骤
   - 提问实施的伪代码
   - 质量检查的具体流程

---

### 2.6 Plan Formatter 模块

#### Agent: `task:plan-formatter`
- **文件**: `/plugins/tools/task/agents/plan-formatter.md`
- **职责**: 执行 JSON → Markdown 转换
- **核心工作流**: 单步骤（读取模板 → 填充数据 → 输出 Markdown）
- **状态维护**: 无（单次调用完成）
- **输出**: Markdown 格式的计划文档
- **职责单一**: 格式化转换，不参与计划逻辑设计

#### Skill: `task:plan-formatter`
- **文件**: `/plugins/tools/task/skills/plan-formatter/SKILL.md`
- **职责**: 定义计划文档格式规范
- **内容**:
  - 标准模板路径（template.md）
  - 关键约束（Mermaid 图单行、状态描述长度、表格格式等）
  - 调用方式示例
  - 禁止操作说明（禁止直接拼接 Markdown）
- **无执行逻辑**: 纯规范文档

#### 边界评估
✅ **边界清晰**：Agent 执行转换，Skill 定义格式规范。无功能重叠。

---

### 2.7 Loop 模块（特殊情况）

#### Skill: `task:loop`
- **文件**: `/plugins/tools/task/skills/loop/SKILL.md`
- **职责**: Loop 持续执行规范
- **性质**: **不是传统 Skill，而是一个完整的编排引擎**
- **内容**:
  - PDCA 流程定义（8 个阶段）
  - 各阶段的执行代码示例（伪代码）
  - 输出格式要求（`[MindFlow]` 前缀）
  - 子技能引用（task:planner、task:execute、task:verifier 等）
- **包含执行逻辑**: ✅ 合理，因为 loop 本身就是一个编排引擎，不是 agent

#### 边界评估
✅ **边界清晰**：Loop 是特殊的编排引擎 Skill，不适用常规 Agent/Skill 边界规则。它直接调用其他 agents（planner、verifier、adjuster 等）。

---

### 2.8 Execute 模块（特殊情况）

#### Skill: `task:execute`
- **文件**: `/plugins/tools/task/skills/execute/SKILL.md`
- **职责**: 定义任务执行规范
- **性质**: **编排规范，不是传统 Skill**
- **内容**:
  - 执行流程（7 个步骤）
  - 执行者复用机制（伪代码）
  - Team 生命周期管理（创建 → 分配 → 监控 → 清理）
  - 并行规则
  - 输出格式定义
- **包含执行逻辑**: ⚠️ 包含详细的伪代码实现

#### 无对应 Agent
⚠️ **缺失**: 没有 `task:execute` agent，执行逻辑直接在 loop 中调用

#### 边界评估
⚠️ **边界模糊**：execute 是一个规范文档，但没有对应的 agent。实际执行逻辑散落在 loop 中。

**建议优化**：
1. **创建 `task:execute` agent**（如需要复杂编排）
2. **或者**将 execute 规范简化为纯文档，执行逻辑保留在 loop 中

---

## 三、功能重叠分析

### 3.1 发现的重叠问题

| 模块 | 重叠类型 | 具体表现 | 影响 |
|------|---------|---------|------|
| **prompt-optimizer** | Skill 包含执行逻辑 | SKILL.md 包含阶段 1-4 的详细执行步骤、伪代码 | Skill 文件过大（480+ 行），违反单一职责原则 |
| **execute** | 缺少对应 Agent | 有 Skill 定义但无 agent 实现，执行逻辑散落在 loop 中 | 职责不清晰，难以维护 |

### 3.2 其他模块评估

| 模块 | 边界状态 | 说明 |
|------|---------|------|
| planner | ✅ 清晰 | Agent 执行流程，Skill 定义规范 |
| verifier | ✅ 清晰 | Agent 执行验证，Skill 定义标准 |
| adjuster | ✅ 清晰 | Agent 执行调整，Skill 定义策略 |
| finalizer | ✅ 清晰 | Agent 执行清理，Skill 定义规范 |
| plan-formatter | ✅ 清晰 | Agent 执行转换，Skill 定义格式 |
| loop | ✅ 清晰（特殊） | 编排引擎，不适用常规边界 |

---

## 四、优化方案

### 4.1 Prompt Optimizer 模块优化

#### 当前问题
- Skill 文件包含大量执行逻辑（阶段 1-4 的步骤）
- Agent 和 Skill 职责边界不清

#### 优化方案

**Agent 文件** (`agents/prompt-optimizer.md`) 保持不变，继续包含：
- 4 个阶段的工作流描述
- 状态转换条件
- 工具调用示例

**Skill 文件** (`skills/prompt-optimizer/SKILL.md`) 重构为纯规范：

```markdown
---
description: 提示词优化规范 - 质量评分标准、5W1H框架、最佳实践
---

# Skills(task:prompt-optimizer) - 提示词优化规范

<scope>
定义提示词质量评估标准、优化原则和输出格式规范。
</scope>

<core_principles>
## 提示词工程最佳实践
（保留 6 项原则：明确性、上下文、范围边界等）

## 5W1H 评估框架
（保留 What/Why/Who/When/Where/How 定义）

## 质量评分标准
（保留三维度评分标准）
</core_principles>

<output_format>
（保留 JSON 输出格式定义）
</output_format>

<references>
- Anthropic Prompt Engineering Guide (2025)
- best-practices.md
</references>
```

**移除内容**（从 Skill 移到 Agent 或删除）：
- 阶段 1-4 的详细执行步骤
- 步骤 1.1、1.2、1.3、2.1 等编号
- 提问实施的伪代码
- 质量检查的具体流程

---

### 4.2 Execute 模块优化

#### 当前问题
- 有 Skill 定义但无对应 agent
- 执行逻辑散落在 loop 中

#### 优化方案（二选一）

**方案 A：创建 task:execute agent**（推荐用于复杂编排）

创建 `agents/execute.md`：
```yaml
---
description: 任务执行 agent - 并行编排、团队管理、进度跟踪
model: sonnet
skills:
  - task:execute
---

<role>
负责按依赖顺序调度任务执行，支持最多 2 个任务并行。
</role>

<workflow>
（将 SKILL.md 中的执行流程移到这里）
</workflow>
```

简化 `skills/execute/SKILL.md` 为纯规范文档。

**方案 B：简化 Skill，保留 loop 直接调用**（推荐用于简单场景）

将 `skills/execute/SKILL.md` 简化为：
```markdown
# Skills(task:execute) - 任务执行规范

<scope>
定义任务并行编排规则和 Team 生命周期管理规范。
</scope>

<rules>
（保留并行规则、约束条件）
</rules>

<output_format>
（保留输出格式定义）
</output_format>
```

执行逻辑保留在 loop 中。

---

## 五、统一实现路径

### 5.1 Agent 内部调用 Skill 的标准模式

所有 Agent 应遵循此模式：

```python
# Agent 文件前置声明
---
skills:
  - task:xxx  # 引用对应的 Skill
---

<role>
你是 XXX agent。详细的执行指南请参考 Skills(task:xxx)。
本文档包含核心原则和工作流。
</role>

<core_principles>
（简要说明核心原则，不超过 200 字）
详细规范请参考 Skills(task:xxx)。
</core_principles>

<workflow>
（多步骤工作流定义）
阶段 1: ...
阶段 2: ...
</workflow>

<references>
- Skills(task:xxx) - 完整规范和字段定义
- 相关子文档
</references>
```

### 5.2 Skill 文件标准结构

```markdown
---
agent: task:xxx  # 对应的 Agent
description: XXX规范 - 简短描述
model: xxx
context: fork
user-invocable: false
---

# Skills(task:xxx) - XXX规范

<scope>
（适用场景，不超过 100 字）
</scope>

<core_principles>
（核心原则，纯概念说明）
</core_principles>

<invocation>
（调用方式示例，伪代码）
</invocation>

<output_format>
（输出格式定义，JSON schema）
</output_format>

<field_reference>
（字段说明表）
</field_reference>

<references>
（相关文档链接）
</references>

<guidelines>
（最佳实践和注意事项）
</guidelines>
```

**禁止内容**：
- ❌ 阶段 1、阶段 2 等执行步骤编号
- ❌ 详细的执行流程伪代码（应在 Agent 中）
- ❌ 状态转换逻辑（应在 Agent 中）
- ❌ 工具调用序列（应在 Agent 中）

---

## 六、验收标准

### 6.1 边界清晰度检查

对于每个模块，检查以下条件：

- [ ] Agent 文件包含多步骤工作流（阶段 1 → 阶段 2 → ...）
- [ ] Agent 文件描述状态维护逻辑
- [ ] Agent 文件包含工具调用示例
- [ ] Skill 文件只包含概念、原则、格式定义
- [ ] Skill 文件不包含执行步骤编号
- [ ] Skill 文件不包含详细的伪代码实现
- [ ] Agent 前置声明中引用了对应的 Skill

### 6.2 功能完整性检查

- [ ] 所有执行逻辑都在 Agent 中
- [ ] 所有规范定义都在 Skill 中
- [ ] 无重复定义（Agent 和 Skill 不重复描述同一内容）
- [ ] 引用关系清晰（Agent → Skill → 子文档）

### 6.3 文档质量检查

- [ ] Agent 文件包含 `<workflow>` 部分
- [ ] Skill 文件包含 `<output_format>` 部分
- [ ] 所有文件包含 `<references>` 部分
- [ ] 文件大小合理（Agent < 300 行，Skill < 400 行）

---

## 七、迁移计划

### Phase 1: 重构 prompt-optimizer（优先级：高）
- [ ] 从 Skill 移除阶段 1-4 的详细执行步骤
- [ ] 保留 6 项原则、5W1H 框架、质量评分标准
- [ ] 验证 Agent 文件包含完整的执行流程
- [ ] 测试优化功能是否正常

### Phase 2: 优化 execute 模块（优先级：中）
- [ ] 决定采用方案 A 或方案 B
- [ ] 如果选方案 A：创建 execute agent，简化 Skill
- [ ] 如果选方案 B：简化 Skill 为纯规范，保留 loop 直接调用
- [ ] 测试任务执行功能是否正常

### Phase 3: 审计其他模块（优先级：低）
- [ ] 复查 planner、verifier、adjuster、finalizer、plan-formatter
- [ ] 确认边界符合标准
- [ ] 统一文档格式

### Phase 4: 更新 README.md（优先级：低）
- [ ] 补充 Agent/Skill 边界说明
- [ ] 更新目录结构说明

---

**文档版本**: v1.0
**创建日期**: 2026-03-21
**负责人**: Task Plugin Team
