---
name: plugin-mcp-development
description: 插件 MCP 开发指南 - 当用户需要为插件添加 Model Context Protocol 服务器时使用。覆盖 .mcp.json 配置、MCP 服务器类型和实现方式。
context: fork
agent: mcp
---

# 插件 MCP 开发指南

## MCP 配置格式

```
.mcp.json                    # MCP 配置
```

## 配置示例

### stdio 类型

```json
{
  "mcpServers": {
    "my-server": {
      "command": "uv",
      "args": ["run", "--directory", "${CLAUDE_PLUGIN_ROOT}", "python", "-m", "mcp_server"]
    }
  }
}
```

### SSE 类型

```json
{
  "mcpServers": {
    "remote-mcp": {
      "url": "https://mcp.example.com/sse"
    }
  }
}
```

### 带环境变量

```json
{
  "mcpServers": {
    "my-server": {
      "command": "uv",
      "args": ["run", "--directory", "${CLAUDE_PLUGIN_ROOT}", "python", "-m", "mcp_server"],
      "env": {
        "API_KEY": "${OPENAI_API_KEY}",
        "DATABASE_URL": "${CLAUDE_PLUGIN_ROOT}/data.db"
      }
    }
  }
}
```

## MCP 服务器类型

| 类型 | 说明 | 用例 |
|------|------|------|
| `stdio` | 标准输入输出进程 | 本地 CLI 工具 |
| `sse` | Server-Sent Events | 远程 MCP 服务 |
| `http` | HTTP 轮询 | Web APIs |

## MCP 服务器实现

### Python 实现模板

```python
# scripts/mcp.py
import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server


class MyMCPServer:
    async def handle_request(self, request: dict) -> dict:
        """处理 MCP 请求。"""
        method = request.get("method")
        if method == "tools/list":
            return self.list_tools()
        elif method == "tools/call":
            return self.call_tool(request)
        return {"error": "Unknown method"}

    def list_tools(self) -> dict:
        """返回可用工具列表。"""
        return {
            "tools": [
                {
                    "name": "my_tool",
                    "description": "我的工具描述",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "param": {"type": "string"}
                        }
                    }
                }
            ]
        }

    def call_tool(self, request: dict) -> dict:
        """调用工具。"""
        tool_name = request.get("params", {}).get("name")
        arguments = request.get("params", {}).get("arguments", {})
        # 实现工具逻辑
        return {"result": "success"}


async def main():
    server = Server("my-mcp-server")
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
```

### main.py 集成

```python
# scripts/main.py
@click.group()
def main(): pass


@main.command()
def mcp():
    """MCP server mode"""
    from scripts.mcp import main as mcp_main
    asyncio.run(mcp_main())
```

## 插件中配置 MCP

```json
{
  "mcpServers": {
    "my-server": {
      "command": "uv",
      "args": ["run", "--directory", "${CLAUDE_PLUGIN_ROOT}", "./scripts/main.py", "mcp"]
    }
  }
}
```

## 相关技能

- [plugin-script-development](plugin-script-development/SKILL.md) - 插件脚本开发
- [plugin-hook-development](plugin-hook-development/SKILL.md) - 插件钩子开发
