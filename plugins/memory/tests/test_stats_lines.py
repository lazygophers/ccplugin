"""
统计模块补充测试 - 覆盖缺失行
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


class TestCleanMemoriesLines:
    """测试 clean_memories 覆盖缺失行"""
    
    @pytest.mark.asyncio
    async def test_clean_unused_dry_run_true(self, db):
        from memory import create_memory, clean_memories
        from memory.models import Memory
        
        await create_memory(uri="test://dry-run", content="测试")
        
        memory = await Memory.first(where="uri = ?", params=("test://dry-run",))
        old_time = (datetime.now() - timedelta(days=100)).isoformat()
        memory.last_accessed_at = old_time
        await memory.save()
        
        stats = await clean_memories(unused_days=30, dry_run=True)
        
        assert stats["cleaned"] >= 1
    
    @pytest.mark.asyncio
    async def test_clean_deprecated_dry_run_true(self, db):
        from memory import create_memory, deprecate_memory, clean_memories
        from memory.models import Memory
        
        await create_memory(uri="test://dep-dry", content="测试")
        await deprecate_memory("test://dep-dry")
        
        memory = await Memory.first(where="uri = ?", params=("test://dep-dry",))
        old_time = (datetime.now() - timedelta(days=100)).isoformat()
        memory.deprecated_at = old_time
        await memory.save()
        
        stats = await clean_memories(deprecated_days=30, dry_run=True)
        
        assert stats["cleaned"] >= 1
