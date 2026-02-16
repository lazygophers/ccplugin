"""
关系管理模块补充测试
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
            from memory import create_memory
            import memory.database as db_module
            db_module._db_initialized = False
            
            await init_db()
            
            await create_memory(uri="test://source", content="源记忆")
            await create_memory(uri="test://target", content="目标记忆")
            
            yield
            
            await close_db()
            db_module._db_initialized = False


class TestRemoveRelationExtra:
    """测试 remove_relation 函数补充"""
    
    @pytest.mark.asyncio
    async def test_remove_relation_nonexistent_memory(self, db):
        from memory import remove_relation
        from memory.models import RelationType
        
        result = await remove_relation("test://nonexistent", "test://target", RelationType.RELATES_TO)
        
        assert result is False
