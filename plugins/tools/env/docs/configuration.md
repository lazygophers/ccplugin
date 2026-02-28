# 配置指南

Env 插件的配置选项。

## 环境文件

### 文件位置

| 文件 | 位置 | 优先级 |
|------|------|--------|
| `.claude/.env` | 项目根目录 | 低 |
| `.claude/.env.local` | 项目根目录 | 高 |

### 文件格式

```bash
# .claude/.env

# API 配置
API_KEY=your_api_key
API_URL=https://api.example.com

# 数据库配置
DATABASE_URL=postgresql://localhost:5432/mydb

# 调试配置
DEBUG=true
LOG_LEVEL=info
```

## 优先级规则

当同一变量在多个文件中定义时：

```
.env.local > .env
```

示例：

```bash
# .claude/.env
API_KEY=production_key

# .claude/.env.local
API_KEY=development_key

# 最终值
API_KEY=development_key
```

## 自动加载

插件在会话开始时会自动运行（通过 SessionStart hook），加载环境变量到会话中。

### 加载流程

1. 检查 `.claude/.env` 文件
2. 检查 `.claude/.env.local` 文件
3. 合并变量（.env.local 优先）
4. 注入到会话环境

## 变量引用

在插件配置中引用环境变量：

```json
{
  "mcpServers": {
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

## 安全建议

### 应该忽略的文件

将 `.env.local` 添加到 `.gitignore`：

```gitignore
# 环境变量
.claude/.env.local
```

### 不应该提交的内容

- 敏感 API 密钥
- 数据库密码
- 认证令牌
- 私有配置

### 可以提交的内容

- 非敏感配置
- 默认值示例
- 开发环境配置
