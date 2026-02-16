"""
统计和清理模块测试
"""

import os
import sys
import tempfile
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))


@pytest.fixture
async def db_with_stats():
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("memory.database.get_project_plugins_dir", return_value=tmpdir):
            from memory.database import init_db, close_db
            from memory import create_memory, deprecate_memory, archive_memory
            import memory.database as db_module
            db_module._db_initialized = False
            
            await init_db()
            
            await create_memory(uri="project://stat1", content="统计测试1", priority=1)
            await create_memory(uri="project://stat2", content="统计测试2", priority=5)
            await create_memory(uri="user://stat3", content="统计测试3", priority=5)
            await create_memory(uri="test://deprecated", content="已废弃")
            await deprecate_memory("test://deprecated")
            await create_memory(uri="test://archived", content="已归档")
            await archive_memory("test://archived")
            
            yield
            
            await close_db()
            db_module._db_initialized = False


class TestGetStats:
    """测试 get_stats 函数"""
    
    @pytest.mark.asyncio
    async def test_get_stats_returns_dict(self, db_with_stats):
        from memory import get_stats
        
        stats = await get_stats()
        
        assert isinstance(stats, dict)
    
    @pytest.mark.asyncio
    async def test_get_stats_has_required_fields(self, db_with_stats):
        from memory import get_stats
        
        stats = await get_stats()
        
        assert "total" in stats
        assert "active" in stats
        assert "deprecated" in stats
        assert "archived" in stats
        assert "by_priority" in stats
        assert "by_uri_prefix" in stats
        assert "versions_count" in stats
        assert "relations_count" in stats
    
    @pytest.mark.asyncio
    async def test_get_stats_counts(self, db_with_stats):
        from memory import get_stats
        
        stats = await get_stats()
        
        assert stats["active"] >= 3
        assert stats["deprecated"] >= 1
        assert stats["archived"] >= 1


class TestCleanMemories:
    """测试 clean_memories 函数"""
    
    @pytest.mark.asyncio
    async def test_clean_dry_run(self, db_with_stats):
        from memory import clean_memories
        
        stats = await clean_memories(unused_days=0, deprecated_days=0, dry_run=True)
        
        assert "cleaned" in stats
        assert "archived" in stats
    
    @pytest.mark.asyncio
    async def test_clean_no_params(self, db_with_stats):
        from memory import clean_memories
        
        stats = await clean_memories()
        
        assert stats["cleaned"] == 0
        assert stats["archived"] == 0
