"""
搜索模块测试
"""

import os
import sys
import tempfile
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))


@pytest.fixture
async def db_with_memories():
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("memory.database.get_project_plugins_dir", return_value=tmpdir):
            from memory.database import init_db, close_db
            from memory import create_memory
            import memory.database as db_module
            db_module._db_initialized = False
            
            await init_db()
            
            await create_memory(uri="project://alpha", content="项目 Alpha 的描述", priority=1)
            await create_memory(uri="project://beta", content="项目 Beta 的描述", priority=2)
            await create_memory(uri="user://john", content="用户 John 的信息", priority=3)
            await create_memory(uri="task://review", content="代码审查任务", priority=5)
            
            yield
            
            await close_db()
            db_module._db_initialized = False


class TestSearchMemories:
    """测试 search_memories 函数"""
    
    @pytest.mark.asyncio
    async def test_search_by_keyword(self, db_with_memories):
        from memory import search_memories
        
        results = await search_memories("项目")
        
        assert len(results) >= 2
    
    @pytest.mark.asyncio
    async def test_search_with_uri_prefix(self, db_with_memories):
        from memory import search_memories
        
        results = await search_memories("", uri_prefix="project://")
        
        assert all(r.uri.startswith("project://") for r in results)
    
    @pytest.mark.asyncio
    async def test_search_with_priority_range(self, db_with_memories):
        from memory import search_memories
        
        results = await search_memories("", priority_min=1, priority_max=3)
        
        for r in results:
            assert 1 <= r.priority <= 3
    
    @pytest.mark.asyncio
    async def test_search_with_limit(self, db_with_memories):
        from memory import search_memories
        
        results = await search_memories("", limit=2)
        
        assert len(results) <= 2
    
    @pytest.mark.asyncio
    async def test_search_no_results(self, db_with_memories):
        from memory import search_memories
        
        results = await search_memories("不存在的关键词xyz123")
        
        assert len(results) == 0


class TestListMemories:
    """测试 list_memories 函数"""
    
    @pytest.mark.asyncio
    async def test_list_all(self, db_with_memories):
        from memory import list_memories
        
        results = await list_memories()
        
        assert len(results) >= 4
    
    @pytest.mark.asyncio
    async def test_list_with_uri_prefix(self, db_with_memories):
        from memory import list_memories
        
        results = await list_memories(uri_prefix="user://")
        
        assert all(r.uri.startswith("user://") for r in results)
    
    @pytest.mark.asyncio
    async def test_list_with_pagination(self, db_with_memories):
        from memory import list_memories
        
        page1 = await list_memories(limit=2, offset=0)
        page2 = await list_memories(limit=2, offset=2)
        
        assert len(page1) <= 2
        assert len(page2) <= 2


class TestGetMemoriesByPriority:
    """测试 get_memories_by_priority 函数"""
    
    @pytest.mark.asyncio
    async def test_get_high_priority(self, db_with_memories):
        from memory import get_memories_by_priority
        
        results = await get_memories_by_priority(max_priority=3)
        
        for r in results:
            assert r.priority <= 3
            assert r.status == "active"
    
    @pytest.mark.asyncio
    async def test_get_empty_result(self, db_with_memories):
        from memory import get_memories_by_priority
        
        results = await get_memories_by_priority(max_priority=0)
        
        assert len(results) == 0
