"""
CRUD 模块测试
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


class TestCreateMemory:
    """测试 create_memory 函数"""
    
    @pytest.mark.asyncio
    async def test_create_new_memory(self, db):
        from memory import create_memory
        
        memory = await create_memory(
            uri="test://new",
            content="新记忆内容",
            priority=5,
        )
        
        assert memory.uri == "test://new"
        assert memory.content == "新记忆内容"
        assert memory.priority == 5
        assert memory.status == "active"
    
    @pytest.mark.asyncio
    async def test_create_memory_with_disclosure(self, db):
        from memory import create_memory
        
        memory = await create_memory(
            uri="test://disclosure",
            content="带触发条件的记忆",
            disclosure="当读取 test.py 时",
        )
        
        assert memory.disclosure == "当读取 test.py 时"
    
    @pytest.mark.asyncio
    async def test_create_memory_with_metadata(self, db):
        from memory import create_memory
        
        memory = await create_memory(
            uri="test://metadata",
            content="带元数据的记忆",
            metadata={"key": "value"},
        )
        
        import json
        meta = json.loads(memory.metadata)
        assert meta["key"] == "value"
    
    @pytest.mark.asyncio
    async def test_update_existing_memory(self, db):
        from memory import create_memory
        
        await create_memory(
            uri="test://update",
            content="原始内容",
            priority=5,
        )
        
        memory = await create_memory(
            uri="test://update",
            content="更新内容",
            priority=3,
        )
        
        assert memory.content == "更新内容"
        assert memory.priority == 3


class TestGetMemory:
    """测试 get_memory 函数"""
    
    @pytest.mark.asyncio
    async def test_get_existing_memory(self, db):
        from memory import create_memory, get_memory
        
        await create_memory(uri="test://get", content="获取测试")
        
        memory = await get_memory("test://get")
        
        assert memory is not None
        assert memory.content == "获取测试"
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_memory(self, db):
        from memory import get_memory
        
        memory = await get_memory("test://nonexistent")
        
        assert memory is None
    
    @pytest.mark.asyncio
    async def test_get_memory_increments_access_count(self, db):
        from memory import create_memory, get_memory
        
        await create_memory(uri="test://access", content="访问计数测试")
        initial_count = (await get_memory("test://access", increment_access=False)).access_count
        
        await get_memory("test://access")
        memory = await get_memory("test://access", increment_access=False)
        
        assert memory.access_count == initial_count + 1
    
    @pytest.mark.asyncio
    async def test_get_memory_without_increment(self, db):
        from memory import create_memory, get_memory
        
        await create_memory(uri="test://no-increment", content="不增加计数")
        initial = await get_memory("test://no-increment", increment_access=False)
        
        memory = await get_memory("test://no-increment", increment_access=False)
        
        assert memory.access_count == initial.access_count


class TestUpdateMemory:
    """测试 update_memory 函数"""
    
    @pytest.mark.asyncio
    async def test_update_content(self, db):
        from memory import create_memory, update_memory
        
        await create_memory(uri="test://update-content", content="原始内容")
        
        memory = await update_memory("test://update-content", content="新内容")
        
        assert memory.content == "新内容"
    
    @pytest.mark.asyncio
    async def test_update_priority(self, db):
        from memory import create_memory, update_memory
        
        await create_memory(uri="test://update-priority", content="内容", priority=5)
        
        memory = await update_memory("test://update-priority", priority=1)
        
        assert memory.priority == 1
    
    @pytest.mark.asyncio
    async def test_update_disclosure(self, db):
        from memory import create_memory, update_memory
        
        await create_memory(uri="test://update-disclosure", content="内容")
        
        memory = await update_memory("test://update-disclosure", disclosure="新触发条件")
        
        assert memory.disclosure == "新触发条件"
    
    @pytest.mark.asyncio
    async def test_update_append_mode(self, db):
        from memory import create_memory, update_memory
        
        await create_memory(uri="test://append", content="原始内容")
        
        memory = await update_memory("test://append", content="追加内容", append=True)
        
        assert "原始内容" in memory.content
        assert "追加内容" in memory.content
    
    @pytest.mark.asyncio
    async def test_update_replace_text(self, db):
        from memory import create_memory, update_memory
        
        await create_memory(uri="test://replace", content="Hello World")
        
        memory = await update_memory("test://replace", old_text="World", new_text="Python")
        
        assert memory.content == "Hello Python"
    
    @pytest.mark.asyncio
    async def test_update_nonexistent_memory(self, db):
        from memory import update_memory
        
        memory = await update_memory("test://nonexistent", content="内容")
        
        assert memory is None


class TestDeleteMemory:
    """测试 delete_memory 函数"""
    
    @pytest.mark.asyncio
    async def test_soft_delete(self, db):
        from memory import create_memory, delete_memory, get_memory
        
        await create_memory(uri="test://soft-delete", content="软删除测试")
        
        result = await delete_memory("test://soft-delete", soft=True)
        
        assert result is True
        
        memory = await get_memory("test://soft-delete")
        assert memory is None
    
    @pytest.mark.asyncio
    async def test_hard_delete(self, db):
        from memory import create_memory, delete_memory, get_memory
        from memory.models import Memory
        
        await create_memory(uri="test://hard-delete", content="硬删除测试")
        
        result = await delete_memory("test://hard-delete", soft=False)
        
        assert result is True
        
        memory = await Memory.first(where="uri = ?", params=("test://hard-delete",))
        assert memory is None
    
    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, db):
        from memory import delete_memory
        
        result = await delete_memory("test://nonexistent")
        
        assert result is False
