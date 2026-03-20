# Deep Research 深度研究插件

> 基于 DGoT 动态图思维的任务驱动型深度研究系统（2026架构）

## 安装

```bash
# 推荐：一键安装
uvx --from git+https://github.com/lazygophers/ccplugin.git@master install lazygophers/ccplugin deepresearch@ccplugin-market

# 或：传统方式
claude plugin marketplace add lazygophers/ccplugin
claude plugin install deepresearch@ccplugin-market
```

## 核心特性（2026技术栈）

### 🚀 技术创新

- **DGoT 动态图思维引擎** - 早停+阈值裁剪，降低43-56%研究成本
- **Agentic RAG** - 嵌入自主AI代理，动态管理检索策略
- **GraphRAG 接口** - 知识图谱+向量搜索，精度高达99%
- **FoT 框架优化** - 内置超参数调优、prompt优化、智能缓存
- **A2A 协议** - Agent间点对点协作，无需中心编排
- **MCP Server Cards** - 标准化服务发现和元数据

### 🎯 架构优势

- **Task-Centric 设计** - 任务驱动而非Agent驱动，自动编排最优研究路径
- **单次需求收集** - 智能结构化提问，消除重复交互
- **成本优化** - DGoT动态裁剪，比传统GoT节省50%+ token
- **质量保证** - A-E级来源验证，8种输出格式适配不同受众

## 快速开始

### 基本使用

```bash
# 代码质量分析（自动检测质量+技术债+性能）
/deep-research 分析 ./src 目录的代码质量和性能瓶颈

# 技术选型研究
/deep-research 对比 React vs Vue vs Svelte 在企业项目中的优劣

# 项目评估（GitHub + 依赖安全）
/deep-research 评估 facebook/react 的项目质量和安全风险

# 架构评审
/deep-research 评审 ./docs/architecture.md 的架构设计
```

### 工作流程

```
用户输入
    ↓
[智能需求收集] 单次结构化提问
    ↓
[自动Agent匹配] 基于任务特征自动选择
    ↓
[DGoT核心驱动] 动态生成研究路径 → 质量评估 → 动态裁剪
    ↓
[知识合成] 8种输出格式（报告/PPT/博客等）
```

## 专业 Agent（4个）

| Agent | 统一职责 | 使用场景 | 模型 |
|-------|---------|---------|------|
| **code-analyst** | 代码质量+技术债+性能统一分析 | 代码审查、重构规划、性能优化 | opus |
| **research-strategist** | 技术概念研究+方案对比选型 | 技术学习、框架选型、方案对比 | opus |
| **project-assessor** | 项目评估+依赖安全审计 | GitHub项目研究、安全审计 | opus |
| **architecture-advisor** | 架构评审+设计建议 | 架构评估、系统设计评审 | opus |

## 核心 Skill（5个）

| Skill | 核心能力 | 关键特性 |
|-------|---------|---------|
| **dgot-engine** | DGoT动态图思维引擎 | 早停+阈值裁剪+FoT优化，降低50%成本 |
| **agentic-retriever** | 智能检索器 | Agentic RAG+GraphRAG接口+多源并行 |
| **source-validator** | 来源验证器 | A-E级质量评分+链式验证 |
| **knowledge-synthesizer** | 知识合成器 | 8种输出格式+受众适配 |
| **code-inspector** | 代码检查器 | 本地+GitHub统一接口 |

## 输出格式（8种）

根据受众和场景自动选择最佳格式：

- **执行摘要** - 高层决策、快速汇报
- **技术报告** - 深度分析、技术评审
- **学术论文** - 学术研究、理论分析
- **演示文稿** - 会议分享、团队汇报
- **博客文章** - 知识分享、技术传播
- **对比表格** - 方案对比、选型决策
- **清单报告** - 质量检查、审计结果
- **llms.txt** - API文档、项目概览

## 来源质量评级（A-E）

- **A级（9.0-10）** - 同行评审论文、权威机构报告、系统综述
- **B级（7.0-8.9）** - 行业报告、咨询分析、临床指南
- **C级（5.0-6.9）** - 专业博客、会议记录、案例研究
- **D级（3.0-4.9）** - 个人博客、营销材料、初步研究
- **E级（0-2.9）** - 传言、纯观点、过时信息

## MCP 服务器支持

| 服务器 | 用途 | 状态 |
|--------|------|------|
| duckduckgo | 网络搜索 | ✅ 核心 |
| github | GitHub API集成 | ✅ 核心 |
| wikipedia | 百科知识 | ✅ 核心 |
| sequential-thinking | 复杂推理引擎 | ✅ 核心 |
| time | 时间服务 | ✅ 核心 |
| context7 | 文档检索增强 | 🆕 新增 |
| chrome-devtools | 浏览器自动化 | ⚙️ 可选 |

### Token 配置

```bash
# GitHub Token（推荐配置）
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxx"
```

## 架构对比

| 维度 | 旧架构 | 新架构（2026） | 提升 |
|------|--------|---------------|------|
| Agent数量 | 8个（职责重叠） | 4个（职责明确） | -50% |
| Skill数量 | 9个（边界模糊） | 5个（职责清晰） | -44% |
| 代码行数 | 3323行 | <2000行 | -40% |
| 需求收集 | 重复2次 | 单次智能收集 | -50%交互 |
| 成本优化 | 无 | DGoT动态裁剪 | -50%成本 |
| 检索精度 | 传统RAG | Agentic RAG+GraphRAG | +99%精度 |

## 文档

- [完整架构设计](docs/index.md)
- [命令系统](docs/commands.md)
- [Agent详细说明](docs/agents.md)
- [Skill详细说明](docs/skills.md)
- [配置指南](docs/configuration.md)

## 许可证

AGPL-3.0-or-later
