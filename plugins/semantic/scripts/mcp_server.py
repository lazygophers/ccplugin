#!/usr/bin/env python3
"""
Semantic Search MCP Server - 语义搜索 MCP 服务器
基于 Model Context Protocol 实现代码语义搜索功能

⚠️ 必须使用 uv 执行此脚本：
  uv run mcp_server.py [options]

依赖：
  - mcp: MCP 协议实现
  - async: 异步 I/O 支持
  - pydantic: 数据验证
  - uvloop: 高性能事件循环（可选）
"""

import warnings
warnings.filterwarnings('ignore')

import asyncio
import json
import sys
import logging
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence
from logging.handlers import RotatingFileHandler

# 添加脚本路径到 sys.path 以导入 semantic.py 的模块
script_path = Path(__file__).parent
sys.path.insert(0, str(script_path))

try:
    from mcp.server.models import InitializationOptions
    from mcp.server import NotificationOptions, Server
    from mcp.types import (
        Resource, Tool, TextContent, ImageContent, EmbeddedResource,
        ListResourcesResult, ListToolsResult, ReadResourceResult,
        GetPromptResult, ListPromptsResult
    )
    from pydantic import BaseModel, Field, validator
except ImportError as e:
    print(f"MCP 依赖安装错误: {e}", file=sys.stderr)
    print("请安装 MCP 依赖: uv pip install mcp", file=sys.stderr)
    sys.exit(1)

# 配置日志（仅文件，不输出到控制台以遵守 MCP stdio 协议）
logger = logging.getLogger("semantic-mcp-server")
logger.setLevel(logging.INFO)

# 禁用 basicConfig 以避免默认的 console handler
# 仅添加文件日志处理程序
log_dir = Path.home() / ".lazygophers" / "ccplugin"
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / "error.log"

# 使用 RotatingFileHandler：最大100MB，保留2份备份
file_handler = RotatingFileHandler(
    str(log_file),
    maxBytes=100 * 1024 * 1024,  # 100MB
    backupCount=2,  # 保留2份备份
    encoding='utf-8'
)
file_handler.setLevel(logging.INFO)  # 捕获 INFO 及以上级别的日志
file_handler.setFormatter(
    logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
)
logger.addHandler(file_handler)

# 防止日志向上传播到 root logger（避免控制台输出）
logger.propagate = False

class SearchRequest(BaseModel):
    """Search request model"""
    query: str = Field(..., description="Search query string")
    limit: int = Field(10, ge=1, le=100, description="Limit on number of results to return")  # default 10, range 1-100
    lang: Optional[str] = Field(None, description="Programming language filter")

    @validator('query')
    def validate_query(cls, v):
        if not v.strip():
            raise ValueError('Query cannot be empty')
        return v.strip()

class SearchResponse(BaseModel):
    """Search response model"""
    results: List[Dict[str, Any]] = Field(default_factory=list)
    error: Optional[str] = None

class SemanticMCPServer:
    """语义搜索 MCP 服务器"""

    def __init__(self):
        self.server = Server("semantic-search")
        self.indexer = None
        self.config_data = None
        self.data_path = None

        # 读取系统提示词
        self.agent_content = self._load_agent_content()

        # 注册 MCP 工具
        self._register_tools()

    def _load_agent_content(self) -> str:
        """加载系统提示词（从 agent_prompt.py 导入内置字符串）"""
        try:
            from agent_prompt import get_semantic_agent_prompt
            logger.info("成功加载系统提示词（从 agent_prompt.py）")
            return get_semantic_agent_prompt()
        except Exception as e:
            logger.error(f"加载系统提示词失败: {e}")
            return self._get_default_prompt()

    def _get_default_prompt(self) -> str:
        """获取默认系统提示词"""
        return """
### 代码语义搜索插件

**使用 semantic 插件进行代码语义搜索**

当需要使用自然语言查询代码时，使用 semantic 插件。其主要功能包括：

- **语义搜索** - 使用自然语言描述查找相关代码
- **代码索引** - 建立代码的向量嵌入索引（支持增量更新）
- **多语言支持** - 支持 17+ 编程语言，针对不同语言优化
- **混合检索** - FastEmbed + CodeModel + Symbol 三引擎融合
- **语言特定优化** - 针对不同语言的解析策略、分块大小、模型推荐

## 使用方式

```bash
# 语义搜索（主要功能）
/semantic-search "如何读取文件"
```

其他管理功能通过 semantic.py 脚本使用。
"""

    def _ensure_indexer_initialized(self):
        """确保索引器已初始化"""
        if self.indexer is None:
            try:
                # 导入索引器（仅支持打包环境 uvx）
                # 在打包环境中，lib 是作为 plugins.semantic.scripts.lib 包存在的
                logger.info("开始加载索引器模块...")
                from lib.indexer import CodeIndexer
                from lib.config import load_config, get_data_path
                from lib.utils import check_and_auto_init
                logger.info("✓ 索引器模块加载成功")

                # 检查初始化状态（MCP 环境中允许未初始化）
                logger.info("检查初始化状态...")
                check_and_auto_init(silent=True)
                logger.info("✓ 初始化状态检查完成")

                # 加载配置（使用默认配置如果不存在）
                logger.info("加载配置...")
                self.config_data = load_config()
                self.data_path = get_data_path()
                logger.info(f"✓ 配置加载成功，数据路径: {self.data_path}")

                # 初始化索引器
                logger.info("初始化 CodeIndexer...")
                self.indexer = CodeIndexer(self.config_data, self.data_path)
                logger.info("✓ CodeIndexer 创建成功")

                logger.info("调用 indexer.initialize()...")
                try:
                    # 尝试初始化索引器（包括模型加载）
                    init_result = self.indexer.initialize()
                    if init_result:
                        logger.info("✓ 索引器初始化成功")
                        return True
                    else:
                        # 初始化失败，但索引结构可能已创建
                        logger.warning("⚠️ 索引器初始化失败（可能是模型加载问题），但索引结构已创建")
                        # 继续运行，搜索请求会返回错误信息
                        return False
                except Exception as e:
                    # 初始化过程出错
                    logger.error(f"索引器初始化异常: {e}")
                    logger.error(f"错误详情:\n{traceback.format_exc()}")
                    # 即使出错也继续运行，搜索时会返回错误
                    return False

            except Exception as e:
                logger.error(f"初始化索引器失败: {e}")
                logger.error(f"错误详情:\n{traceback.format_exc()}")
                # 在 MCP 环境中，即使索引器初始化失败也继续运行
                # 搜索请求会返回适当的错误信息
                self.indexer = None
                return False
        return True

    def _register_tools(self):
        """注册 MCP 工具"""

        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """返回可用工具列表"""
            return [
                Tool(
                    name="search",
                    description="Search code using natural language queries. Supports multiple programming languages and returns code snippets ranked by similarity.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query using natural language to describe the code functionality or logic you're looking for"
                            },
                            "limit": {
                                "type": "number",
                                "description": "Maximum number of results to return (default 10, range 1-100)",
                                "minimum": 1,
                                "maximum": 100,
                                "default": 10
                            },
                            "lang": {
                                "type": "string",
                                "description": "Programming language filter (optional), such as python, javascript, go, etc."
                            }
                        },
                        "required": ["query"]
                    }
                )
            ]

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """处理工具调用"""
            if name == "search":
                return await self._handle_search(arguments)
            else:
                return [TextContent(
                    type="text",
                    text=f"Error: Unknown tool '{name}'"
                )]

    async def _handle_search(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """处理搜索请求"""
        try:
            # 解析和验证输入
            search_request = SearchRequest(**arguments)
            logger.info(f"收到搜索请求: query='{search_request.query}', limit={search_request.limit}, lang={search_request.lang}")

            # 确保索引器已初始化
            if not self._ensure_indexer_initialized():
                return [TextContent(
                    type="text",
                    text="Error: Semantic search index not initialized. Please check plugin configuration and restart Claude Code."
                )]

            # Check index status
            stats = self.indexer.get_stats()
            total_chunks = stats.get("total_chunks", 0)
            if total_chunks == 0:
                return [TextContent(
                    type="text",
                    text="Error: Code index is empty. Please build code index first: run `/semantic-index` or use semantic.py script to create index."
                )]

            # 执行搜索
            threshold = self.config_data.get("similarity_threshold", 0.5)  # 默认阈值
            results = self.indexer.search(
                query=search_request.query,
                limit=search_request.limit,
                language=search_request.lang,
                threshold=threshold,
            )

            # 格式化结果
            return self._format_search_results(results, search_request)

        except Exception as e:
            logger.error(f"搜索错误: {e}")
            return [TextContent(
                type="text",
                text=f"Search failed: {str(e)}"
            )]

    def _format_search_results(self, results: List[Dict], request: SearchRequest) -> List[TextContent]:
        """格式化搜索结果"""
        if not results:
            return [TextContent(
                type="text",
                text=f"No code found related to query '{request.query}'"
            )]

        # Build result text
        output_lines = [
            f"Found {len(results)} results (query: '{request.query}')",
            "",
        ]

        for i, result in enumerate(results[:request.limit], 1):
            similarity = result.get('similarity', 0)
            file_path = result.get('file_path', '')
            start_line = result.get('start_line', 0)
            end_line = result.get('end_line', 0)
            code_type = result.get('code_type', 'block')
            name = result.get('name', '')
            code = result.get('code', '')

            # Format each result
            output_lines.extend([
                f"**Result {i}**",
                f"File: {file_path}:{start_line}-{end_line}",
                f"Similarity: {similarity:.3f}",
                f"Type: {code_type} | Name: {name}",
                "",
                "```" + (self._guess_language_from_path(file_path) or ""),
                code[:500] + ("..." if len(code) > 500 else ""),
                "```",
                ""
            ])

        return [TextContent(type="text", text="\n".join(output_lines))]

    def _guess_language_from_path(self, file_path: str) -> Optional[str]:
        """从文件路径猜测编程语言"""
        if not file_path:
            return None

        path = Path(file_path)
        ext = path.suffix.lower()

        # 语言映射
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.go': 'go',
            '.rs': 'rust',
            '.cpp': 'cpp',
            '.c': 'c',
            '.cs': 'csharp',
            '.php': 'php',
            '.rb': 'ruby',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.scala': 'scala',
            '.dart': 'dart',
            '.vue': 'vue',
            '.jsx': 'jsx',
            '.tsx': 'tsx',
            '.html': 'html',
            '.css': 'css',
            '.json': 'json',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.toml': 'toml',
            '.sql': 'sql',
            '.sh': 'bash',
            '.fish': 'fish',
            '.zsh': 'zsh',
            '.md': 'markdown',
        }

        return language_map.get(ext)

    async def run(self):
        """启动 MCP 服务器"""
        from mcp.server.stdio import stdio_server
        from mcp.server.models import InitializationOptions

        # 准备统计信息（用于初始化检查）
        self._ensure_indexer_initialized()

        # 运行服务器
        logger.info("Semantic MCP Server 启动")
        async with stdio_server() as (read_stream, write_stream):
            initialization_options = self.server.create_initialization_options()
            await self.server.run(read_stream, write_stream, initialization_options)

def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="语义搜索 MCP 服务器")
    parser.add_argument("--mcp", action="store_true", help="以 MCP 服务器模式运行")
    parser.add_argument("--debug", action="store_true", help="启用调试日志")
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.INFO)

    if args.mcp:
        # 运行 MCP 服务器
        server = SemanticMCPServer()
        asyncio.run(server.run())
    else:
        # 默认启动 MCP 服务器
        server = SemanticMCPServer()
        asyncio.run(server.run())

if __name__ == "__main__":
    main()