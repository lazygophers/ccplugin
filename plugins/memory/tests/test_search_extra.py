"""
搜索模块补充测试
"""

import os
import sys
import tempfile
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))


@pytest.fixture
async def db():
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("memory.database.get_project_plugins_dir", return_value=tmpdir):
            from memory.database import init_db, close_db
            import memory.database as db_module
            db_module._db_initialized = False
            
            await init_db()
            
            yield
            
            await close_db()
            db_module._db_initialized = False


class TestSearchMemoriesExtra:
    """测试 search_memories 函数补充"""
    
    @pytest.mark.asyncio
    async def test_search_with_status(self, db):
        from memory import create_memory, search_memories, deprecate_memory
        
        await create_memory(uri="test://status-active", content="活跃记忆")
        await create_memory(uri="test://status-dep", content="废弃记忆")
        await deprecate_memory("test://status-dep")
        
        results = await search_memories("", status="deprecated")
        
        assert all(r.status == "deprecated" for r in results)
    
    @pytest.mark.asyncio
    async def test_search_with_priority_min_only(self, db):
        from memory import create_memory, search_memories
        
        await create_memory(uri="test://prio-min", content="测试", priority=8)
        
        results = await search_memories("", priority_min=5)
        
        for r in results:
            assert r.priority >= 5
    
    @pytest.mark.asyncio
    async def test_search_with_priority_max_only(self, db):
        from memory import create_memory, search_memories
        
        await create_memory(uri="test://prio-max", content="测试", priority=2)
        
        results = await search_memories("", priority_max=5)
        
        for r in results:
            assert r.priority <= 5


class TestListMemoriesExtra:
    """测试 list_memories 函数补充"""
    
    @pytest.mark.asyncio
    async def test_list_with_status(self, db):
        from memory import create_memory, list_memories, deprecate_memory
        
        await create_memory(uri="test://list-active", content="活跃")
        await create_memory(uri="test://list-dep", content="废弃")
        await deprecate_memory("test://list-dep")
        
        results = await list_memories(status="deprecated")
        
        assert all(r.status == "deprecated" for r in results)
    
    @pytest.mark.asyncio
    async def test_list_with_priority_filters(self, db):
        from memory import create_memory, list_memories
        
        await create_memory(uri="test://list-p1", content="测试", priority=1)
        await create_memory(uri="test://list-p5", content="测试", priority=5)
        await create_memory(uri="test://list-p10", content="测试", priority=10)
        
        results = await list_memories(priority_min=3, priority_max=7)
        
        for r in results:
            assert 3 <= r.priority <= 7
