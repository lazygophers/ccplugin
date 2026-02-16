"""
统计和清理模块补充测试
"""

import os
import sys
import tempfile
from datetime import datetime, timedelta
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


class TestCleanMemoriesExtra:
    """测试 clean_memories 函数补充"""
    
    @pytest.mark.asyncio
    async def test_clean_unused_memories(self, db):
        from memory import create_memory, clean_memories, list_memories
        from memory.models import Memory
        
        await create_memory(uri="test://clean-unused", content="未访问记忆")
        
        memory = await Memory.first(where="uri = ?", params=("test://clean-unused",))
        old_time = (datetime.now() - timedelta(days=100)).isoformat()
        memory.last_accessed_at = old_time
        await memory.save()
        
        stats = await clean_memories(unused_days=30, dry_run=False)
        
        assert stats["archived"] >= 1
    
    @pytest.mark.asyncio
    async def test_clean_deprecated_memories(self, db):
        from memory import create_memory, deprecate_memory, clean_memories
        from memory.models import Memory
        
        await create_memory(uri="test://clean-dep", content="废弃记忆")
        await deprecate_memory("test://clean-dep")
        
        memory = await Memory.first(where="uri = ?", params=("test://clean-dep",))
        old_time = (datetime.now() - timedelta(days=100)).isoformat()
        memory.deprecated_at = old_time
        await memory.save()
        
        stats = await clean_memories(deprecated_days=30, dry_run=False)
        
        assert stats["cleaned"] >= 1
