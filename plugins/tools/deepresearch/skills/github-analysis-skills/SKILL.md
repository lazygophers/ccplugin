---
name: github-analysis-skills
description: GitHub分析技能 - 分析GitHub项目、仓库、代码贡献、社区活跃度等GitHub相关内容
user-invocable: false
---

## GitHub分析技能

专门用于分析GitHub平台上的项目和内容的技能，集成了GitHub MCP服务器以提供强大的数据获取和分析能力。

### 核心能力

#### 项目分析
- 项目元数据提取
- 代码库结构分析
- 开发活动统计
- 社区健康度评估

#### 数据获取
- GitHub API调用（通过MCP服务器）
- 仓库信息检索
- 提交历史分析
- Issue和PR分析

#### 指标计算
- Stars/Forks/Watchers趋势
- 贡献者活跃度
- 代码变更频率
- Issue和PR处理速度

### MCP工具集成

本技能使用以下MCP服务器提供的工具：

#### GitHub MCP服务器工具

**环境要求**：
- 需设置环境变量 `GITHUB_TOKEN`（Personal Access Token）
- 配置代理：`http://127.0.0.1:7890`

**可用工具**：

| 工具名称 | 功能 | 使用场景 |
|---------|------|---------|
| `mcp__github__get_repository` | 获取仓库详细信息 | 获取项目描述、语言、统计信息 |
| `mcp__github__search_repositories` | 搜索仓库 | 按条件查找相关项目 |
| `mcp__github__list_issues` | 列出Issues | 分析问题分布和处理情况 |
| `mcp__github__list_pull_requests` | 列出PRs | 评估代码审查和贡献质量 |
| `mcp__github__get_file_contents` | 获取文件内容 | 读取README、配置文件等 |
| `mcp__github__list_commits` | 列出提交记录 | 分析开发活动和贡献趋势 |
| `mcp__github__list_contributors` | 列出贡献者 | 评估社区参与度和活跃度 |
| `mcp__github__list_releases` | 列出发布版本 | 分析版本发布节奏 |
| `mcp__github__get_branches` | 获取分支信息 | 分析开发分支策略 |

#### 使用示例

**获取仓库基本信息**：
```
输入参数：
- owner: "facebook"
- repo: "react"

获取：
- 项目描述、Star数、Fork数
- 主要编程语言
- 开源协议
- 创建和更新时间
```

**分析活跃度**：
```
1. 使用 list_commits 获取最近30天提交记录
2. 使用 list_contributors 获取贡献者列表
3. 使用 list_pull_requests 分析PR合并速度
4. 计算活跃度指标
```

**评估代码质量**：
```
1. 使用 get_file_contents 读取 README.md
2. 使用 get_file_contents 读取 CONTRIBUTING.md
3. 使用 list_pull_requests 分析代码审查流程
4. 检查CI/CD配置
```

### DuckDuckGo MCP服务器工具

用于搜索GitHub相关的最新信息和讨论：

| 工具名称 | 功能 | 使用场景 |
|---------|------|---------|
| `mcp__duckduckgo__search` | 网络搜索 | 搜索GitHub项目相关文章、讨论 |
| `mcp__duckduckgo__fetch_content` | 获取网页内容 | 读取技术博客、对比文章 |

**使用示例**：
```
搜索 "facebook react best practices 2024"
获取 React 官方文档和社区最佳实践
```

### Wikipedia MCP服务器工具

用于获取技术背景和概念解释：

| 工具名称 | 功能 | 使用场景 |
|---------|------|---------|
| `mcp__duckduckgo__search` + Wikipedia | 搜索百科知识 | 理解技术概念、框架背景 |

### 使用方式

当需要以下分析时激活此技能：
- 分析GitHub项目的基本信息
- 评估项目的社区活跃度
- 研究项目的开发趋势
- 对比多个GitHub项目

### 最佳实践

#### Token配置
```bash
# 必需：设置GitHub Token
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxx"

# 验证Token
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user
```

#### API速率限制
- 未认证：60次/小时
- Token认证：5000次/小时
- 建议使用Token以提高速率限制

#### 数据收集策略
1. **优先使用缓存**：避免重复调用相同API
2. **批量获取**：一次获取多个数据点
3. **渐进式加载**：先获取摘要，再按需获取详情
4. **错误处理**：处理API限流和网络错误

#### 分析框架

**项目健康度评分**：
```markdown
- 活跃度 (40%): 提交频率、贡献者数量、PR处理速度
- 质量 (30%): 代码审查、测试覆盖、文档完整性
- 社区 (20%): Stars增长、Issue响应、社区参与
- 维护 (10%): 最近更新、依赖健康、安全修复
```

### 常见任务

#### 任务1：快速项目概览
```markdown
1. get_repository( owner, repo )
2. list_commits( owner, repo, per_page=10 )
3. list_contributors( owner, repo )
4. 生成项目卡片
```

#### 任务2：深度项目分析
```markdown
1. get_repository() - 基本信息
2. list_commits() - 开发活动
3. list_pull_requests() - 代码审查
4. list_issues() - 问题追踪
5. list_releases() - 版本管理
6. get_file_contents() - 代码质量检查
7. 生成综合评估报告
```

#### 任务3：项目对比
```markdown
1. 搜索多个相关项目
2. 对比关键指标
3. 分析优劣势
4. 生成对比报告
```

### 输出格式

分析结果通常包含：
- 项目基本信息表
- 活跃度趋势图
- 贡献者统计
- 质量评估
- 风险提示
- 改进建议

### 相关技能

- Skills(content-retriever) - 获取GitHub文档和资源
- Skills(citation-validator) - 验证项目信息和引用
- Skills(synthesizer) - 整合多源分析结果
- Skills(explorer) - 探索相关项目和替代方案

### 参考资源

- [GitHub MCP Server](https://github.com/modelcontextprotocol/servers/tree/main/src/github)
- [GitHub API文档](https://docs.github.com/en/rest)
- [项目评估指南](../../agents/project-evaluation-agent.md)
