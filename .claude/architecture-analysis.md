# 参考插件架构分析报告（2026）

> 基于 deepresearch、task、version 三个参考插件的架构分析

## 执行摘要

本报告分析三个参考插件的架构设计，提取关键设计模式和2026最新技术规范，为全局 .claude/ 目录的 Skills 和 Agents 架构重新设计提供依据。

**关键发现**：
- **Commands 已废弃**：deepresearch 已将命令迁移到 Skills 系统
- **Task-Centric 设计**：任务驱动而非 Agent 驱动
- **0%职责重叠**：Agent 职责严格划分
- **文件行数限制**：所有 .md 文件 ≤300 行
- **2026 技术栈**：DGoT、Agentic RAG、GraphRAG、FoT、A2A 协议

---

## 一、deepresearch 插件分析（2026架构）

### 架构特点

**设计理念**：Task-Centric 任务驱动型深度研究系统

**核心统计**：
- Agents：4个（8个 → 4个，-50%）
- Skills：6个（9个 → 6个，-33%）
- Commands：0个（已废弃，迁移到 Skills）
- 总代码行数：~2000行（3323行 → 2000行，-40%）
- 检查清单项：<200项（1000+项 → 200项，-80%）

### Agents 设计（4个）

| Agent | 职责 | 模型 | 特点 |
|-------|------|------|------|
| **code-analyst** | 代码质量+技术债+性能 | opus | 合并3个旧Agent |
| **research-strategist** | 概念研究+方案对比 | opus | 合并2个旧Agent |
| **project-assessor** | 项目评估+依赖安全 | opus | 合并2个旧Agent |
| **architecture-advisor** | 架构评审+设计建议 | opus | 保留核心优化 |

**设计原则**：
- **统一模型**：所有 Agent 使用 opus 模型
- **0%职责重叠**：严格职责边界，无功能重复
- **自动匹配**：基于任务关键词自动选择 Agent
- **A2A 协作**：Agent 间点对点协作，无需中心编排

**Agent 定义规范**：
```yaml
---
description: |
  代码分析师 - 代码质量+技术债+性能的一站式分析专家
  场景：代码审查、技术债识别、性能瓶颈定位、重构规划
  示例：分析 ./src 的代码质量 | 识别项目技术债并排序 | 定位API性能瓶颈
model: opus
color: blue
memory: project
skills:
  - dgot-engine
  - code-inspector
  - source-validator
  - knowledge-synthesizer
---
```

### Skills 设计（6个）

| Skill | 类型 | 职责 | 关键技术 |
|-------|------|------|---------|
| **deep-research** | 用户入口 | 研究工作流编排 | Task-Centric |
| **dgot-engine** | 内部能力 | DGoT动态图思维引擎 | 早停+裁剪，-50%成本 |
| **agentic-retriever** | 内部能力 | 智能检索器 | Agentic RAG，99%精度 |
| **source-validator** | 内部能力 | 来源验证器 | A-E评级 |
| **knowledge-synthesizer** | 内部能力 | 知识合成器 | 8种输出格式 |
| **code-inspector** | 内部能力 | 代码检查器 | 本地+GitHub统一接口 |

**Skill 层次结构**：
- **1个用户入口**：deep-research（user-invocable: true）
- **5个核心能力**：内部 skills，由入口 skill 调用

**Skill 定义规范**：
```yaml
---
name: deep-research
description: 执行完整的深度研究工作流程 - Task-Centric任务驱动，DGoT核心优化，单次需求收集
user-invocable: true
context: fork
model: sonnet
skills:
  - dgot-engine
  - agentic-retriever
  - source-validator
  - knowledge-synthesizer
  - code-inspector
---
```

### 2026 技术创新

| 技术 | 功能 | 效果 |
|------|------|------|
| **DGoT** | 动态图思维引擎，早停+阈值裁剪 | -43~56%成本 |
| **Agentic RAG** | 嵌入自主AI代理，动态检索策略 | 99%精度 |
| **GraphRAG** | 知识图谱+向量搜索 | 结构化关系推理 |
| **FoT** | 框架优化，超参数调优+prompt优化 | 智能缓存 |
| **A2A协议** | Agent间点对点协作 | 无需中心编排 |
| **MCP Server Cards** | 标准化服务发现 | 元数据标准 |

### Commands 废弃策略

**旧架构**：
- commands/deep-research.md（命令文件）
- 用户通过 `/deep-research` 调用

**新架构**：
- skills/deep-research/SKILL.md（user-invocable: true）
- 用户直接描述任务，系统自动匹配 Agent
- 删除 commands/ 目录

**迁移步骤**：
1. 创建 skills/deep-research/SKILL.md
2. 设置 `user-invocable: true`
3. 保留所有功能，优化交互流程
4. 删除 commands/deep-research.md
5. 更新 plugin.json（移除 commands 字段）

---

## 二、task 插件分析

### 架构特点

**设计理念**：基于 PDCA 循环的智能任务编排引擎

**核心统计**：
- Agents：6个
- Skills：10个
- Commands：0个（通过 /loop 调用，但实现在 skills/loop/）
- 角色定位：Team Leader（统一用户交互、调度多个 agent）

### Agents 设计（6个）

| Agent | 职责 | 模型 | 特点 |
|-------|------|------|------|
| **prompt-optimizer** | 提示词优化 | sonnet | 5W1H框架、质量评估 |
| **planner** | 计划设计 | opus | MECE原则、DAG依赖 |
| **verifier** | 结果验证 | sonnet | 验收标准检查 |
| **adjuster** | 失败调整 | sonnet | 分级升级策略 |
| **finalizer** | 资源清理 | sonnet | 系统性清理 |
| **plan-formatter** | 计划格式化 | sonnet | JSON→Markdown |

**设计原则**：
- **Team Leader 模式**：loop skill 作为 leader，统一管理所有调度
- **集中式通信**：agents 通过 SendMessage 上报给 leader
- **框架与执行分离**：task 负责流程编排，执行由外部 agents 完成

**Agent 定义示例**：
```yaml
---
description: |-
  Use this agent when you need to optimize and clarify user prompts for complex tasks. This agent specializes in analyzing prompt quality, identifying ambiguities, and refining prompts through intelligent questioning. Examples:

  <example>
  Context: Loop command initialization - prompt optimization phase
  user: "Optimize the user's task description before planning"
  assistant: "I'll use the prompt-optimizer agent to analyze and refine the prompt."
  <commentary>
  Early prompt optimization prevents misunderstanding and wasted effort in later stages.
  </commentary>
  </example>
model: sonnet
memory: project
color: blue
skills:
  - task:prompt-optimizer
---
```

### Skills 设计（10个）

| Skill | 类型 | 职责 |
|-------|------|------|
| **loop** | 用户入口 | PDCA循环，8个阶段编排 |
| **prompt-optimizer** | 核心能力 | 提示词优化规范 |
| **planner** | 核心能力 | 计划设计规范 |
| **execute** | 核心能力 | 任务执行规范 |
| **verifier** | 核心能力 | 结果验证规范 |
| **adjuster** | 核心能力 | 失败调整规范 |
| **finalizer** | 核心能力 | 完成清理规范 |
| **deep-iteration** | 核心能力 | 深度迭代规范 |
| **plan-formatter** | 辅助能力 | 计划格式化规范 |
| **hitl、observability** | 辅助能力 | 人机交互、可观测性 |

**8个工作阶段**：
1. 初始化（Initialization）
2. 提示词优化（Prompt Optimization）[新增]
3. 深度研究（Deep Research）[可选]
4. 计划设计（Planning）
5. 任务执行（Execution）
6. 结果验证（Verification）
7. 失败调整（Adjustment）
8. 全部完成（Completion）

### 提示词优化功能（新增）

**核心特性**：
- **自动质量评估**：清晰度、完整性、可执行性（0-10分）
- **智能静默**：质量≥8分完全静默跳过
- **结构化提问**：基于5W1H框架
- **最佳实践融合**：质量<6分搜索最新技巧
- **不限提问次数**：确保信息完整

**质量评分标准**：
| 得分 | 等级 | AI 行为 |
|------|------|---------|
| 9-10分 | 优秀 | 静默跳过 |
| 8-8.9分 | 良好 | 静默跳过 |
| 6-7.9分 | 中等 | 提问澄清 |
| 4-5.9分 | 较低 | 提问+WebSearch |
| 0-3.9分 | 很低 | 多次提问+WebSearch |

**5W1H框架**：
- What（目标）：要实现什么功能？
- Why（动机）：为什么需要？
- Who（受众）：目标用户是谁？
- When（时间）：什么时候完成？
- Where（范围）：影响哪些模块？
- How（方式）：技术方案偏好？

---

## 三、version 插件分析

### 架构特点

**设计理念**：轻量级版本管理，仅使用 Hooks

**核心统计**：
- Agents：0个
- Skills：0个
- Hooks：2个（SessionStart、UserPromptSubmit）
- 实现方式：Python 脚本

**设计特点**：
- **极简设计**：无 Agents/Skills，仅 Hooks + 脚本
- **自动化**：会话启动和提交时自动执行
- **异步执行**：async: true，不阻塞用户交互

**适用场景**：
- 简单的自动化任务
- 无需用户交互的后台任务
- 轻量级功能

---

## 四、关键设计模式提取

### 1. Agent 设计模式

**职责合并原则**：
- deepresearch：8个 → 4个（合并职责相近的 agents）
- task：保持 6个（每个职责独立）

**模型选择原则**：
- **opus**：复杂推理、深度分析（planner、复杂 agents）
- **sonnet**：快速响应、轻量任务（verifier、adjuster、prompt-optimizer）

**颜色标识原则**：
- **blue**：分析类（code-analyst、prompt-optimizer）
- **purple**：研究类（research-strategist）
- **orange**：执行类（planner、verifier）

**YAML frontmatter 标准字段**：
```yaml
---
description: |
  简要说明（1-2行）
  场景：具体使用场景（3-5个）
  示例：触发示例（3-5个）
model: opus | sonnet
color: blue | purple | orange | green | red
memory: project | conversation
skills:
  - skill1
  - skill2
---
```

### 2. Skill 设计模式

**层次结构**：
- **用户入口 Skill**（1-2个）：user-invocable: true
- **核心能力 Skill**（5-10个）：内部调用
- **辅助能力 Skill**（0-5个）：可选

**YAML frontmatter 标准字段**：
```yaml
---
name: skill-name
description: 简要说明
user-invocable: true | false
context: fork | same
model: opus | sonnet
skills:
  - dependency-skill1
  - dependency-skill2
---
```

**文件结构**：
```
skills/
├── skill-name/
│   ├── SKILL.md（主文件，≤300行）
│   ├── best-practices.md（最佳实践，≤300行）
│   ├── examples.md（示例，≤300行）
│   └── sub-skills/（可选子目录）
```

### 3. Commands → Skills 迁移模式

**迁移步骤**（参考 deepresearch）：
1. 创建 `skills/command-name/SKILL.md`
2. 设置 `user-invocable: true`
3. 保留所有功能，优化交互流程
4. 删除 `commands/command-name.md`
5. 更新 `plugin.json`（移除 commands 字段）

**迁移前**：
```json
{
  "commands": ["./commands/deep-research.md"],
  "skills": "./skills/"
}
```

**迁移后**：
```json
{
  "skills": "./skills/"
}
```

**调用方式变化**：
- **旧**：`/deep-research 任务描述`
- **新**：直接描述任务，系统自动匹配

### 4. 文件行数限制（≤300行）

**实施策略**：
- **拆分**：将大文件拆分为多个子文件
- **链接**：主文件使用链接引用详细文档
- **精简**：移除重复内容、版本历史
- **分层**：概览（主文件）→ 详细（子文件）

**示例**（docs/index.md）：
- **原始**：419行
- **优化后**：220行（-47.5%）
- **策略**：移除详细定义，改为链接到专门文档

---

## 五、2026技术规范总结

### 架构规范

| 规范项 | 要求 | 示例 |
|--------|------|------|
| **架构模式** | Task-Centric 任务驱动 | deepresearch |
| **Agent职责** | 0%重叠，严格边界 | 4个统一职责 agents |
| **模型选择** | 统一模型（opus 或 sonnet） | deepresearch 全用 opus |
| **文件行数** | ≤300行 | 所有 .md 文件 |
| **命令系统** | 已废弃，迁移到 Skills | deepresearch |

### 技术栈（2026）

| 技术 | 用途 | 优势 |
|------|------|------|
| **DGoT** | 动态图思维引擎 | -43~56%成本 |
| **Agentic RAG** | 智能检索 | 99%精度 |
| **GraphRAG** | 知识图谱 | 结构化推理 |
| **FoT** | 框架优化 | 超参数调优 |
| **A2A协议** | Agent协作 | 无需中心编排 |

### 质量标准

| 维度 | 标准 | 验证方法 |
|------|------|---------|
| **AI理解准确率** | 100% | 质量检查工具 |
| **文件行数** | ≤300行 | wc -l |
| **职责重叠** | 0% | 人工审查 |
| **用户体验** | 高质量输入静默跳过 | 功能测试 |

---

## 六、建议架构设计方向

### 全局 .claude/agents/ 设计

**目标**：3-5个实用 agents，覆盖常见开发场景

**建议 Agents**：
1. **code-reviewer**（代码审查专家）- 合并现有 agent.md 部分功能
2. **architect**（架构顾问）- 架构设计、模式识别
3. **plugin-dev-advisor**（插件开发顾问）- 合并现有 8个 plugin 相关 agents

**职责划分**：
- **code-reviewer**：代码质量、测试覆盖、最佳实践
- **architect**：架构设计、SOLID 原则、重构建议
- **plugin-dev-advisor**：插件结构、manifest、components、MCP/LSP 集成

### 全局 .claude/skills/ 设计

**目标**：8-12个 skills，覆盖开发全流程

**建议 Skills**：
1. **code-review**（代码审查）- user-invocable
2. **refactoring**（重构指导）- user-invocable
3. **architecture-review**（架构评审）- user-invocable
4. **testing**（测试策略）- 内部能力
5. **documentation**（文档生成）- 内部能力
6. **git-workflow**（Git 工作流）- user-invocable
7. **plugin-development**（插件开发）- user-invocable，保留现有 plugin-skills/
8. **performance-optimization**（性能优化）- 内部能力

### Commands 迁移策略

**当前 commands**：
- .claude/commands/new.md

**迁移目标**：
- .claude/skills/new-plugin/SKILL.md（user-invocable: true）

**迁移后删除**：
- .claude/commands/ 目录

---

## 七、架构对比

| 维度 | 现有架构 | 建议新架构 | 改进 |
|------|---------|-----------|------|
| Agents | 8个（细分） | 3-5个（实用） | 职责整合 |
| Skills | 1个目录 | 8-12个 | 覆盖全流程 |
| Commands | 1个 | 0个 | 迁移到 Skills |
| 职责重叠 | 可能有 | 0% | 严格边界 |
| 文件行数 | 未限制 | ≤300行 | 易读易维护 |
| 技术栈 | 传统 | 2026技术栈 | 成本-50% |

---

## 附录：参考文档

### deepresearch 插件
- [README.md](../plugins/tools/deepresearch/README.md)
- [架构文档](../plugins/tools/deepresearch/docs/index.md)
- [Agents 详细说明](../plugins/tools/deepresearch/docs/agents.md)
- [Skills 详细说明](../plugins/tools/deepresearch/docs/skills.md)

### task 插件
- [README.md](../plugins/tools/task/README.md)
- [提示词优化功能](../plugins/tools/task/skills/prompt-optimizer/SKILL.md)

### version 插件
- [plugin.json](../plugins/tools/version/.claude-plugin/plugin.json)

---

**报告版本**：v1.0
**创建时间**：2026-03-20
**分析对象**：deepresearch v0.0.181, task v0.0.180, version v0.0.180
**下一步**：基于本报告设计全局 Skills 和 Agents 架构
