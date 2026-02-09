# Plugin Manifest 配置

## 标准格式

```json
{
  "name": "plugin-name",
  "version": "0.0.1",
  "description": "插件简短描述（1-2句话）",
  "author": {
    "name": "Author Name",
    "email": "author@example.com",
    "url": "https://github.com/username"
  },
  "homepage": "https://github.com/...",
  "repository": "https://github.com/...",
  "license": "MIT",
  "keywords": ["keyword1", "keyword2"],
  "commands": [
    "./commands/command.md"
  ],
  "agents": [
    "./agents/agent.md"
  ],
  "skills": "./skills/",
  "mcpServers": "./.mcp.json",
  "outputStyles": "./styles/",
  "lspServers": "./.lsp.json"
}
```

## 字段详解

### name（必需）

插件唯一标识符：

```json
{
  "name": "task"
}
```

**要求：**
- 小写字母+连字符
- 唯一性（市场内）
- 最多 64 字符

### version（必需）

语义化版本号：

```json
{
  "version": "0.0.108"
}
```

**格式：** `major.minor.patch`

### description（必需）

简短描述，用于插件发现：

```json
{
  "description": "插件功能简短描述"
}
```

**要求：**
- 1-2 句话
- 包含功能关键词
- 最多 1024 字符

### author（可选）

作者信息：

```json
{
  "author": {
    "name": "Author Name",
    "email": "author@example.com",
    "url": "https://github.com/username"
  }
}
```

### commands（可选）

命令列表：

```json
{
  "commands": [
    "./commands/add.md",
    "./commands/list.md",
    "./commands/delete.md"
  ]
}
```

### agents（可选）

代理列表：

```json
{
  "agents": [
    "./agents/dev.md",
    "./agents/review.md"
  ]
}
```

### skills（可选）

技能目录路径：

```json
{
  "skills": "./skills/"
}
```

### mcpServers（可选）

MCP 服务器配置：

```json
{
  "mcpServers": "./.mcp.json"
}
```

### outputStyles（可选）

输出样式目录：

```json
{
  "outputStyles": "./styles/"
}
```

### lspServers（可选）

LSP 服务器配置：

```json
{
  "lspServers": "./.lsp.json"
}
```

## 完整示例

```json
{
  "name": "task",
  "version": "0.0.108",
  "description": "项目任务管理 - 添加、列出和跟踪开发任务",
  "author": {
    "name": "Author Name",
    "email": "author@example.com",
    "url": "https://github.com/lazygophers"
  },
  "homepage": "https://github.com/lazygophers/ccplugin",
  "repository": "https://github.com/lazygophers/ccplugin",
  "license": "MIT",
  "keywords": [
    "task",
    "management",
    "productivity"
  ],
  "commands": [
    "./commands/add.md",
    "./commands/list.md",
    "./commands/stats.md"
  ],
  "agents": [
    "./agents/planner.md"
  ],
  "skills": "./skills/",
  "mcpServers": "./.mcp.json"
}
```
