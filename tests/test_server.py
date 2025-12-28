"""MCP Server 测试."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from market.server import MarketServer
from market.config import config


@pytest.fixture
def market_server():
    """创建 server 实例用于测试."""
    return MarketServer()


@pytest.mark.asyncio
async def test_server_initialization(market_server):
    """测试服务器初始化."""
    assert market_server.server is not None
    assert market_server.server.name == "market-server"


@pytest.mark.asyncio
async def test_memory_store(market_server):
    """测试记忆存储功能."""
    result = await market_server._handle_memory_store({
        "content": "测试记忆内容",
        "tags": ["test", "memory"],
        "metadata": {"source": "test"}
    })

    assert result.isError is False
    assert "已存储记忆" in result.content[0].text


@pytest.mark.asyncio
async def test_memory_search(market_server):
    """测试记忆搜索功能."""
    result = await market_server._handle_memory_search({
        "query": "测试查询",
        "tags": ["test"],
        "limit": 5
    })

    assert result.isError is False
    assert "搜索记忆" in result.content[0].text


@pytest.mark.asyncio
async def test_context_save(market_server):
    """测试上下文保存功能."""
    result = await market_server._handle_context_save({
        "session_id": "test-session",
        "content": "测试上下文",
        "role": "user"
    })

    assert result.isError is False
    assert "已保存上下文" in result.content[0].text


@pytest.mark.asyncio
async def test_context_retrieve(market_server):
    """测试上下文检索功能."""
    result = await market_server._handle_context_retrieve({
        "session_id": "test-session",
        "limit": 20
    })

    assert result.isError is False
    assert "检索会话上下文" in result.content[0].text


@pytest.mark.asyncio
async def test_task_create(market_server):
    """测试任务创建功能."""
    result = await market_server._handle_task_create({
        "title": "测试任务",
        "description": "这是一个测试任务",
        "priority": 1,
        "tags": ["test"]
    })

    assert result.isError is False
    assert "已创建任务" in result.content[0].text


@pytest.mark.asyncio
async def test_task_list(market_server):
    """测试任务列表功能."""
    result = await market_server._handle_task_list({
        "status": "open",
        "tags": ["test"]
    })

    assert result.isError is False
    assert "任务列表" in result.content[0].text


@pytest.mark.asyncio
async def test_knowledge_add(market_server):
    """测试知识添加功能."""
    result = await market_server._handle_knowledge_add({
        "content": "测试知识内容",
        "source": "test_source",
        "metadata": {"category": "test"}
    })

    assert result.isError is False
    assert "已添加知识" in result.content[0].text


@pytest.mark.asyncio
async def test_knowledge_search(market_server):
    """测试知识搜索功能."""
    result = await market_server._handle_knowledge_search({
        "query": "测试查询",
        "limit": 5
    })

    assert result.isError is False
    assert "知识库搜索" in result.content[0].text


def test_config_validation():
    """测试配置验证."""
    config.validate()
    assert config.log_level in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
    assert config.max_timeout > 0
