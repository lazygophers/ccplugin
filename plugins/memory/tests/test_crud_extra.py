"""
CRUD 模块补充测试
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


class TestUpdateMemoryExtra:
    """测试 update_memory 函数补充"""
    
    @pytest.mark.asyncio
    async def test_update_with_metadata(self, db):
        from memory import create_memory, update_memory, get_memory
        
        await create_memory(uri="test://meta", content="测试")
        
        memory = await update_memory("test://meta", metadata={"key": "value"})
        
        import json
        meta = json.loads(memory.metadata)
        assert meta["key"] == "value"
    
    @pytest.mark.asyncio
    async def test_update_merge_metadata(self, db):
        from memory import create_memory, update_memory
        
        await create_memory(uri="test://meta-merge", content="测试", metadata={"a": 1})
        
        memory = await update_memory("test://meta-merge", metadata={"b": 2})
        
        import json
        meta = json.loads(memory.metadata)
        assert meta["a"] == 1
        assert meta["b"] == 2
