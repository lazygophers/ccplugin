"""Memory Server 单元测试."""

import pytest
from mcp.types import CallToolRequest, CallToolRequestParams

from memory.server import MemoryServer


@pytest.fixture
def memory_server():
    """创建测试用 MemoryServer 实例."""
    return MemoryServer()


@pytest.mark.asyncio
async def test_list_tools(memory_server):
    """测试工具列表."""
    tools = await memory_server.server._tool_manager.list_tools()  # type: ignore

    assert len(tools) == 2
    tool_names = [t.name for t in tools]
    assert "memory_store" in tool_names
    assert "memory_search" in tool_names


@pytest.mark.asyncio
async def test_memory_store(memory_server):
    """测试记忆存储."""
    result = await memory_server._handle_memory_store({
        "content": "测试记忆内容",
        "tags": ["test", "memory"],
        "metadata": {"source": "test"}
    })

    assert result.isError is False
    assert len(result.content) == 1
    assert "已存储记忆" in result.content[0].text
    assert "测试记忆内容" in result.content[0].text


@pytest.mark.asyncio
async def test_memory_store_minimal(memory_server):
    """测试最小参数的记忆存储."""
    result = await memory_server._handle_memory_store({
        "content": "简单记忆"
    })

    assert result.isError is False
    assert "已存储记忆" in result.content[0].text


@pytest.mark.asyncio
async def test_memory_search(memory_server):
    """测试记忆搜索."""
    result = await memory_server._handle_memory_search({
        "query": "测试查询",
        "tags": ["test"],
        "limit": 5
    })

    assert result.isError is False
    assert "搜索记忆" in result.content[0].text
    assert "测试查询" in result.content[0].text


@pytest.mark.asyncio
async def test_memory_search_minimal(memory_server):
    """测试最小参数的记忆搜索."""
    result = await memory_server._handle_memory_search({
        "query": "测试"
    })

    assert result.isError is False
    assert "搜索记忆" in result.content[0].text
