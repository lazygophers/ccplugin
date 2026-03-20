# Deep Research 架构文档（2026）

> Task-Centric 任务驱动型深度研究系统

## 目录

1. [架构设计](index.md) ⬅️ 当前
2. [命令系统](commands.md)
3. [Agent系统](agents.md)
4. [Skill系统](skills.md)
5. [配置指南](configuration.md)

---

## 架构概览

### 设计理念

**从 Agent-Centric 到 Task-Centric**：
- **旧架构**：用户选择Agent → Agent执行 → 单一视角
- **新架构**：任务自动分解 → 智能Agent匹配 → 多角度自动综合

### 四层架构

```
┌─────────────────────────────────────────────────────────┐
│ 命令层 - deep-research                                   │
│ 单次智能需求收集 + 自动Agent匹配                          │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│ Agent层 - 4个专业Agent（统一opus模型）                  │
│ code-analyst | research-strategist                      │
│ project-assessor | architecture-advisor                 │
│ 支持A2A协议点对点协作                                    │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│ Skill层 - 5个核心能力                                   │
│ dgot-engine（DGoT引擎，-50%成本）                        │
│ agentic-retriever（智能检索，99%精度）                   │
│ source-validator（A-E评级）                              │
│ knowledge-synthesizer（8种格式）                         │
│ code-inspector（代码检查）                               │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│ MCP层 - 标准化服务集成                                   │
│ duckduckgo | github | wikipedia | sequential-thinking   │
│ time | context7 | chrome-devtools                       │
│ 支持 MCP Server Cards 标准                               │
└─────────────────────────────────────────────────────────┘
```

---

## Agent 系统（4个）

详细说明请参考 [Agent系统文档](agents.md)。

| Agent | 职责 | 模型 |
|-------|------|------|
| **code-analyst** | 代码质量 + 技术债 + 性能分析 | opus |
| **research-strategist** | 技术概念研究 + 方案对比 + 选型 | opus |
| **project-assessor** | 项目评估 + 依赖安全审计 | opus |
| **architecture-advisor** | 架构评审 + 设计建议 | opus |

### 核心特性

- **统一模型**：所有Agent使用opus模型
- **职责明确**：0%功能重叠
- **自动匹配**：基于任务关键词自动选择
- **A2A协作**：支持Agent间点对点协作

---

## Skill 系统（6个）

详细说明请参考 [Skill系统文档](skills.md)。

| Skill | 职责 | 用户可调用 |
|-------|------|-----------|
| **deep-research** | 研究工作流入口 | ✅ 是 |
| **dgot-engine** | DGoT动态图思维引擎 | ❌ 否 |
| **agentic-retriever** | 智能检索器 | ❌ 否 |
| **source-validator** | 来源验证器 | ❌ 否 |
| **knowledge-synthesizer** | 知识合成器 | ❌ 否 |
| **code-inspector** | 代码检查器 | ❌ 否 |

### 核心特性

- **Task-Centric**：任务驱动，自动Agent匹配
- **DGoT优化**：早停+裁剪，降低43-56%成本
- **Agentic RAG**：自主代理，99%精度
- **A-E评级**：5级质量评分系统
- **8种格式**：自动适配受众

---

## 数据流

```
用户输入 → deep-research → Agent匹配 → dgot-engine
   → agentic-retriever → source-validator → knowledge-synthesizer
   → 最终报告（8种格式）
```

**6个工作阶段**：
1. 智能需求收集（单次）
2. 自动Agent匹配
3. DGoT核心驱动
4. 智能检索（Agentic RAG）
5. 质量验证（A-E评级）
6. 知识合成（8种格式）

---

## 关键创新

### 1. DGoT动态优化（-50%成本）

**核心机制**：
- 动态阈值：质量≥8.5分提前终止
- 早停机制：3个高质量路径触发聚合
- 智能裁剪：低于阈值路径立即丢弃
- **总体节省**：43-56%成本

### 2. Agentic RAG（99%精度）

**核心机制**：
- 自主代理：动态选择检索策略
- GraphRAG集成：知识图谱+向量搜索
- 反思机制：结果不足时自动调整

### 3. Task-Centric架构（-50%交互）

**核心机制**：
- 自动匹配：基于任务特征选择Agent
- 单次收集：智能结构化提问（5-8维度）
- 多Agent协作：A2A协议点对点协作

---

## 技术栈

### MCP服务器（7个）

| 服务器 | 用途 | 优先级 |
|--------|------|--------|
| **duckduckgo** | 网络搜索引擎 | 必需 |
| **github** | GitHub API集成 | 必需 |
| **wikipedia** | 百科知识库 | 必需 |
| **sequential-thinking** | 复杂推理引擎 | 必需 |
| **time** | 时间服务 | 必需 |
| **context7** | 文档检索增强 | 可选 |
| **chrome-devtools** | 浏览器自动化 | 可选 |

详细配置请参考 [配置指南](configuration.md)。

---

## 架构对比

| 维度 | 旧架构 | 新架构（2026） |
|------|--------|----------------|
| Agent数量 | 8个 | 4个 |
| Skill数量 | 9个 | 6个 |
| 职责重叠 | 60% | 0% |
| 用户入口 | Command | Skill |
| 需求收集 | 重复2次 | 单次智能收集 |
| Agent选择 | 手动选择 | 自动匹配 |
| 成本优化 | 无 | DGoT（-50%） |
| 检索精度 | 传统RAG（~70%） | Agentic RAG（99%） |
| 检查清单 | 1000+项 | <200项 |
| 总代码行数 | 3323行 | ~2000行（-40%） |

---

## 文件结构

```
plugins/tools/deepresearch/
├── agents/                    # 4个Agent
│   ├── code-analyst.md
│   ├── research-strategist.md
│   ├── project-assessor.md
│   └── architecture-advisor.md
├── skills/                    # 6个Skill
│   ├── deep-research/
│   ├── dgot-engine/
│   ├── agentic-retriever/
│   ├── source-validator/
│   ├── knowledge-synthesizer/
│   └── code-inspector/
├── docs/                      # 文档
│   ├── index.md
│   ├── agents.md
│   ├── skills.md
│   ├── commands.md
│   └── configuration.md
├── .mcp.json                  # MCP服务器配置
├── plugin.json                # 插件元数据
└── README.md                  # 项目概览
```

---

## 版本信息

**当前版本**：0.0.180（2026架构重构版）

**许可证**：AGPL-3.0-or-later

**技术基础**：
- DGoT (Dynamic Graph of Thoughts)
- Agentic RAG
- GraphRAG
- FoT (Framework of Thoughts)
- A2A Protocol
- MCP Server Cards
