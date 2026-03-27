# 配置指南（2026架构）

Deep Research 插件的MCP服务器和环境配置。

## MCP 服务器配置

### 核心服务器（必需）

| 服务器 | 用途 | 优先级 | 依赖Skills |
|--------|------|--------|-----------|
| **duckduckgo** | 网络搜索引擎 | 必需 | agentic-retriever |
| **wikipedia** | 百科知识库 | 必需 | research-strategist |
| **sequential-thinking** | 复杂推理引擎 | 必需 | architecture-advisor |
| **time** | 时间服务 | 必需 | source-validator |

### 可选服务器

| 服务器 | 用途 | 使用场景 |
|--------|------|---------|
| **context7** | 文档检索增强（2026新增） | 框架文档、API参考 |
| **chrome-devtools** | 浏览器自动化 | UI测试、页面截图 |

---

## 配置文件（.mcp.json）

### 标准配置

```json
{
  "mcpServers": {
    "duckduckgo": {
      "type": "stdio",
      "command": "uvx",
      "args": ["duckduckgo-mcp-server"],
      "env": {
        "ALL_PROXY": "${PROXY_URL}",
        "HTTPS_PROXY": "${PROXY_URL}",
        "HTTP_PROXY": "${PROXY_URL}"
      },
      "metadata": {
        "description": "网络搜索引擎 - agentic-retriever核心依赖",
        "priority": "required",
        "usage": "信息检索、技术文档搜索、市场数据"
      }
    }
  }
}
```

### metadata 字段说明（MCP Server Cards标准）

- **description**：服务器功能描述
- **priority**：优先级（required | optional）
- **usage**：具体使用场景

---

## 环境变量配置

### GitHub CLI（gh 命令）

GitHub 功能通过 `gh` CLI 实现，无需 MCP 服务器：

```bash
# 安装 gh CLI
brew install gh

# 登录认证
gh auth login

# 验证
gh auth status
```

**常用命令**：
- `gh repo view` - 仓库信息
- `gh issue list` - Issue列表
- `gh pr list` - PR列表
- `gh api repos/{owner}/{repo}/contents/{path}` - 文件内容

### 代理配置（可选）

```bash
# 设置代理（仅在需要时）
export PROXY_URL="http://127.0.0.1:7890"

# 或使用其他代理
export PROXY_URL="socks5://127.0.0.1:1080"
```

**注意**：PROXY_URL 无默认值，不设置则不使用代理。

---

## 时区配置

time MCP服务器默认时区：

```json
"time": {
  "command": "uvx",
  "args": [
    "mcp-server-time",
    "--local-timezone=Asia/Shanghai"
  ]
}
```

**可选时区**：
- `Asia/Shanghai` - 中国标准时间
- `America/New_York` - 美国东部时间
- `Europe/London` - 英国时间
- `UTC` - 协调世界时

---

## 配置验证

### 检查MCP服务器状态

```bash
# 列出所有MCP服务器
claude mcp list

# 测试特定服务器
claude mcp test duckduckgo

# 验证 gh CLI
gh auth status
```

### 检查环境变量

```bash
# 验证GitHub Token
echo $GITHUB_TOKEN | wc -c  # 应该>20字符

# 验证代理设置
echo $PROXY_URL
```

---

## 故障排除

### GitHub CLI 认证失败

**症状**：project-assessor无法获取GitHub数据

**解决**：
1. 运行 `gh auth status` 检查认证状态
2. 运行 `gh auth login` 重新认证
3. 确保网络连接正常

### 代理连接失败

**症状**：duckduckgo搜索超时

**解决**：
1. 检查代理服务是否运行
2. 验证PROXY_URL格式正确
3. 尝试不使用代理（`unset PROXY_URL`）

### MCP服务器启动失败

**症状**：服务器无法启动

**解决**：
```bash
# 更新MCP服务器
uvx --upgrade duckduckgo-mcp-server

# 清理缓存
rm -rf ~/.cache/uv
```

---

## 最小配置

仅使用核心功能的最小配置：

```json
{
  "mcpServers": {
    "duckduckgo": {
      "type": "stdio",
      "command": "uvx",
      "args": ["duckduckgo-mcp-server"]
    }
  }
}
```

**说明**：
- GitHub 功能通过 `gh` CLI 提供，无需 MCP 服务器
- 无代理支持、无metadata元数据

---

## 与旧架构对比

| 维度 | 旧架构 | 新架构（2026） |
|------|--------|---------------|
| MCP服务器数 | 7个 | 5个（移除gitlab/github，新增context7，GitHub改用gh CLI） |
| metadata支持 | ❌ 无 | ✅ MCP Server Cards标准 |
| 代理默认值 | 有默认值 | 无默认值（按需设置） |
| 优先级标识 | ❌ 无 | ✅ required/optional |
| 使用场景说明 | ❌ 无 | ✅ 详细的usage字段 |
