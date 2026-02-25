# Deep Research 深度研究插件

> 基于图思维框架（Graph of Thoughts）的多智能体深度研究系统

## 安装

```bash
# 推荐：一键安装
uvx --from git+https://github.com/lazygophers/ccplugin.git@master install lazygophers/ccplugin deepresearch@ccplugin-market

# 或：传统方式
claude plugin marketplace add lazygophers/ccplugin
claude plugin install deepresearch@ccplugin-market
```

## 功能特性

### 🎯 核心功能

- **多智能体研究系统** - 并行执行多维度研究任务
- **图思维框架** - 智能优化研究路径和资源分配
- **引用验证系统** - A-E级质量评估和链式验证
- **知识合成引擎** - 自动整合多源发现生成综合报告
- **智能问题优化** - 将模糊问题转化为结构化研究计划

### 🔍 研究场景支持

- **技术研究** - 技术原理、实现方案、性能分析
- **市场研究** - 市场规模、竞争格局、用户需求
- **政策研究** - 监管环境、合规要求、政策影响
- **学术研究** - 文献综述、理论分析、创新发现
- **行业分析** - 发展趋势、机会识别、风险评估

## 快速开始

### 基本使用

```bash
# 本地代码分析
/deep-research 本地代码分析 --scope ./src

# GitHub项目研究
/deep-research github项目研究 --project facebook/react

# 依赖包分析
/deep-research 依赖包分析 --security

# 关键词探索
/deep-research 关键词探索 "微服务架构"

# 架构分析
/deep-research 架构分析 --design-doc ./architecture.md

# 技术方案搜索
/deep-research 技术方案搜索 "REST vs GraphQL"
```

## 📦 包含组件

| 组件类型 | 名称 | 描述 |
|---------|------|------|
| Skill | `local-code-analysis` | 本地代码分析技能 |
| Skill | `content-retriever-skills` | 内容检索技能 |
| Skill | `question-refiner-skills` | 问题优化技能 |
| Skill | `got-controller-skills` | 图思维控制技能 |
| Skill | `synthesizer` | 知识合成技能 |

## 专业 Agent

| Agent | 职责 | 场景 |
|-------|------|------|
| 本地代码分析专家 | 深度分析本地代码库 | 代码审查、重构分析 |
| GitHub项目研究专家 | 研究开源项目 | 技术选型、竞品分析 |
| 依赖包分析专家 | 分析第三方依赖 | 安全审计、依赖优化 |
| 关键词探索专家 | 深度主题研究 | 概念学习、领域研究 |
| 架构分析专家 | 分析系统架构 | 架构评估、设计评审 |
| 技术方案搜索专家 | 搜索对比技术方案 | 技术选型、方案对比 |

## 来源质量评级

- **A级**：同行评审论文、权威机构报告
- **B级**：专家观点、行业指南
- **C级**：专业博客、案例报告
- **D级**：预印本、初步研究
- **E级**：传言、猜测

## 配置选项

### MCP 服务器支持

| 服务器 | 用途 |
|--------|------|
| chrome-devtools | 浏览器自动化 |
| duckduckgo | 网络搜索 |
| github | GitHub 集成 |
| gitlab | GitLab 集成 |
| wikipedia | 百科知识 |
| sequential-thinking | 复杂推理 |

### Token 配置

```bash
# GitHub Token
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxx"

# GitLab Token
export GITLAB_TOKEN="glpat-xxxxxxxxxxxxxxxxxxxx"
```

## 许可证

AGPL-3.0-or-later
