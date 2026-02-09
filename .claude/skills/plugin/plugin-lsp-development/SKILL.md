---
name: plugin-lsp-development
description: 插件 LSP 开发指南 - 当用户需要为插件配置语言服务器协议时使用。覆盖 .lsp.json 配置、服务器类型和集成方式。
context: fork
agent: lsp
---

# 插件 LSP 开发指南

## LSP 配置格式

```
.lsp.json                    # LSP 配置
```

## 配置示例

### stdio 类型

```json
{
  "lspServers": {
    "pyls": {
      "type": "stdio",
      "command": "pyls",
      "args": ["--check-parent-process"]
    }
  }
}
```

### SSE 类型

```json
{
  "lspServers": {
    "rust-analyzer": {
      "type": "sse",
      "url": "http://localhost:3000"
    }
  }
}
```

### HTTP 类型

```json
{
  "lspServers": {
    "custom-lsp": {
      "type": "http",
      "url": "http://localhost:8080",
      "headers": {
        "Authorization": "Bearer ${LSP_TOKEN}"
      }
    }
  }
}
```

## 服务器类型

| 类型 | 说明 | 用例 |
|------|------|------|
| `stdio` | 标准输入输出 | pyls, rust-analyzer |
| `sse` | Server-Sent Events | 远程 LSP 服务 |
| `http` | HTTP 轮询 | Web-based LSP |
| `websocket` | WebSocket | 实时协作 LSP |

## 插件中配置 LSP

在 `plugin.json` 中无需额外配置，`.lsp.json` 会自动加载。

## 相关技能

- [plugin-development](plugin-development/SKILL.md) - 插件开发
- [plugin-mcp-development](plugin-mcp-development/SKILL.md) - 插件 MCP 开发
