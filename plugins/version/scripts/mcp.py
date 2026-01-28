"""
Version MCP Server - 版本管理 MCP 服务器
"""
import asyncio
import json
import sys

from lib import logging
from version import get_version, init_version, inc_major, inc_minor, inc_patch


class VersionMCPServer:
    """版本管理 MCP 服务器"""

    def __init__(self):
        self.tools = self._register_tools()

    def _register_tools(self):
        """注册所有可用的工具"""
        return {
            "get_version": {
                "name": "get_version",
                "description": "获取当前项目的版本号",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            "init_version": {
                "name": "init_version",
                "description": "初始化版本文件（如果不存在则创建默认版本 0.0.1.0）",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            "inc_major": {
                "name": "inc_major",
                "description": "更新主版本号（第一级），其余级别重置为 0。例如：1.2.3.4 -> 2.0.0.0",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            "inc_minor": {
                "name": "inc_minor",
                "description": "更新次版本号（第二级），patch 和 build 重置为 0。例如：1.2.3.4 -> 1.3.0.0",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            "inc_patch": {
                "name": "inc_patch",
                "description": "更新补丁版本号（第三级），build 重置为 0。例如：1.2.3.4 -> 1.2.4.0",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        }

    async def handle_request(self, request: dict) -> dict:
        """处理 MCP 请求"""
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")

        try:
            if method == "tools/list":
                return await self._tools_list()
            elif method == "tools/call":
                return await self._tools_call(params, request_id)
            elif method == "initialize":
                return await self._initialize(params)
            elif method == "ping":
                return {"result": {}}
            else:
                logging.warn(f"Unknown method: {method}")
                return {
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    },
                    "id": request_id
                }
        except Exception as e:
            logging.error(f"Request handling error: {e}")
            return {
                "error": {
                    "code": -32603,
                    "message": str(e)
                },
                "id": request_id
            }

    async def _initialize(self, params: dict) -> dict:
        """初始化握手"""
        try:
            return {
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "version-mcp-server",
                        "version": "1.0.0"
                    }
                }
            }
        except Exception as e:
            return {
                "error": {
                    "code": -32603,
                    "message": f"Initialize error: {str(e)}"
                }
            }

    async def _tools_list(self) -> dict:
        """列出所有可用工具"""
        try:
            return {
                "result": {
                    "tools": list(self.tools.values())
                }
            }
        except Exception as e:
            return {
                "error": {
                    "code": -32603,
                    "message": f"Tools list error: {str(e)}"
                }
            }

    async def _tools_call(self, params: dict, request_id) -> dict:
        """调用工具"""
        name = params.get("name")
        arguments = params.get("arguments", {})

        if name not in self.tools:
            logging.warn(f"Unknown tool requested: {name}")
            return {
                "error": {
                    "code": -32602,
                    "message": f"Unknown tool: {name}"
                },
                "id": request_id
            }

        try:
            logging.info(f"Executing tool: {name}")
            result = await self._execute_tool(name, arguments)
            return {
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": result
                        }
                    ]
                },
                "id": request_id
            }
        except Exception as e:
            logging.error(f"Tool execution error for {name}: {e}")
            return {
                "error": {
                    "code": -32603,
                    "message": f"Tool execution error: {str(e)}"
                },
                "id": request_id
            }

    async def _execute_tool(self, name: str, arguments: dict) -> str:
        """执行具体的工具逻辑"""
        try:
            if name == "get_version":
                version = get_version()
                return f"当前版本: {version}"
            elif name == "init_version":
                init_version()
                return "版本文件已初始化"
            elif name == "inc_major":
                inc_major()
                new_version = get_version()
                return f"主版本号已更新，当前版本: {new_version}"
            elif name == "inc_minor":
                inc_minor()
                new_version = get_version()
                return f"次版本号已更新，当前版本: {new_version}"
            elif name == "inc_patch":
                inc_patch()
                new_version = get_version()
                return f"补丁版本号已更新，当前版本: {new_version}"
            else:
                raise ValueError(f"Unknown tool: {name}")
        except Exception as e:
            logging.error(f"Error executing {name}: {e}")
            raise

    async def run(self):
        """启动 MCP 服务器（stdio 模式）"""
        logging.info("MCP server starting")

        # 写入初始化响应
        await self._write_response({
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        })

        # 读取 stdin 并处理请求
        while True:
            try:
                line = await asyncio.get_event_loop().run_in_executor(
                    None, sys.stdin.readline
                )
                if not line:
                    logging.info("EOF received, server shutting down")
                    break

                line = line.strip()
                if not line:
                    continue

                try:
                    request = json.loads(line)
                    response = await self.handle_request(request)

                    # 添加 jsonrpc 版本和请求 ID
                    if "id" in request and "id" not in response:
                        response["id"] = request["id"]
                    if "jsonrpc" not in response:
                        response["jsonrpc"] = "2.0"

                    await self._write_response(response)

                except json.JSONDecodeError as e:
                    logging.error(f"JSON decode error: {e}")
                    await self._write_response({
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32700,
                            "message": f"Parse error: {str(e)}"
                        }
                    })

            except Exception as e:
                logging.error(f"Server loop error: {e}")
                await self._write_response({
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32603,
                        "message": f"Internal error: {str(e)}"
                    }
                })

    async def _write_response(self, response: dict):
        """写入响应到 stdout"""
        try:
            json_str = json.dumps(response, ensure_ascii=False)
            await asyncio.get_event_loop().run_in_executor(
                None, lambda: print(json_str, flush=True)
            )
        except Exception as e:
            logging.error(f"Failed to write response: {e}")
            # 无法写入响应时，至少尝试输出到 stderr
            try:
                print(f"Response error: {e}", file=sys.stderr, flush=True)
            except:
                pass  # 完全无法输出时放弃
