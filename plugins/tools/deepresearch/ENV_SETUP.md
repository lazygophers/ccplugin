# 环境配置说明

本文档说明如何配置deepresearch插件所需的环境变量。

## 必需的环境变量

### Token配置

#### GitHub Token

GitHub MCP服务器需要Personal Access Token (PAT)才能访问私有仓库和获取更高的API速率限制。

**获取GitHub Token**：

1. 访问 [GitHub Token设置](https://github.com/settings/tokens)
2. 点击 "Generate new token" → "Generate new token (classic)"
3. 设置Token名称（如：`deepresearch-mcp`）
4. 选择权限：
   - ✅ `repo` - 完整仓库访问权限
   - ✅ `read:org` - 读取组织信息
5. 点击 "Generate token"
6. **重要**：复制token（只会显示一次）

**配置环境变量**：

```bash
# 临时设置（当前会话）
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxx"

# 永久设置（添加到 ~/.zshrc 或 ~/.bashrc）
echo 'export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxx"' >> ~/.zshrc
source ~/.zshrc
```

#### GitLab Token

GitLab MCP服务器需要Personal Access Token才能访问私有项目和API。

**获取GitLab Token**：

1. 访问 [GitLab Token设置](https://gitlab.com/-/user_settings/personal_access_tokens)
2. 点击 "Add new token"
3. 设置Token名称（如：`deepresearch-mcp`）
4. 设置到期日期（建议：90天或更长）
5. 选择权限：
   - ✅ `api` - 完整API访问
   - ✅ `read_api` - 读取API
   - ✅ `read_repository` - 读取仓库
6. 点击 "Create personal access token"
7. **重要**：复制token（只会显示一次）

**配置环境变量**：

```bash
# 临时设置（当前会话）
export GITLAB_TOKEN="glpat-xxxxxxxxxxxxxxxxxxxx"

# 永久设置（添加到 ~/.zshrc 或 ~/.bashrc）
echo 'export GITLAB_TOKEN="glpat-xxxxxxxxxxxxxxxxxxxx"' >> ~/.zshrc
source ~/.zshrc
```

---

## 验证配置

### 验证GitHub Token

```bash
# 测试GitHub API访问
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user
```

成功响应示例：
```json
{
  "login": "your-username",
  "id": 12345678,
  ...
}
```

### 验证GitLab Token

```bash
# 测试GitLab API访问
curl -H "PRIVATE-TOKEN: $GITLAB_TOKEN" https://gitlab.com/api/v4/user
```

成功响应示例：
```json
{
  "id": 12345678,
  "username": "your-username",
  ...
}
```

---

## 代理配置

### 环境变量

deepresearch插件支持通过以下环境变量配置代理：

```bash
# 方式1：使用PROXY_URL（推荐）
export PROXY_URL="http://127.0.0.1:7890"

# 方式2：使用标准代理变量
export HTTP_PROXY="http://127.0.0.1:7890"
export HTTPS_PROXY="http://127.0.0.1:7890"
export ALL_PROXY="http://127.0.0.1:7890"
```

### 默认配置

如果未设置环境变量，插件将使用以下默认值：

| 变量 | 默认值 |
|------|--------|
| `PROXY_URL` | `http://127.0.0.1:7890` |
| `HTTP_PROXY` | `http://127.0.0.1:7890` |
| `HTTPS_PROXY` | `http://127.0.0.1:7890` |
| `ALL_PROXY` | `http://127.0.0.1:7890` |

### 优先级

代理配置的优先级顺序：
1. `PROXY_URL` - 最高优先级
2. `HTTP_PROXY` / `HTTPS_PROXY` / `ALL_PROXY` - 标准代理变量
3. 默认值 `http://127.0.0.1:7890`

### 永久配置

```bash
# 添加到 ~/.zshrc 或 ~/.bashrc
cat >> ~/.zshrc << 'EOF'
# DeepResearch Proxy Configuration
export PROXY_URL="http://127.0.0.1:7890"
# 或使用标准代理变量（备选）
# export HTTP_PROXY="http://127.0.0.1:7890"
# export HTTPS_PROXY="http://127.0.0.1:7890"
# export ALL_PROXY="http://127.0.0.1:7890"
EOF

# 重新加载配置
source ~/.zshrc
```

---

## 安全建议

### Token安全

1. **不要提交到版本控制**：确保 `.gitignore` 包含以下内容
   ```gitignore
   .env
   .env.local
   .env.*.local
   ```

2. **使用环境变量**：永远不要在代码中硬编码Token

3. **定期轮换**：建议每90天更新一次Token

4. **最小权限原则**：只授予必需的权限

5. **监控使用情况**：定期检查Token的使用记录

### 本地开发环境

```bash
# 推荐方式：使用 .env 文件（不提交到git）
cat > .env.local << EOF
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
GITLAB_TOKEN=glpat-xxxxxxxxxxxxxxxxxxxx
EOF

# 添加到 .gitignore
echo ".env.local" >> .gitignore
```

---

## 故障排除

### 问题：GitHub API 401 错误

**错误信息**：`Bad credentials (HTTP 401)`

**解决方案**：
1. 检查Token是否正确：`echo $GITHUB_TOKEN`
2. 确认Token未过期
3. 验证Token权限是否包含 `repo`

### 问题：GitLab API 401 错误

**错误信息**：`401 Unauthorized`

**解决方案**：
1. 检查Token是否正确：`echo $GITLAB_TOKEN`
2. 确认Token未过期
3. 验证Token权限是否包含 `api`

### 问题：代理连接失败

**错误信息**：`Failed to connect to 127.0.0.1:7890`

**解决方案**：
1. 确认代理服务正在运行
2. 检查代理端口是否正确
3. 尝试直接访问（不使用代理）

### 问题：环境变量未生效

**解决方案**：
```bash
# 重新加载shell配置
source ~/.zshrc  # 或 source ~/.bashrc

# 验证环境变量
echo $GITHUB_TOKEN
echo $GITLAB_TOKEN
```

---

## 完整配置示例

### macOS / Linux (~/.zshrc)

```bash
# Git Tokens
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxx"
export GITLAB_TOKEN="glpat-xxxxxxxxxxxxxxxxxxxx"

# 代理（如果需要）
# export http_proxy="http://127.0.0.1:7890"
# export https_proxy="http://127.0.0.1:7890"
# export all_proxy="http://127.0.0.1:7890"
```

### Windows PowerShell

```powershell
# Git Tokens
$env:GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxx"
$env:GITLAB_TOKEN="glpat-xxxxxxxxxxxxxxxxxxxx"

# 永久设置
[System.Environment]::SetEnvironmentVariable('GITHUB_TOKEN', 'ghp_xxxxxxxxxxxxxxxxxxxx', 'User')
[System.Environment]::SetEnvironmentVariable('GITLAB_TOKEN', 'glpat-xxxxxxxxxxxxxxxxxxxx', 'User')
```

---

## 相关链接

- [GitHub Personal Access Tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)
- [GitLab Personal Access Tokens](https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html)
- [MCP Specification](https://modelcontextprotocol.io/)
