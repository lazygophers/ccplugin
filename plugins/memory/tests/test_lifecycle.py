"""
生命周期管理模块测试
"""

import os
import sys
import tempfile
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))


@pytest.fixture
async def db_with_memory():
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("memory.database.get_project_plugins_dir", return_value=tmpdir):
            from memory.database import init_db, close_db
            from memory import create_memory
            import memory.database as db_module
            db_module._db_initialized = False
            
            await init_db()
            
            await create_memory(uri="test://lifecycle", content="生命周期测试", priority=5)
            
            yield
            
            await close_db()
            db_module._db_initialized = False


class TestSetPriority:
    """测试 set_priority 函数"""
    
    @pytest.mark.asyncio
    async def test_set_valid_priority(self, db_with_memory):
        from memory import set_priority
        
        memory = await set_priority("test://lifecycle", 1)
        
        assert memory.priority == 1
    
    @pytest.mark.asyncio
    async def test_set_priority_boundary_0(self, db_with_memory):
        from memory import set_priority
        
        memory = await set_priority("test://lifecycle", 0)
        
        assert memory.priority == 0
    
    @pytest.mark.asyncio
    async def test_set_priority_boundary_10(self, db_with_memory):
        from memory import set_priority
        
        memory = await set_priority("test://lifecycle", 10)
        
        assert memory.priority == 10
    
    @pytest.mark.asyncio
    async def test_set_invalid_priority_low(self, db_with_memory):
        from memory import set_priority
        
        with pytest.raises(ValueError):
            await set_priority("test://lifecycle", -1)
    
    @pytest.mark.asyncio
    async def test_set_invalid_priority_high(self, db_with_memory):
        from memory import set_priority
        
        with pytest.raises(ValueError):
            await set_priority("test://lifecycle", 11)
    
    @pytest.mark.asyncio
    async def test_set_priority_nonexistent(self, db_with_memory):
        from memory import set_priority
        
        memory = await set_priority("test://nonexistent", 5)
        
        assert memory is None


class TestDeprecateMemory:
    """测试 deprecate_memory 函数"""
    
    @pytest.mark.asyncio
    async def test_deprecate(self, db_with_memory):
        from memory import deprecate_memory, get_memory
        from memory.models import MemoryStatus
        
        memory = await deprecate_memory("test://lifecycle")
        
        assert memory.status == MemoryStatus.DEPRECATED.value
        assert memory.deprecated_at is not None
    
    @pytest.mark.asyncio
    async def test_deprecate_with_reason(self, db_with_memory):
        from memory import deprecate_memory
        
        memory = await deprecate_memory("test://lifecycle", reason="已过时")
        
        import json
        meta = json.loads(memory.metadata)
        assert meta.get("deprecation_reason") == "已过时"
    
    @pytest.mark.asyncio
    async def test_deprecate_nonexistent(self, db_with_memory):
        from memory import deprecate_memory
        
        memory = await deprecate_memory("test://nonexistent")
        
        assert memory is None


class TestArchiveMemory:
    """测试 archive_memory 函数"""
    
    @pytest.mark.asyncio
    async def test_archive(self, db_with_memory):
        from memory import archive_memory
        from memory.models import MemoryStatus
        
        memory = await archive_memory("test://lifecycle")
        
        assert memory.status == MemoryStatus.ARCHIVED.value
    
    @pytest.mark.asyncio
    async def test_archive_nonexistent(self, db_with_memory):
        from memory import archive_memory
        
        memory = await archive_memory("test://nonexistent")
        
        assert memory is None


class TestRestoreMemory:
    """测试 restore_memory 函数"""
    
    @pytest.mark.asyncio
    async def test_restore(self, db_with_memory):
        from memory import archive_memory, restore_memory
        from memory.models import MemoryStatus
        
        await archive_memory("test://lifecycle")
        memory = await restore_memory("test://lifecycle")
        
        assert memory.status == MemoryStatus.ACTIVE.value
        assert memory.deprecated_at is None
    
    @pytest.mark.asyncio
    async def test_restore_nonexistent(self, db_with_memory):
        from memory import restore_memory
        
        memory = await restore_memory("test://nonexistent")
        
        assert memory is None
