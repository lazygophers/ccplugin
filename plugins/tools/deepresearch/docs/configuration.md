# 配置指南

Deep Research 插件的配置选项。

## MCP 服务器配置

### 支持的 MCP 服务器

| 服务器 | 用途 | 必需 |
|--------|------|------|
| `chrome-devtools` | 浏览器自动化 | 推荐 |
| `duckduckgo` | 网络搜索 | 推荐 |
| `github` | GitHub 集成 | 可选 |
| `gitlab` | GitLab 集成 | 可选 |
| `wikipedia` | 百科知识 | 可选 |
| `sequential-thinking` | 复杂推理 | 可选 |

### 配置示例

```json
{
  "mcpServers": {
    "duckduckgo": {
      "command": "uvx",
      "args": ["mcp-server-duckduckgo"]
    },
    "github": {
      "command": "uvx",
      "args": ["mcp-server-github"],
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      }
    }
  }
}
```

## Token 配置

### GitHub Token

```bash
# 设置 GitHub Token
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxx"
```

### GitLab Token

```bash
# 设置 GitLab Token
export GITLAB_TOKEN="glpat-xxxxxxxxxxxxxxxxxxxx"
```

## 环境变量

| 变量 | 描述 | 必需 |
|------|------|------|
| `GITHUB_TOKEN` | GitHub API Token | GitHub 研究时 |
| `GITLAB_TOKEN` | GitLab API Token | GitLab 研究时 |

## 研究配置

### 深度设置

```yaml
research:
  max_depth: 5        # 最大研究深度
  max_sources: 20     # 最大来源数量
  timeout: 300        # 超时时间（秒）
```

### 质量设置

```yaml
quality:
  min_rating: B       # 最低来源评级
  require_citation: true  # 要求引用
  verify_links: true  # 验证链接
```

### 输出设置

```yaml
output:
  format: markdown    # 输出格式
  include_sources: true   # 包含来源
  include_summary: true   # 包含摘要
```
